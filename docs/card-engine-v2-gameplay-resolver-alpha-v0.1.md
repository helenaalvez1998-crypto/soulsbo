# Card Engine v2 — resolvedor de gameplay alpha v0.1

**Status:** primeiro vertical funcional de gameplay, isolado.  
**Base:** pacote de persistência Card Engine v2 + contratos dos Grupos A–F aprovados.  
**Runtime legado:** não modificado.  
**Integração de produção:** não realizada.

## Entregue nesta etapa

O `GameplayResolver` recebe registries fornecidos pelo servidor e executa quatro tipos de ação:

| `action_type` | Resultado funcional |
|---|---|
| `unit.remove` | Remoção/execução com causa canônica, proteção, contadores, eventos e Vingança |
| `unit.sacrifice` | Sacrifício explícito, ignorando escudos, com contador e Vingança após sucesso |
| `unit.move` | Movimento de uma instância própria no campo para fileira autorizada |
| `unit.grant_bonus` | Concessão de bônus definida por configuração confiável |
| `unit.grant_protection` | Concessão de proteção definida por configuração confiável |

São cinco `action_type` porque remoção e sacrifício são caminhos distintos no contrato.

### Seleção e ofertas

- `target_offer_for_action()` escolhe a policy associada ao tipo de ação e, quando aplicável, à causa de remoção.
- `build_target_offer()` calcula elegibilidade, métricas disponíveis, ordenação, quantidade e prévia de alvos secundários no servidor.
- A oferta inclui `state_revision`; a chamada que confirma a ação deve usar essa revisão em `expected_revision`.
- O handler recalcula a oferta e valida cada `target_instance_id` contra a seleção resultante. Valores de poder, parâmetros de efeito, perfil de proteção, cargas e duração enviados pelo cliente são rejeitados/ignorados conforme o contrato da ação.
- `manual_primary_auto_fill` mostra o alvo primário e a prévia de alvos adicionais; a confirmação envia somente o alvo primário e o servidor recalcula a seleção completa.

### Remoção, proteção e Vingança

- Causas aceitas vêm da configuração fechada da ação e do conjunto canônico de causas.
- Execução pode utilizar uma policy de seleção diferente de remoção comum por meio de `cause_target_policy_ids`.
- Proteção só bloqueia causas declaradas pelo `ProtectionProfile`; sacrifício ignora proteção.
- Um grant consumido perde uma carga; grant de carga zero é removido. O resultado registra IDs dos grants consumidos.
- Prioridade: menor sequência do evento de concessão; em empate, menor `grant_id`. Se o evento histórico não existir, a ação falha fechada.
- Todos os resultados diretos de uma remoção multi-alvo são finalizados antes de gerar efeitos reativos.
- Vingança só ocorre para uma unidade removida com sucesso. É um evento `reactive`, ligado ao evento direto por `caused_by_event_ids`, e concede grants independentes aos aliados sobreviventes na fileira da remoção.
- Remoções bloqueadas não disparam Vingança. Sacrifício ignora escudo e, quando bem-sucedido, dispara Vingança.

### Movimento e bônus

- Movimento exige alvo próprio no campo e uma fileira destino autorizada pelo registry da ação.
- Bônus usa valor, duração e `bonus_clamp_policy_id` definidos no servidor; o cliente não pode substituí-los.
- Proteção usa perfil, cargas e duração definidos no servidor; o cliente não pode substituí-los.
- Cada ação grava eventos de domínio e atualiza snapshot, ledger e journal na mesma unidade transacional do repositório.

## Interface interna

O formato interno entregue a `GameplayResolver.execute()` é:

```python
request = {
    "operation_id": "<UUIDv4>",
    "actor": {"type": "player", "player_id": "1001"},
    "expected_revision": 0,
    "action_type": "unit.remove",
    "payload": {
        "source_instance_id": "<instance UUIDv4>",
        "cause_id": "normal_removal",
        "selection": {
            "mode": "manual_set",
            "target_instance_ids": ["<target instance UUIDv4>"],
        },
    },
}
receipt = resolver.execute(repository, match_id, request)
```

O request é validado e executado pelo `SQLiteMatchRepository`. `BEGIN IMMEDIATE`, idempotência, CAS e gravação de eventos ocorrem na mesma transação. Repetição idêntica de `operation_id` retorna o resultado salvo; fingerprint diferente causa conflito. Revisão desatualizada é registrada como rejeição sem avanço de estado.

## Validação

- Runner: `docs/scripts/test-card-engine-v2-alpha-v0.1.py`.
- Resultado atual: 62/62 testes aprovados.
- Cobertura inclui ofertas autoritativas, políticas por causa, preview de alvos secundários, remoção, execução, sacrifício, escudos, Vingança, remoção multi-alvo, movimento, bônus, concessão de proteção, proteção contra parâmetros enviados pelo cliente, idempotência e validação dos schemas de request/result/offer.
- As verificações são locais e sintéticas. Não são uma suite de integração com Discord/API/UI nem com o banco publicado.

## Limites conhecidos e próximos módulos

1. **Catálogo real:** falta carregar `ActionDefinition`, `TargetPolicy` e `ProtectionProfile` de um release validado e ligar cada carta/efeito real a esses registries.
2. **Métricas efetivas:** ainda não há cálculo canônico de poder efetivo com clima e estados; policies `effective_power` exigem um `metric_resolver` confiável, vinculado ao release. Sem isso, a seleção falha fechada.
3. **Clamp:** `bonus_clamp_policy_id` é rastreado como metadado, mas seu algoritmo não foi implementado.
4. **Custos de turno:** o resultado tem os campos previstos no contrato, mas turnos, ativações e custos genéricos ainda não existem no state machine; somente cargas de proteção e consumo de carta-fonte configurado são aplicados.
5. **Consumo de fonte:** nesta alpha está implementado para ações de remoção/sacrifício e a fonte consumível deve estar na mão.
6. **Gameplay restante:** combate/dano, combos, líderes, clima, fases/turnos, `round_close` global e restante do catálogo estão fora desta fatia.
7. **Operação assíncrona:** o repositório continua `sqlite3` síncrono; falta adapter/worker antes do uso no event loop real.
8. **Produção:** não foram executados migração, cutover, smoke test do banco do bot ou entrega real da outbox.

O próximo bloco de código deve carregar um subconjunto de cartas/efeitos reais, implementar o cálculo de poder efetivo e executar uma batalha de teste ponta a ponta inteiramente no engine v2 isolado.

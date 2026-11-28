# Aprovação do Grupo C — ciclo de vida, estados e duração v0.1

**Data do registro:** 2026-11-27  
**Baseline revisado:** `soulsbo-main-continuity-2026-11-27-rev10.zip`  
**Status:** `OWNER_APPROVED`  
**Evidência de aprovação:** resposta explícita do proprietário: “aprovo”, enviada imediatamente após a pergunta de aprovação das dez resoluções do Grupo C, inclusive `vigil_seal` com expiração `board_exit`.  
**Runtime/DB/API/frontend alterados:** não.  
**Contrato congelado:** não; `CardInstance v0.4` é draft documental.

## 1. Escopo aprovado

O aceite cobre as dez resoluções recomendadas no parecer `card-game-state-lifecycle-group-C-review-v0.1.md`, conforme o campo `recommended_resolution` de `card-game-state-lifecycle-group-C-decisions-v0.1.json`:

| ID | Decisão aprovada | Regra aprovada |
|---|---|---|
| CI-008 | Limpeza explícita por transição e rodada | `round_close` ocorre depois do snapshot imutável de pontuação/resultado; expira apenas grants marcados `round_close`, em todas as zonas e também na rodada terminal. Grants `permanent_instance` permanecem. Bônus ativos de unidades removidas podem permanecer no descarte até a expiração declarada. |
| CI-009 | Resistência climática separada | `intrinsic_weather_resistance` pertence ao `DefinitionSnapshot`; modificadores pertencem à instância e registram origem, valor, evento de aplicação e expiração. O escalar legado `weather_resist` não é canônico. |
| BUF-008 | Semântica de fileiras separada | `printed_row` é imutável; `current_row` é `null` fora de `board`; `last_board_row` é projeção persistida da última posição válida; `last_unit_play_row` é estado do jogador/rodada e muda apenas após jogada bem-sucedida de unidade. |
| BUF-009 | Proteção por categoria | O perfil padrão bloqueia `unit_removal` e `execution`; `sacrifice` faz bypass. Status e debuffs não são bloqueados por padrão. Noite/Chama e Lâmina Negra permanecem exceções explícitas por efeito, sem imunidade universal. |
| BUF-010 | Resolver central e custos separados | Bloqueio compatível consome exatamente uma carga do grant correspondente. O custo da carta/relíquia é independente: Noite/Chama consome a ativação quando bloqueada; Lâmina Negra não consome/devolve a ativação quando bloqueada. |
| BUF-011 | Duração do Selo de Vigília | `vigil_seal` cria modificador `expires_on=board_exit`; a resistência não sobrevive à saída do campo por inferência acidental do escalar legado. O branch genérico sem binding ativo continua fora do catálogo novo, conforme BUF-012. |
| BUF-014 | Bônus rastreáveis e clamp explícito | Bônus são projeções de grants rastreáveis com delta, origem, evento, expiração e `clamp_policy_id`. Cada efeito/release declara sua política; não existe piso/teto global implícito. |
| RSRX-07 | Política de bônus no retorno | Ressurgir e Réquiem usam `reset_to_zero`; Esgar usa `previous_bonus_plus_one`, com o +1 representado por grant/evento separado. Lágrima Sagrada é recuperação para a mão, não ressurreição. |
| RSRX-08 | Política de fileira no retorno | Ressurgir/Réquiem usam `last_board_row`; se ausente/inválida, usam fileira solicitada válida e depois `melee`. Esgar força a fileira solicitada válida; valor ausente/inválido é rejeitado, sem fallback silencioso. |
| RSRX-10 | Normalização no retorno | Retorno ao campo limpa aplicações de status e grants de proteção, aplica a política de bônus/fileira do efeito, preserva resistência intrínseca e grants `round_close` ainda ativos/`permanent_instance`, e não repete hooks on-play, passiva de facção ou combo na chegada. |

## 2. Limites do aceite

A aprovação não transforma evidência do legado em regra intencional. Em especial, a persistência histórica de `weather_resist` não é mantida: a duração `board_exit` do Selo de Vigília é a regra nova aprovada.

Também não aprova:

- os limites numéricos finais, ordem de empilhamento e regras de limiar dos estados negativos que ainda dependem de revisão do registry/ruleset;
- a lista final de causas que ativam Vingança (Grupo F);
- as políticas completas de seleção, fallback, alvo parcial e outcomes de operação (Grupo D);
- persistência concorrente, CAS/locks reais, migração de snapshots e testes de banco (Grupo E);
- números finais de balanceamento, `clamp_policy_id` concretos para cada efeito, nem publicação de releases.

O limite de marcas, transições de limiar e comportamento repetido de Malenia/Oráculo da Geada continuam dependentes da revisão específica dos estados; esta aprovação fecha rastreabilidade, expiração e política de purificação seletiva, não esses números/efeitos.

## 3. Consequência documental

Os Grupos A, B e C podem ser tratados como aprovados para elaborar `CardInstance v0.4` como draft. O schema v4 deste pacote é uma proposta estrutural coerente com os aceites, mas ainda não está congelado, porque D/F/E permanecem abertos e algumas políticas de balanceamento/estados ainda requerem release versionado.

`round_close` deve ser representado no ledger de eventos: primeiro um evento de pontuação com snapshot imutável; depois o evento global de fechamento; depois os eventos de expiração/limpeza por instância e grant afetados. O `round_close` também ocorre na última rodada. Grants explicitamente permanentes não são apagados por ele.

## 4. Guardrail permanente

Nenhum aceite desta revisão autoriza alterar `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`, catálogo ativo, resolvedores candidatos ou schema de produção. Não iniciar migrador nem integrar `CardInstance` ao jogo até fechar os grupos D/F/E e validar a persistência transacional real.


## Contrato subsequente

As resoluções aprovadas foram incorporadas ao draft `docs/card-game-card-instance-contract-v0.4.md`, schema `docs/schemas/card-game-card-instance-match.schema.v4.json` e fixture v4. A validação documental do draft registrou 72/72 casos; ver `docs/card-game-card-instance-contract-validation-v0.4.md`. Essa validação não congela o contrato nem autoriza integração.

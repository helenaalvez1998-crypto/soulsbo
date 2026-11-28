# Grupo B — auditoria de snapshot de definição e causalidade v0.1

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev7.zip`  
**Status:** `AUDIT_COMPLETE; GROUP_B_OWNER_APPROVED; RUNTIME_NOT_MODIFIED`  
**Escopo:** CI-005, CI-011, BUF-001, BUF-002, BUF-012, RSRX-03 e RSRX-05.  
**Integração:** nenhuma. O motor, o banco, o catálogo ativo, os handlers e o frontend permanecem inalterados.

## 1. Síntese executiva

O pacote já contém snapshots históricos, schemas candidatos e contratos de `definition_snapshot`, mas ainda não possui um manifesto imutável de release que permita reconstruir de forma inequívoca quais definições, efeitos e regras de balanceamento regeram uma partida. No runtime legado, `novo_estado()` não fixa versões nem digests por partida, e as instâncias recebidas do deck não carregam `definition_snapshot`.

O motor também não registra causalidade estruturada. `event_log` conserva até 20 mensagens descritivas em texto; `aplicar_jogada()` não recebe `operation_id` nem contexto de evento; `_remover_unidade()` executa Vingança sincronamente, sem criar evento-filho identificável.

O defeito mais claro da interação raridade/causalidade foi reproduzido: Chama Negra Épica provoca uma remoção; a unidade removida tem Vingança; a reação concede +1 aos sobreviventes; depois, o amplificador de raridade varre as diferenças globais de bônus e acrescenta outro +1 ao primeiro sobrevivente elegível na ordem do tabuleiro. A raridade da carta de remoção acaba ampliando um efeito reativo que não foi produzido diretamente por ela.

Rykard confirma uma cadeia distinta: o sacrifício chama `_remover_unidade()`, Vingança é resolvida durante a remoção e, em seguida, o líder concede +2 aos sobreviventes. Com a vítima tendo Vingança, os sobreviventes recebem +1 reativo e +2 direto, totalizando +3. A ação de líder de Rykard não passa pelo amplificador de raridade; as duas origens de bônus são independentes.

## 2. Evidências verificadas

### 2.1 Snapshot e versionamento

| Evidência | Observado | Implicação |
|---|---|---|
| `data/card_game/catalog-legacy-baseline-v0.1.json` | `snapshot_type=legacy_catalog_baseline`, `snapshot_version=0.1`, status `historical_snapshot_not_runtime_source_of_truth`; contém SHA-256 de arquivos-fonte | Os hashes documentam proveniência do código histórico; não identificam um release de catálogo/regras aprovado e compilado. |
| `data/card_game/effect-registry-candidate.v1.json` | `schema_version=1`, 54 efeitos candidatos; sem `release_id` ou digest de conteúdo | `schema_version` descreve o formato; o arquivo continua candidato, não é release imutável. |
| `docs/card-game-canonical-model-v1.md` | Prevê `balance_rules_version` como saída do compilador depois da aprovação do balanceamento | A versão de balanceamento ainda é um artefato futuro, não um release publicado pelo pacote. |
| `docs/examples/card-instance-match.example.v2.json` | Usa `catalog_version=soulsbo-catalog-v1` e `balance_rules_version=balance-v0.2` | São rótulos do exemplo; não há manifesto correspondente que os resolva a conteúdo imutável. |
| `sistemas/gwent.py::novo_estado()` | Constrói o estado da partida sem `definition_snapshot`, IDs de release ou digest | O motor legado não fixa a definição por partida. |
| `sistemas/gwent.py` | Não contém `definition_snapshot`, `catalog_release_id`, `balance_rules_release_id` nem `definition_digest` | O contrato v2 é documental/candidato, não é consumido pelo runtime legado. |

**Distinção necessária:** `schema_version` deve continuar identificando a versão estrutural do contrato. Não deve ser usado como versão do conteúdo de catálogo, do registry de efeitos ou do balanceamento. Um rótulo como `balance-v0.2` só deve ser aceito em uma partida se resolver para um release imutável disponível e verificável.

### 2.2 Operação e histórico de eventos

| Evidência | Observado | Implicação |
|---|---|---|
| `aplicar_jogada()` | Parâmetros de ação, carta, fileira e alvo; não recebe `operation_id`, `event_id` ou `parent_event_id` | A ação lógica não possui chave de idempotência ou contexto causal no contrato legado. |
| `_registrar_evento()` | Lê `last_event` como texto, acrescenta ao `event_log` e limita o histórico a 20 entradas | O log serve para mensagem/histórico curto; não é um ledger de eventos de domínio nem é suficiente para replay/auditoria causal. |
| `database.py::cartas_gwent_matches` | Colunas `id`, `creator_id`, `opponent_id`, `status`, `state_json`, timestamps | O DDL atual não possui revisão dedicada nem ledger durável de operações/eventos. O estado inteiro é persistido em `state_json`. |
| `aplicar_jogada()` | Faz `deepcopy(state)` antes de resolver a ação | Isso isola o objeto devolvido; por si só não garante idempotência, atomicidade ou exclusão mútua no banco. |

`operation_id` e `event_id` não são sinônimos. Uma ação lógica do jogador deve ter um `operation_id`; a resolução dessa ação pode gerar vários `event_id` distintos, ligados por relações causais e por uma sequência monotônica. O ledger de idempotência guarda o resultado da operação; o event stream explica os efeitos e reações. Um não substitui o outro.

### 2.3 Chama Negra, Vingança e raridade

Referências principais:

- `sistemas/gwent.py::_aplicar_potencia_raridade()` (aprox. linhas 659–689)
- `sistemas/gwent.py::_remover_unidade()` (aprox. linhas 995–1021)
- ramo `skill == "gwent_queima"` (aprox. linhas 1616–1620)
- chamada posterior a `_aplicar_potencia_raridade()` (aprox. linha 1804)
- `docs/scripts/audit-buffs-movement-protection-v0.1.py::test_chama_negra_rarity_amplifies_vengeance_trigger()`

O amplificador coleta diferenças de bônus para a carta jogada e para unidades nos dois tabuleiros. A chave de acompanhamento é `id(unit)` (identidade de objeto Python); a rotina não recebe `source_effect_id` nem distingue deltas diretos de deltas reativos.

Chama Negra chama `_remover_unidade()` para a unidade mais forte de cada lado. Se a unidade aliada removida possui `vinganca`, `_remover_unidade()` concede +1, naquele momento, aos aliados restantes na mesma fileira. Só depois o ramo da especial chama `_aplicar_potencia_raridade()`, que encontra esses deltas no diff global.

A fixture reproduzida confirma: os dois sobreviventes deveriam receber +1 apenas por Vingança; com a Chama Negra Épica, o primeiro sobrevivente recebe +2 e o segundo +1. A amplificação extra acompanha a ordem do tabuleiro, não a origem semântica do bônus.

### 2.4 Rykard, sacrifício e Vingança

Referências principais:

- `sistemas/gwent.py` ramo `effect == "rykard_devour"` (aprox. linhas 1427–1448)
- `docs/scripts/test-card-removal-resurrection-candidate-v0.1.py::test_legacy_rykard_stacks_vengeance_then_row_bonus()`
- `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md`, caso IR-04

A sequência observada é:

1. A habilidade de líder escolhe o aliado de menor poder efetivo na fileira escolhida.
2. Chama `_remover_unidade(..., "sacrificio")`.
3. Se a vítima possui Vingança, a remoção dispara +1 aos aliados restantes na mesma fileira.
4. O handler de Rykard percorre os sobreviventes e concede +2.

A fixture de runtime reproduz +3 por sobrevivente quando a vítima possui Vingança. Isso comprova o comportamento atual, não aprova a acumulação como regra definitiva. O ramo de líder de Rykard não chama `_aplicar_potencia_raridade()`; portanto, não deve ser confundido com o problema da Chama Negra.

## 3. Conflito documental identificado na auditoria (estado anterior à aprovação)

Há duas direções incompatíveis para BUF-001:

| Alternativa | Regra | Base documental | Consequência |
|---|---|---|---|
| **A — remover amplificação por raridade** | Raridade é classificação; magnitude, alvos e duração pertencem ao `effect_id` e seus parâmetros, não à raridade. Remover `RARITY_EFFECT_BUDGET` do motor novo. | `docs/card-game-balance-spec-v0.1.md`, seção 6 e critérios de aceite 8 | Elimina o canal de herança direta/indireta de raridade e simplifica o contrato de efeitos. Exige rever cartas/testes/textos que hoje dependem do multiplicador legado. |
| **B — manter amplificação restrita** | Raridade pode ampliar apenas outputs diretos do efeito que está sendo resolvido; eventos reativos não herdam a raridade da ação que os disparou, salvo regra própria explícita. | Recomendação BUF-001/002 em `docs/card-game-cross-decision-review-ci-buf-rsrx-v0.1.md` | Preserva uma camada de balanceamento por raridade, mas exige attribution causal correta para cada output e mais regras/testes. |

**Recomendação técnica deste parecer: Alternativa A.** Ela é mais coerente com a especificação de balanceamento v0.1 e evita que raridade esconda variações mecânicas fora do contrato de cada efeito. A Alternativa B continua apresentada para preservar a recomendação anterior. No momento desta auditoria, nenhuma opção estava aprovada; a decisão posterior do proprietário consta na seção 9 e no registro de aprovação.

Se A for aprovada, BUF-002 torna-se uma proteção redundante, mas útil como invariante: efeitos reativos nunca herdam propriedades de balanceamento da causa externa. Se B for aprovada, BUF-002 deve ser regra explícita no modelo de eventos.

## 4. Modelo causal candidato

A proposta separa três objetos:

1. **Manifesto de definição da partida:** congela releases de catálogo, registry de efeitos, balanceamento e conjunto de regras, com digest de conteúdo verificável.
2. **Operação lógica:** uma entrada do jogador/sistema, identificada por `operation_id`; é a unidade de idempotência.
3. **Eventos de domínio:** efeitos produzidos pela operação, cada qual com `event_id`, sequência e relações `caused_by_event_ids`; são a unidade de causalidade e auditoria.

Envelope ilustrativo (não é schema aprovado):

```json
{
  "operation_id": "uuidv4-da-operacao",
  "expected_revision": 12,
  "definition_manifest": {
    "catalog_release_id": "catalog-release-id",
    "effect_registry_release_id": "effects-release-id",
    "balance_rules_release_id": "balance-release-id",
    "ruleset_release_id": "ruleset-release-id",
    "definition_digest": "sha256:<digest-canonico>"
  },
  "events": [
    {
      "event_id": "uuidv4-evento-1",
      "caused_by_event_ids": [],
      "sequence": 1,
      "kind": "operation_started",
      "effect_scope": "none"
    },
    {
      "event_id": "uuidv4-evento-2",
      "caused_by_event_ids": ["uuidv4-evento-1"],
      "sequence": 2,
      "kind": "unit_removed",
      "effect_scope": "direct",
      "source_effect_id": "special.remove_units",
      "source_instance_id": "uuidv4-da-carta-especial",
      "target_instance_ids": ["uuidv4-da-unidade-removida"]
    },
    {
      "event_id": "uuidv4-evento-3",
      "caused_by_event_ids": ["uuidv4-evento-2"],
      "sequence": 3,
      "kind": "revenge_bonus_applied",
      "effect_scope": "reactive",
      "source_effect_id": "unit.death_revenge",
      "source_instance_id": "uuidv4-da-unidade-com-vinganca",
      "target_instance_ids": ["uuidv4-do-aliado-afetado"]
    }
  ]
}
```

### 4.1 Campos sugeridos por evento

- `event_id`: UUIDv4 único no escopo da partida.
- `operation_id`: vínculo com a operação lógica que originou a resolução.
- `sequence`: ordem total monotônica dentro da partida, atribuída no commit.
- `caused_by_event_ids`: lista de eventos causais; permite combos/efeitos dependentes de mais de um evento. O grafo deve ser acíclico.
- `kind`: tipo de evento de domínio.
- `effect_scope`: `direct`, `reactive` ou `system`.
- `source_effect_id`: efeito que realmente produziu o output, não o efeito raiz por conveniência.
- `source_instance_id`: instância que possui o efeito, quando houver; pode ser nulo para líder, clima, regra ou sistema.
- `target_instance_ids`: instâncias exatas atingidas, inclusive listas vazias quando uma regra registrar um no-op.
- `payload/deltas`: valores aplicados e identificadores da policy/regra usada, sem depender de texto livre de `last_event`.

Não é necessário copiar o manifesto completo em cada evento: a operação/evento referencia o `match_id`, e a partida aponta para um manifesto imutável. O manifesto precisa continuar resolvível durante toda a retenção/replay da partida.

### 4.2 Snapshot de definição

Proposta:

- Manifesto imutável por partida com `catalog_release_id`, `effect_registry_release_id`, `balance_rules_release_id`, `ruleset_release_id` e `definition_digest`.
- Cada instância conserva uma projeção resolvida de sua definição mecânica (`card_id`, `kind`, `power_base`, `printed_row`, `effect_id`, `effect_params`, tags e outros atributos usados em jogo) e um digest dessa definição.
- A partida não consulta silenciosamente o catálogo corrente para reinterpretar uma partida antiga.
- Alterações de schema e alterações de conteúdo têm versionamentos diferentes.
- Hashes de arquivos-fonte ajudam na proveniência, mas o digest do manifesto deve ser calculado sobre conteúdo canônico dos artefatos de release, não sobre o arquivo Python inteiro.

A canonicalização exata do JSON, normalização Unicode, representação numérica e política de artefatos derivados ainda exigem especificação própria antes de congelar o digest.

### 4.3 Idempotência e atomicidade

A proposta de CI-011 permanece alinhada ao contrato anterior:

- `operation_id` identifica uma única tentativa lógica.
- O fingerprint inclui `match_id`, ator, `expected_revision`, ação e payload semântico normalizado, além da referência ao manifesto fixado.
- Mesma chave + mesmo fingerprint: devolver o resultado já registrado, sem reaplicar os efeitos.
- Mesma chave + fingerprint diferente: conflito explícito.
- Estado atualizado, revisão nova, resultado da operação e eventos gerados devem ser persistidos juntos, em uma transação.
- `event_id` não substitui `operation_id`; um comando pode produzir zero, um ou muitos eventos.

A garantia transacional/CAS real pertence ao Grupo E e não foi implementada nem testada contra DB concorrente nesta auditoria.

## 5. Propostas de resolução do Grupo B

| Decisão | Proposta candidata | Status |
|---|---|---|
| **CI-005** | Adotar manifesto imutável de definição por partida e snapshot mecânico resolvido por instância; separar `schema_version` de release IDs; digest calculado sobre conteúdo canônico. | Aberta |
| **CI-011** | Separar `operation_id` idempotente de `event_id` causal; eventos ordenados, append-only e com grafo acíclico; persistir resultado, revisão e eventos atomicamente. | Aberta |
| **BUF-001** | Preferência deste parecer: remover amplificação por raridade, seguindo o balance spec v0.1; alternativa B mantém amplificação somente em outputs diretos. | Aberta — conflito a resolver |
| **BUF-002** | Efeitos reativos têm fonte própria e não herdam raridade/parâmetros do efeito raiz. Se a Alternativa A for aprovada, torna-se invariante de não-herança. | Aberta |
| **BUF-012** | Publicar no registry novo apenas atribuições ativas e verificadas; handlers/aliases sem binding ativo permanecem em arquivo histórico/compatibilidade, não como capacidades do jogo. | Aberta |
| **RSRX-03** | Uma remoção/sacrifício bem-sucedido gera seu evento de remoção; se o alvo tiver Vingança e a regra aprovada permitir a causa, gera um evento reativo separado. Bloqueio por escudo não gera evento de remoção nem Vingança. A lista de causas permitidas continua a ser fechada no Grupo F. | Aberta |
| **RSRX-05** | Rykard deve manter outputs separados: evento reativo de Vingança (+1) e evento direto do líder (+2), com ordem causal explícita. O total legado +3 é evidência; a acumulação final continua dependente de aprovação. | Aberta |

## 6. Validação reproduzível

Script: `docs/scripts/audit-card-game-snapshot-causality-group-B-v0.1.py`  
Resultado estruturado: `docs/card-game-snapshot-causality-group-B-audit-v0.1.json`  

**Resultado:** 20/20 verificações aprovadas, sem falhas.

A bateria cobre:

- status e proveniência do baseline histórico;
- ausência de release imutável no registry candidato e no catálogo de balanceamento;
- rótulos provisórios do exemplo CardInstance v2;
- ausência de manifesto e `definition_snapshot` no construtor legado;
- ausência de `operation_id` e causalidade estruturada no runtime;
- natureza textual/limitada do `event_log`;
- varredura global de delta de bônus pela raridade;
- disparo síncrono de Vingança em remoção;
- reprodução de Chama Negra + Vingança e Rykard + Vingança;
- validade estrutural de um grafo causal candidato e rejeição de pais inexistentes, ciclos e herança implícita de raridade.

**Limites:** os testes de comportamento usam fixtures sintéticas e invocam o motor legado local. A validação do grafo causal opera sobre dados sintéticos, não um novo runtime. Não houve DB de produção, concorrência real, HTTP, Discord, frontend ou partidas competitivas. A bateria não aprova regras de design.

## 7. Gate e próximos passos

1. Resolver explicitamente o conflito BUF-001 (Alternativa A ou B).
2. Aprovar/ajustar o manifesto de definição e o contrato de eventos do Grupo B.
3. Fechar as causas de Vingança no Grupo F; não assumir ainda que todo sacrifício deve dispará-la só porque o legado atual dispara.
4. Só então preparar `CardInstance v0.3`/schemas revisados. Não criar migrador nem integrar ao runtime nesta etapa.

**Integridade:** este trabalho é somente auditoria documental e de testes. Nenhum arquivo funcional foi alterado.

## 8. Regressões anteriores reexecutadas nesta revisão

| Suite | Resultado |
|---|---:|
| Grupo B — snapshot e causalidade | 20/20 |
| Grupo A — identidade | 30/30 |
| CardInstance v0.2 | 30/30 |
| Matriz cruzada CI/BUF/RSRX | 272/272 |
| Buffs e interações cruzadas | 9/9 |
| Buffs, movimentação e proteção | 14/14 |
| Líderes | 22/22 |
| Estados negativos | 41/41 |
| Remoção/ressurreição candidata | 49/49 |
| Catálogo candidato de efeitos | 23/23 |
| Contrato canônico de cartas | 35/35 |
| UI/seleção manual | 12/12 |
| Sequência de poder | 10/10 |
| Seleção e escopo de fileiras | 15/15 |
| Identidade e ciclo de vida | 17/17 |
| Comportamento de identidades ativas | 33/33 |

As suítes possuem escopos diferentes e algumas validam modelos candidatos enquanto outras reproduzem o legado. Os totais não devem ser somados como uma cobertura única nem interpretados como prova de integração em produção.


## 9. Aprovação posterior do proprietário (2026-11-27)

O proprietário aprovou explicitamente o Grupo B, incluindo a Alternativa A de BUF-001. O registro auditável está em `docs/card-game-snapshot-causality-group-B-approval-v0.1.md/.json`.

- CI-005, CI-011, BUF-001, BUF-002 e BUF-012: aprovadas.
- RSRX-03: aprovado como contrato de eventos, com conjunto de causas de Vingança ainda dependente do Grupo F.
- RSRX-05: aprovada a separação causal dos outputs de Vingança e Rykard; o total legado +3 não é congelado como regra de balanceamento.
- BUF-001 Alternativa A: raridade não altera magnitude, thresholds, quantidade/seleção de alvos, duração ou outros parâmetros de execução. `rarity_id` é metadado classificatório; o resolvedor novo não recebe raridade como input.

A aprovação autoriza atualizar o contrato candidato para v0.3. Não autoriza alterar `sistemas/gwent.py`, publicar releases reais, migrar partidas ou alterar DB/API/frontend. EFP, custo, teto 32, leader_load e cortes numéricos continuam não aprovados.

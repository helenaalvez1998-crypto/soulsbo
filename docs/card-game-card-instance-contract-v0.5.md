# Contrato `CardInstance` v0.5 — Grupos A/B/C/D aprovados; Grupo F auditado, decisões pendentes; E aberto

**Data:** 2026-11-27  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev12.zip`  
**Status:** `DRAFT_AFTER_GROUP_A_B_C_D_APPROVAL_NOT_FROZEN`  
**Integração:** nenhuma. Runtime, DB, catálogo ativo, API, bot e frontend permanecem inalterados.

## 1. Escopo desta revisão

A v0.5 incorpora as decisões aprovadas dos Grupos A, B, C e D. Além de identidade, manifesto, causalidade e ciclo de vida, ela define os contratos candidatos de request, oferta de alvo, política declarativa e resultado de ação. O Grupo F (causas finais de remoção/Vingança) foi auditado em modo somente leitura; suas cinco resoluções FCAUSE-001..005 permanecem pendentes de aprovação. O Grupo E (persistência concorrente, ledger durável, replay e migração) continua aberto. O contrato não está congelado e não é um schema de produção.

Artefatos normativos do draft:

- `docs/schemas/card-game-card-instance-match.schema.v5.json` — envelope da partida e ledger de operações;
- `docs/examples/card-instance-match.example.v5.json` — fixture estrutural v5;
- `docs/schemas/card-game-action-request.schema.v1.json` — request futuro;
- `docs/schemas/card-game-target-offer.schema.v1.json` — oferta de alvo gerada pelo servidor;
- `docs/schemas/card-game-effect-target-policy.schema.v1.json` — política por efeito/release;
- `docs/schemas/card-game-action-result.schema.v1.json` — resultado por operação e alvo;
- `docs/card-game-selection-group-D-approval-v0.1.md/.json` — aceite do Grupo D.

`schema_version=5` é versão estrutural do envelope. Não altera os quatro release IDs do `DefinitionManifest` e não representa uma versão de catálogo/registry/balanceamento/ruleset.

## 2. Decisões aprovadas incorporadas

### 2.1 Grupos A/B/C

As regras de v0.4 permanecem normativas: UUIDv4 por ocorrência; `card_id` repetível; `exemplar_id` preservado apenas com proveniência; manifesto e snapshots imutáveis; eventos append-only e causalmente ligados; raridade apenas classificatória; fontes reativas próprias; `bonus_grants[]`, `protection_grants[]`, `status_applications[]` e `weather_resistance_modifiers[]`; `round_close` após snapshot de pontuação; políticas explícitas por transição; `vigil_seal` expira em `board_exit`; políticas distintas para Ressurgir/Réquiem/Esgar/Lágrima Sagrada.

### 2.2 Grupo D — seleção e custos (aprovado)

O registro completo é `docs/card-game-selection-group-D-approval-v0.1.md`. Em v0.5, as consequências são:

- `source_instance_id`, `target_instance_id(s)`, `choice_id` e `target_row` são dimensões distintas. O legado `target_id` não é contrato novo.
- O servidor é autoridade para offers, candidatos, métricas, ranking e prévias de alvos secundários. Toda submissão revalida `expected_revision`, identidade, zona, fileira, predicates e cardinalidade. O cliente renderiza, não recalcula.
- Cada binding ativo referencia `target_policy_id` versionado. A policy declara lado, zona, escopo de fileira, predicates versionados, métrica de elegibilidade, métrica exibida, ordenação, desempate, cardinalidade, fallback, parcialidade, seleção secundária, proteção e custo.
- `rarity_id` não é input de policy; quantidade é explícita no efeito/release. `up_to 2` com mínimo 1 e apenas um candidato disponível pode ser `applied`.
- Preferir `manual_set` para seleção múltipla. Secundários automáticos precisam aparecer na oferta e ser confirmados antes da ação.
- Fallback é por efeito, nunca global. Sem alvo, usar `reject`, `consume_no_effect` ou fallback nomeado conforme policy.
- Outcomes globais são `applied`, `partial`, `blocked`, `consumed_no_effect` e `rejected`. Outcomes por alvo são `applied`, `blocked` e `skipped`. `conflict`/revisão obsoleta não é outcome de gameplay; pertence ao Grupo E.
- Custos são independentes: `turn_consumed`, `source_consumed`, `activation_consumed`, `protection_grants_consumed` e `other_costs`.
- Proteção escolhe grant ativo/compatível mais antigo por `applied_event.sequence` ascendente; `grant_id` lexicográfico desempata. Override precisa ser explícito no release.
- A resolução lógica planeja sem mutação, valida alvos/custos/proteção, aplica em working copy, verifica invariantes e faz um commit único. Falha inesperada descarta a working copy. Persistência transacional real continua Grupo E.
- Request futuro inclui `operation_id` UUIDv4 e `expected_revision`; o enforcement concorrente real permanece Grupo E.
- A oferta serializa eligibility/display/sort metrics, valores e secundários; UI e API exibem a métrica realmente usada.

## 3. Semântica do resultado e do ledger

`operations[operation_id].result` usa o contrato de Action Result v1. O `operation_id` externo e o interno devem coincidir. `expected_revision` no registro deve coincidir com `result.revision_before`.

| Outcome | Semântica | Custos | Revisão |
|---|---|---|---|
| `applied` | Ação aceita e efeito aplicado | Conforme policy | Avança se o commit altera estado/ledger de domínio |
| `partial` | Resultado misto entre alvos aplicados e bloqueados/pulados | Conforme cada parte/policy | Avança quando há outputs/custos aceitos |
| `blocked` | Alvos protegidos; nenhum alvo sofre o efeito principal | Carga(s) de proteção e custos do efeito conforme policy | Pode avançar porque bloqueio pode consumir carga/turno/fonte |
| `consumed_no_effect` | Ação aceita/consumida sem alteração no alvo | Somente custos declarados | Avança quando custo/evento é commitado |
| `rejected` | Validação de gameplay falhou antes de commit | Nenhum custo; nenhum evento de domínio | `revision_after == revision_before` |

Um request com `expected_revision` obsoleto, replay incompatível ou falha CAS resulta em conflito de transporte/persistência do Grupo E, não em `rejected` de gameplay. A persistência do registro de rejeição/idempotência também precisa ser definida e testada em E; o envelope v5 não prova durabilidade.

`partial` significa resultado misto por alvo, não simplesmente que um seletor `up_to N` encontrou menos que seu máximo. Quando a policy tem mínimo 1, máximo 2 e só um alvo elegível existe, o efeito pode resultar `applied`.

## 4. Ofertas e políticas não são estado canônico da partida

`TargetOffer` é um recurso de serviço temporário ligado a `state_revision`, não uma nova zona nem uma fonte de verdade persistida em `CardInstance`. Pode expirar. Ao receber o request, o servidor recalcula elegibilidade e valida a seleção contra o estado atual. `preview_token` de `manual_primary_auto_fill` deve ser opaco, emitido pelo servidor e ligado à oferta/revisão; a preferência continua sendo `manual_set`.

Predicates são IDs versionados no registry, nunca código/expressões enviados pelo cliente. Os quatro schemas candidatos do Grupo D estão em `docs/schemas/` e permanecem contratos documentais sem rota implementada.

## 5. O que v0.5 valida e o que continua fora

O schema v5 valida envelope, instâncias, resultados de operação, custos e referências estruturais. O validador semântico confere correspondência de operation IDs, `expected_revision == revision_before`, relação entre outcomes e custos/revisões, e invariantes do exemplo.

Ainda não valida execução real de browser/UI, rede, concorrência multi-processo, CAS SQLite, transações, replay durável, nem compatibilidade HTTP. Não congela parâmetros por carta/efeito, valores finais de targets, nem desempates especiais ainda ausentes do release.

## 6. Grupos F e E — gates abertos

- **F:** fechar causas elegíveis de Vingança; tratamento de sacrifício; contadores separados para remoções e sacrifícios; aditividade/ordem de Vingança e Rykard; diferença entre remoção real e arquivamento de fim de rodada.
- **E:** CAS/serialização por partida; lock/constraints; ledger e fingerprints duráveis; replay idempotente; rollback; migração única de snapshots antigos e testes reais no banco.

RSRX-03/RSRX-05 aprovados no Grupo B são apenas separação causal e não fecham a regra de disparo por causa nem o balanceamento aditivo. RSRX-04 permanece aberto. Grupo C aprovado define limpeza/retorno, mas não define causas de Vingança.

## 7. Guardrails

- Não alterar `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`, catálogo ativo, resolvedores ou schema de produção.
- Não executar migrador nem converter snapshots persistidos.
- Não criar rota de Action Request/Offer/Result antes de F/E e validações integradas.
- Não promover bindings órfãos nem restaurar amplificação por raridade.
- Não tratar validação de schema/harness como teste de produção.

## 8. Próximo gate

O Grupo F foi auditado; ver `docs/card-game-removal-causes-group-F-review-v0.1.md`, `docs/card-game-removal-causes-group-F-decisions-v0.1.json` e `docs/card-game-removal-causes-group-F-audit-v0.1.json`. FCAUSE-001..005 continuam `PENDING_OWNER_APPROVAL`. Após o aceite de F, incorporar suas decisões em `CardInstance v0.6` como draft. Grupo E continua um gate independente para persistência real, CAS, ledger durável, replay e migração. Nenhum grupo autoriza integração do runtime nesta etapa.

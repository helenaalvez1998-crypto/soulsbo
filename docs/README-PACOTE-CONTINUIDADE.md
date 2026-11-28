# Continuidade atual — revisão rev. 31 (2026-11-28)

**Pacote de referência:** `soulsbo-main-continuity-2026-11-28-rev31.zip`  
**Baseline:** `soulsbo-main-continuity-2026-11-28-rev30.zip`.  
**Estado:** Card Engine v2 permanece alpha isolada; `CardInstance v0.7`/schema 7 ainda é draft, não congelado.  
**Última entrega:** fechamento de prontidão operacional, conquistas autoritativas e proteção fail-closed para apostas/evolução com risco incompletas; Docker/Compose, CI, backup e preflight reproduzíveis adicionados.  
**Validação:** 240 testes aprovados + 61 subtests parametrizados; suite playable alpha, staging 137/27/110, Bo3 A 2–1 B (97 eventos) e demo combo/passiva/líder 20–10 (49 eventos), SQLite íntegro; py_compile, Node, shell e parse YAML aprovados.  
**Preflight deste ambiente:** 9 pass, 0 warnings, 22 blockers. Docker CLI, dependências exatas, secrets Discord/OAuth, URL, volume e DB real não estão presentes; não houve build de container, login real ou deploy.  
**Módulos bloqueados:** apostas (sem escrow/liquidação), evolução com risco (sem estado/ledger/amuleto) e conquistas associadas a esses eventos. Catálogo 110 cartas ainda bloqueadas, 18 combos inativos; balanceamento sem playtest humano.

Leia primeiro `docs/card-game-handoff.md`, `docs/card-engine-v2-rev31-product-completion.md`, `docs/card-engine-v2-rev31-validation.json`, `docs/card-engine-v2-operational-deployment-v0.1.md` e `deploy/README.md`.

---

# Continuidade histórica — revisão rev. 26 (2026-11-28)

**Pacote de referência:** `soulsbo-main-continuity-2026-11-28-rev26.zip`  
**Baseline:** `soulsbo-main-continuity-2026-11-28-rev25.zip`  
**Estado:** Card Engine v2 isolado em alpha; CardInstance v0.7/schema 7 continua draft não congelado.  
**Última entrega:** Deck Builder e aplicação competitiva alpha v0.1. Regras adotadas: 30 cartas, máximo de três cópias, mão inicial quatro e primeiro jogador sorteado pelo servidor.  
**Implementado:** validação por allowlist e inventário, repositório SQLite separado para decks, versionamento otimista, matchmaking com ownership revalidado, embaralhamento server-side, sorteio de starter e fachada async para futuros transports.  
**Catálogo:** 137 históricos; 27 permitidos e 110 bloqueados; dez líderes alpha.  
**Validação:** 171/171 testes; py_compile aprovado; staging 137/27/110; Bo3 A 2–1 B com 97 eventos; demo combo/passiva/líder com 49 eventos; SQLite íntegro.  
**Limites:** inventário ainda por quantidade de `card_id`, sem vínculo à identidade de exemplar evoluído; sem interface/handlers Discord ou HTTP conectados; sem playtest humano/produção. Os cinco arquivos centrais do legado não foram alterados.

Leia primeiro `docs/card-game-handoff.md`, `docs/card-engine-v2-deck-builder-alpha-v0.1.md`, `docs/card-engine-v2-deck-builder-alpha-v0.1-validation.json` e `sistemas/card_engine_v2/README.md`.

---

# Continuidade histórica — revisão rev. 24 (2026-11-28)

**Pacote de referência:** `soulsbo-main-continuity-2026-11-28-rev24.zip`  
**Baseline:** `soulsbo-main-continuity-2026-11-28-rev23.zip`  
**Estado:** Card Engine v2 isolado em alpha; CardInstance v0.7/schema 7 continua draft não congelado.  
**Última entrega:** economia de energia alpha v0.1: +1 no início de cada turno, teto 5, saldo persistente entre rodadas; runtime validado e persistido no sidecar.  
**Custos:** pagamentos explícitos por `card_id` e `leader_id` já são aplicados transacionalmente, porém os mapas de custo permanecem vazios. Ações sem preço continuam compatíveis e sem cobrança nesta alpha; raridade e `deck_cost_legacy` não são fontes energéticas.  
**Validação:** 145/145 testes; `py_compile` aprovado; staging 137/27/110 aprovado; Bo3 A 2–1 B com 87 eventos e seis fatigue ticks; demo combo/passiva/líder A 20–10 B com 44 eventos; integridade SQLite `ok`.  
**Preservação:** sem alteração de schema 7/DDL ou dos cinco arquivos centrais do motor legado.

Leia primeiro `docs/card-game-handoff.md`, `docs/card-engine-v2-energy-economy-alpha-v0.1.md`, `docs/card-engine-v2-playable-alpha-validation-v0.5.md` e `sistemas/card_engine_v2/README.md`.

---

# Continuidade histórica — revisão rev. 23 (2026-11-28)

**Pacote de referência:** `soulsbo-main-continuity-2026-11-28-rev23.zip`  
**Baseline:** `soulsbo-main-continuity-2026-11-28-rev22.zip`  
**Estado:** Card Engine v2 isolado em alpha; CardInstance v0.7/schema 7 continua draft não congelado.  
**Última entrega:** deck fatigue integrado ao controlador de partidas alpha.  
**Deck fatigue:** começa em 1 ponto, progride +1 a cada turno individual com pilha vazia, sem teto; contador independente por jogador; primeira vez de cada jogador isenta; dano letal encerra a partida antes da ação. Política de balanceamento provisória.  
**Setup:** mão inicial padrão reduzida a quatro cartas, conforme redesign. Até duas cartas são compradas na transição de nova rodada pelo harness alpha; cadência completa de compra ainda não está definida.  
**Validação:** 135/135 testes; staging 137/27/110; Bo3 A 2–1 B com 72 eventos, seis fatigue ticks e SQLite íntegro; demonstração combo/passiva/líder aprovada.  
**Preservação:** schema 7 e SQL não alterados; os cinco arquivos centrais do legado permanecem byte a byte idênticos ao baseline rev. 22.

Leia primeiro `docs/card-game-handoff.md`, `docs/card-engine-v2-deck-fatigue-alpha-v0.2.md`, `docs/card-engine-v2-deck-fatigue-alpha-v0.2-change-manifest.md` e `sistemas/card_engine_v2/README.md`.

---

# Continuidade histórica — revisão rev. 22 (2026-11-28)

**Pacote de referência:** `soulsbo-main-continuity-2026-11-28-rev22.zip`  
**Baseline:** `soulsbo-main-continuity-2026-11-28-rev21.zip`  
**Estado:** Card Engine v2 isolado em alpha; CardInstance v0.7/schema 7 continua draft não congelado.  
**Última entrega:** auditoria do ciclo de vida de remoção e contrato candidato/testável de deck fatigue. A referência matemática fica isolada e não está ligada ao controlador.  
**Ciclo de vida:** remoção/Execução/sacrifício, contadores separados, proteção, Vingança causal e arquivamento de rodada conferidos contra aprovações dos Grupos C/F. Não há HP individual nem morte de unidade por dano de combate.  
**Deck fatigue:** o redesign define dano crescente por turno quando o deck esvazia, mas não fixa valores nem cadência de compra. A alpha compra duas cartas na transição de rodada e hoje para quando a pilha esvazia. A rev. 22 registra a incompatibilidade e deixa cadência, dano inicial, incremento, teto e casos de compra parcial pendentes.  
**Catálogo:** 137 modelos históricos; 27 alpha-only e 110 bloqueados.  
**Combos/passivas/líderes:** 27 combos registrados (9 alcançáveis, 18 inertes), quatro passivas e dez handlers alpha.  
**Validação:** 126/126 testes; seis testes novos do modelo candidato; py_compile aprovado; regressões oficiais de staging, partida Bo3 e demo combo/passiva/líder aprovadas; SQLite íntegro.  
**Integração:** nenhuma; sem Discord/HTTP/frontend/banco publicado/migração/cutover. Os cinco arquivos centrais do legado permanecem byte a byte idênticos ao baseline rev. 21.

Leia primeiro `docs/card-game-handoff.md`, `docs/card-engine-v2-deck-fatigue-contract-v0.1.md`, `docs/card-engine-v2-lifecycle-audit-v0.1.md`, `docs/card-engine-v2-sacrifice-match-alpha-v0.1.md` e `sistemas/card_engine_v2/README.md`.

---

# Handoff mais recente — combate por fileira Card Engine v2 alpha (rev. 20)

**Baseline:** `soulsbo-main-continuity-2026-11-27-rev19.zip`.  
**Pacote atual:** `soulsbo-main-continuity-2026-11-28-rev20.zip`.  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado; não congelado.  
**Ruleset:** `alpha-test-only.ruleset.v0.2`; 20 de vida inicial por jogador.  
**Validação:** 117/117 testes; staging 137/27/110; Bo3 A 2–1 B, 16 operações/60 eventos; demo combo/passiva/líder 25 eventos.

## Estado da rev. 20

- Combate por fileira integrado ao fechamento da rodada. A diferença positiva de poder efetivo causa dano à vida do oponente naquela fileira.
- Vida inicial 20, persistida em `life_by_player`; dano letal encerra a partida e letal simultâneo gera empate.
- `combat_row_resolved`, `player_damage_applied` e `player_defeated` são registrados com causalidade.
- A resistência existente continua sendo resistência climática; o contrato não define ataque/armadura/HP por unidade. O combate não destrói unidades automaticamente.
- Sacrifício normal no controlador, deck fatigue, custos completos e integração Discord/API/frontend permanecem pendentes.
- Motor legado preservado; nenhum banco publicado foi acessado.

Leia primeiro `docs/card-game-handoff.md`, `docs/card-engine-v2-combat-alpha-v0.1.md` e `docs/card-engine-v2-combat-alpha-v0.1-change-manifest.md`.

---

# Handoff mais recente — combos, passivas e líderes Card Engine v2 alpha (rev. 19)

**Baseline:** `soulsbo-main-continuity-2026-11-27-rev18.zip`.  
**Pacote atual:** `soulsbo-main-continuity-2026-11-27-rev19.zip`.  
**Contrato:** `CardInstance v0.7`, schema 7, draft implementado; não congelado.  
**Decisões:** Grupos A–F aprovados nos registros formais.  
**Validação:** 109/109 testes; staging 137/27/110; partida Bo3 A 2–1 B; demonstração combo/passiva/líder A 20–10 B.

## O que mudou nesta revisão

- O catálogo allowlist alpha atual é `data/card_game/card-engine-v2-alpha-catalog.v0.3.json`: 27 identidades explícitas. `AlphaCatalog` valida os novos artefatos e inclui os hashes dos combos, passivas e líderes no `DefinitionManifest`.
- `data/card_game/card-engine-v2-alpha-combos.v0.1.json` contém 27 combos. Nove são alcançáveis com tags existentes nas 27 cartas; 18 permanecem registrados, mas inertes até que cartas fornecedoras das tags sejam incluídas.
- `data/card_game/card-engine-v2-alpha-faction-passives.v0.1.json` contém quatro passivas de facção. A primeira unidade da facção escolhida, jogada em cada rodada, recebe +1; a ativação reinicia no fechamento da rodada.
- `data/card_game/card-engine-v2-alpha-leaders.v0.1.json` contém dez líderes alpha. Cada jogador seleciona um no setup e pode ativá-lo uma vez por partida; a facção do líder precisa corresponder à facção escolhida.
- `sistemas/card_engine_v2/synergies.py` resolve combos e passivas; `sistemas/card_engine_v2/leaders.py` implementa os dez handlers; `match.py` integra os efeitos ao fluxo de partida e ao fechamento de rodada.
- O staging histórico atualizado é `data/card_game/card-engine-v2-legacy-catalog-staging.v0.2.json`: 137 modelos, 27 alpha-only, 110 bloqueados. O staging v0.1 e o catálogo alpha v0.2 são históricos da revisão anterior.
- O schema `docs/schemas/card-game-card-instance-match.schema.v7.json` e `validation.py` aceitam os campos opcionais de facção/líder e estado de ativação por rodada, preservando compatibilidade de leitura para snapshots anteriores.

## Comandos de validação e demonstração

```bash
python -m py_compile sistemas/card_engine_v2/*.py docs/scripts/*.py tests/card_engine_v2/*.py
python docs/scripts/test-card-engine-v2-playable-alpha-v0.4.py
python docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.2.py
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py
python docs/scripts/simulate-card-engine-v2-combo-faction-leader-alpha-v0.1.py
```

Relatórios principais:
- `docs/card-engine-v2-playable-alpha-validation-v0.4.md/.json` — 109/109.
- `docs/card-engine-v2-combos-faction-passives-leaders-alpha-v0.1.md` — escopo e limitações.
- `docs/card-engine-v2-combo-faction-leader-alpha-run.v0.1.json` — demo A 20–10 B, 21 eventos, SQLite íntegro.
- `docs/card-engine-v2-playable-match-alpha-run.v0.3.json` — Bo3 A 2–1 B, 16 operações e 48 eventos.

## Estado e limites

- 27 cartas alpha; 110 modelos históricos continuam bloqueados.
- 27 combos registrados; nove alcançáveis, 18 inertes no allowlist atual.
- Quatro passivas e dez handlers de líderes no ambiente alpha; não equivalem a publicação/aprovação do catálogo completo.
- Testes sintéticos/isolados; não é playtest por UI humana. O jogo ainda não inclui combate/dano completo, todas as ações/custos, o fluxo normal de sacrifício no controlador, ou integração com Discord/HTTP/frontend.
- Sem acesso ou alteração do banco publicado, sem migração e sem cutover.
- Os cinco arquivos centrais do legado (`sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`) permanecem byte a byte idênticos ao baseline rev. 18.

## Próxima prioridade de implementação

Fechar o caminho normal de combate/dano e de sacrifício no controlador de partida, ampliar a cobertura de combos que hoje estão inertes por falta de tags-fonte e conectar os demais efeitos reais em fatias pequenas. Manter a allowlist alpha explícita e continuar sem integrar o runtime legado.

---

# Estado mais recente — expansão de catálogo Card Engine v2 alpha (rev. 18, 2026-11-27)

**Pacote atual:** `soulsbo-main-continuity-2026-11-27-rev18.zip`  
**Baseline:** `soulsbo-main-continuity-2026-11-27-rev17.zip`  
**Contrato:** `CardInstance v0.7`, schema 7, draft de implementação; não congelado.  
**Decisões:** Grupos A, B, C, D, E e F aprovados nos registros formais.  
**Catálogo alpha:** 24 IDs explícitos hash-pinned; 14 adicionados nesta expansão; 12 famílias novas de efeitos de entrada implementadas.  
**Staging histórico:** 137 modelos rastreados; 24 alpha-only e 113 bloqueados. Os 137 ainda requerem rebuild e revisão de facção; 19 registram divergência histórica de custo.  
**Validação:** 97/97 testes; staging 8/8 verificações; partida Bo3 de regressão termina 2–1 com 16 operações e 48 eventos.  
**Integração:** nenhuma; sem alteração do motor legado, bot, API, frontend ou banco publicado.

## Leia primeiro nesta revisão

1. `docs/card-engine-v2-catalog-expansion-report-v0.2.md/.json` — cartas habilitadas, 12 famílias de efeito e limites.
2. `docs/card-engine-v2-catalog-expansion-change-manifest-v0.2.md` — lista de arquivos criados/alterados e integridade do legado.
3. `data/card_game/card-engine-v2-alpha-catalog.v0.2.json` — allowlist de 24 cartas, carregada e hash-pinned pelo `AlphaCatalog`.
4. `data/card_game/card-engine-v2-alpha-effects.v0.2.json` — famílias/parametrizações ligadas às cartas alpha.
5. `data/card_game/card-engine-v2-legacy-catalog-staging.v0.1.json` — rastreabilidade dos 137 modelos; não é catálogo de runtime.
6. `sistemas/card_engine_v2/README.md` — execução, limites e comandos atualizados.
7. `docs/card-engine-v2-playable-alpha-validation-v0.3.md/.json` — 97 testes.
8. `docs/card-engine-v2-playable-match-alpha-run.v0.2.json` — partida de regressão e integridade SQLite.

## O que já funciona

- Núcleo de identidade/persistência: UUIDv4, transações SQLite, CAS, idempotência, journal, causalidade, rewards/outbox e backup verificado.
- Resolvedor genérico: oferta de alvos revision-bound, remoção/sacrifício, proteção, movimentação, grants e Vingança reativa.
- Controlador de partida para dois jogadores, melhor de três, com unidades, especiais alpha, poder efetivo, clima/Frost, pontuação e fechamento de rodadas.
- `AlphaCatalog` carrega e valida o artefato allowlist v0.2; o hash entra no `DefinitionManifest`.
- 24 cartas executáveis somente na alpha de teste, com 12 novas famílias de efeitos de entrada cobertas por testes de integração do controlador.
- Staging dos 137 registros históricos, com bloqueio explícito dos 113 fora da allowlist.

## Limites atuais

- O staging de 137 cartas não é catálogo autoral aprovado. 137/137 ainda não estão reconstruídas e sem revisão de facção; 19 têm divergências históricas de custo.
- 12 famílias novas de efeito de entrada não equivalem às 54 famílias candidatas completas; ainda faltam combos, líderes e passivas de facção.
- Custos/deckbuilding, textos finais, facções e balanço dos 24 fixtures alpha não estão aprovados para publicação.
- Não há integração com Discord, HTTP, frontend, `database.py` nem banco publicado; não existe adapter assíncrono/worker ou cenário multi-host.
- Nenhuma migração real, cutover ou substituição do motor antigo foi executada.

## Como validar

Na raiz do projeto:

```bash
python docs/scripts/test-card-engine-v2-playable-alpha-v0.3.py
python docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.1.py
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.2.py
```

Alternativa: `python -m unittest discover -s tests/card_engine_v2 -v`.

**Guardrails:** usar somente SQLite novo e dedicado; não carregar as 113 cartas bloqueadas; não apontar o alpha para o banco legado; não integrar com bot/API/frontend; não migrar partidas reais nem substituir o motor antigo sem uma etapa explícita de integração e validação.

---

# Histórico — Grupo D antes da aprovação e da auditoria do Grupo F (rev. 12, 2026-11-27)

O pacote rev. 11 foi reaberto como baseline. A auditoria de seleção, fallback, resultados e custos do Grupo D terminou em **23/23**; os schemas e exemplos candidatos passaram em **13/13**. As 12 propostas DSEL-DEC-001..012 permanecem `PENDING_OWNER_APPROVAL`. Grupo A, B e C continuam aprovados.

**Relatório:** `docs/card-game-selection-group-D-review-v0.1.md`. **Decisões:** `docs/card-game-selection-group-D-decisions-v0.1.json`. **Auditoria detalhada:** `docs/card-game-selection-group-D-audit-v0.1.json`. **Validação:** `docs/card-game-selection-group-D-validation-v0.1.md/.json`.

**Schemas candidatos:** `docs/schemas/card-game-action-request.schema.v1.json`, `card-game-target-offer.schema.v1.json`, `card-game-effect-target-policy.schema.v1.json` e `card-game-action-result.schema.v1.json`. Exemplos correspondentes estão em `docs/examples/`. Harnesses: `docs/scripts/audit-card-game-selection-group-D-v0.1.py` e `docs/scripts/validate-card-game-selection-group-D-v0.1.py`.

**Achados principais:** o legado mistura target id e escolha de modo; a UI reconstrói candidatos de relíquia localmente e não exibe as mesmas métricas usadas na validação; fallbacks automáticos variam por carta; Égide/Passo derivam cardinalidade da raridade no legado (conflito com BUF-001 aprovado); ações bloqueadas e ações consumidas sem efeito têm custos distintos; proteção com múltiplos grants ainda não tem desempate no contrato v0.4.

**Proposta:** request usa `operation_id`, `expected_revision`, `source_instance_id`, `selection.target_instance_id(s)`, `choice_id` e `target_row` separados. O servidor gera ofertas e prévia de secundários; toda seleção é revalidada. Cada efeito declara escopo, métricas, predicados, cardinalidade, fallback, parcialidade, proteção e custos. Outcomes são `applied`, `partial`, `blocked`, `consumed_no_effect` e `rejected`; `conflict` pertence ao Grupo E. Custos de turno, fonte, ativação e cargas de proteção ficam separados. A escolha entre protection grants compatíveis recomenda evento de aplicação mais antigo primeiro, com `grant_id` como desempate.

**Regressões reexecutadas:** Grupo D 23/23; schemas/exemplos D 13/13; seleção/fileira 15/15; paridade UI 12/12; CardInstance v0.4 72/72; Grupo A 30/30; Grupo B 20/20; Grupo C 43/43; matriz cruzada 272/272. Escopos diferentes; não são cobertura integrada nem testes de produção.

**Limites:** DSEL-DEC-001..012 aguardam aprovação. Grupo F (causas de remoção/Vingança) e Grupo E (persistência, CAS, idempotência/replay real e migração) permanecem abertos. `operation_id` e `expected_revision` estão nos schemas candidatos, mas não na API existente. O runtime e o contrato v0.4 não foram integrados nem congelados.

**Integridade:** todos os arquivos novos/alterados nesta etapa ficam em `docs/`. Nenhum arquivo funcional fora de `docs/` foi alterado.

**Próximo gate:** proprietário aprovar/ajustar as 12 decisões do Grupo D; depois preparar `CardInstance v0.5` como draft. Manter Grupos F/E como gates independentes.

---

# Histórico — estado após aprovação dos Grupos A, B e C (rev. 11)

# Estado mais recente — Grupos A, B e C aprovados; `CardInstance v0.4` draft (2026-11-27)

O proprietário aprovou as resoluções dos Grupos A, B e C. O registro novo do Grupo C é `docs/card-game-state-lifecycle-group-C-approval-v0.1.md/.json`; o relatório e JSON originais da auditoria do Grupo C permanecem como fotografia histórica das recomendações antes do aceite. A aprovação cobre CI-008/009, BUF-008/009/010/011/014 e RSRX-07/08/10, incluindo `vigil_seal` com expiração `board_exit`.

**Contrato atual:** `docs/card-game-card-instance-contract-v0.4.md` — draft, não congelado. **Schema:** `docs/schemas/card-game-card-instance-match.schema.v4.json`. **Exemplo:** `docs/examples/card-instance-match.example.v4.json`. **Validação:** `docs/card-game-card-instance-contract-validation-v0.4.md/.json` e `docs/scripts/validate-card-game-card-instance-v0.4.py`.

**Resultado novo:** 72/72 verificações do CardInstance v0.4 passaram, incluindo Draft 2020-12, exemplo, identidade/zonas, fileiras, grants/aplicações, referências causais e simulações isoladas de transição. Regressões reexecutadas: Grupo A 30/30; Grupo B 20/20; matriz histórica CI/BUF/RSRX 272/272; auditoria do Grupo C 43/43; CardInstance v0.3 42/42. Escopos diferentes; não são cobertura integrada nem testes de produção.

**Modelo v0.4:** `intrinsic_weather_resistance` fica na definição; modificadores climáticos, bônus, proteção e status são listas de concessões/aplicações rastreáveis com origem, `applied_event_id` e `expires_on`. `current_row` é nulo fora de `board`; `last_board_row` persiste a última fileira válida; `last_unit_play_row` fica no estado de rodada do jogador. `round_close` ocorre após o snapshot imutável de pontuação, expira apenas itens marcados `round_close` em todas as zonas (inclusive rodada terminal), limpa marcadores de combo e `last_unit_play_row`, e preserva `permanent_instance`. `vigil_seal` expira em `board_exit`.

**Limites de aprovação:** Grupos D, F e E permanecem abertos. Os caps/thresholds numéricos dos estados negativos não foram congelados; a lista final de causas de Vingança depende do Grupo F; seleção/fallback/outcomes completos dependem do Grupo D; persistência concorrente e migração real dependem do Grupo E. O `clamp_policy_id` existe no contrato, mas valores finais precisam ser definidos em releases versionados.

**Integridade:** nesta revisão foram acrescentados/atualizados somente documentos, schemas de contrato e scripts sob `docs/`. Nenhum arquivo funcional fora de `docs/` foi alterado. `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py` e `site/app.js` permanecem byte a byte idênticos à rev. 10. Não houve alteração de runtime, DB de produção, API, catálogo ativo, resolvedores ou frontend. Não migrar snapshots nem integrar o contrato até fechar D/F/E e validar persistência transacional real.

Leia nesta ordem:
1. `docs/card-game-state-lifecycle-group-C-approval-v0.1.md/.json` — evidência e escopo exato do aceite.
2. `docs/card-game-card-instance-contract-v0.4.md` — contrato consolidado A/B/C e limites D/F/E.
3. `docs/schemas/card-game-card-instance-match.schema.v4.json` e `docs/examples/card-instance-match.example.v4.json` — schema e fixture.
4. `docs/card-game-card-instance-contract-validation-v0.4.md/.json` e `docs/scripts/validate-card-game-card-instance-v0.4.py` — 67 verificações reproduzíveis.
5. `docs/card-game-state-lifecycle-group-C-review-v0.1.md` e `.json` — auditoria original do Grupo C, anterior à aprovação.
6. `docs/card-game-handoff.md` — histórico e próximos gates.

**Próximo passo:** Grupo D — seleção, fallback, alvos múltiplos, bloqueio/rejeição/no-effect, custos e desempate entre grants compatíveis. Manter F e E como gates independentes. O motor antigo continua intacto.

---

# Histórico — Grupo C auditado antes da aprovação (2026-11-27)

O pacote rev. 9 foi reaberto e conferido por hash. Este bloco registra a fotografia da auditoria antes do aceite explícito do proprietário. O status atual está no bloco superior desta página e no registro `card-game-state-lifecycle-group-C-approval-v0.1.md`.

**Relatório:** `docs/card-game-state-lifecycle-group-C-review-v0.1.md`. **Decisões:** `docs/card-game-state-lifecycle-group-C-decisions-v0.1.json`. **Exemplo:** `docs/examples/card-game-state-lifecycle-group-C.example.v0.1.json`. **Validação:** `docs/card-game-state-lifecycle-group-C-validation-v0.1.json` e `docs/scripts/validate-card-game-state-lifecycle-group-C-v0.1.py`.

**Resultado Grupo C:** 43/43 verificações estruturais e de leitura estática passaram. Regressões reexecutadas nesta revisão: Grupo B 20/20; CardInstance v0.3 + Grupo B 42/42; matriz cruzada 272/272; Grupo A 30/30; estados candidatos 41/41; remoção/ressurreição 49/49. As suítes têm escopos independentes; não são cobertura integrada nem testes de produção.

**Achados centrais:** o encerramento não terminal limpa bônus/escudos/estados/combo apenas nas unidades que ainda estão no campo; unidades removidas anteriormente podem reter bônus no descarte. O ramo terminal retorna antes dessa limpeza. `weather_resist` é escalar e não distingue resistência intrínseca de modificador temporário. Escudos não bloqueiam universalmente status/debuffs; Noite/Chama e Lâmina Negra têm comportamentos locais diferentes quanto ao custo da ação quando bloqueadas. Ressurgir/Réquiem, Esgar e Lágrima Sagrada têm políticas de retorno distintas.

**Proposta principal:** `round_close` deve ser evento global posterior ao snapshot imutável da pontuação, expirando apenas concessões marcadas `round_close` em todas as zonas, inclusive descarte/mão/pilha e fechamento terminal. Bônus, escudos e marcas devem ser projeções apoiadas por concessões/aplicações com fonte, evento e expiração. Resistência climática deve separar atributo intrínseco de modificadores temporários. As 10 decisões CI/BUF/RSRX do Grupo C continuam `PENDING_OWNER_APPROVAL`.

**Guardrails:** nenhum arquivo fora de `docs/` foi alterado; não houve alteração de runtime, catálogo ativo, registry candidato, DB, API, Discord, frontend, migração nem integração. `CardInstance v0.3` não foi congelado. Não criar migrador nem integrar resolvedores antes do aceite dos grupos dependentes.

Leia nesta ordem:
1. `docs/card-game-state-lifecycle-group-C-review-v0.1.md` — evidências, achados e políticas propostas.
2. `docs/card-game-state-lifecycle-group-C-decisions-v0.1.json` — as 10 decisões em formato estruturado.
3. `docs/examples/card-game-state-lifecycle-group-C.example.v0.1.json` — exemplo de concessões rastreáveis e expiração em descarte; não é schema.
4. `docs/card-game-state-lifecycle-group-C-validation-v0.1.json` e `docs/scripts/validate-card-game-state-lifecycle-group-C-v0.1.py` — 43 verificações reproduzíveis.
5. `docs/card-game-card-instance-contract-v0.3.md` e `docs/card-game-snapshot-causality-group-B-approval-v0.1.md` — contratos e decisões A/B aprovadas.

**Próximo gate recomendado:** aprovação ou ajuste do Grupo C. Depois, elaborar `CardInstance v0.4` como draft com as políticas de duração e transição. Grupos D, F e E permanecem pendentes; o runtime legado continua intacto.

---

# Estado mais recente — Grupo B auditado; decisões ainda abertas (2026-11-27)

O Grupo A permanece aprovado (CI-001/002/003/004/006/010, BUF-013 e RSRX-09). `CardInstance v0.2` continua como contrato candidato, não congelado. A auditoria do Grupo B foi concluída em modo somente leitura, usando o pacote rev. 7 como baseline.

**Relatório:** `docs/card-game-snapshot-causality-group-B-audit-v0.1.md`. **Matriz proposta:** `docs/card-game-snapshot-causality-group-B-decisions-v0.1.json`. **Harness:** `docs/scripts/audit-card-game-snapshot-causality-group-B-v0.1.py`. **Resultado:** 20/20 verificações do Grupo B passaram; regressões reexecutadas incluem Grupo A 30/30, CardInstance v0.2 30/30, matriz CI/BUF/RSRX 272/272, estados 41/41, remoção/ressurreição 49/49, catálogo 23/23, contrato de cartas 35/35, além das auditorias de buffs, líderes, UI, sequência, alvos e identidade. As suítes têm escopos diferentes. Não houve DB de produção, concorrência real ou integração.

**Achados centrais:** não existe manifesto imutável de releases de catálogo/efeitos/balanceamento por partida; o legado não cria `definition_snapshot`; `event_log` guarda até 20 mensagens textuais, não eventos causais; Chama Negra pode amplificar indiretamente a Vingança pelo diff global de bônus; Rykard produz +1 reativo de Vingança seguido por +2 direto quando a vítima possui Vingança.

**Conflito a resolver:** BUF-001 tem duas direções documentais: a especificação de balanceamento v0.1 diz que raridade deve ser classificação e que o amplificador deve ser removido; a revisão cruzada anterior propõe limitar amplificação aos outputs diretos. Este parecer recomenda a primeira opção, mas nenhuma está aprovada. CI-005/011, BUF-001/002/012 e RSRX-03/05 continuam abertas.

**Guardrails:** nenhum arquivo funcional foi alterado. Não criar migrador, não publicar release de catálogo, não mudar o amplificador do runtime e não integrar o grafo causal antes da aprovação explícita do Grupo B e do fechamento dos grupos dependentes.

Leia nesta ordem:
1. `docs/card-game-snapshot-causality-group-B-audit-v0.1.md` — evidências e proposta de arquitetura.
2. `docs/card-game-snapshot-causality-group-B-decisions-v0.1.json` — decisões em formato estruturado.
3. `docs/card-game-snapshot-causality-group-B-audit-v0.1.json` — saída dos 20 testes.
4. `docs/scripts/audit-card-game-snapshot-causality-group-B-v0.1.py` — reprodução.
5. `docs/card-game-card-instance-contract-v0.2.md` e `docs/card-game-cross-decision-review-ci-buf-rsrx-v0.1.md` — contratos e dependências anteriores.

**Próximo gate:** aprovação ou ajuste do Grupo B. O runtime antigo permanece intacto.

---

# Estado mais recente — Grupo A aprovado e `CardInstance v0.2` (2026-11-27)

O proprietário respondeu `ok, continue` à pergunta explícita de aprovação do Grupo A. O registro de aprovação cobre CI-001/002/003/004/006/010, BUF-013 e RSRX-09, conforme as propostas do parecer v0.1. A correção de CI-004 usa o DDL atual: `cartas_exemplares.id` é PK global; o vínculo precisa validar `user_id`/owner e `card_id`.

**Contrato atualizado:** `docs/card-game-card-instance-contract-v0.2.md`. O schema Draft 2020-12 do envelope está em `docs/schemas/card-game-card-instance-match.schema.v2.json`; o fragmento de seleção física em `docs/schemas/card-game-target-selection.schema.v1.json`; o exemplo em `docs/examples/card-instance-match.example.v2.json`.

**Validação nova:** `docs/card-game-card-instance-contract-validation-v0.2.json` e `docs/scripts/validate-card-game-card-instance-v0.2.py`. O harness executa 30 verificações sintéticas/estruturais e leitura estática do DDL; não testa integração, DB real, concorrência, HTTP, Discord ou produção.

**Limite atual:** apenas o Grupo A está aprovado. Grupos B/C/D/F/E e decisões CI/BUF/RSRX fora das oito chaves continuam abertos. `weather_resistance`, `policy.identity_only` e `result=applied` são placeholders/deprecated, não políticas aprovadas. Não iniciar migrador nem integrar ao runtime.

Leia nesta ordem:
1. `docs/card-game-identity-group-A-approval-v0.1.md` e `.json` — prova documental da aprovação e seu escopo.
2. `docs/card-game-card-instance-contract-v0.2.md` — contrato atualizado e decisões que permanecem abertas.
3. `docs/schemas/card-game-card-instance-match.schema.v2.json`, `docs/schemas/card-game-target-selection.schema.v1.json` e `docs/examples/card-instance-match.example.v2.json` — schemas e exemplo.
4. `docs/card-game-card-instance-contract-validation-v0.2.json` e `docs/scripts/validate-card-game-card-instance-v0.2.py` — 30 verificações reproduzíveis.
5. `docs/card-game-cross-decision-review-ci-buf-rsrx-v0.1.md` — dependências transversais e sequência dos grupos.

**Próximo gate recomendado:** Grupo B — snapshot e causalidade. O motor antigo permanece intacto.

---


# Estado mais recente — revisão cruzada CI/BUF/RSRX v0.1 (2026-11-27)

A revisão do pacote rev. 4 consolidou **14 decisões CI, 14 decisões BUF e 10 decisões de remoção/ressurreição (chaves RSRX locais deste parecer)**. Foram registradas recomendações técnicas e dependências; **nenhuma decisão foi aprovada**. O status permanece `TECHNICAL_RECOMMENDATIONS_FOR_OWNER_REVIEW_NOT_APPROVED`.

Leia nesta ordem:

1. `docs/card-game-cross-decision-review-ci-buf-rsrx-v0.1.md` — parecer completo, resoluções recomendadas, conflitos, grupos de dependência e gates de implementação.
2. `docs/card-game-cross-decision-review-ci-buf-rsrx-v0.1.json` — matriz estruturada das 38 decisões/referências, gaps de schema e resultados de regressão.
3. `docs/scripts/validate-card-game-cross-decision-review-v0.1.py` — valida a integridade estrutural da matriz; não valida regras de jogo.
4. `docs/card-game-card-instance-contract-v0.1.md` — contrato candidato atual, ainda não congelado.
5. `docs/card-game-buffs-decision-register-v0.1.md` — fonte original das decisões BUF.
6. `docs/card-game-removal-sacrifice-resurrection-review-v0.1.md` e `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md` — evidência e pendências RSRX.
7. `docs/card-game-handoff.md` — histórico e restrições de continuidade.

**Conclusão técnica:** não congelar ainda o schema CardInstance v1 nem iniciar o migrador. O campo escalar `weather_resistance`, a policy única `policy.identity_only` e o resultado único `applied` não cobrem as políticas BUF/RSRX necessárias. A persistência atual em `database.py` também não tem revisão/ledger dedicados; CI-014 exige decisão e teste real de transação.

**Validações reexecutadas:** CardInstance 30/30; RSRX 49/49; buffs/proteção 14/14; interações cruzadas 9/9; sequência 10/10; seleção TGT 15/15; paridade TUI 12/12; identidade/ciclo de vida 17/17. Suites independentes, não somáveis.

**Integridade:** somente documentação/scripts de validação sob `docs/` foram acrescentados ou atualizados nesta etapa. Nenhum runtime, catálogo ativo, schema de produção, DB, API, resolvedor, bot ou frontend foi modificado. O motor antigo permanece intacto.

**Próximo passo:** obter aprovação/ajuste dos grupos A (identidade), B (snapshot/causalidade) e C (estado/duração) antes de desenhar CardInstance v0.2. A migração fica bloqueada até fechar as dependências.

---

# Estado mais recente — contrato candidato `CardInstance` e transições de zona v0.1 (2026-11-27)

A etapa formalizou o modelo de identidade por ocorrência, o envelope de zonas, invariantes globais e uma operação de transição atômica/idempotente de referência. O envelope usa `state_revision` monotônica e `expected_revision` para rejeitar ações obsoletas; a persistência ainda exige CAS ou serialização equivalente (CI-014). Status: `CANDIDATE_FOR_REVIEW_NOT_APPROVED`; nenhuma decisão CI-001…CI-014 foi aprovada e nenhuma parte foi integrada ao runtime.

Leia nesta ordem:

1. `docs/card-game-card-instance-contract-v0.1.md` — contrato completo, evidências, invariantes, transições, migração e decisões CI-001…CI-014.
2. `docs/card-game-card-instance-match.schema.v1.json` — JSON Schema Draft 2020-12 para o envelope candidato.
3. `docs/examples/card-instance-match.example.v1.json` — snapshot de exemplo com duas ocorrências do mesmo `card_id`, cada uma com `instance_id` diferente.
4. `docs/card-game-card-instance-contract-validation-v0.1.json` — resultado estruturado dos 30 casos.
5. `docs/scripts/test-card-instance-contract-v0.1.py` — harness isolado; executar da raiz com `python docs/scripts/test-card-instance-contract-v0.1.py`.
6. `docs/card-game-identity-lifecycle-audit-v0.1.md` — evidência de origem do legado e ciclo de vida.
7. `docs/card-game-handoff.md` — continuidade técnica consolidada.

**Modelo proposto:** `card_id` identifica modelo; `exemplar_id` identifica um exemplar da coleção dentro do proprietário; `instance_id` identifica uma ocorrência física/virtual única no escopo global da partida. `instances` mantém um único registro por ocorrência e as quatro zonas (`hand`, `draw_pile`, `board`, `discard`) contêm apenas referências a esses registros. Toda ocorrência aparece em exatamente uma zona; `board` aceita somente unidades; cópias do mesmo modelo podem existir como instâncias distintas, sem alterar a regra atual do deck builder.

**Transição candidata:** `policy.identity_only` move uma referência entre zonas do mesmo proprietário, preserva integralmente o registro e seu estado, confirma a zona de origem esperada, usa `operation_id` UUIDv4 e ledger com fingerprint SHA-256; repetição idêntica é idempotente e reutilização conflitante falha. A normalização de bônus/escudo/estados fica em políticas nomeadas ainda não aprovadas.

**Validação:** 30/30 casos do harness candidato passaram. O schema passou pela meta-validação Draft 2020-12 e o exemplo foi validado sem erros com `jsonschema`. Regressões reexecutadas: identidade/ciclo de vida 17/17; paridade manual/UI/alvo 12/12; remoção/ressurreição 49/49; contrato canônico de cartas 35/35. Suítes com escopos independentes; não somar como uma cobertura única.

**Integridade:** somente `docs/` foi adicionado/alterado. `sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`, o catálogo ativo e os resolvedores candidatos permaneceram sem alterações nesta etapa. Sem acesso a DB real, API, navegador, Discord, R2 ou partidas de produção.

**Próximo passo:** revisar explicitamente CI-001…CI-014 e as políticas de estado RSRX/BUF. Só depois da aprovação criar migrador persistente e integração gradual. O runtime antigo continua preservado.

---

# Estado mais recente — identidade física e ciclo de vida de unidades v0.1 (2026-11-27)

A etapa atual auditou a identidade de modelo/exemplar/instância e o percurso de unidades entre mão, campo e descarte. Resultado: **17/17 assertions aprovadas**, com fixtures sintéticas e verificações estáticas. Status: `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`.

Leia nesta ordem:

1. `docs/card-game-identity-lifecycle-audit-v0.1.md` — achados, matriz de ciclo de vida, riscos, requisitos candidatos e limites.
2. `docs/card-game-identity-lifecycle-audit-v0.1.json` — resultados estruturados e referências das funções auditadas.
3. `docs/scripts/audit-card-identity-lifecycle-v0.1.py` — harness reproduzível; executar da raiz com `python docs/scripts/audit-card-identity-lifecycle-v0.1.py`.
4. `docs/card-game-removal-sacrifice-resurrection-review-v0.1.md` e `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md` — política candidata de remoção/retorno e interações anteriores.
5. `docs/card-game-manual-target-ui-parity-audit-v0.1.md` — serialização de alvos e risco de `target_id` ambíguo.
6. `docs/card-game-handoff.md` — continuidade técnica e restrições permanentes.

**Achados centrais:** a gravação atual de deck exige 12 modelos distintos, mas o snapshot loader só confere a quantidade; o caminho padrão de `preparar_carta()` perde `exemplar_id`; `novo_estado()` não cria `instance_id`; a UI/handler selecionam por `id`; `_remover_unidade()` usa igualdade estrutural e pode deixar o mesmo objeto em campo e descarte; Lágrima Sagrada preserva o payload ao voltar à mão; Réquiem e Ressurgir normalizam bônus/escudo, mas não zeram explicitamente estados em registros obsoletos; Esgar remove todas as entradas de descarte com o mesmo `id`. O resolvedor candidato usa identidade de objeto e `target_instance_id`, mas ainda não faz validação global de colisões entre zonas.

**Regressões direcionadas reexecutadas:** identidade/ciclo de vida 17/17; TUI 12/12; TGT 15/15; buffs/proteção 14/14; sequência 10/10; remoção/ressurreição 49/49; mapeamento de identidade 33/33; efeitos de ciclo de vida 7/7; estados negativos 41/41; catálogo de efeitos 23/23. Escopos distintos; não somar como uma única cobertura.

**Limites:** os casos usam fixtures sintéticas e análise estática; não foi aberto banco real nem sessão de produção. A possibilidade de snapshots antigos/malformados com duplicatas foi identificada no código, mas não prova que existam registros assim. Os estados obsoletos com status remanescente em Réquiem/Ressurgir também foram injetados deliberadamente; os caminhos centrais conhecidos limpam esses estados antes do descarte.

**Estado:** somente `docs/` foi alterado. Runtime, catálogo ativo, schema, banco, API, resolvedor candidato e frontend permanecem sem mudanças nesta etapa. Nenhuma regra foi aprovada e o motor antigo não deve ser substituído.

**Próximo passo desta etapa histórica (concluído):** a especificação candidata `CardInstance` e as transições de zona estão em `docs/card-game-card-instance-contract-v0.1.md`. A continuidade atual é revisar CI-001…CI-014 e as políticas BUF/RSRX antes de qualquer integração.

---

# Estado mais recente — paridade de seleção manual, UI e motor v0.1 (2026-11-27)

A etapa mais recente auditou a correspondência entre opções apresentadas, filtros locais da interface, payload `target_id`, validação do motor, fallback “Automático”, alvos secundários e alvos de relíquia. Resultado: **12/12 verificações aprovadas** (fixtures do motor + verificações estáticas do frontend). Status: `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`.

Leia nesta ordem:

1. `docs/card-game-manual-target-ui-parity-audit-v0.1.md` — resultados TUI-001…TUI-012, riscos, contratos candidatos e decisões pendentes.
2. `docs/card-game-manual-target-ui-parity-audit-v0.1.json` — resultados estruturados.
3. `docs/scripts/audit-manual-target-ui-parity-v0.1.py` — script reproduzível; executar da raiz com `python docs/scripts/audit-manual-target-ui-parity-v0.1.py`.
4. `docs/card-game-buffs-decision-register-v0.1.md` — adendo TUI à matriz BUF/TGT; nenhuma decisão foi aprovada.
5. `docs/card-game-target-selection-row-scope-audit-v0.1.md` — métricas e escopos de seleção automática.
6. `docs/card-game-handoff.md` — continuidade e limites operacionais.

**Achados centrais:** o seletor de Execução e os de recuperação exibem `poder + bonus`, embora a elegibilidade use respectivamente poder efetivo ou poder-base; o botão Automático possui fallbacks distintos por carta; Égide e Passo afetam alvos secundários não escolhidos individualmente; `target_id` não distingue instâncias físicas com IDs repetidos; a UI de relíquias recompõe opções localmente embora a API também envie `relic_options`; Algemas pode consumir-se sem reduzir bônus.

**Regressões reexecutadas nesta continuidade:** TUI 12/12; seleção automática TGT 15/15; buffs/proteção 14/14; interações cruzadas 9/9; sequência 10/10; estados 41/41; remoção/ressurreição 49/49; combos/passivas 87/87; líderes 22/22; comportamento de cartas 13/13; efeitos genéricos 39/39; contrato canônico 35/35; catálogo candidato 23/23; auditoria semântica 11/11. Escopos diferentes; não somar como uma única cobertura.

**Integridade:** comparado ao ZIP anterior desta continuidade, não há arquivos funcionais fora de `docs/` ausentes, adicionados ou alterados. Os cinco arquivos centrais (`sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`) permanecem idênticos por SHA-256.

**Estado:** somente documentação e instrumentos de auditoria foram alterados. Runtime, catálogo ativo, DB, API e frontend permanecem sem mudanças nesta etapa. Não aprovar automaticamente as recomendações e não substituir o motor legado.

---

# Estado mais recente — seleção de alvos e escopo de fileira v0.1 (2026-11-27)

A etapa mais recente auditou critérios de seleção automática, filtros por fileira corrente, métricas de poder, escudo/estado, limites de quantidade e desempate. O resultado foi **15/15 verificações aprovadas** em fixtures sintéticas que chamam funções reais do motor legado. Status: `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`.

Leia nesta ordem:

1. `docs/card-game-target-selection-row-scope-audit-v0.1.md` — matriz de escopo/métrica, achados, ramos ativos versus arquivados e requisitos candidatos.
2. `docs/card-game-target-selection-row-scope-audit-v0.1.json` — resultados estruturados dos 15 casos.
3. `docs/scripts/audit-target-selection-row-scope-v0.1.py` — auditoria reproduzível; executar a partir da raiz com `python docs/scripts/audit-target-selection-row-scope-v0.1.py`.
4. `docs/card-game-buffs-decision-register-v0.1.md` — adendo TGT para BUF-006, BUF-008 e BUF-013; nenhuma decisão foi fechada.
5. `docs/card-game-sequence-power-state-audit-v0.1.md` — histórico de `last_row`/sequência.
6. `docs/card-game-buffs-cross-interactions-v0.1.md` — nove cruzamentos anteriores entre movimento, clima, estados, raridade, combos, proteção e sacrifício.
7. `docs/card-game-handoff.md` — histórico consolidado e restrições permanentes.

**Achados centrais:** seletores que dizem “mais forte/mais fraco” podem ordenar por poder efetivo ou por bônus bruto, conforme o efeito; a elegibilidade de fileira consulta `row` corrente; alguns efeitos selecionam globalmente e outros limitam a uma fileira; empates em `max()`/`sorted()` preservam a primeira ordem do tabuleiro. O novo catálogo precisa declarar filtro, escopo, métrica, quantidade, fallback e desempate por efeito.

**Cuidado com branches órfãos:** Tiro de Cobertura e Contrafogo têm identidades filtradas por V18; `v75_blood_pursuit` e `v75_moon_ward` não têm binding individual ativo. Seus ramos não foram contados como capacidades ativas.

**Regressão preservada:** o runtime legado, o catálogo ativo, DB, API e frontend não foram modificados. Nenhuma decisão BUF foi aprovada. Não iniciar substituição do motor antes do fechamento dos contratos.

---

# Estado mais recente — sequência e ciclo de vida de `last_row` v0.1 (2026-11-27)

A auditoria de buffs/movimento revelou que efeitos de sequência usam o histórico de jogada do jogador, não a posição atual da unidade. Esta etapa fecha a evidência comportamental desse estado para as três habilidades genéricas ativas, sem aprovar ainda a regra definitiva.

Leia nesta ordem:

1. `docs/card-game-sequence-power-state-audit-v0.1.md` — dez casos, semântica do estado e requisitos candidatos.
2. `docs/card-game-sequence-power-state-audit-v0.1.json` — resultados estruturados.
3. `docs/scripts/audit-sequence-power-state-v0.1.py` — script reproduzível.
4. `docs/card-game-buffs-decision-register-v0.1.md` — BUF-008 atualizado com a evidência de `last_row`.
5. `docs/card-game-buffs-cross-interactions-v0.1.md` — nove cruzamentos anteriores entre movimento, clima, estado, raridade, combo, proteção e sacrifício.
6. `docs/card-game-effect-semantic-audit-v0.1.md` — família candidata `effect.sequence_power` e aliases ativos/arquivados.
7. `docs/card-game-handoff.md` — histórico técnico consolidado e restrições permanentes.

**Resultado:** 10/10 verificações passaram. `encadeamento` consulta a fileira da última unidade jogada pelo próprio jogador (igual: +2); `adaptacao` exige uma jogada anterior em outra fileira (+1); `quebra_ritmo` compara a fileira atual com a última unidade jogada pelo adversário (+1). Movimento, remoção e cartas especiais não reescrevem o histórico; a transição de rodada o redefine para `None`.

**Regressões reexecutadas:** auditoria base de buffs 14/14; matriz cruzada de buffs 9/9; estados 41/41; remoção/ressurreição 49/49; combos/passivas 87/87; líderes 22/22; comportamento genérico 13/13; catálogo de efeitos 23/23; auditoria semântica 11/11. O contrato canônico foi revalidado com 35/35 testes. Suites têm escopos distintos; não somar os resultados como cobertura única.

**Consequência de modelagem:** separar `current_row` da unidade e `last_unit_play_row` do jogador; histórico de movimento é outro dado. A recomendação é candidata, não aprovada.

**Estado:** `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`. Sem alteração no runtime, catálogo ativo, DB, API ou frontend. O motor antigo continua preservado.

**Próximo passo:** auditar as demais famílias de alta prioridade que dependem de estado e seleção, então revisar em conjunto BUF-001…BUF-014. Não iniciar substituição do motor antes do fechamento explícito dos contratos.

---

## Etapa anterior — matriz cruzada de interações v0.1 (2026-11-27)


A etapa atual amplia a auditoria de buffs/movimentação/proteção para cruzamentos com estados negativos, clima, combos, raridade, passivas e sacrifício. O status permanece `READ_ONLY_LEGACY_AUDIT; DIAGNOSTIC_ONLY; NOT_APPROVED_DESIGN`: nenhuma regra desta matriz foi aprovada ou integrada ao runtime. O motor antigo permanece preservado.

Leia nesta ordem:

1. `docs/card-game-buffs-cross-interactions-v0.1.md` — nove cruzamentos reproduzíveis, ordem de resolução e dependências de contrato.
2. `docs/card-game-buffs-cross-interactions-v0.1.json` — resultado estruturado dos nove casos.
3. `docs/scripts/audit-buffs-cross-interactions-v0.1.py` — script para repetir a bateria.
4. `docs/card-game-buffs-decision-register-v0.1.md` — registro das 14 decisões, alternativas e recomendações candidatas ainda não aprovadas.
5. `docs/card-game-buffs-movement-protection-audit-v0.1.md` — auditoria base e evidências BUF-001 a BUF-014.
6. `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md` — remoção, sacrifício, Vingança, retorno e combos.
7. `docs/card-game-status-effects-review-v0.1.md` — quatro estados, aplicações e purificadores.
8. `docs/card-game-combo-policy-v0.1.md` — política de combos aprovada e implementada.
9. `docs/card-game-handoff.md` — histórico técnico consolidado e restrições permanentes.

**Resultado:** 9/9 verificações cruzadas aprovadas. Foram comprovados: poder efetivo (clima + estados) influenciando seletores de alvos; purificação sem consumir escudo; Gravidade do Flagelo selecionando pela posição de origem e recalculando clima na posição de destino; combo usando `row` corrente após movimento; ordem combo → raridade → passiva de facção; Passo alterando a fileira corrente sem atualizar `last_row`; Preço em Sangue usando poder efetivo e ignorando escudo por sacrifício; Vingança não disparando quando escudo bloqueia a remoção.

**Validação de regressão nesta continuidade:** auditoria de buffs 14/14; estados candidatos 41/41; remoção/ressurreição 49/49; combos/passiva 87/87; líderes 22/22; comportamento genérico 13/13; contrato de cartas 35/35; catálogo de efeitos 23/23; auditoria semântica 11/11. Cada conjunto tem escopo próprio e não deve ser somado como cobertura única. Auditoria semântica: 11/11, executada isoladamente após uma chamada combinada ter excedido o tempo limite.

**Próximo passo:** revisar o registro `docs/card-game-buffs-decision-register-v0.1.md` e fechar as 14 decisões explicitamente. As recomendações são candidatas; nenhuma foi aprovada. Não substituir o motor antigo.

---

# Etapa anterior — buffs, movimentação, proteção e clima v0.1 (2026-11-27)

Esta foi a etapa de auditoria anterior. O status registrado foi `READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED`: o relatório descreve o comportamento do motor legado e decisões pendentes; **não é especificação aprovada e não foi integrado ao runtime**. A restrição permanece: não apagar nem substituir o motor antigo antes de fechar os contratos e as interações cruzadas.

Leia nesta ordem:

1. `docs/card-game-buffs-movement-protection-audit-v0.1.md` — evidências, semântica observada, inconsistências e decisões BUF-001 a BUF-014.
2. `docs/card-game-buffs-movement-protection-audit-v0.1.json` — 14 casos reproduzíveis e seus resultados.
3. `docs/scripts/audit-buffs-movement-protection-v0.1.py` — script de auditoria; executar com `python docs/scripts/audit-buffs-movement-protection-v0.1.py`.
4. `docs/card-game-removal-sacrifice-resurrection-review-v0.1.md` e `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md` — dependências com sacrifício, remoção, escudo e Vingança.
5. `docs/card-game-effect-semantic-audit-v0.1.md` — mapa de famílias candidatas e ramos legados.
6. `docs/card-game-handoff.md` — histórico por etapa, resultados, limites e estado global.

**Resultado:** 14/14 verificações direcionadas passaram. Foram confirmados: raridade pode amplificar Vingança disparada indiretamente pela Chama Negra; Égide Rara protege duas unidades embora seu texto estático seja singular; Passo Raro move até duas unidades; escudo não bloqueia universalmente status/debuffs e é ignorado por sacrifício; `weather_resist` persiste no objeto arquivado após limpeza de rodada. Também foi reproduzido o no-op silencioso de Bastião em fileira vazia e a validação mínima de duas unidades do Juramento.

**Escopo e cautela:** os testes usam fixtures sintéticas e funções reais do motor, sem banco, HTTP, Discord, navegador ou partida de produção. São testes de comportamento legado, não testes de balanceamento nem aprovação de design. As suites complementares anteriormente executadas — comportamento de efeitos 13/13, combos/passiva 87/87 e líderes 22/22 — mantêm escopos separados e não devem ser somadas como cobertura única.

**Achados centrais:** não foi localizada operação genérica de transferência de bônus; efeitos que reduzem bônus inimigo e concedem bônus a outra unidade são operações compostas distintas. `row` representa a posição corrente e muda com movimentação; `fileira` permanece como referência original. `weather_resist` não tem duração explicitada. Buffs com alvo “primeiro”, “mais fraco” ou “mais forte” possuem critérios/desempates que precisam ser formalizados.

**Próximo passo (superado pela etapa mais recente):** a matriz cruzada foi criada em `docs/card-game-buffs-cross-interactions-v0.1.md`; as decisões foram consolidadas em `docs/card-game-buffs-decision-register-v0.1.md`. O motor legado permanece preservado como evidência.

---

# Etapa anterior — remoção, execução, sacrifício e retorno do descarte v0.1 (2026-11-27)

Esta é a etapa atual. A proposta está marcada `CANDIDATE_FOR_REVIEW_NOT_APPROVED` e **não está conectada a `sistemas/gwent.py`**. Leia nesta ordem:

1. `docs/card-game-removal-sacrifice-resurrection-review-v0.1.md` — evidência de cada mecânica, defeitos comprovados, decisões pendentes e próximas etapas.
2. `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md` — 12 interações cruzadas e ordem exata dos efeitos de entrada/ressurreição.
3. `data/card_game/removal-resurrection-registry-candidate.v1.json` e `data/card_game/removal-resurrection-registry.schema.v1.json` — nove atribuições e contrato de remoção/retorno.
4. `sistemas/card_removal_resurrection_candidate.py` — resolvedor isolado de referência, não usado no runtime.
5. `docs/scripts/test-card-removal-resurrection-candidate-v0.1.py` e `docs/card-game-removal-resurrection-validation-v0.1.md/.json` — comando e resultado reproduzível.
6. `docs/card-game-handoff.md` — histórico por arquivo, estado global e continuidade.

**Resultado desta etapa:** nove atribuições mapeadas: Chama Negra, Lâmina da Morte Destinada, Devorar, Preço em Sangue, Rykard, Ressurgir, Chamado dos Mortos, Esgar e Lágrima Sagrada. A última é retorno à mão, não ressurreição. Foram comprovados defeitos de cópias físicas por igualdade de dicionário, descarte duplicado pelo Esgar, ausência de limpeza de status em Ressurgir/Réquiem, limite fixo 6 da Execução, no-op silencioso de Devorar sem aliado e interação Vingança + Rykard.

**Validação desta etapa:** 49/49 testes passaram (schema Draft 2020-12, módulo candidato e reprodução controlada de comportamentos legados). Esse número não se soma aos testes das etapas anteriores como se fosse uma única cobertura. O módulo é independente; nenhum handler legado, banco, API, frontend, imagem, custo ou catálogo de cartas foi alterado nesta etapa.

**Interações cruzadas confirmadas:** Vingança em Devorar fortalece somente aliados pré-existentes; Rykard acumula +1 da Vingança e +2 do líder (+3); a unidade ressuscitada só pode contribuir para combos de jogadas futuras porque entra depois da verificação de combo. O resolvedor candidato reconhece o `effect_id` canônico singular. Consulte a matriz de 12 interações.

**Decisões ainda pendentes:** limite da Execução no novo poder 1–15; no-target de Devorar; se sacrifício ativa Vingança e incrementa o contador de baixas; acumulação Vingança + Rykard; limites de poder para cada retorno; bônus e fileira de chegada; introdução de `instance_id` físico em exemplares e ações. Não integrar sem aprovação explícita.

**Próximo passo:** auditar buffs, movimento e efeitos de fileira, sempre cruzando com remoção/sacrifício/retorno; em seguida consolidar decisões de design e só então integrar o resolvedor. A matriz de interações atual está em `docs/card-game-removal-resurrection-interaction-matrix-v0.1.md`.

---

# Pacote de continuidade — leia primeiro

> **AVISO PARA UM CHAT NOVO: ESTE PACOTE FOI PREPARADO EXPRESSAMENTE PARA QUE OUTRO CHAT/AGENTE ASSUMA O DESENVOLVIMENTO DO ZERO, SEM ACESSO A ESTA CONVERSA E SEM DEPENDER DE EXPLICAÇÕES ADICIONAIS DO USUÁRIO.** O ZIP contém o código-fonte disponível e os documentos de contexto necessários para retomar a auditoria e a reconstrução do jogo de cartas. Trate o conteúdo deste pacote como o ponto de partida da nova sessão; não peça ao usuário para repetir informações que já estejam documentadas.

## Etapa anterior — auditoria e proposta dos quatro estados negativos v0.1 (2026-11-27)

A revisão mais recente cobre Geada, Podridão Escarlate, Sangramento e Loucura Frenética. Leia primeiro `docs/card-game-status-effects-review-v0.1.md`, depois `data/card_game/status-registry-candidate.v1.json`, `data/card_game/status-registry.schema.v1.json`, `sistemas/card_status_candidate.py` e `docs/card-game-status-effects-validation-v0.1.md/.json`. O registry é explicitamente `CANDIDATE_FOR_REVIEW_NOT_APPROVED`; o resolvedor é independente e **não está conectado** ao motor legado.

**Resultado:** quatro perfis de estado; 15 aplicações mapeadas (sete especiais, cinco identidades, dois líderes e uma relíquia); cinco caminhos de purificação. A proposta mantém máximo de duas marcas, cap agregado de -3 para Geada/Podridão/Loucura, Sangramento sem penalidade direta de poder, consequências de limiar apenas na transição para duas marcas, e nenhuma amplificação oculta por raridade. Expiração proposta no fechamento de toda rodada, inclusive a final.

**Riscos legados comprovados:** Malenia pode repetir corrosão de Podridão no limite; Oráculo da Geada pode repetir bônus próprio quando o alvo já está no limite; amplificação geral de raridade pode duplicar alteração de bônus; algumas aplicações por raridade escolhem alvos pela ordem do tabuleiro; snapshot terminal pode conservar estados. A proposta corrige esses pontos, mas ainda aguarda aprovação.

**Validação atual desta revisão:** 41/41 testes do resolvedor candidato; JSON Schema Draft 2020-12 e instância válidos; contrato 35/35; catálogo 23/23; auditoria semântica 11/11; motor legado 251/251 em oito suites; stateful 12/12. São suites de escopos distintos, não uma métrica de balanceamento. Os cinco arquivos funcionais principais (`sistemas/gwent.py`, `sistemas/cartas.py`, `bot.py`, `database.py`, `site/app.js`) continuam byte a byte iguais ao ZIP mestre aberto no início desta etapa. Nenhum handler legado, banco, API, frontend ou imagem foi modificado.

**Próximo passo:** revisar/aprovar ou ajustar a proposta de estados; em seguida prosseguir para remoção/execução, sacrifício e ressurreição. Não integrar os estados nem limpar código legado sem decisão explícita.

## Estado anterior — catálogo candidato + auditoria semântica v0.1 (2026-11-27)

A referência atual para a consolidação do catálogo é `docs/card-game-effect-catalog-decision-v0.1.md`. Foram mapeadas 54 famílias canônicas candidatas (36 unidade, 12 especiais e seis relíquias), todos os 59 IDs de `HABILIDADES` (32 unidades, 21 especiais e seis relíquias), 22 overrides de identidade (16 suprimem uma habilidade genérica na execução antiga), 27 combos, dez líderes e quatro passivas de facção. O mapa de alias preserva nomes/textos originais, parâmetros default, IDs das cartas atualmente atribuídas e uma disposição proposta por alias (manter, fundir, redesenhar ou remover do novo runtime).

**Auditoria semântica adicionada:** `docs/card-game-effect-semantic-audit-v0.1.md/.json` liga cada uma das 54 famílias candidatas aos aliases, localizações AST, handlers ou hooks encontrados, e registra diferenças de condição/alvo/limite/duração. Classificação heurística de revisão: 18 famílias HIGH, seis MEDIUM e 30 LOW (não equivale a aprovação). Cobertura do catálogo legado: 59 IDs — 56 branches diretos, dois hooks de ciclo de vida (`vinganca`, `espolios`) e um sem handler (`sobrevivente`); `gloria` é um hook separado em `_resolve_round()`. As 22 identidades ativas têm branch localizado; quatro campos antigos têm branch de resolver mas nenhum binding ativo.

**Validação atual:** `docs/scripts/test-effect-catalog-candidate-v0.1.py` passou 23/23; auditoria semântica AST gerada e `docs/scripts/test-effect-semantic-audit-v0.1.py` passou 11/11. O registry candidato passou JSON Schema Draft 2020-12 e `validate_effect_registry()`. Os testes de base continuam 35/35 do contrato, 251/251 do motor legado, 12/12 stateful e 32/32 da política de combos, cada conjunto com escopo próprio. Nenhum handler novo está implementado, nenhuma carta nova recebeu estes efeitos e nenhum arquivo funcional de runtime foi alterado nesta etapa.

Leia também `docs/card-game-effect-semantic-audit-v0.1.md/.json` para a comparação manual de semântica, além de `data/card_game/effect-registry-candidate.v1.json`, `data/card_game/legacy-effect-aliases-v0.1.json`, `data/card_game/leader-registry-candidate.v1.json`, `data/card_game/faction-passives-candidate.v1.json` e `docs/card-game-effect-catalog-validation-v0.1.md/.json`. Este é um candidato para revisão de equivalência semântica, **não** catálogo aprovado. EFP, custo, raridade e as atribuições das novas cartas seguem pendentes.

**Próximo passo:** comparar os efeitos agrupados em cada família pelos resultados reais do motor antigo; dividir famílias compostas quando condições/alvos/limites não forem equivalentes e então classificar cada ramo como keep/merge/redesign/remove. Não conectar ao runtime nem apagar o legado antes da revisão.




## Contexto operacional confirmado pelo proprietário (2026-11-27)

Leia `docs/PROJECT-OPERATING-CONTEXT.md`. O proprietário informou que o jogo ainda não tem jogadores reais; quaisquer contas/registros são testes feitos por ele. Essa informação não foi verificada contra serviços externos, mas altera a estratégia: não é preciso desenhar migrações complexas para preservar progresso de uma comunidade. O inventário real de SQLite/R2 é opcional e só deve bloquear o trabalho quando precisarmos preservar/reutilizar artes ou registros específicos. Dados de teste podem ser resetados/recriados quando o escopo do reset estiver claro. Isso **não** autoriza apagar indiscriminadamente artes, bucket R2, configurações ou credenciais.

## Estado atual — primeira camada da reconstrução canônica (2026-11-27)

Foi criado o contrato estrutural v1 em `docs/card-game-canonical-model-v1.md`, `data/card_game/card-definition.schema.v1.json`, `data/card_game/effect-registry.schema.v1.json` e `sistemas/card_contract.py`. O snapshot histórico `data/card_game/catalog-legacy-baseline-v0.1.json` captura 137 modelos: 110 unidades, 21 especiais e seis relíquias. Relíquias ficam em slot separado. O baseline tem 15 cartas puras (10,95% dos modelos); a quota mínima de 30% exige 42. O novo catálogo ainda não está ligado ao runtime.

**Validação desta etapa v1.1:** 35/35 testes `unittest`; CLI testado com catálogo sintético válido e inválido; os dois JSON Schemas Draft 2020-12 foram verificados e os dois exemplos passaram; snapshot gerado duas vezes com SHA-256 idêntico. O validador agora confere tipos, limites, parâmetros obrigatórios e chaves extras de cada efeito, além de IDs e prioridades únicas e mínimo de dois participantes em combos. A fórmula EFP/custo/raridade e teto de deck permanecem não aprovados e não implementados. A política de combos aprovada continua vigente.

**Arquivos novos/atualizados para ler:** `docs/card-game-contract-validation-v1.1.md/.json`, `docs/card-game-canonical-model-v1.md`, `docs/card-game-legacy-baseline-v0.1.md`, `data/card_game/README.md`, `data/card_game/catalog-legacy-baseline-v0.1.json`, os dois schemas em `data/card_game/` e os scripts `build-card-catalog-baseline-v0.1.py`, `test-card-contract-v1.py`, `validate-card-catalog-v1.py` e `validate-card-json-schemas-v1.1.py`.

## Estado anterior — auditoria HTTP estática (referência histórica)


A revisão documental mais recente produziu um mapa estático de 12 rotas Gwent em `card-game-http-contract-map-v0.1.md/.json`, gerado por `scripts/audit-gwent-http-contracts-v0.1.py`. O mapa identificou que o backend ainda não soma custo no salvamento de deck e que `preparar_carta()` descarta `payload['custo']` porque não o retorna. A integração HTTP real continua pendente por ausência de `discord.py`/`aiosqlite` e bloqueio de DNS na instalação.

A política de combos v0.1 foi aprovada pelo usuário e já está implementada em `sistemas/gwent.py`. O novo chat deve tratá-la como regra oficial atual, não como decisão pendente. Os 27 combos agora têm mínimo explícito de duas instâncias distintas e prioridade única; a carta que recebe o bônus individual precisa contribuir com tag exigida; apenas um combo ativa por jogada; combos pendentes exigem um participante posterior. Os demais parâmetros de balanceamento (EFP, custos, raridade e teto de deck) continuam propostas não aprovadas.

**Última validação:** oito suites comportamentais, 251/251 asserts; separadamente, a suíte stateful passou 12/12 cenários. Foram percorridas quatro partidas controladas de três rodadas pelo motor em memória, com snapshots JSON; 137/137 modelos foram preparados; também foram verificados combo por jogadas normais, líder + especial climático, relíquia, clima manual, compatibilidade de snapshot legado e round-trip de `state_json` com DDL real em SQLite `:memory:`. A verificação bot/site é estática: os handlers HTTP e o wrapper assíncrono de banco não foram executados porque `discord.py` e `aiosqlite` não estão instalados no ambiente de análise. A instalação temporária via `pip` foi tentada e falhou por indisponibilidade de DNS/rede; não foram criados mocks ou stubs. Não confundir esses testes controlados com partidas competitivas, DB ou produção.

Partidas já persistidas preservam bônus de combos concedidos antes do deploy. A política nova vale nas próximas jogadas resolvidas após atualização do processo; o DB de produção não veio no ZIP e não foi migrado.

## Estado mais recente — auditoria de produção read-only preparada (2026-11-27)

O pacote contém um runbook e ferramentas locais para inventariar SQLite, Cloudflare R2 e referências de arte sem expor credenciais. Os sete testes locais passaram com fixtures, inclusive snapshot em WAL; **nenhuma fonte real foi acessada**. À luz do contexto operacional informado pelo proprietário (jogo sem jogadores reais; somente dados de teste), executar esse runbook **não é pré-requisito para continuar a reconstrução**. Use-o apenas se houver necessidade de preservar ou reutilizar artes, submissões ou registros existentes. Não invente contagens reais.

**Arquivos novos prioritários:**
- `docs/card-game-production-audit-runbook-v0.1.md` — comandos operacionais e modelo dos quatro pipelines de arte.
- `docs/scripts/snapshot-sqlite-readonly-v0.1.py` — snapshot SQLite consistente, origem `mode=ro`.
- `docs/scripts/audit-production-card-db-v0.1.py` — relatório DB sanitizado; opcional `--verify-local-generated-art`.
- `docs/scripts/inventory-r2-readonly-v0.1.py` — somente `ListObjectsV2`, hashes das chaves, sem download ou mutação.
- `docs/scripts/reconcile-production-card-assets-v0.1.py` — DB↔R2; exige inventário completo do bucket primário.
- `docs/scripts/test-production-audit-tooling-v0.1.py` — 7 testes sintéticos reproduzíveis, incluindo fixture SQLite em WAL.

Não incluir snapshot `.sqlite3`, `.env`, tokens, chaves R2, imagens ou inventários com chaves brutas no ZIP mestre. Os scripts exportam hashes e resumos e gravam relatórios operacionais fora do repositório. Compartilhar preferencialmente somente `card-game-production-assets-reconciliation.json`.

**Quatro origens de arte:** `cartas_atelie_submissoes` (R2 `atelier/submissions/` e BLOB legado), `cartas_atelie_artes` (referências de anexos Discord), `cartas_gwent_lideres_artes` (BLOB SQLite), e `cartas_geradas`/`cartas_geradas_artes` (PNG local em `DATA_DIR/cartas_geradas/` com SHA-256). R2 `cards/` é cache/CDN e não equivale a arte original aprovada.

## Instrução de entrada para o próximo chat

Ao receber este pacote, faça o seguinte antes de alterar qualquer arquivo:

1. Confirme que recebeu e conseguiu abrir `soulsbo-main-continuity-2026-11-27-rev4.zip`.
2. Leia este arquivo (`docs/README-PACOTE-CONTINUIDADE.md`) e `docs/PROJECT-OPERATING-CONTEXT.md`; depois siga a **Ordem obrigatória de leitura** abaixo.
3. Leia `docs/card-game-handoff.md` integralmente, inclusive o quadro de completude dos quatro blocos da Regra 8, o estado exato, o histórico e os próximos passos.
4. Consulte a auditoria, matriz de 137 cartas, catálogo EFP, especificação v0.1 e script/amostragem. Não deduza regras ausentes a partir de nomes ou de conversas anteriores.
5. Diferencie sempre: (a) comportamento comprovado no código-base, (b) requisito confirmado pelo usuário, (c) proposta ainda não aprovada e (d) hipótese que exige teste.
6. Não implemente nem remova mecânicas antes de validar as pendências registradas no handoff. Não trate `card-game-balance-spec-v0.1.md` como especificação aprovada.
7. Antes de encerrar qualquer etapa, atualize os documentos afetados, registre cada alteração por arquivo/função/campo/motivo/impacto/validação e gere um novo ZIP mestre com o projeto e todos os documentos necessários.

**Mensagem inicial sugerida para o novo chat:**

> Leia integralmente `docs/README-PACOTE-CONTINUIDADE.md`, `docs/card-game-handoff.md`, `docs/card-game-mapping-audit.md` e os documentos referenciados. Assuma a continuidade do projeto a partir deste pacote, sem depender do chat anterior. Primeiro informe o estado comprovado, as lacunas conhecidas e o próximo passo autorizado. Trate `card-game-combo-policy-v0.1.md` como política de combos aprovada e implementada. Trate `card-game-canonical-model-v1.md` como contrato estrutural novo, ainda não conectado ao runtime, e o snapshot legado como fotografia, não como catálogo novo. Não reverta a política de combos. Diferencie requisitos confirmados das propostas EFP/custo/raridade ainda não aprovadas. Em toda entrega, atualize e forneça um único ZIP mestre.

Este pacote contém uma cópia do projeto-fonte disponível e toda a documentação de auditoria/continuidade produzida para o trabalho de reconstrução do jogo de cartas. Use este arquivo como índice de entrada quando iniciar um novo chat ou agente.

## Manifesto do pacote

Consulte também [`docs/PACOTE-MANIFESTO.md`](PACOTE-MANIFESTO.md) para escopo, modificações e validações desta revisão.

## Ordem obrigatória de leitura

### Leitura prioritária da revisão atual

1. `docs/card-game-status-effects-review-v0.1.md` e `docs/card-game-status-effects-validation-v0.1.md/.json` — auditoria fonte a fonte de Geada, Podridão, Sangramento, Loucura, aplicadores, purificadores, amplificação de raridade, riscos e testes. É a etapa mais recente, mas continua candidata, não aprovada.
2. `data/card_game/status-registry-candidate.v1.json` e `data/card_game/status-registry.schema.v1.json` — perfis e mapeamentos de estado, ainda sem runtime.
3. `sistemas/card_status_candidate.py` e `docs/scripts/test-card-status-candidate-v0.1.py` — resolvedor de referência isolado e 41 testes. Não importar no motor legado antes da aprovação.
4. `docs/card-game-effect-catalog-decision-v0.1.md` — revisão das 54 famílias candidatas, IDs legados, cartas atualmente atribuídas, combos e ramos antigos.
5. `docs/card-game-effect-semantic-audit-v0.1.md/.json` — 54 famílias ligadas aos branches AST; 56 handlers diretos, dois hooks e um ID sem handler; riscos e divergências semânticas.
6. `docs/card-game-effect-catalog-validation-v0.1.md/.json` — evidência de 23/23 testes estruturais, 11/11 testes semânticos, validação do registry e limites.
7. `data/card_game/effect-registry-candidate.v1.json` e `data/card_game/legacy-effect-aliases-v0.1.json` — registry proposto e ponte detalhada por ID.
8. `data/card_game/leader-registry-candidate.v1.json` e `data/card_game/faction-passives-candidate.v1.json` — líderes e passivas em slots separados.
9. `docs/scripts/build-effect-catalog-candidate-v0.1.py`, `test-effect-catalog-candidate-v0.1.py`, `audit-effect-semantic-groups-v0.1.py`, `test-effect-semantic-audit-v0.1.py` e `summarize-effect-catalog-candidate-v0.1.py` — reprodução e verificação.

1. `docs/card-game-effect-catalog-decision-v0.1.md` — revisão das 54 famílias candidatas, IDs legados, cartas atualmente atribuídas, combos e ramos antigos.
2. `docs/card-game-effect-semantic-audit-v0.1.md/.json` — 54 famílias ligadas aos branches AST; 56 handlers diretos, dois hooks e um ID sem handler; riscos e divergências semânticas.
3. `docs/card-game-effect-catalog-validation-v0.1.md/.json` — evidência de 23/23 testes estruturais, 11/11 testes semânticos, validação do registry e limites.
4. `data/card_game/effect-registry-candidate.v1.json` e `data/card_game/legacy-effect-aliases-v0.1.json` — registry proposto e ponte detalhada por ID.
5. `data/card_game/leader-registry-candidate.v1.json` e `data/card_game/faction-passives-candidate.v1.json` — líderes e passivas em slots separados.
6. `docs/scripts/build-effect-catalog-candidate-v0.1.py`, `test-effect-catalog-candidate-v0.1.py`, `audit-effect-semantic-groups-v0.1.py`, `test-effect-semantic-audit-v0.1.py` e `summarize-effect-catalog-candidate-v0.1.py` — reprodução e verificação.

**Nota de precedência:** a lista numerada acima é a leitura da revisão atual; a lista histórica que segue continua como mapa ampliado de todo o pacote, incluindo os artefatos antigos.

**Revisão semântica obrigatória:** `effect.sequence_power` agora declara `requires_previous_play=true` em todos os aliases porque o motor legado não concede bônus sem `last_row` válido. `gloria` tem hook funcional de vitória de rodada; `sobrevivente` é apenas texto sem handler e não pode ser migrado como equivalente. A família `effect.round_victory_survivor` é proposta nova que exige aprovação, não um merge comprovado.

**Não assumir aprovação:** o registry é candidato; os handlers são nomes futuros, não implementações. Nenhum efeito foi apagado nem atribuído às novas cartas. Primeiro revisar equivalência semântica das famílias e classificar `keep/merge/redesign/remove`.

### Contexto estrutural e histórico

1. `docs/PROJECT-OPERATING-CONTEXT.md` — informação do proprietário sobre ausência de jogadores reais e consequências para migração/reset.
2. `docs/card-game-handoff.md` — estado atual, decisões confirmadas, auditoria, Regra 8, histórico e próximos passos.
3. `docs/card-game-canonical-model-v1.md` — contrato estrutural do novo modelo; não está ligado ao runtime antigo.
4. `docs/card-game-legacy-baseline-v0.1.md` e `data/card_game/catalog-legacy-baseline-v0.1.json` — fotografia histórica dos 137 modelos; não usar como catálogo novo.
5. `sistemas/card_contract.py`, `data/card_game/card-definition.schema.v1.json`, `data/card_game/effect-registry.schema.v1.json` e `docs/scripts/test-card-contract-v1.py` — contrato, schemas e 35 testes.
6. `docs/scripts/build-card-catalog-baseline-v0.1.py`, `docs/scripts/validate-card-catalog-v1.py` e `docs/scripts/validate-card-json-schemas-v1.1.py` — geração do snapshot e validação do catálogo/registry.
7. `docs/card-game-contract-validation-v1.1.md/.json` — resultados e limites da validação da fundação estrutural.
8. `docs/card-game-combo-policy-v0.1.md` — contrato oficial dos 27 combos, aprovado e implementado.
9. `docs/card-game-behavior-validation-v0.3.md/.json` + `docs/scripts/summarize-card-game-behavior-v0.3.py` — oito suites, 251/251 asserts comportamentais isolados.
10. `docs/card-game-match-snapshot-integration-v0.1.md/.json` + `docs/scripts/assert-full-match-stateful-v0.1.py` — 12/12 cenários stateful; HTTP real não executado.
11. `docs/card-game-http-contract-map-v0.1.md/.json` + `docs/scripts/audit-gwent-http-contracts-v0.1.py` — mapa estático das 12 rotas e contrato de custo ainda ausente.
12. `docs/card-game-combo-overlap-v0.2.md/.json` + `docs/scripts/audit-combo-overlap-v0.2.py` — auditoria enumerativa após a correção.
13. `docs/scripts/assert-combo-policy-v0.1.py` + `docs/card-game-combo-policy-assertions-v0.1.json` — regressões específicas da política aprovada.
14. `docs/card-game-mapping-audit.md` — arquitetura, arquivos, APIs, banco, eventos, habilidades, combos, líderes, relíquias, arte e nota do contrato novo.
15. `docs/card-game-effect-source-map-v0.2.json` + `docs/scripts/build-effect-source-map-v0.2.py` — mapa AST atual; v0.1 é histórico congelado.
16. Suites individuais e relatórios JSON de identidade, habilidades genéricas, ciclo de vida, especiais/relíquias, líderes e combos/passivas.
17. `docs/card-game-stale-identity-disposition-v0.1.md/.json` + script — classificação de 28 ramos antigos; recomendações, não remoções.
18. `docs/card-game-card-traceability.md/.csv/.json` — matriz dos 137 modelos do baseline; verificar campos derivados após alterações no catálogo.
19. `docs/card-game-effect-score-catalog.json` e `docs/card-game-efp-methodology-v0.2.md` — EFP preliminar/metodologia, ainda não aprovados.
20. `docs/card-game-balance-spec-v0.1.md` e `docs/card-game-balance-validation-v0.1.md` — propostas e validação exploratória de custo/raridade, não implementadas.
21. `docs/card-game-deck-cost-sampling-v0.2.json` + script e `docs/card-game-combo-activation-v0.1.json` + script — amostragens exploratórias, não simulações competitivas.
22. `docs/card-game-combo-overlap-v0.1.md/.json` — histórico congelado do defeito pré-correção; para estado atual usar v0.2.
23. `docs/card-game-production-audit-runbook-v0.1.md` — runbook opcional para preservar/recuperar ativos; não é gate para continuar.
24. `docs/card-game-handler-coverage-v0.1.json`, `docs/card-game-effect-runtime-smoke-v0.1.json` e os demais scripts — cobertura estática e testes de fumaça com limites declarados.
25. Os demais arquivos de `docs/` — documentação preexistente; conferir as advertências do handoff antes de tratá-los como regra atual.

## Resumo de orientação da proposta de balanceamento v0.1

> A proposta é **rascunho técnico, não aprovada e não implementada**. Não aplicar estes números ao runtime sem simulação e aprovação do usuário.

- **Poder:** requisito do proprietário: poder-base das unidades estritamente entre 1 e 15. O contrato estrutural v1 usa `power_base=null` para especiais e relíquias porque não são corpos de combate; isso é uma convenção de modelagem explícita, não poder 0.
- **Pureza:** requisito confirmado: mínimo de `ceil(0,30 × N_modelos)`. No baseline de 137 modelos (110 unidades, 21 especiais, seis relíquias), a quota é 42 unidades puras. A meta opcional de 35% não foi aprovada.
- **EFP:** escala provisória para estimar poder, remoção, compra, ressurreição, escudo, purificação, movimento e combos. Scores são hipóteses; `null` significa efeito incompleto/não validado, não efeito zero.
- **Custo:** unidades `C = clamp(ceil((P + 2E) / 3,5), 1, 10)`; especiais `C = clamp(ceil((2E) / 3,5), 1, 10)`.
- **Deck:** teto experimental 32 foi testado em cenários de 12 cartas + `leader_load`, com e sem relíquia equipada. A inclusão de relíquia e carga do líder no orçamento, bem como o teto, ainda não foi aprovada. As regras atuais do deck builder (12 cartas, mínimo 8 unidades, máximo 4 especiais) permanecem distintas da proposta.
- **Raridade:** `R = 2P + 3E + 0,5(10-C)`, com faixas de Comum a Singular documentadas no spec. Raridade não deve aumentar secretamente a força do efeito.
- **Distribuição:** manifesto versionado por `card_id`; nenhuma seleção mecânica por sorteio/hash. RNG, se mantido, apenas para cosméticos.
- **Lore/facções:** Ordem Áurea, Véu Carmesim, Lua Negra e Os Esquecidos têm diretrizes temáticas próprias; lore separada da descrição mecânica.

A amostragem de 100.000 decks é uma análise de distribuição de custo, **não** simulação de partidas nem prova de equilíbrio. A primeira amostragem v0.1 está superada; o v0.2 inclui cenários com/sem relíquia, mas ainda depende de EFP estimado. A frequência de combos foi medida separadamente sob ordem aleatória; isso não mede efeito no resultado. Consulte `card-game-balance-validation-v0.1.md` antes de qualquer alteração.

## Estado desta entrega

- Baseline do projeto: ZIP recebido `soulsbo-main(1).zip`, datado no registro da auditoria como 2026-11-27; pacote mestre atualizado após cada etapa.
- Trabalho funcional concluído nesta etapa: política de combos v0.1 aprovada e implementada em `sistemas/gwent.py`. Nenhum outro arquivo funcional, schema de banco, endpoint, frontend ou imagem foi modificado.
- Regras atuais de combos: `minimum: 2` em todas as 27 definições; `priority` único; carta atual contribui com tag requerida; uma ativação por jogada; combo pendente só dispara por participante posterior; bônus individual para a carta participante; bônus de equipe existente preservado.
- Diagnósticos atuais: mapa estático das 12 rotas Gwent, sem dispatch HTTP real; oito suites comportamentais, 251/251 asserts; separadamente, integração stateful 12/12. Quatro partidas controladas de três rodadas percorreram o motor em memória; 137 payloads foram preparados; combo por jogadas normais, líder/especial/clima, relíquia, clima manual, snapshot legado e round-trip de `state_json` passaram. A análise bot/site é estática e HTTP não foi executado.
- Trabalho documental: regra oficial de combos, relatório pós-política, regressões, mapa de fonte AST e mapa estático das 12 rotas HTTP atualizados; auditorias pré-patch preservadas como histórico.
- Limitações: o `POST /api/gwent/deck` ainda não calcula orçamento; `preparar_carta()` não devolve `custo` e descarta esse atributo dos payloads que o recebem antes da preparação. A análise é estática; partidas ativas conservam bônus já concedidos; DB de produção, credenciais, configuração de execução, estado publicado de R2 e artes aprovadas não vieram com o ZIP. Não houve migração/inspeção de produção.
- Próximos passos: obter um ambiente com `discord.py==2.7.1` e `aiosqlite==0.22.1` instalados (ou wheels locais, pois o pip não alcançou o índice por falha de DNS nesta sessão); executar dispatch HTTP real com `aiohttp.TestClient`, persistência pela classe `Database`, convites, solo/IA, autenticação e recompensas; validar respostas no browser e imagens/R2. Depois ampliar partidas para decks legais obtidos pelo deck builder, testar interações cruzadas/IA e só então simular equilíbrio e calibrar EFP/custo/raridade. A proposta de balanceamento v0.1 permanece não aprovada.
- `docs/CARD_GAME_REDESIGN.md` permanece documentação antiga e não deve prevalecer sobre o motor nem sobre regras aprovadas no handoff.

## Regra de continuidade

A cada nova entrega, atualizar os documentos afetados e recriar um único ZIP contendo o projeto disponível e todos os materiais de handoff. O arquivo mais recente é a referência; não exigir que o próximo chat consulte mensagens anteriores. Consulte `docs/card-game-handoff.md`, seção **Regra permanente de pacote de continuidade**.

## Exclusões conscientes do pacote

Arquivos de cache Python (`__pycache__`, `*.pyc`) e binários locais de fontes tipográficas não são incluídos neste pacote de handoff. O código-fonte e as referências a esses recursos permanecem presentes. O pacote é destinado à continuidade da análise e desenvolvimento; para validar renderização visual pixel a pixel, os assets tipográficos originais do ambiente do projeto podem ser necessários.



## Estado de continuidade — revisão 14 (2026-11-27)

- Grupos A, B, C, D e F aprovados. Grupo E auditado e aguardando aprovação.
- `CardInstance v0.6` é draft; inclui causas canônicas de remoção, Vingança e contadores separados.
- Grupo E encontrou `BEGIN IMMEDIATE` e WAL úteis, mas sem `state_revision` persistida, ledger de ações, journal/outbox ou migration ledger.
- Auditoria E: 24/24 verificações com SQLite isolado; não houve acesso ao banco de produção nem execução de aiosqlite/HTTP.
- Não houve alteração fora de `docs/`; runtime e banco permanecem intactos.

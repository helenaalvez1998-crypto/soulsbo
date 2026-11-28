# Manifesto de mudanças — Deck Builder com proveniência física (rev. 27)

**Baseline:** rev. 26.  
**Resultado:** integração de `cartas_exemplares.id` até ao snapshot da partida; sem alteração do motor legado.

## Código alterado

- `sistemas/card_engine_v2/deck_builder.py` — validação um-para-um de exemplar, proprietário, modelo e atributos individuais; embaralhamento de slots pareados.
- `sistemas/card_engine_v2/deck_repository.py` — schema v2; persistência de `exemplar_ids_json`; migração v1 sem inventar IDs físicos.
- `sistemas/card_engine_v2/application.py` — save/validate e matchmaking revalidam exemplares; adapter somente leitura de coleção legada; projeção por jogador; seeds de embaralhamento não fazem parte da API de aplicação.
- `sistemas/card_engine_v2/match.py` — criação de `deck_exemplar` com poder congelado e view com privacidade de mão.
- `sistemas/card_engine_v2/models.py` e `validation.py` — contrato/runtime de `exemplar_snapshot` e proveniência obrigatória para novos exemplares competitivos.
- `sistemas/card_engine_v2/power.py`, `leaders.py` e `targeting.py` — usam a projeção de poder individual da instância.
- `sistemas/card_engine_v2/alpha_catalog.py` — inclui `Primordial` no vocabulário de classificação visual.

## Contratos e testes alterados

- `docs/schemas/card-game-card-instance-match.schema.v7.json` e `docs/examples/card-instance-match.example.v7.json` — snapshot individual e valor classificatório `primordial`.
- `tests/card_engine_v2/test_deck_builder.py`, `test_deck_repository_application.py` e `test_combat.py` — proveniência, revalidação, unicidade global, evolução/aprimoramento, privacidade de view e invariância da raridade.
- `docs/scripts/test-card-engine-v2-playable-alpha-v0.5.py` — relatório oficial cobre proveniência física, view segura por jogador e bloqueio de seeds de embaralhamento na API sync/async de aplicação.
- `sistemas/card_engine_v2/README.md` — exemplos e limites atualizados para `exemplar_ids`.

## Evidência

- 188/188 testes oficiais.
- `py_compile` aprovado.
- Staging 137/27/110 aprovado.
- Bo3 A 2–1 B, 97 eventos, SQLite íntegro.
- Demo combos/passivas/líderes 20–10, 49 eventos, SQLite íntegro.
- Migração de saved-decks v1→v2 testada; decks antigos ficam sem proveniência e são recusados no matchmaking até serem revalidados e gravados novamente.

## Fora do escopo

- Nenhuma alteração em `database.py`, `bot.py`, `sistemas/gwent.py`, `sistemas/cartas.py`, `site/app.js`.
- Nenhum handler Discord/HTTP/frontend nem autenticação de produção.
- Nenhuma escrita no banco legado ou publicado.
- Nenhuma liberação dos 110 modelos bloqueados.
- Nenhum playtest humano ou aprovação final de balanceamento.

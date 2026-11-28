# Card Engine v2 — manifesto de alterações da expansão de catálogo v0.2

- **Baseline:** `soulsbo-main-continuity-2026-11-27-rev17.zip`.
- **Resultado:** rev. 18; expansão do catálogo alpha de 10 para 24 IDs explícitos, com 12 famílias novas de efeito de entrada.
- **Validação:** 97/97 testes; staging 8/8; partida Bo3 terminou 2–1 com 16 operações e 48 eventos; SQLite `quick_check`/`integrity_check` `ok`.
- **Escopo:** catálogo alpha isolado e staging review-only; nenhuma integração com bot/API/frontend/banco publicado.

## Arquivos novos

- `data/card_game/card-engine-v2-alpha-catalog.v0.2.json`
- `data/card_game/card-engine-v2-alpha-effects.v0.2.json`
- `data/card_game/card-engine-v2-legacy-catalog-staging.v0.1.json`
- `docs/card-engine-v2-catalog-expansion-report-v0.2.json`
- `docs/card-engine-v2-catalog-expansion-report-v0.2.md`
- `docs/card-engine-v2-legacy-catalog-staging-validation-v0.1.json`
- `docs/card-engine-v2-legacy-catalog-staging-validation-v0.1.md`
- `docs/card-engine-v2-playable-alpha-validation-v0.3.json`
- `docs/card-engine-v2-playable-alpha-validation-v0.3.md`
- `docs/card-engine-v2-playable-match-alpha-run.v0.2.json`
- `docs/scripts/build-card-engine-v2-catalog-expansion-report-v0.2.py`
- `docs/scripts/compile-card-engine-v2-legacy-catalog-staging-v0.1.py`
- `docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.2.py`
- `docs/scripts/test-card-engine-v2-playable-alpha-v0.3.py`
- `docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.1.py`
- `sistemas/card_engine_v2/entry_effects.py`
- `tests/card_engine_v2/test_expanded_entry_effects.py`

## Arquivos alterados

- `data/card_game/README.md`
- `docs/PACOTE-MANIFESTO.md`
- `docs/README-PACOTE-CONTINUIDADE.md`
- `docs/card-game-handoff.md`
- `sistemas/card_engine_v2/README.md`
- `sistemas/card_engine_v2/alpha_catalog.py`
- `sistemas/card_engine_v2/match.py`
- `tests/card_engine_v2/test_playable_match.py`

## Arquivos removidos

- Nenhum.

## Integridade do runtime legado

Os cinco arquivos centrais continuam byte a byte idênticos ao baseline rev. 17:
- `sistemas/gwent.py` — idêntico
- `sistemas/cartas.py` — idêntico
- `bot.py` — idêntico
- `database.py` — idêntico
- `site/app.js` — idêntico

## Fronteira do catálogo

- Snapshot histórico: 137 modelos.
- Allowlist alpha: 24 modelos.
- Bloqueados no staging: 113 modelos.
- Não reconstruídos: 137 modelos; facções sem revisão: 137; divergências históricas de custo: 19.
- O allowlist v0.2 e seus hashes são validados pelo `AlphaCatalog` e incluídos no `DefinitionManifest`.
- Nenhuma carta foi aprovada para publicação por esta expansão.

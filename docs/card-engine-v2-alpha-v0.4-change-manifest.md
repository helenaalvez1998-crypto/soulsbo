# Manifesto de alterações — Card Engine v2 alpha v0.4 / revisão 19

- **Baseline:** `soulsbo-main-continuity-2026-11-27-rev18.zip`.
- **Pacote resultante:** `soulsbo-main-continuity-2026-11-27-rev19.zip`.
- **Objetivo:** conectar combos, passivas de facção e líderes ao controlador de partida, mantendo catálogo e registries como artefatos alpha hash-pinned.
- **Contrato:** `CardInstance v0.7`, schema 7; continua draft de implementação, não congelado.
- **Validação:** 109/109 testes; staging 137/27/110; demonstração combo/passiva/líder A 20–10 B; partida Bo3 A 2–1 B.
- **Escopo:** alterações apenas em `data/card_game/`, `docs/`, `sistemas/card_engine_v2/` e `tests/card_engine_v2/`.

## Alterações funcionais

- `sistemas/card_engine_v2/synergies.py`: resolução determinística de combos e passivas, com prioridade, tags, participantes físicos distintos, ativação máxima e reset por rodada.
- `sistemas/card_engine_v2/leaders.py`: dez handlers alpha, com setup compatível por facção e uso único por partida.
- `sistemas/card_engine_v2/alpha_catalog.py`: valida e carrega os registries; prende hashes no manifesto da partida.
- `sistemas/card_engine_v2/match.py`: setup de facção/líder, hooks de combo/passiva após a jogada, ativação do líder e reset de flags no fechamento da rodada.
- `sistemas/card_engine_v2/validation.py` e schema v7: validam o estado opcional de facção, líder, ativação e estado por rodada.
- `tests/card_engine_v2/test_combo_faction_leaders.py`: cobre prioridade/seleção de combo, ativação por rodada, passivas, os dez líderes e hashes de definição.

## Dados novos

- `data/card_game/card-engine-v2-alpha-catalog.v0.3.json`: allowlist alpha com 27 cartas.
- `data/card_game/card-engine-v2-alpha-combos.v0.1.json`: 27 definições; nove alcançáveis com as tags disponíveis e 18 inertes por falta de fontes na allowlist atual.
- `data/card_game/card-engine-v2-alpha-faction-passives.v0.1.json`: quatro passivas.
- `data/card_game/card-engine-v2-alpha-leaders.v0.1.json`: dez líderes.
- `data/card_game/card-engine-v2-legacy-catalog-staging.v0.2.json`: 137 modelos históricos particionados em 27 alpha-only e 110 bloqueados.

## Arquivos novos

- `data/card_game/card-engine-v2-alpha-catalog.v0.3.json`
- `data/card_game/card-engine-v2-alpha-combos.v0.1.json`
- `data/card_game/card-engine-v2-alpha-faction-passives.v0.1.json`
- `data/card_game/card-engine-v2-alpha-leaders.v0.1.json`
- `data/card_game/card-engine-v2-legacy-catalog-staging.v0.2.json`
- `docs/card-engine-v2-combo-faction-leader-alpha-run.v0.1.json`
- `docs/card-engine-v2-combos-faction-passives-leaders-alpha-v0.1.md`
- `docs/card-engine-v2-alpha-v0.4-summary.json`
- `docs/card-engine-v2-legacy-catalog-staging-validation-v0.2.json`
- `docs/card-engine-v2-legacy-catalog-staging-validation-v0.2.md`
- `docs/card-engine-v2-playable-alpha-validation-v0.4.json`
- `docs/card-engine-v2-playable-alpha-validation-v0.4.md`
- `docs/card-engine-v2-playable-match-alpha-run.v0.3.json`
- `docs/scripts/simulate-card-engine-v2-combo-faction-leader-alpha-v0.1.py`
- `docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py`
- `docs/scripts/test-card-engine-v2-playable-alpha-v0.4.py`
- `docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.2.py`
- `sistemas/card_engine_v2/leaders.py`
- `sistemas/card_engine_v2/synergies.py`
- `tests/card_engine_v2/test_combo_faction_leaders.py`

## Arquivos atualizados

- `data/card_game/README.md`
- `docs/PACOTE-MANIFESTO.md`
- `docs/README-PACOTE-CONTINUIDADE.md`
- `docs/card-game-handoff.md`
- `docs/PROJECT-OPERATING-CONTEXT.md`
- `docs/schemas/card-game-card-instance-match.schema.v7.json`
- `sistemas/card_engine_v2/README.md`
- `sistemas/card_engine_v2/alpha_catalog.py`
- `sistemas/card_engine_v2/match.py`
- `sistemas/card_engine_v2/validation.py`
- `tests/card_engine_v2/test_expanded_entry_effects.py`
- `tests/card_engine_v2/test_playable_match.py`
- `tests/card_engine_v2/test_schema.py`

## Arquivos removidos

- Nenhum.

## Resultado do diff contra rev. 18

- Arquivos novos: 21 (inclui este manifesto).
- Arquivos atualizados: 13.
- Arquivos removidos: 0.
- Mudanças fora de `data/card_game/`, `docs/`, `sistemas/card_engine_v2/`, `tests/card_engine_v2/`: 0.

## Resultados reproduzidos

- `python docs/scripts/test-card-engine-v2-playable-alpha-v0.4.py`: **109/109**, zero falhas e zero ignorados.
- `python docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.2.py`: PASS; 137 IDs, allowlist 27, bloqueados 110, hashes de origem e partição conferidos.
- `python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py`: partida Bo3 encerrada, Player A 2–1 Player B; 16 operações e 48 eventos.
- `python docs/scripts/simulate-card-engine-v2-combo-faction-leader-alpha-v0.1.py`: Player A 20–10 Player B; 21 eventos incluindo combo, passiva de facção e líder; SQLite íntegro.
- `python -m py_compile sistemas/card_engine_v2/*.py docs/scripts/*.py tests/card_engine_v2/*.py`: compilação concluída sem erro.

## Integridade do motor antigo

Os cinco arquivos centrais permanecem byte a byte idênticos ao baseline rev. 18:

- `sistemas/gwent.py`
- `sistemas/cartas.py`
- `bot.py`
- `database.py`
- `site/app.js`

Nenhum arquivo foi alterado fora dos quatro diretórios permitidos. Não houve integração com Discord, HTTP, frontend, banco publicado ou adapter assíncrono; nenhuma migração/cutover foi executada.

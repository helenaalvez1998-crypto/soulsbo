# Change manifest — Deck Builder / Application alpha v0.1

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev25.zip`  
**Resultado de testes:** 171/171 aprovados.

**Regra de setup adicional:** o caminho competitivo sorteia o primeiro jogador no servidor; a camada de aplicação/transport não permite que o cliente force o resultado.

## Arquivos novos

- `sistemas/card_engine_v2/deck_builder.py`
- `sistemas/card_engine_v2/deck_repository.py`
- `sistemas/card_engine_v2/application.py`
- `tests/card_engine_v2/test_deck_builder.py`
- `tests/card_engine_v2/test_deck_repository_application.py`
- `docs/card-engine-v2-deck-builder-alpha-v0.1.md`
- `docs/card-engine-v2-deck-builder-alpha-v0.1-validation.json`
- `docs/card-engine-v2-deck-builder-alpha-v0.1-change-manifest.md`

## Arquivos alterados

- `sistemas/card_engine_v2/match.py` — entrada competitiva estrita, metadados do setup, sorteio server-side do primeiro jogador; harness de testes preservado.
- `sistemas/card_engine_v2/__init__.py` — exports públicos do Deck Builder, repositório e application service.
- `sistemas/card_engine_v2/README.md` — documentação de uso, serviço async e limites.
- `docs/card-game-handoff.md` — novo estado rev. 26 e limites de produção.
- `docs/README-PACOTE-CONTINUIDADE.md` e `docs/PACOTE-MANIFESTO.md` — revisão e índice atualizados.
- `docs/card-engine-v2-playable-alpha-validation-v0.5.json/.md` — relatório oficial atualizado para 171 testes.
- `docs/card-engine-v2-playable-match-alpha-run.v0.3.json` — simulação Bo3 reproduzida nesta revisão.

## Inventário final de diferenças

- **8 arquivos novos**.
- **9 arquivos existentes alterados**.
- **0 arquivos removidos**.
- Não foram incluídos artefatos `__pycache__`, `.pyc`, bases SQLite temporárias ou diretórios locais de execução.

## Integridade de escopo

Não foram alterados:

- `bot.py`
- `database.py`
- `site/app.js`
- `sistemas/gwent.py`
- `sistemas/cartas.py`

Não foram lidos/escritos bancos publicados. As bases dos testes são temporárias e os novos repositórios exigem caminhos SQLite dedicados com marcador próprio. Nenhum cutover foi executado.

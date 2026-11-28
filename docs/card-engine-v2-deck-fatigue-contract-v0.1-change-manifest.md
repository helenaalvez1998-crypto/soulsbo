# Manifesto de alterações — deck fatigue candidate v0.1 / rev. 22

**Baseline:** rev. 21  
**Resultado:** contrato candidato e referência matemática isolada; runtime inalterado.
**Diff em relação ao ZIP rev. 21:** oito arquivos modificados, sete novos, zero removidos.

## Arquivos novos

- `sistemas/card_engine_v2/deck_fatigue_candidate.py`
- `tests/card_engine_v2/test_deck_fatigue_candidate.py`
- `data/card_game/card-engine-v2-deck-fatigue-policy-candidate.v0.1.json`
- `docs/card-engine-v2-deck-fatigue-contract-v0.1.md`
- `docs/card-engine-v2-deck-fatigue-contract-v0.1-validation.json`
- `docs/card-engine-v2-deck-fatigue-contract-v0.1-change-manifest.md`
- `docs/card-engine-v2-lifecycle-audit-v0.1.md`

## Arquivos atualizados

- `docs/card-game-handoff.md`
- `docs/README-PACOTE-CONTINUIDADE.md`
- `sistemas/card_engine_v2/README.md`

## Escopo e exclusões

- Nenhum método de `AlphaMatchController` foi alterado.
- `match.py`, `combat.py`, `gameplay.py`, `repository.py`, schemas, SQL, catálogo, allowlist e ruleset permanecem iguais à rev. 21.
- Nenhum dos cinco arquivos centrais do legado foi alterado; seus hashes SHA-256 estão no relatório de validação.
- Não foi adicionado dano de fatigue ao runtime; os parâmetros de balanceamento continuam nulos.
- A referência aritmética é testada com fixtures, não é uma decisão final de design.

## Validação

- `py_compile`: aprovado.
- Testes Card Engine v2: 130/130.
- Regressões oficiais de playable alpha e staging: aprovadas.
- Simulação Bo3: Player A venceu 2–1; 60 eventos; SQLite íntegro.
- Demo combo/passiva/líder: aprovada; 25 eventos; SQLite íntegro.

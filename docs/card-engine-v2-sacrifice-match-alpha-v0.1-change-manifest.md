# Change manifest — sacrifício normal no controlador alpha v0.1 (rev. 21)

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev20.zip`  
**Resultado:** `soulsbo-main-continuity-2026-11-28-rev21.zip`  
**Status:** implementação alpha isolada; sem integração de produção.

## Arquivos adicionados

- `docs/card-engine-v2-sacrifice-match-alpha-v0.1.md` — especificação da ação, oferta, confirmação, transação, semântica de remoção, eventos e limites.
- `docs/card-engine-v2-sacrifice-match-alpha-v0.1-validation.json` — evidências e resultados de validação da tranche.
- `docs/card-engine-v2-sacrifice-match-alpha-v0.1-change-manifest.md` — este manifesto.

## Arquivos de código alterados

- `sistemas/card_engine_v2/match.py` — registra `unit.sacrifice`; adiciona oferta vinculada à revisão e confirmação da ação normal via `SQLiteMatchRepository.execute_operation`; consome o turno e mantém a cadeia de eventos.
- `tests/card_engine_v2/test_playable_match.py` — adiciona testes de integração para execução/replay idempotente, bypass de Égide com Vingança e rejeição de oferta obsoleta.
- `docs/scripts/test-card-engine-v2-playable-alpha-v0.4.py` — inclui a ação normal de sacrifício na cobertura e explicita os limites da implementação interna alpha.

## Documentação e relatórios atualizados

- `sistemas/card_engine_v2/README.md` — documenta a ação normal, integração ao controlador e semântica preservada do Grupo F.
- `docs/card-game-handoff.md` — adiciona handoff rev. 21 antes do histórico rev. 20 e das revisões anteriores.
- `docs/PROJECT-OPERATING-CONTEXT.md` — registra rev. 21 como contexto operacional corrente, preservando atualizações antigas como histórico.
- `docs/README-PACOTE-CONTINUIDADE.md` — adiciona estado atual rev. 21 e links de leitura prioritários.
- `docs/PACOTE-MANIFESTO.md` — adiciona manifesto rev. 21, preservando manifestos anteriores.
- `docs/card-engine-v2-playable-alpha-validation-v0.4.json` e `.md` — relatório geral regenerado pelo script oficial, incluindo 120/120 testes e o escopo do sacrifício.
- Os scripts de staging e simulação foram executados como validação reproduzível; seus resultados estão resumidos no handoff e no relatório JSON desta tranche. Não houve alteração de catálogo publicado.

## Não alterado por esta tranche

- `sistemas/gwent.py`
- `sistemas/cartas.py`
- `bot.py`
- `database.py`
- `site/app.js`
- Schema `CardInstance v0.7`, schema 7, e ruleset alpha v0.2.
- Allowlist de 27 cartas e bloqueio dos 110 modelos históricos.
- Regras aprovadas do Grupo F; o controlador apenas passa a usar o handler de sacrifício existente.

## Comandos de validação

```bash
python -m py_compile sistemas/card_engine_v2/*.py docs/scripts/*.py tests/card_engine_v2/*.py
python -m unittest discover -s tests/card_engine_v2 -v
python docs/scripts/test-card-engine-v2-playable-alpha-v0.4.py
python docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.2.py
python docs/scripts/simulate-card-engine-v2-playable-match-alpha-v0.3.py
python docs/scripts/simulate-card-engine-v2-combo-faction-leader-alpha-v0.1.py
```

**Resultado reproduzido:** 120/120 testes; staging 137 modelos/27 alpha/110 bloqueados; Bo3 Player A 2–1 Player B (16 operações/60 eventos); demonstração combo/passiva/líder com 25 eventos. Todos os bancos SQLite de validação são descartáveis e locais.

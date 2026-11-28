# Manifesto de mudanças — Soulsbo rev. 31

**Baseline:** `soulsbo-main-continuity-2026-11-28-rev30.zip`  
**Pacote resultante:** `soulsbo-main-continuity-2026-11-28-rev31.zip`  
**Status:** pacote local validado; deploy externo não executado.
**Diferença contra rev. 30:** 15 arquivos existentes modificados, 23 adicionados, nenhum removido. Os cinco arquivos legados protegidos permaneceram byte a byte iguais.

## Mudanças de runtime

- `sistemas/card_game_achievements.py`: projeção de conquistas a partir de métricas autoritativas, leitura read-only e persistência monotônica.
- `site_hub.py`: endpoints de conquistas calculam progresso no servidor; JSON forjado/malformado rejeitado; apostas e evolução com risco falham fechadas e não alteram inventário/saldo; rota `/apostas` declarada.
- `site/conquistas.html`: painel conectado aos endpoints autoritativos.
- `site/apostas.html` e `site/evolucao.html`: páginas informam indisponibilidade segura; Forja de raridade permanece distinta.
- `site/tutorial.html`: links e avisos coerentes com o estado real dos módulos.
- `scripts/runtime_preflight.py`: verificação de instalação, secrets, callback, host não-placeholder, storage e schema SQLite read-only.
- `scripts/backup_sqlite.py`: backup online com `integrity_check`; URI segura para caminhos com espaços/caracteres especiais.

## Artefatos de operação

- `Dockerfile`, `compose.yaml`, `deploy/docker-entrypoint.sh`, `deploy/Caddyfile.example`.
- `.env.production.example`, `.dockerignore`, `requirements-dev.txt`.
- `.github/workflows/ci.yml`.
- `deploy/README.md`, `docs/card-engine-v2-operational-deployment-v0.1.md`.

## Testes e documentação

- Novos testes de conquistas puras/persistidas, endpoints HTTP, preflight, backup e métricas competitivas.
- Atualizados `docs/card-engine-v2-achievements-alpha-v0.1.md`, `docs/card-game-handoff.md`, `docs/README-PACOTE-CONTINUIDADE.md`, `docs/PACOTE-MANIFESTO.md` e `sistemas/card_engine_v2/README.md`.
- Adicionados `docs/card-engine-v2-rev31-product-completion.md` e `docs/card-engine-v2-rev31-validation.json`.

## Regras de segurança

- Apostas não debitam Denários nem reservam exemplares enquanto escrow/liquidação não estiverem implementados.
- Evolução com risco não altera exemplares ou amuletos enquanto nível/ledger/custos não estiverem persistidos de forma transacional.
- Progresso de conquistas é derivado pelo servidor; desbloqueios persistidos não são revertidos.
- Segredos não são incluídos no pacote.

## Arquivos legados protegidos

Os cinco arquivos `bot.py`, `database.py`, `site/app.js`, `sistemas/gwent.py` e `sistemas/cartas.py` devem permanecer byte a byte iguais ao baseline rev. 30. O relatório final registra seus hashes comparados.

## Limitações

A validação não incluiu `docker build`, conexão de token Discord, OAuth público, staging real ou banco de produção: as ferramentas/credenciais não estavam disponíveis no ambiente de criação.

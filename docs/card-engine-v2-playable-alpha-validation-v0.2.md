# Card Engine v2 — playable alpha validation v0.2

**Status:** PASS  
**Executado (UTC):** 2026-11-28T02:25:00.941905+00:00  
**Resultado:** 78/78 testes aprovados; 0 falhas; 0 ignorados.

## Escopo

- Repositório SQLite, CAS, ledger idempotente, journal e outbox.
- Resolvedor genérico: alvos, remoção/sacrifício, proteção, bônus e Vingança.
- Controlador de partida jogável melhor de três com allowlist de 10 cartas.
- Schemas e contrato CardInstance v0.7.

## Limites

- Tests use disposable local SQLite databases and local independent connections.
- No production database, aiosqlite, Discord, HTTP, frontend or multi-host infrastructure was used.
- The match uses an explicit 10-card alpha allowlist, not the full production catalog.
- The controller does not yet implement all catalog effects, leaders, combos, damage or full turn/cost systems.

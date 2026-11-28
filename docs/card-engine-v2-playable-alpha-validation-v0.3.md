# Card Engine v2 — expanded playable alpha validation v0.3

**Status:** PASS  
**Executado (UTC):** 2026-11-28T02:41:28.302802+00:00  
**Resultado:** 97/97 testes aprovados; 0 falhas; 0 ignorados.

## Escopo

- Repositório SQLite, CAS, ledger idempotente, journal e outbox.
- Resolvedor genérico: alvos, remoção/sacrifício, proteção, bônus e Vingança.
- Controlador de partida jogável melhor de três com allowlist de 24 cartas alpha.
- Doze famílias de efeitos de entrada de unidade, com parâmetros ligados a IDs explícitos.
- Staging dos 137 registros históricos: 24 alpha-only e 113 bloqueados.
- Schemas e contrato CardInstance v0.7.

## Limites

- Tests use disposable local SQLite databases and local independent connections.
- No production database, aiosqlite, Discord, HTTP, frontend or multi-host infrastructure was used.
- The runtime alpha uses an explicit, hash-pinned allowlist of 24 historical card models; it is not the full production catalog.
- The staging artifact traces 137 historical models: 24 alpha-test-only and 113 blocked; all still require review/rebuild as specified in the staging summary.
- Twelve on-play unit effect families are implemented for selected allowlisted cards; this is not the full effect registry.
- Leaders, combos, faction passives, damage, and full turn/resource-cost systems remain incomplete.

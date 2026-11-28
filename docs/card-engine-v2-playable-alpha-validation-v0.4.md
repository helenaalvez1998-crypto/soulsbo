# Card Engine v2 — expanded playable alpha validation v0.4

**Status:** PASS  
**Executado (UTC):** 2026-11-28T04:18:56.340258+00:00  
**Resultado:** 135/135 testes aprovados; 0 falhas; 0 ignorados.

## Conteúdo validado

- 27 cartas alpha explicitamente permitidas; 110 dos 137 modelos históricos continuam bloqueados.
- 12 famílias de efeitos de entrada.
- 27 definições de combo registradas; nove alcançáveis com as tags atuais.
- Quatro passivas de facção e dez handlers de líderes.
- Persistência SQLite, resolvedor de gameplay, partidas Bo3 e schemas.
- Combate por fileira no fechamento da rodada, vida inicial de 20, dano letal e empate simultâneo (ruleset alpha v0.2).
- Sacrifício como ação normal interna do `AlphaMatchController`: oferta server-side vinculada à revisão, confirmação transacional, custo de turno, bypass de Égide, contador separado, Vingança causal e replay idempotente.
- Deck fatigue no controlador alpha: checagem no início de cada turno individual com pilha vazia; dano progressivo 1, 2, 3... antes da ação; contadores separados por jogador e finalização letal imediata (ruleset v0.3).
- A política de fatigue é uma decisão provisória de balanceamento alpha, não uma regra final aprovada para publicação.

## Limites

- Tests use disposable local SQLite databases; no production database is accessed.
- No Discord, HTTP, frontend, aiosqlite or multi-host integration is exercised.
- The 27-card allowlist, 27 combo definitions, four faction passives and ten leaders are alpha-only fixtures, not a published catalog.
- Only nine registered combos have all required tags represented in the current 27-card allowlist; 18 remain inert until tag-source cards are added.
- Combo/passive/leader tests use isolated test matches; not every handler has been playtested through a human UI flow.
- The remaining 110 historical models are blocked; the full card catalog, per-unit attack/armor/hit-point rules, all special families and production adapter are incomplete.
- Normal sacrifice is exposed only as an internal alpha controller action; its current cost is turn consumption only, with no energy/resource economy or Discord/HTTP/frontend interaction.
- Deck fatigue is enabled only in the isolated alpha match controller; it is not integrated with Discord, HTTP, frontend or the production game runtime.
- The default alpha setup follows the redesign's four-card initial hand; deterministic legacy simulation fixtures may explicitly override the hand size.
- The alpha harness retains its existing draw of up to two cards at each new round; this draw schedule is a harness rule, not a complete production draw economy.
- Deck fatigue uses a provisional alpha balance policy: 1 damage on the first empty-deck turn, then +1 per later fatigue turn, no cap, per-player match counter, no reset and no discard reshuffle.
- Each player's first turn after the initial deal is fatigue-exempt; subsequent individual turns are checked before the player can act.

# Card Engine v2 — expanded playable alpha validation v0.5

**Status:** PASS  
**Executado (UTC):** 2026-11-28T06:51:16.188198+00:00  
**Resultado:** 240/240 testes aprovados; 0 falhas; 0 ignorados.

## Conteúdo validado

- 27 cartas alpha explicitamente permitidas; 110 dos 137 modelos históricos continuam bloqueados.
- 12 famílias de efeitos de entrada.
- 27 definições de combo registradas; nove alcançáveis com as tags atuais.
- Quatro passivas de facção e dez handlers de líderes.
- Persistência SQLite, resolvedor de gameplay, partidas Bo3 e schemas.
- Combate por fileira no fechamento da rodada, vida inicial de 20, dano letal e empate simultâneo (ruleset alpha v0.2).
- Sacrifício como ação normal interna do `AlphaMatchController`: oferta server-side vinculada à revisão, confirmação transacional, custo de turno, bypass de Égide, contador separado, Vingança causal e replay idempotente.
- Deck fatigue no controlador alpha: checagem no início de cada turno individual com pilha vazia; dano progressivo 1, 2, 3... antes da ação; contadores separados por jogador e finalização letal imediata (ruleset v0.3).
- Economia de energia: +1 no início de cada turno, limite 5, saldo persistente entre rodadas, guardrails de runtime e cobrança transacional.
- Agenda alpha provisória por ID: 27 cartas e 10 líderes; custos de cartas 1–5 e líderes 2–3. Não aprovada para release/playtest humano.
- Raridade e custo legado de deck não determinam energia; ações sem custo explícito são rejeitadas. Sacrifício consome turno, sem custo energético.
- Ativação manual genérica: API server-side testada com fixture sintética; registry real vazio (0 habilidades), pois nenhuma das 27 cartas declara habilidade manual. Efeitos de entrada não são reativáveis.
- Simulações de gameplay usam fixture uniforme de custo 1 apenas para isolar mecânicas; testes de economia percorrem todos os preços da tabela real provisória.
- Deck Builder competitivo vincula cada slot a um `cartas_exemplares.id` global único, revalida posse e modelo no matchmaking e congela o poder individual atual na instância da partida.
- A ponte do inventário legado é somente leitura (`coliseu_listar_exemplares`); raridade Primordial é suportada como classificação, sem efeito mecânico.
- A view destinada a jogador oculta a mão adversária e IDs físicos do oponente; autenticação Discord/HTTP ainda deve fornecer o ID do principal autenticado.
- As APIs sync/async de aplicação não aceitam seed de embaralhamento do cliente; aleatoriedade do sistema é usada no matchmaking. Seeds determinísticas só existem no controlador interno para testes.
- A política de fatigue é uma decisão provisória de balanceamento alpha, não uma regra final aprovada para publicação.

## Limites

- Tests use disposable local SQLite databases; no production database is accessed.
- No Discord, HTTP, frontend, aiosqlite or multi-host integration is exercised.
- The 27-card allowlist, 27 combo definitions, four faction passives and ten leaders are alpha-only fixtures, not a published catalog.
- Only nine registered combos have all required tags represented in the current 27-card allowlist; 18 remain inert until tag-source cards are added.
- Combo/passive/leader tests use isolated test matches; not every handler has been playtested through a human UI flow.
- The remaining 110 historical models are blocked; the full card catalog, per-unit attack/armor/hit-point rules, all special families and production adapter are incomplete.
- Competitive deck slots are bound to exact global cartas_exemplares.id values; current per-copy unit power is frozen into the match instance. Existing saved deck rows migrated from schema v1 have empty exemplar provenance and must be rebuilt from the live collection before matchmaking.
- The legacy collection bridge reads Database.coliseu_listar_exemplares only; database.py and the published/legacy engine are not modified or written. No Discord/HTTP authentication transport is connected yet.
- Player-safe match views hide the opponent's hand and physical exemplar IDs when the authenticated player ID is supplied. The transport must derive that ID from its session/Discord principal, never from client payload data; a privileged no-viewer projection remains for internal simulations.
- Synchronous and asynchronous application matchmaking APIs do not accept client-provided shuffle seeds; server system randomness is used. Deterministic seeds remain restricted to the low-level internal controller for reproducible tests/simulations.
- Primordial is supported as an additional display rarity classification. Rarity remains excluded from power, targeting and effect resolution.
- Energy gain is implemented in the isolated alpha runtime (+1 at each individual turn start, cap 5, carried across rounds); all 27 allowlisted card IDs and all ten leader IDs have explicit provisional per-ID costs in ruleset v0.5.
- The per-ID schedule is experimental and not approved for release or balance sign-off; its values have not been validated by human playtests or telemetry. Rarity and legacy deck-cost fields are not used as turn-energy prices.
- All play/leader/manual-ability actions without an explicit configured price are rejected; there are no free unpriced alpha actions. Sacrifice is a separate turn-consuming action and has no energy price in this alpha.
- No manual activated ability is declared for the live 27-card allowlist; the registry is intentionally empty. The generic server-registry activation API is tested with a synthetic fixture only; no on-play effect was converted into a repeatable manual ability.
- Reproducible gameplay simulations use a uniform-energy-cost=1 test fixture to isolate other mechanics; they do not validate the provisional per-ID balance schedule. Dedicated economy tests validate every 27 card and ten leader price entries.
- Deck fatigue is enabled only in the isolated alpha match controller; it is not integrated with Discord, HTTP, frontend or the production game runtime.
- The default alpha setup follows the redesign's four-card initial hand; deterministic legacy simulation fixtures may explicitly override the hand size.
- The alpha harness retains its existing draw of up to two cards at each new round; this draw schedule is a harness rule, not a complete production draw economy.
- Deck fatigue uses a provisional alpha balance policy: 1 damage on the first empty-deck turn, then +1 per later fatigue turn, no cap, per-player match counter, no reset and no discard reshuffle.
- Each player's first turn after the initial deal is fatigue-exempt; subsequent individual turns are checked before the player can act.

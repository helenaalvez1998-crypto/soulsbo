# Card Engine v2 — expansão de catálogo alpha v0.2

**Status:** PASS_ALPHA_ONLY_NOT_RELEASE_APPROVED  
**Gerado (UTC):** 2026-11-28T02:41:30.441323+00:00  
**Cartas permitidas:** 24 (14 adicionadas nesta expansão)  
**Famílias novas implementadas:** 12  
**Testes da suíte:** 97/97 aprovados

## Escopo efetivamente habilitado

O snapshot histórico tem 137 modelos. O runtime alpha permite somente 24 IDs explícitos; 113 continuam bloqueados. A lista permitida está versionada em `data/card_game/card-engine-v2-alpha-catalog.v0.2.json`, validada pelo `AlphaCatalog` e incluída por SHA-256 no `DefinitionManifest`.

### 14 cartas adicionadas

- `arma_duas_luas` — `effect.cross_row_presence_power`
- `arma_grande_sino` — `effect.comeback_power`
- `chefe_dama_vazio` — `effect.enemy_bonus_reduction`
- `chefe_maliketh_morte_destinada` — `effect.enemy_bonus_reduction`
- `chefe_oraculo_ruina` — `effect.ruin_omen`
- `chefe_rei_afogado` — `effect.discard_advantage_power`
- `gwent_singular_primeiro` — `effect.solitary_row_power`
- `magia_nevoa_antiga` — `effect.weather_affinity_power`
- `magia_selo_vigilia` — `effect.weather_ward_support`
- `magia_sol_negro` — `effect.enemy_positive_bonus_power`
- `magia_trovao_oco` — `effect.enemy_bonus_reduction`
- `patente_1` — `effect.arcane_hunter_power`
- `patente_10` — `effect.sequence_power`
- `patente_9` — `effect.ahead_power`

### 12 famílias de efeito de entrada

- `effect.ahead_power`: `patente_9`
- `effect.arcane_hunter_power`: `patente_1`
- `effect.comeback_power`: `arma_grande_sino`
- `effect.cross_row_presence_power`: `arma_duas_luas`
- `effect.discard_advantage_power`: `chefe_rei_afogado`
- `effect.enemy_bonus_reduction`: `chefe_dama_vazio`, `chefe_maliketh_morte_destinada`, `magia_trovao_oco`
- `effect.enemy_positive_bonus_power`: `magia_sol_negro`
- `effect.ruin_omen`: `chefe_oraculo_ruina`
- `effect.sequence_power`: `patente_10`
- `effect.solitary_row_power`: `gwent_singular_primeiro`
- `effect.weather_affinity_power`: `magia_nevoa_antiga`
- `effect.weather_ward_support`: `magia_selo_vigilia`

## Staging histórico

| Métrica | Quantidade |
|---|---:|
| Modelos históricos | 137 |
| Permitidos somente na alpha | 24 |
| Bloqueados no staging | 113 |
| Ainda não reconstruídos | 137 |
| Facções ainda sem revisão | 137 |
| Divergências históricas de custo | 19 |

O staging é rastreabilidade, não publicação. Não foram inferidos handlers para cartas bloqueadas apenas porque há texto ou alias semelhante.

## Regressão da partida jogável

A partida de referência terminou com vencedor `1001` e resultado de rodadas `{'1001': 2, '2002': 1}`. Foram persistidas 16 operações e 48 eventos; SQLite: `ok`.

## Testes

A suíte completa registrou **97/97 aprovados**, 0 falhas e 0 ignorados.

Validação adicional: `docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.1.py` confirma hashes de origem, 137 IDs sem duplicidade, 24 IDs alpha e 113 bloqueados.

## Limites

- O arquivo com 137 cartas é um staging histórico para revisão, não um catálogo executável.
- Somente os 24 IDs explícitos são aceitos pela alpha isolada; os outros 113 permanecem bloqueados.
- Os 137 registros históricos continuam exigindo reconstrução de definição e revisão de facção conforme o snapshot de origem.
- Esta expansão não implementa as 54 famílias candidatas completas, 27 combos, líderes ou passivas de facção.
- Custos de deck, texto, atribuição de facção e status de publicação não são aprovados por esta allowlist alpha.
- Discord, HTTP, frontend, banco de produção, runtime legado e migração de produção permanecem desconectados e inalterados.

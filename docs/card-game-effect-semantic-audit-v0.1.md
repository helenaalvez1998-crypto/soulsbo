# Auditoria semântica das famílias de efeito — v0.1

**Estado:** auditoria read-only do código legado e do registry candidato. Não aprova automaticamente fusões e não altera o runtime.

## 1. Resultado da rastreabilidade

- Famílias candidatas: **54**.
- Aliases genéricos: **59**; branches diretos: **56**; hooks de ciclo de vida: **2**; sem handler encontrado: **1**.
- Identidades ativas: **22**; branches de identidade encontrados: **22**.
- Prioridade de revisão (heurística): alta **18**, média **6**, baixa **30**.

Os branches diretos são identificados por comparações de `skill` no `aplicar_jogada()`. Hooks são verificados separadamente em `_remover_unidade()` e `_resolve_round()`. As identidades ativas são cruzadas entre `CARD_IDENTITY_ABILITIES` e `_aplicar_habilidade_identidade()`. O mapa por família inclui também aliases candidatos arquivados quando a auditoria os vincula explicitamente a uma família; isso não os reativa.

## 2. Mapa das 54 famílias

| Família | Tipo | Aliases legados | Risco de revisão | Parâmetros semânticos variáveis |
|---|---|---:|---|---|
| `effect.first_round_power` | unit | 2 — `lei_primeva`, `primeira_luz` | **LOW** | — |
| `effect.comeback_power` | unit | 5 — `contragolpe`, `fome_abismo`, `instinto`, `retaliacao`, `last_bell` | **LOW** | — |
| `effect.ahead_power` | unit | 1 — `impeto` | **LOW** | — |
| `effect.third_round_power` | unit | 1 — `ultimo_folego` | **LOW** | — |
| `effect.sequence_power` | unit | 6 — `adaptacao`, `encadeamento`, `quebra_ritmo`, `veil_shift`, `pilgrim_duel`, `mist_trail` | **HIGH** | reference_side, row_relation |
| `effect.tied_score_power` | unit | 1 — `sangue_frio` | **LOW** | — |
| `effect.ranged_row_power` | unit | 1 — `precisao` | **LOW** | — |
| `effect.enemy_bonus_reduction` | unit | 5 — `drenagem`, `void_rend`, `destined_death`, `hollow_thunder`, `counterflame` | **HIGH** | target_scope |
| `effect.arcane_hunter_power` | unit | 1 — `cacador_arcano` | **LOW** | — |
| `effect.enemy_field_suppression` | unit | 1 — `decreto_soberano` | **LOW** | — |
| `effect.weather_affinity_power` | unit | 2 — `olho_tempestade`, `ancient_mist` | **HIGH** | — |
| `effect.late_round_reversal_power` | unit | 1 — `paradoxo_eterno` | **LOW** | — |
| `effect.same_row_formation_power` | unit | 3 — `dupla_fornalha`, `guardiao_fileira`, `forge_rhythm` | **HIGH** | faction_filter, mode |
| `effect.solitary_row_power` | unit | 1 — `cacador_solitario` | **LOW** | — |
| `effect.row_aura_bonus` | unit | 2 — `estandarte`, `grey_watch` | **LOW** | — |
| `effect.weather_resistance` | unit | 1 — `resistencia_climatica` | **LOW** | — |
| `effect.weather_ward_support` | unit | 1 — `vigil_seal` | **MEDIUM** | — |
| `effect.discard_special_power` | unit | 2 — `eco_arcano`, `echo_orb` | **HIGH** | — |
| `effect.death_revenge` | unit | 1 — `vinganca` | **LOW** | — |
| `effect.entry_shield` | unit | 1 — `escudo_ferro` | **LOW** | — |
| `effect.ally_sacrifice_power` | unit | 2 — `devorar`, `v75_blood_price` | **HIGH** | — |
| `effect.revive_from_discard` | unit | 1 — `ressurgir` | **MEDIUM** | — |
| `effect.round_victory_survivor` | unit | 2 — `sobrevivente`, `gloria` | **MEDIUM** | — |
| `effect.victory_draw` | unit | 1 — `espolios` | **LOW** | — |
| `effect.cross_row_presence_power` | unit | 3 — `irmandade_veu`, `twin_dance`, `shadow_paths` | **HIGH** | mode |
| `effect.formation_or_discard_power` | unit | 1 — `circulo_arcano` | **LOW** | — |
| `effect.row_pair_blessing` | unit | 2 — `ash_guardian`, `v75_golden_vow` | **HIGH** | ally_selection |
| `effect.discard_advantage_power` | unit | 1 — `abyss_tithe` | **LOW** | — |
| `effect.ruin_omen` | unit | 1 — `ruin_omen` | **HIGH** | — |
| `effect.enemy_positive_bonus_power` | unit | 1 — `devouring_eclipse` | **LOW** | — |
| `effect.cross_row_support` | unit | 2 — `veiled_moon`, `covering_shot` | **HIGH** | — |
| `effect.row_status_pressure` | unit | 4 — `scarlet_bloom`, `impaling_spear`, `v75_frost_oracle`, `v75_blood_mark` | **HIGH** | status, target_scope |
| `effect.gravity_reposition` | unit | 1 — `star_gravity` | **HIGH** | — |
| `effect.frost_storm_momentum` | unit | 1 — `time_storm` | **HIGH** | — |
| `effect.grace_purification` | unit | 1 — `v75_grace_mender` | **MEDIUM** | — |
| `effect.gravity_shear` | unit | 1 — `v75_gravity_shear` | **LOW** | — |
| `effect.weather_row` | special | 1 — `gwent_clima` | **LOW** | — |
| `effect.apply_status_marks` | special | 7 — `gwent_chuva`, `gwent_geada`, `gwent_geada_cariana`, `gwent_loucura`, `gwent_nevoa`, `gwent_podrida`, `gwent_sangramento` | **HIGH** | status, target_scope, threshold_action |
| `effect.row_buff` | special | 3 — `gwent_chifre`, `gwent_muralha`, `gwent_vinculo` | **MEDIUM** | — |
| `effect.return_unit_to_hand` | special | 1 — `gwent_medico` | **LOW** | — |
| `effect.remove_units` | special | 2 — `gwent_execucao`, `gwent_queima` | **HIGH** | power_limit, target_scope |
| `effect.clear_weather` | special | 1 — `gwent_purificar` | **LOW** | — |
| `effect.draw_cards` | special | 1 — `gwent_batedor` | **LOW** | — |
| `effect.grant_shield` | special | 1 — `gwent_egide` | **LOW** | — |
| `effect.revive_to_board` | special | 1 — `gwent_requiem` | **MEDIUM** | — |
| `effect.move_unit` | special | 1 — `gwent_passo` | **LOW** | — |
| `effect.purify_frost_buff` | special | 1 — `gwent_chama` | **LOW** | — |
| `effect.summon_wolves` | special | 1 — `gwent_invocacao` | **LOW** | — |
| `effect.relic_godrick_rune` | relic | 1 — `reliquia_godrick` | **LOW** | — |
| `effect.relic_unborn_rune` | relic | 1 — `reliquia_renala` | **LOW** | — |
| `effect.relic_death_rune` | relic | 1 — `reliquia_morte` | **LOW** | — |
| `effect.relic_night_flame_sword` | relic | 1 — `reliquia_noite_chama` | **HIGH** | — |
| `effect.relic_black_blade` | relic | 1 — `reliquia_lamina_negra` | **HIGH** | — |
| `effect.relic_margit_shackles` | relic | 1 — `reliquia_algemas` | **HIGH** | — |

## 3. Achados semânticos prioritários

| ID | Prioridade | Família | Achado e tratamento | Estado |
|---|---|---|---|---|
| SEM-001 | HIGH | `effect.sequence_power` | O bônus só deve ocorrer quando existe uma referência de jogada anterior válida. O registry v0.1 não expressava essa pré-condição. **Proposta:** Adicionado requires_previous_play:boolean obrigatório e verdadeiro em todos os aliases; texto agora explicita que é necessária uma jogada anterior. | `FIXED_IN_CANDIDATE_V0.1; NOT_RUNTIME` |
| SEM-002 | HIGH | `effect.apply_status_marks / effect.row_status_pressure` | O nome de família comum não significa efeito idêntico. Geada, Podridão, Sangramento e Loucura têm escopo, limiar, ação secundária, reset e duração diferentes. **Proposta:** Manter só como abstração técnica parametrizada; cada combinação de status e consequência exige teste específico e texto próprio. | `OPEN_REQUIRES_BEHAVIOR_TESTS` |
| SEM-003 | HIGH | `effect.remove_units` | Chama Negra seleciona a unidade mais forte de cada lado; Execução escolhe alvo inimigo na fileira com limite de poder. Não são a mesma regra de seleção. **Proposta:** Exigir escopo de seleção, lado, limite e política de escudo explícitos no futuro handler; remover sentinela ambígua power_limit=0 ou declarar flag `has_power_limit`. | `OPEN_REQUIRES_HANDLER_DESIGN` |
| SEM-004 | HIGH | `effect.ally_sacrifice_power` | Devorar e Preço em Sangue diferem no teto do ganho e no bônus de fallback quando não há vítima. Sacrifício também ignora escudo por escolha do helper legado. **Proposta:** Manter parâmetros gain_cap/fallback_bonus/minimum_gain; criar teste explícito para escudo, gatilho de Vingança e descarte da vítima. | `OPEN_REQUIRES_BEHAVIOR_TESTS` |
| SEM-005 | HIGH | `effect.cross_row_support / effect.row_pair_blessing` | Efeitos de suporte variam entre fortalecer apenas aliado e fortalecer a própria carta mais um aliado; seleção varia entre primeiro aliado e aliado mais fraco. **Proposta:** Manter self_bonus, ally_bonus e ally_selection explícitos; ordem dos empates para alvo mais fraco deve ser determinística e documentada. | `OPEN_REQUIRES_TARGETING_RULE` |
| SEM-006 | MEDIUM | `effect.round_victory_survivor` | Glória tem hook funcional: se o jogador vencer uma rodada não final, conserva no campo a mais forte entre as cartas com habilidade gloria; bônus/escudo/status são limpos. Sobrevivente só tem texto declarado, sem handler e sem carta atribuída no snapshot efetivo. **Proposta:** Não declarar os dois como comportamento equivalente comprovado. Desenhar uma única regra nova explicitamente e decidir se mantém a retenção da mais forte. | `REQUIRES_PRODUCT_RULE_APPROVAL` |
| SEM-007 | HIGH | `effect.sequence_power` | As variantes própria/mesma, própria/diferente e adversária/mesma usam referências distintas; o estado last_row é reiniciado ao fim de cada rodada. **Proposta:** `reference_side`, `row_relation` e `requires_previous_play` devem ser obrigatórios; nenhum handler deve inferir referência de valor nulo. | `FIXED_IN_CANDIDATE_V0.1; NOT_RUNTIME` |

## 4. Cobertura de cada alias genérico

| ID | Cartas atuais | Classificação | Evidência |
|---|---|---|---|
| `adaptacao` | `magia_selo_vigilia` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1840` |
| `cacador_arcano` | `chefe_maliketh_morte_destinada`, `gwent_unidade_invocador`, `patente_1`, `patente_7` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1841` |
| `cacador_solitario` | `gwent_singular_primeiro` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1855` |
| `circulo_arcano` | — | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1895` |
| `contragolpe` | — | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1836` |
| `decreto_soberano` | `primordial_trono` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1850` |
| `devorar` | `gwent_unidade_carniceiro_forja` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1871` |
| `drenagem` | `chefe_malenia_lamina_miquella`, `covenant_coroa_abismo`, `magia_trovao_oco` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1847` |
| `dupla_fornalha` | — | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1891` |
| `eco_arcano` | — | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1866` |
| `encadeamento` | `magia_nevoa_antiga`, `patente_5` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1839` |
| `escudo_ferro` | — | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1869` |
| `espolios` | — | `LIFECYCLE_HOOK` | `_resolve_round:1159` |
| `estandarte` | `gwent_mitica_coroa` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1858` |
| `fome_abismo` | `primordial_abismo` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1834` |
| `guardiao_fileira` | — | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1853` |
| `gwent_batedor` | `gwent_especial_batedor` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1647` |
| `gwent_chama` | `elden_especial_chama` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1660` |
| `gwent_chifre` | `gwent_especial_chifre` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1598` |
| `gwent_chuva` | `gwent_especial_chuva` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1583` |
| `gwent_clima` | `gwent_especial_tempestade` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1567` |
| `gwent_egide` | `gwent_especial_egide` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1748` |
| `gwent_execucao` | `gwent_especial_execucao` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1623` |
| `gwent_geada` | `gwent_especial_geada` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1592` |
| `gwent_geada_cariana` | `elden_especial_geada` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1697` |
| `gwent_invocacao` | `elden_especial_invocacao` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1669` |
| `gwent_loucura` | `elden_especial_loucura` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1729` |
| `gwent_medico` | `gwent_especial_medico` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1604` |
| `gwent_muralha` | `gwent_especial_muralha` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1654` |
| `gwent_nevoa` | `gwent_especial_nevoa` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1575` |
| `gwent_passo` | `gwent_especial_passo` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1780` |
| `gwent_podrida` | `elden_especial_podrida` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1712` |
| `gwent_purificar` | `gwent_especial_purificar` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1621` |
| `gwent_queima` | `gwent_especial_queima` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1616` |
| `gwent_requiem` | `gwent_especial_requiem` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1762` |
| `gwent_sangramento` | `elden_especial_sangramento` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1680` |
| `gwent_vinculo` | `gwent_especial_vinculo` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1639` |
| `impeto` | `chefe_oraculo_ruina`, `patente_9` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1837` |
| `instinto` | `arma_grande_sino`, `gwent_unidade_gigante` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1834` |
| `irmandade_veu` | — | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1893` |
| `lei_primeva` | `primordial_origem` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1830` |
| `olho_tempestade` | `chefe_placidusax_lorde_dragao`, `primordial_tempestade` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1846` |
| `paradoxo_eterno` | `gwent_singular_cacador_chefes`, `primordial_eternidade` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1832` |
| `precisao` | `arma_duas_luas`, `gwent_singular_intocavel` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1833` |
| `primeira_luz` | `chefe_rei_afogado`, `covenant_lua_velada` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1829` |
| `quebra_ritmo` | `chefe_guardiao_cinzas`, `chefe_messmer_impalador`, `chefe_radahn_flagelo_estrelas`, `magia_sol_negro`, `patente_10` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1845` |
| `reliquia_algemas` | `reliquia_algemas_margit` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1561` |
| `reliquia_godrick` | `reliquia_grande_runa_godrick` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1516` |
| `reliquia_lamina_negra` | `reliquia_lamina_negra` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1549` |
| `reliquia_morte` | `reliquia_runa_morte` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1529` |
| `reliquia_noite_chama` | `reliquia_noite_chama` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1537` |
| `reliquia_renala` | `reliquia_runa_nao_nascidos` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1521` |
| `resistencia_climatica` | — | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1862` |
| `ressurgir` | `gwent_unidade_necromante` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1879` |
| `retaliacao` | `covenant_irmandade_ferro`, `patente_6`, `patente_8` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1835` |
| `sangue_frio` | — | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1838` |
| `sobrevivente` | — | `NO_CURRENT_HANDLER_FOUND` | `—` |
| `ultimo_folego` | `chefe_dama_vazio`, `gwent_singular_nivel1` | `DIRECT_PLAY_BRANCH` | `aplicar_jogada:1831` |
| `vinganca` | `gwent_unidade_detonador`, `gwent_unidade_herdeiro_portao`, `gwent_unidade_senhor_cacada` | `LIFECYCLE_HOOK` | `_remover_unidade:1015` |

## 5. Identidades ativas

| Carta | Efeito identidade | Handler encontrado | Campo genérico suprimido |
|---|---|---|---|
| `arma_duas_luas` | `twin_dance` | `ACTIVE_IDENTITY_BRANCH_FOUND` (469) | True |
| `arma_grande_sino` | `last_bell` | `ACTIVE_IDENTITY_BRANCH_FOUND` (471) | True |
| `chefe_dama_vazio` | `void_rend` | `ACTIVE_IDENTITY_BRANCH_FOUND` (443) | True |
| `chefe_guardiao_cinzas` | `ash_guardian` | `ACTIVE_IDENTITY_BRANCH_FOUND` (439) | True |
| `chefe_malenia_lamina_miquella` | `scarlet_bloom` | `ACTIVE_IDENTITY_BRANCH_FOUND` (527) | True |
| `chefe_maliketh_morte_destinada` | `destined_death` | `ACTIVE_IDENTITY_BRANCH_FOUND` (536) | True |
| `chefe_messmer_impalador` | `impaling_spear` | `ACTIVE_IDENTITY_BRANCH_FOUND` (538) | True |
| `chefe_oraculo_ruina` | `ruin_omen` | `ACTIVE_IDENTITY_BRANCH_FOUND` (449) | True |
| `chefe_placidusax_lorde_dragao` | `time_storm` | `ACTIVE_IDENTITY_BRANCH_FOUND` (544) | True |
| `chefe_radahn_flagelo_estrelas` | `star_gravity` | `ACTIVE_IDENTITY_BRANCH_FOUND` (533) | True |
| `chefe_rei_afogado` | `abyss_tithe` | `ACTIVE_IDENTITY_BRANCH_FOUND` (447) | True |
| `covenant_lua_velada` | `veiled_moon` | `ACTIVE_IDENTITY_BRANCH_FOUND` (498) | True |
| `gwent_v75_lua_graviturgista` | `v75_gravity_shear` | `ACTIVE_IDENTITY_BRANCH_FOUND` (618) | False |
| `gwent_v75_lua_oraculo_geada` | `v75_frost_oracle` | `ACTIVE_IDENTITY_BRANCH_FOUND` (608) | False |
| `gwent_v75_ordem_confessora_graca` | `v75_grace_mender` | `ACTIVE_IDENTITY_BRANCH_FOUND` (562) | False |
| `gwent_v75_ordem_veterano_juramento` | `v75_golden_vow` | `ACTIVE_IDENTITY_BRANCH_FOUND` (550) | False |
| `gwent_v75_veu_acolito_sangue` | `v75_blood_mark` | `ACTIVE_IDENTITY_BRANCH_FOUND` (582) | False |
| `gwent_v75_veu_carrasco_preco` | `v75_blood_price` | `ACTIVE_IDENTITY_BRANCH_FOUND` (594) | False |
| `magia_nevoa_antiga` | `ancient_mist` | `ACTIVE_IDENTITY_BRANCH_FOUND` (487) | True |
| `magia_selo_vigilia` | `vigil_seal` | `ACTIVE_IDENTITY_BRANCH_FOUND` (482) | True |
| `magia_sol_negro` | `devouring_eclipse` | `ACTIVE_IDENTITY_BRANCH_FOUND` (489) | True |
| `magia_trovao_oco` | `hollow_thunder` | `ACTIVE_IDENTITY_BRANCH_FOUND` (485) | True |

## 6. Hooks ocultos e campos sem vínculo

### Hooks de ciclo de vida

| ID | Cartas atribuídas no catálogo efetivo | Implementação | Linhas |
|---|---|---|---:|
| `gloria` | `luterano_anjo`, `luterano_anjo2`, `luterano_vigia` | `HOOK_IMPLEMENTED` | 1168 |
| `sobrevivente` | — | `DECLARED_WITHOUT_HOOK` | — |

### Campos não mapeados

| Campo | Branch do resolver | Vínculo ativo | Conclusão |
|---|---:|---|---|
| `devoto` | 504 | False | `BRANCH_EXISTS_BUT_NO_ACTIVE_CARD_IDENTITY_BINDING` |
| `legado` | 501 | False | `BRANCH_EXISTS_BUT_NO_ACTIVE_CARD_IDENTITY_BINDING` |
| `escolha_ritmo` | 509 | False | `BRANCH_EXISTS_BUT_NO_ACTIVE_CARD_IDENTITY_BINDING` |
| `sinergia_faccao` | 512 | False | `BRANCH_EXISTS_BUT_NO_ACTIVE_CARD_IDENTITY_BINDING` |

## 7. Regras de interpretação

1. Compartilhar `effect_id` significa compartilhar uma estrutura de resolver, não necessariamente o mesmo resultado. Alvo, condição, quantidade, limites, duração, reset, prioridade e efeitos colaterais devem ser parâmetros explícitos.
2. O nível de risco é triagem conservadora; não é decisão `keep/merge/remove`.
3. `gloria` está implementada no fim da rodada; `sobrevivente` tem descrição, mas nenhum hook identificado. Não afirmar equivalência implementada.
4. Os campos `legado`, `devoto`, `escolha_ritmo` e `sinergia_faccao` têm ramos escritos dentro do resolver de identidade, mas não possuem vínculo ativo em `CARD_IDENTITY_ABILITIES`; não os tratar como habilidade genérica executável.
5. O novo registry não está conectado ao motor antigo. Nenhum efeito foi apagado ou atribuído a carta nova.

## 8. Reproduzir

```bash
python docs/scripts/build-effect-catalog-candidate-v0.1.py
python docs/scripts/test-effect-catalog-candidate-v0.1.py
python docs/scripts/audit-effect-semantic-groups-v0.1.py
python docs/scripts/test-effect-semantic-audit-v0.1.py
python docs/scripts/summarize-effect-catalog-candidate-v0.1.py
```

O JSON ao lado contém os mesmos achados, hashes das fontes, linhas de evidência e o inventário por família.

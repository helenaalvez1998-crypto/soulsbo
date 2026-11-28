# Consolidação do catálogo de efeitos — candidato v0.1

**Estado:** proposta de migração, não aprovada como regra final e ainda não conectada ao runtime. Gerado em 2026-11-27.

## 1. Resultado da extração

| Registro | Quantidade |
|---|---:|
| Definições em `HABILIDADES` | 59 |
| Efeitos genéricos de unidades | 32 |
| Especiais táticas | 21 |
| Relíquias | 6 |
| Identidades ativas | 22 |
| Combos | 27 |
| Líderes | 10 |
| Famílias canônicas candidatas | 54 |
| Famílias de unidade | 36 |
| Famílias de especial | 12 |
| Famílias de relíquia | 6 |

A proposta reduz definições repetidas por parametrização, mas preserva os IDs antigos no mapa de migração. Nenhum efeito é removido do runtime nesta etapa.

## 2. Famílias candidatas

| Novo effect_id | Nome | Tipo | IDs legados absorvidos |
|---|---|---|---|
| `effect.first_round_power` | Ímpeto da Primeira Luz | unit | `primeira_luz`, `lei_primeva` |
| `effect.comeback_power` | Força da Retomada | unit | `retaliacao`, `contragolpe`, `instinto`, `fome_abismo`, `last_bell` |
| `effect.ahead_power` | Ímpeto da Vantagem | unit | `impeto` |
| `effect.third_round_power` | Último Fôlego | unit | `ultimo_folego` |
| `effect.sequence_power` | Postura Encadeada | unit | `encadeamento`, `adaptacao`, `quebra_ritmo`, `veil_shift`, `pilgrim_duel`, `mist_trail` |
| `effect.tied_score_power` | Concentração | unit | `sangue_frio` |
| `effect.ranged_row_power` | Mira Cariana | unit | `precisao` |
| `effect.enemy_bonus_reduction` | Supressão de Bônus | unit | `drenagem`, `hollow_thunder`, `counterflame`, `void_rend`, `destined_death` |
| `effect.arcane_hunter_power` | Caçador de Feitiços | unit | `cacador_arcano` |
| `effect.enemy_field_suppression` | Decreto Soberano | unit | `decreto_soberano` |
| `effect.weather_affinity_power` | Afinidade com a Tempestade | unit | `olho_tempestade`, `ancient_mist` |
| `effect.late_round_reversal_power` | Paradoxo Eterno | unit | `paradoxo_eterno` |
| `effect.same_row_formation_power` | Formação da Fileira | unit | `guardiao_fileira`, `dupla_fornalha`, `forge_rhythm` |
| `effect.solitary_row_power` | Caçador Solitário | unit | `cacador_solitario` |
| `effect.row_aura_bonus` | Estandarte da Fileira | unit | `estandarte`, `grey_watch` |
| `effect.weather_resistance` | Resistência Climática | unit | `resistencia_climatica` |
| `effect.weather_ward_support` | Selo de Vigília | unit | `vigil_seal` |
| `effect.discard_special_power` | Eco das Cinzas Arcanas | unit | `eco_arcano`, `echo_orb` |
| `effect.death_revenge` | Vingança | unit | `vinganca` |
| `effect.entry_shield` | Escudo de Ferro | unit | `escudo_ferro` |
| `effect.ally_sacrifice_power` | Sacrifício Devorador | unit | `devorar`, `v75_blood_price` |
| `effect.revive_from_discard` | Ressurgir | unit | `ressurgir` |
| `effect.round_victory_survivor` | Glória da Sobrevivência | unit | `sobrevivente`, `gloria` |
| `effect.victory_draw` | Espólios | unit | `espolios` |
| `effect.cross_row_presence_power` | Passos entre Fileiras | unit | `irmandade_veu`, `twin_dance`, `shadow_paths`, `v75_lunar_cartography` |
| `effect.formation_or_discard_power` | Círculo de Ressonância | unit | `circulo_arcano` |
| `effect.row_pair_blessing` | Bênção de Companheiros | unit | `ash_guardian`, `v75_golden_vow` |
| `effect.discard_advantage_power` | Dízimo do Abismo | unit | `abyss_tithe` |
| `effect.ruin_omen` | Presságio da Ruína | unit | `ruin_omen` |
| `effect.enemy_positive_bonus_power` | Eclipse Devorador | unit | `devouring_eclipse` |
| `effect.cross_row_support` | Aliança Lunar | unit | `veiled_moon`, `covering_shot` |
| `effect.row_status_pressure` | Pressão de Estados | unit | `scarlet_bloom`, `impaling_spear`, `v75_blood_mark`, `v75_frost_oracle` |
| `effect.gravity_reposition` | Gravidade do Flagelo | unit | `star_gravity` |
| `effect.frost_storm_momentum` | Tempestade do Tempo | unit | `time_storm` |
| `effect.grace_purification` | Regressão Serena | unit | `v75_grace_mender` |
| `effect.gravity_shear` | Cisalhamento Gravitacional | unit | `v75_gravity_shear` |
| `effect.weather_row` | Tempestade dos Picos | special | `gwent_clima` |
| `effect.apply_status_marks` | Aplicação de Estados | special | `gwent_nevoa`, `gwent_geada`, `gwent_chuva`, `gwent_sangramento`, `gwent_geada_cariana`, `gwent_podrida`, `gwent_loucura` |
| `effect.row_buff` | Bênção de Fileira | special | `gwent_chifre`, `gwent_muralha`, `gwent_vinculo` |
| `effect.return_unit_to_hand` | Lágrima Sagrada | special | `gwent_medico` |
| `effect.remove_units` | Remoção Tática | special | `gwent_queima`, `gwent_execucao` |
| `effect.clear_weather` | Lei da Regressão | special | `gwent_purificar` |
| `effect.draw_cards` | Passo do Cão de Caça | special | `gwent_batedor` |
| `effect.grant_shield` | Bênção da Árvore Áurea | special | `gwent_egide` |
| `effect.revive_to_board` | Chamado dos Mortos | special | `gwent_requiem` |
| `effect.move_unit` | Passo do Lobo | special | `gwent_passo` |
| `effect.purify_frost_buff` | Chama do Gigante | special | `gwent_chama` |
| `effect.summon_wolves` | Cinzas dos Lobos Solitários | special | `gwent_invocacao` |
| `effect.relic_godrick_rune` | Grande Runa de Godrick | relic | `reliquia_godrick` |
| `effect.relic_unborn_rune` | Grande Runa dos Não Nascidos | relic | `reliquia_renala` |
| `effect.relic_death_rune` | Runa da Morte | relic | `reliquia_morte` |
| `effect.relic_night_flame_sword` | Espada da Noite e da Chama | relic | `reliquia_noite_chama` |
| `effect.relic_black_blade` | Lâmina Negra | relic | `reliquia_lamina_negra` |
| `effect.relic_margit_shackles` | Algemas de Margit | relic | `reliquia_algemas` |

## 3. Rastreabilidade de cada ID antigo

| ID antigo | Nome legado | Cartas atualmente atribuídas | Efeito candidato | Decisão proposta |
|---|---|---:|---|---|
| `adaptacao` | Passo do Peregrino | 1 | `effect.sequence_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `cacador_arcano` | Caçador de Feitiços | 4 | `effect.arcane_hunter_power` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `cacador_solitario` | Caçador Solitário | 1 | `effect.solitary_row_power` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `circulo_arcano` | Círculo de Ressonância | 0 | `effect.formation_or_discard_power` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `contragolpe` | Contragolpe | 0 | `effect.comeback_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `decreto_soberano` | Decreto Soberano | 1 | `effect.enemy_field_suppression` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `devorar` | Devorar | 1 | `effect.ally_sacrifice_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `drenagem` | Selo Enfraquecedor | 3 | `effect.enemy_bonus_reduction` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `dupla_fornalha` | Pacto da Fornalha | 0 | `effect.same_row_formation_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `eco_arcano` | Eco Arcano | 0 | `effect.discard_special_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `encadeamento` | Postura Encadeada | 2 | `effect.sequence_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `escudo_ferro` | Escudo de Ferro | 0 | `effect.entry_shield` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `espolios` | Espólios | 0 | `effect.victory_draw` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `estandarte` | Estandarte | 1 | `effect.row_aura_bonus` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `fome_abismo` | Fome do Abismo | 1 | `effect.comeback_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `guardiao_fileira` | Guardião da Fileira | 0 | `effect.same_row_formation_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `gwent_batedor` | Passo do Cão de Caça | 1 | `effect.draw_cards` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `gwent_chama` | Chama do Gigante | 1 | `effect.purify_frost_buff` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `gwent_chifre` | Rugido de Godfrey | 1 | `effect.row_buff` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `gwent_chuva` | Sangue Corrompido | 1 | `effect.apply_status_marks` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `gwent_clima` | Tempestade dos Picos | 1 | `effect.weather_row` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `gwent_egide` | Bênção da Árvore Áurea | 1 | `effect.grant_shield` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `gwent_execucao` | Lâmina da Morte Destinada | 1 | `effect.remove_units` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `gwent_geada` | Lua Gélida | 1 | `effect.apply_status_marks` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `gwent_geada_cariana` | Geada Cariana | 1 | `effect.apply_status_marks` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `gwent_invocacao` | Cinzas dos Lobos Solitários | 1 | `effect.summon_wolves` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `gwent_loucura` | Loucura Frenética | 1 | `effect.apply_status_marks` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `gwent_medico` | Lágrima Sagrada | 1 | `effect.return_unit_to_hand` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `gwent_muralha` | Bastião de Leyndell | 1 | `effect.row_buff` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `gwent_nevoa` | Névoa de Sellia | 1 | `effect.apply_status_marks` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `gwent_passo` | Passo do Lobo | 1 | `effect.move_unit` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `gwent_podrida` | Podridão Escarlate | 1 | `effect.apply_status_marks` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `gwent_purificar` | Lei da Regressão | 1 | `effect.clear_weather` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `gwent_queima` | Chama Negra | 1 | `effect.remove_units` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `gwent_requiem` | Chamado dos Mortos | 1 | `effect.revive_to_board` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `gwent_sangramento` | Sangramento | 1 | `effect.apply_status_marks` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `gwent_vinculo` | Juramento do Crisol | 1 | `effect.row_buff` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `impeto` | Ímpeto do Lorde | 2 | `effect.ahead_power` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `instinto` | Instinto de Caçador | 2 | `effect.comeback_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `irmandade_veu` | Formação do Véu | 0 | `effect.cross_row_presence_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `lei_primeva` | Lei Primeva | 1 | `effect.first_round_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `olho_tempestade` | Olho da Tempestade | 2 | `effect.weather_affinity_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `paradoxo_eterno` | Paradoxo Eterno | 2 | `effect.late_round_reversal_power` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `precisao` | Mira Cariana | 2 | `effect.ranged_row_power` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `primeira_luz` | Graça Dourada | 2 | `effect.first_round_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `quebra_ritmo` | Ruptura de Postura | 5 | `effect.sequence_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `reliquia_algemas` | Algemas de Margit | 1 | `effect.relic_margit_shackles` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `reliquia_godrick` | Grande Runa de Godrick | 1 | `effect.relic_godrick_rune` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `reliquia_lamina_negra` | Lâmina Negra | 1 | `effect.relic_black_blade` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `reliquia_morte` | Runa da Morte | 1 | `effect.relic_death_rune` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `reliquia_noite_chama` | Espada da Noite e da Chama | 1 | `effect.relic_night_flame_sword` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `reliquia_renala` | Grande Runa dos Não Nascidos | 1 | `effect.relic_unborn_rune` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `resistencia_climatica` | Resistência Climática | 0 | `effect.weather_resistance` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `ressurgir` | Ressurgir | 1 | `effect.revive_from_discard` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `retaliacao` | Retaliação dos Semideuses | 3 | `effect.comeback_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `sangue_frio` | Concentração | 0 | `effect.tied_score_power` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `sobrevivente` | Sobrevivente | 0 | `effect.round_victory_survivor` | `REDESIGN_AS_EXPLICIT_ROUND_END_EFFECT; NEW_HANDLER_REQUIRED` |
| `ultimo_folego` | Último Suspiro | 2 | `effect.third_round_power` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |
| `vinganca` | Vingança | 3 | `effect.death_revenge` | `KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST` |

## 4. Tratamento das 16 cartas com identidade + habilidade genérica

Foram encontradas **16** cartas com campo genérico preenchido e identidade ativa. O motor suprime o campo genérico e executa só a identidade. Na migração, o `effect_id` de identidade vira o único efeito da carta; o valor genérico suprimido é arquivado, não somado.

| card_id | campo genérico suprimido | efeito canônico único | decisão proposta |
|---|---|---|---|
| `arma_duas_luas` | `precisao` | `effect.cross_row_presence_power` | `KEEP_AS_SINGLE_CARD_EFFECT_CANDIDATE` |
| `arma_grande_sino` | `instinto` | `effect.comeback_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `chefe_dama_vazio` | `ultimo_folego` | `effect.enemy_bonus_reduction` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `chefe_guardiao_cinzas` | `quebra_ritmo` | `effect.row_pair_blessing` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `chefe_malenia_lamina_miquella` | `drenagem` | `effect.row_status_pressure` | `REDESIGN_OR_SPLIT_AFTER_BEHAVIOR_REVIEW` |
| `chefe_maliketh_morte_destinada` | `cacador_arcano` | `effect.enemy_bonus_reduction` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `chefe_messmer_impalador` | `quebra_ritmo` | `effect.row_status_pressure` | `REDESIGN_OR_SPLIT_AFTER_BEHAVIOR_REVIEW` |
| `chefe_oraculo_ruina` | `impeto` | `effect.ruin_omen` | `REDESIGN_OR_SPLIT_AFTER_BEHAVIOR_REVIEW` |
| `chefe_placidusax_lorde_dragao` | `olho_tempestade` | `effect.frost_storm_momentum` | `REDESIGN_OR_SPLIT_AFTER_BEHAVIOR_REVIEW` |
| `chefe_radahn_flagelo_estrelas` | `quebra_ritmo` | `effect.gravity_reposition` | `REDESIGN_OR_SPLIT_AFTER_BEHAVIOR_REVIEW` |
| `chefe_rei_afogado` | `primeira_luz` | `effect.discard_advantage_power` | `KEEP_AS_SINGLE_CARD_EFFECT_CANDIDATE` |
| `covenant_lua_velada` | `primeira_luz` | `effect.cross_row_support` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `magia_nevoa_antiga` | `encadeamento` | `effect.weather_affinity_power` | `MERGE_AS_PARAMETERIZED_FAMILY` |
| `magia_selo_vigilia` | `adaptacao` | `effect.weather_ward_support` | `KEEP_AS_SINGLE_CARD_EFFECT_CANDIDATE` |
| `magia_sol_negro` | `quebra_ritmo` | `effect.enemy_positive_bonus_power` | `KEEP_AS_SINGLE_CARD_EFFECT_CANDIDATE` |
| `magia_trovao_oco` | `drenagem` | `effect.enemy_bonus_reduction` | `MERGE_AS_PARAMETERIZED_FAMILY` |

## 5. Efeitos sem ligação, filtrados ou ocultos

| ID | Referência atual | Classificação | Decisão proposta |
|---|---|---|---|
| `shadow_paths` | `chefe_cervo_sombrio` | `ARCHIVE_AS_OPTIONAL_ALIAS` | `REMOVE_FROM_NEW_RUNTIME; PRESERVE_OPTIONAL_ALIAS_METADATA` |
| `faceless_hunt` | `chefe_cacador_sem_rosto` | `ARCHIVE_DO_NOT_REACTIVATE_AUTOMATICALLY` | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` |
| `grey_watch` | `chefe_vigia_cinzento` | `ARCHIVE_AS_OPTIONAL_ALIAS` | `REMOVE_FROM_NEW_RUNTIME; PRESERVE_OPTIONAL_ALIAS_METADATA` |
| `veil_shift` | `chefe_aparicao_veio` | `ARCHIVE_AS_OPTIONAL_ALIAS` | `REMOVE_FROM_NEW_RUNTIME; PRESERVE_OPTIONAL_ALIAS_METADATA` |
| `pilgrim_duel` | `arma_lamina_peregrino` | `ARCHIVE_AS_OPTIONAL_ALIAS` | `REMOVE_FROM_NEW_RUNTIME; PRESERVE_OPTIONAL_ALIAS_METADATA` |
| `forge_rhythm` | `arma_martelo_fornalha` | `ARCHIVE_AS_OPTIONAL_ALIAS` | `REMOVE_FROM_NEW_RUNTIME; PRESERVE_OPTIONAL_ALIAS_METADATA` |
| `tide_resonance` | `arma_cajado_marulho` | `ARCHIVE_DO_NOT_REACTIVATE_AUTOMATICALLY` | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` |
| `astral_thread` | `arma_agulha_astro` | `ARCHIVE_DO_NOT_REACTIVATE_AUTOMATICALLY` | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` |
| `furnace_charge` | `arma_lanca_fornalha` | `ARCHIVE_DO_NOT_REACTIVATE_AUTOMATICALLY` | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` |
| `covering_shot` | `arma_arco_peregrino` | `ARCHIVE_AS_OPTIONAL_ALIAS` | `REMOVE_FROM_NEW_RUNTIME; PRESERVE_OPTIONAL_ALIAS_METADATA` |
| `wandering_ember` | `magia_brasa_errante` | `ARCHIVE_DO_NOT_REACTIVATE_AUTOMATICALLY` | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` |
| `conductive_spark` | `magia_fagulha` | `ARCHIVE_DO_NOT_REACTIVATE_AUTOMATICALLY` | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` |
| `echo_orb` | `magia_orbe_eco` | `ARCHIVE_AS_OPTIONAL_ALIAS` | `REMOVE_FROM_NEW_RUNTIME; PRESERVE_OPTIONAL_ALIAS_METADATA` |
| `counterflame` | `magia_chama_fria` | `ARCHIVE_AS_OPTIONAL_ALIAS` | `REMOVE_FROM_NEW_RUNTIME; PRESERVE_OPTIONAL_ALIAS_METADATA` |
| `shared_sentinel` | `covenant_sentinelas` | `ARCHIVE_DO_NOT_REACTIVATE_AUTOMATICALLY` | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` |
| `last_oath` | `covenant_ultimos` | `ARCHIVE_DO_NOT_REACTIVATE_AUTOMATICALLY` | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` |
| `ember_kin` | `covenant_filhos_brasa` | `ARCHIVE_DO_NOT_REACTIVATE_AUTOMATICALLY` | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` |
| `mist_trail` | `covenant_peregrinos_nevoa` | `ARCHIVE_AS_OPTIONAL_ALIAS` | `REMOVE_FROM_NEW_RUNTIME; PRESERVE_OPTIONAL_ALIAS_METADATA` |
| `v75_crucible_guard` | `gwent_v75_ordem_guardiao_crisol` | `ARCHIVE_STALE_BRANCH` | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` |
| `v75_golden_standard` | `gwent_v75_ordem_arauto_estandarte` | `ARCHIVE_STALE_BRANCH` | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` |
| `v75_blood_feast` | `gwent_v75_veu_devota_hemorragia` | `ARCHIVE_STALE_BRANCH` | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` |
| `v75_blood_pursuit` | `gwent_v75_veu_cacador_sangue` | `ARCHIVE_STALE_BRANCH` | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` |
| `v75_lunar_cartography` | `gwent_v75_lua_cartografo_lunar` | `ARCHIVE_STALE_BRANCH` | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` |
| `v75_moon_ward` | `gwent_v75_lua_guardia` | `ARCHIVE_STALE_BRANCH` | `REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED` |
| `devoto` | `campo global` | `ARCHIVE_UNREGISTERED_FIELD_EFFECT` | `REMOVE_UNREGISTERED_FIELD_EFFECT_FROM_NEW_RUNTIME` |
| `legado` | `campo global` | `ARCHIVE_UNREGISTERED_FIELD_EFFECT` | `REMOVE_UNREGISTERED_FIELD_EFFECT_FROM_NEW_RUNTIME` |
| `escolha_ritmo` | `campo global` | `ARCHIVE_UNREGISTERED_FIELD_EFFECT` | `REMOVE_UNREGISTERED_FIELD_EFFECT_FROM_NEW_RUNTIME` |
| `sinergia_faccao` | `campo global` | `ARCHIVE_UNREGISTERED_FIELD_EFFECT` | `REMOVE_UNREGISTERED_FIELD_EFFECT_FROM_NEW_RUNTIME` |
| `gloria` | `luterano_anjo`, `luterano_anjo2`, `luterano_vigia` | `HOOK_DE_CICLO_DE_VIDA` | `REDESIGN_AS_EXPLICIT_ROUND_END_EFFECT; REVIEW_SOBREVIVENTE_DECLARATION_SEPARATELY` |
| `sobrevivente` | declaração sem carta | `HOOK_DE_CICLO_DE_VIDA` | `KEEP_AS_UNIMPLEMENTED_LEGACY_TEXT; DO_NOT_MIGRATE_WITHOUT_NEW_RULE_APPROVAL` |

## 6. Combos e tags

Os **27 combos** atuais foram copiados com prioridade, tags, mínimo de participantes e bônus. Cada um tem pelo menos um par de IDs distintos do catálogo atual que cobre as tags exigidas. A regra aprovada de participação permanece: a carta que recebe o bônus tem de contribuir com tag exigida.

Existem 5 IDs órfãos em `CARD_SYNERGY_TAGS`; eles serão excluídos do novo catálogo até que uma carta real seja definida:

- `gwent_unidade_cruzado`
- `gwent_unidade_evangelista`
- `gwent_unidade_missionario`
- `gwent_unidade_protetor`
- `gwent_unidade_sacerdote`

| Combo | Prioridade | Tags requeridas | Exemplo de dois participantes |
|---|---:|---|---|
| `cinzas_fornalha` | 10 | `cinzas`, `fornalha` | `chefe_guardiao_cinzas`, `gwent_unidade_baluarte` |
| `veu_sombrio` | 20 | `veu_sombrio` | `chefe_aparicao_veio`, `chefe_cervo_sombrio` |
| `vazio_astral` | 30 | `astral`, `vazio` | `arma_agulha_astro`, `chefe_dama_vazio` |
| `mare_abissal` | 40 | `abismo` | `chefe_rei_afogado`, `covenant_coroa_abismo` |
| `juramento_estandarte` | 50 | `estandarte` | `covenant_irmandade_ferro`, `gwent_unidade_portaestandarte` |
| `passos_duas_luas` | 60 | `duas_luas` | `arma_duas_luas`, `covenant_lua_velada` |
| `eco_convergente` | 70 | `astral`, `eco` | `arma_agulha_astro`, `gwent_unidade_eco` |
| `chama_dupla` | 80 | `chama` | `magia_brasa_errante`, `magia_chama_fria` |
| `muralha_inabalavel` | 90 | `muralha` | `gwent_unidade_herdeiro_portao`, `gwent_unidade_sentinela_rubra` |
| `banquete_guerra` | 100 | `banquete` | `gwent_unidade_carniceiro_forja`, `gwent_unidade_intendente` |
| `procissao_fantasma` | 110 | `fantasmas` | `gwent_unidade_cacadora_fantasma`, `gwent_unidade_cantora_lamentos` |
| `caravana_saqueadora` | 120 | `caravana` | `gwent_unidade_contrabandista`, `gwent_unidade_saqueadora_veu` |
| `ritual_runico` | 130 | `runico` | `gwent_unidade_detonador`, `gwent_unidade_guardiao_runas` |
| `eclipse_voraz` | 140 | `eclipse_voraz` | `gwent_unidade_bibliotecaria`, `gwent_unidade_devorador_mana` |
| `rota_peregrina` | 150 | `peregrino` | `arma_arco_peregrino`, `arma_lamina_peregrino` |
| `juramento_erdtree` | 160 | `ordem_dourada` | `chefe_guardiao_cinzas`, `gwent_unidade_baluarte` |
| `convergencia_lunar` | 170 | `lua_cariana` | `arma_agulha_astro`, `arma_duas_luas` |
| `ritual_dinastia` | 180 | `sangue_mohgwyn` | `chefe_rei_afogado`, `covenant_coroa_abismo` |
| `v75_juramento_dois_crisol` | 190 | `v75_crucible_guard`, `v75_erdtree_oath` | `gwent_v75_ordem_arauto_estandarte`, `gwent_v75_ordem_confessora_graca` |
| `v75_banquete_hemorragia` | 200 | `v75_blood_feast`, `v75_blood_mark` | `gwent_v75_veu_acolito_sangue`, `gwent_v75_veu_carrasco_preco` |
| `v75_convergencia_gelida` | 210 | `v75_frost_lore`, `v75_lunar_paths` | `gwent_v75_lua_cartografo_lunar`, `gwent_v75_lua_graviturgista` |
| `fe_gloria` | 220 | `fe`, `gloria_divina` | `luterano_anjo`, `luterano_anjo2` |
| `fe_devocao` | 230 | `devocao`, `fe` | `luterano_anjo`, `luterano_bispo` |
| `fe_evangelho` | 240 | `evangelho`, `fe` | `luterano_anjo`, `luterano_apostolo` |
| `fe_irmandade` | 250 | `fe`, `irmandade` | `luterano_anjo`, `luterano_irmao` |
| `fe_soberania` | 260 | `fe`, `soberania` | `luterano_anjo`, `luterano_papa` |
| `fe_sacerdos` | 270 | `fe`, `sacerdos` | `luterano_anjo`, `luterano_sacerdote` |

## 7. Líderes e passivas

Os 10 líderes foram extraídos para `leader-registry-candidate.v1.json`. Líder não é carta do deck e continua em um slot próprio. As quatro passivas de facção são extraídas para `faction-passives-candidate.v1.json`; o +1 da primeira unidade da facção por rodada não desqualifica carta pura.

## 8. Decisões estruturais importantes

1. `CARD_IDENTITY_ABILITIES` deixa de existir como lookup paralelo: o ID da carta aponta para exatamente um `effect_id`.
2. `CARD_SYNERGY_TAGS` migra para `combo_tags` no próprio registro da carta.
3. `FACTION_BOOST` fica em registro de passivas globais, separado dos efeitos individuais.
4. `RARITY_EFFECT_BUDGET` deve ser removido do novo runtime: raridade não pode ampliar efeitos silenciosamente.
5. `gloria` é um hook legado funcional em `_resolve_round()`; `sobrevivente` é somente texto declarado e sem handler. Não migrar os dois como equivalentes. Se a nova base mantiver uma regra de sobrevivência, especificá-la como mecânica nova, aprovada e testada, e decidir separadamente se o comportamento histórico de `gloria` será preservado.
6. Efeitos de status compartilham um sistema de marcas parametrizado, mas mantêm parâmetros distintos de status, alvo, limiar, expiração e consequência.

## 9. Pendências antes de aprovar o registry

- Rever efeitos compostos/fortes: `star_gravity`, `time_storm`, `v75_blood_price`, `ruin_omen` e `v75_gravity_shear`.
- Rever status e duração de Geada, Podridão, Sangramento e Loucura numa especificação única.
- Aprovar ou rejeitar cada família candidata e os aliases.
- Calibrar EFP, custo e raridade com simulações de partidas; ainda não usar a fórmula v0.1.
- Construir testes do novo resolver; `resolution_handler` neste registry é nome proposto, não função implementada.
- Atribuir cada efeito a cartas novas somente depois da aprovação do manifesto de cartas e da quota de 30% puras.

## 10. Reprodutibilidade e arquivos

Gerar novamente:
```bash
python docs/scripts/build-effect-catalog-candidate-v0.1.py
python docs/scripts/test-effect-catalog-candidate-v0.1.py
python docs/scripts/audit-effect-semantic-groups-v0.1.py
python docs/scripts/test-effect-semantic-audit-v0.1.py
python docs/scripts/summarize-effect-catalog-candidate-v0.1.py
```

Arquivos gerados:
- `data/card_game/effect-registry-candidate.v1.json` — definições de efeito e combos, validação do contrato v1.
- `data/card_game/legacy-effect-aliases-v0.1.json` — mapa de migração por ID, com parâmetros default e supressões.
- `data/card_game/leader-registry-candidate.v1.json` — líderes em slot separado.
- `data/card_game/faction-passives-candidate.v1.json` — passivas por facção.
- `docs/card-game-effect-catalog-decision-v0.1.json` — registro estruturado completo.
- `docs/card-game-effect-semantic-audit-v0.1.md/.json` — branches AST, hooks, riscos e diferenças semânticas revisadas.

**Limitação:** nenhuma função do motor legado foi alterada. As famílias e handlers são uma proposta de migração e precisam de aprovação e testes comportamentais antes de entrar em produção.

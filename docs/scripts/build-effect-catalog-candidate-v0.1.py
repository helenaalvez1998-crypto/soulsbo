#!/usr/bin/env python3
"""Build a traceable candidate registry from the legacy card-game runtime.

This script is a migration artifact builder. It does NOT edit runtime modules,
assign effects to the new card catalogue, or approve balance values.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import date
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import sistemas.cartas as legacy_cards  # noqa: E402
import sistemas.gwent as legacy_engine  # noqa: E402
from sistemas.card_contract import validate_effect_registry  # noqa: E402

OUT_REGISTRY = ROOT / "data/card_game/effect-registry-candidate.v1.json"
OUT_ALIASES = ROOT / "data/card_game/legacy-effect-aliases-v0.1.json"
OUT_LEADERS = ROOT / "data/card_game/leader-registry-candidate.v1.json"
OUT_FACTIONS = ROOT / "data/card_game/faction-passives-candidate.v1.json"
OUT_DECISIONS = ROOT / "docs/card-game-effect-catalog-decision-v0.1.json"
OUT_REPORT = ROOT / "docs/card-game-effect-catalog-decision-v0.1.md"


def p_int(minimum: int, maximum: int, description: str) -> dict:
    return {"type": "integer", "minimum": minimum, "maximum": maximum, "description": description}


def p_bool(description: str) -> dict:
    return {"type": "boolean", "description": description}


def p_enum(values: list[str], description: str) -> dict:
    return {"type": "string", "enum": values, "description": description}


def p_str(min_length: int, max_length: int, description: str) -> dict:
    return {"type": "string", "minLength": min_length, "maxLength": max_length, "description": description}


# New families consolidate effects that have the same gameplay rule and vary
# only by numeric or targeting parameters. Handler names are proposed names;
# no new handler is implemented in this step.
FAMILIES: list[dict] = [
    # Unit effects
    {"slug":"first_round_power","name":"Ímpeto da Primeira Luz","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_first_round_power","template":"Na primeira rodada, esta unidade recebe +{bonus} de bônus ao entrar em campo.","params":{"bonus":p_int(1,2,"Bônus recebido na primeira rodada.")},"aliases":{"primeira_luz":{"bonus":1},"lei_primeva":{"bonus":2}}},
    {"slug":"comeback_power","name":"Força da Retomada","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_comeback_power","template":"Se sua pontuação estiver abaixo da adversária, esta unidade recebe +{bonus} de bônus.","params":{"bonus":p_int(1,2,"Bônus recebido quando está atrás.")},"aliases":{"retaliacao":{"bonus":1},"contragolpe":{"bonus":2},"instinto":{"bonus":2},"fome_abismo":{"bonus":2},"last_bell":{"bonus":2}}},
    {"slug":"ahead_power","name":"Ímpeto da Vantagem","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_ahead_power","template":"Se sua pontuação estiver acima da adversária, esta unidade recebe +{bonus} de bônus.","params":{"bonus":p_int(1,1,"Bônus fixo quando está vencendo.")},"aliases":{"impeto":{"bonus":1}}},
    {"slug":"third_round_power","name":"Último Fôlego","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_third_round_power","template":"Na terceira rodada, esta unidade recebe +{bonus} de bônus ao entrar em campo.","params":{"bonus":p_int(1,1,"Bônus fixo na terceira rodada.")},"aliases":{"ultimo_folego":{"bonus":1}}},
    {"slug":"sequence_power","name":"Postura Encadeada","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_sequence_power","template":"Se houver jogada anterior do jogador de referência e a última unidade dele tiver sido jogada na fileira {row_relation}, esta unidade recebe +{bonus} de bônus.","params":{"reference_side":p_enum(["own","opponent"],"Jogador cuja última fileira será consultada."),"row_relation":p_enum(["same","different"],"Relação entre a fileira atual e a última fileira."),"requires_previous_play":p_bool("Exige que o jogador de referência já tenha jogado uma unidade nesta rodada."),"bonus":p_int(1,2,"Bônus concedido quando a condição é atendida.")},"aliases":{"encadeamento":{"reference_side":"own","row_relation":"same","requires_previous_play":True,"bonus":2},"adaptacao":{"reference_side":"own","row_relation":"different","requires_previous_play":True,"bonus":1},"quebra_ritmo":{"reference_side":"opponent","row_relation":"same","requires_previous_play":True,"bonus":1},"veil_shift":{"reference_side":"own","row_relation":"different","requires_previous_play":True,"bonus":2},"pilgrim_duel":{"reference_side":"opponent","row_relation":"same","requires_previous_play":True,"bonus":2},"mist_trail":{"reference_side":"own","row_relation":"different","requires_previous_play":True,"bonus":1}}},
    {"slug":"tied_score_power","name":"Concentração","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_tied_score_power","template":"Se as pontuações estiverem empatadas, esta unidade recebe +{bonus} de bônus.","params":{"bonus":p_int(2,2,"Bônus fixo em caso de empate.")},"aliases":{"sangue_frio":{"bonus":2}}},
    {"slug":"ranged_row_power","name":"Mira Cariana","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_ranged_row_power","template":"Ao entrar na fileira de Longa Distância, esta unidade recebe +{bonus} de bônus.","params":{"bonus":p_int(1,1,"Bônus fixo na fileira ranged.")},"aliases":{"precisao":{"bonus":1}}},
    {"slug":"enemy_bonus_reduction","name":"Supressão de Bônus","kind":"unit","timing":"on_play","duration":"persistent_until_changed","stacking":"capped","targeting":"enemy_units","handler":"resolve_enemy_bonus_reduction","template":"Reduz em {amount} o bônus dos inimigos conforme o escopo {target_scope}; o bônus não fica abaixo de {floor}.","params":{"target_scope":p_enum(["all_enemies","chosen_enemy_row","strongest_enemy","top_two_in_enemy_row"],"Escopo de alvos inimigos."),"amount":p_int(1,2,"Redução de bônus por alvo."),"floor":p_int(-2,0,"Limite inferior do bônus do alvo."),"only_positive":p_bool("Se verdadeiro, só considera alvos com bônus positivo.")},"aliases":{"drenagem":{"target_scope":"all_enemies","amount":1,"floor":-2,"only_positive":False},"hollow_thunder":{"target_scope":"chosen_enemy_row","amount":1,"floor":-2,"only_positive":False},"counterflame":{"target_scope":"top_two_in_enemy_row","amount":1,"floor":-2,"only_positive":False},"void_rend":{"target_scope":"strongest_enemy","amount":2,"floor":-2,"only_positive":False},"destined_death":{"target_scope":"strongest_enemy","amount":2,"floor":-2,"only_positive":False}}},
    {"slug":"arcane_hunter_power","name":"Caçador de Feitiços","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_arcane_hunter_power","template":"Se o adversário tiver uma unidade da Lua Negra ou uma unidade com bônus positivo, esta unidade recebe +{bonus}.","params":{"bonus":p_int(1,1,"Bônus fixo quando uma condição de caça é atendida.")},"aliases":{"cacador_arcano":{"bonus":1}}},
    {"slug":"enemy_field_suppression","name":"Decreto Soberano","kind":"unit","timing":"on_play","duration":"persistent_until_changed","stacking":"capped","targeting":"all_enemy_units","handler":"resolve_enemy_field_suppression","template":"Reduz em {amount} o bônus de todas as unidades inimigas, até o limite {floor}.","params":{"amount":p_int(2,2,"Redução aplicada a cada inimigo."),"floor":p_int(-2,-2,"Limite inferior de bônus." )},"aliases":{"decreto_soberano":{"amount":2,"floor":-2}}},
    {"slug":"weather_affinity_power","name":"Afinidade com a Tempestade","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_weather_affinity_power","template":"Se a condição climática {weather_scope} estiver ativa, esta unidade recebe +{bonus}.","params":{"weather_scope":p_enum(["own_row_active","any_row_active"],"Condição de clima que ativa o bônus."),"bonus":p_int(2,2,"Bônus fixo de afinidade climática.")},"aliases":{"olho_tempestade":{"weather_scope":"own_row_active","bonus":2},"ancient_mist":{"weather_scope":"any_row_active","bonus":2}}},
    {"slug":"late_round_reversal_power","name":"Paradoxo Eterno","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_late_round_reversal_power","template":"Na terceira rodada, se o adversário venceu a segunda, esta unidade recebe +{bonus}.","params":{"bonus":p_int(2,2,"Bônus fixo de reversão.")},"aliases":{"paradoxo_eterno":{"bonus":2}}},
    {"slug":"same_row_formation_power","name":"Formação da Fileira","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_same_row_formation_power","template":"Esta unidade recebe bônus pela presença de aliados na mesma fileira conforme os parâmetros da formação.","params":{"mode":p_enum(["per_ally","if_any"],"Modo de contabilização de aliados."),"bonus_per_ally":p_int(1,2,"Bônus por aliado ou bônus fixo do modo if_any."),"max_bonus":p_int(2,3,"Teto do bônus concedido."),"minimum_allies":p_int(1,2,"Quantidade mínima de aliados na mesma fileira."),"faction_filter":p_enum(["any","golden_order"],"Filtra aliados por facção ou aceita qualquer facção.")},"aliases":{"guardiao_fileira":{"mode":"per_ally","bonus_per_ally":1,"max_bonus":3,"minimum_allies":1,"faction_filter":"any"},"dupla_fornalha":{"mode":"if_any","bonus_per_ally":2,"max_bonus":2,"minimum_allies":1,"faction_filter":"any"},"forge_rhythm":{"mode":"per_ally","bonus_per_ally":1,"max_bonus":2,"minimum_allies":1,"faction_filter":"golden_order"}}},
    {"slug":"solitary_row_power","name":"Caçador Solitário","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_solitary_row_power","template":"Se não houver outro aliado na mesma fileira, esta unidade recebe +{bonus}.","params":{"bonus":p_int(2,2,"Bônus fixo por estar sozinho.")},"aliases":{"cacador_solitario":{"bonus":2}}},
    {"slug":"row_aura_bonus","name":"Estandarte da Fileira","kind":"unit","timing":"on_play","duration":"until_round_end","stacking":"additive","targeting":"allied_units_same_row","handler":"resolve_row_aura_bonus","template":"Concede +{bonus} de bônus às unidades da mesma fileira; os parâmetros determinam se esta carta também recebe o bônus.","params":{"bonus":p_int(1,1,"Bônus concedido por unidade."),"include_self":p_bool("Inclui a própria unidade na aura; falso significa apenas aliados já em campo.")},"aliases":{"estandarte":{"bonus":1,"include_self":False},"grey_watch":{"bonus":1,"include_self":False}}},
    {"slug":"weather_resistance","name":"Resistência Climática","kind":"unit","timing":"on_play","duration":"while_on_board","stacking":"replace","targeting":"self","handler":"resolve_weather_resistance","template":"Reduz em {resistance} a penalidade climática sofrida por esta unidade; se não houver clima ativo ao entrar, recebe +{bonus_if_no_weather}.","params":{"resistance":p_int(2,2,"Pontos de penalidade climática ignorados."),"bonus_if_no_weather":p_int(1,1,"Bônus se nenhum clima estiver ativo na entrada.")},"aliases":{"resistencia_climatica":{"resistance":2,"bonus_if_no_weather":1}}},
    {"slug":"weather_ward_support","name":"Selo de Vigília","kind":"unit","timing":"on_play","duration":"while_on_board","stacking":"replace","targeting":"self_and_one_same_row_ally","handler":"resolve_weather_ward_support","template":"Recebe {weather_resistance} de resistência climática e concede +{ally_bonus} a um aliado da mesma fileira, se houver.","params":{"weather_resistance":p_int(1,1,"Resistência climática recebida."),"ally_bonus":p_int(1,1,"Bônus concedido ao aliado." )},"aliases":{"vigil_seal":{"weather_resistance":1,"ally_bonus":1}}},
    {"slug":"discard_special_power","name":"Eco das Cinzas Arcanas","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_discard_special_power","template":"Recebe bônus por cartas especiais em seu descarte, conforme os parâmetros de acumulação.","params":{"bonus_per_special":p_int(1,2,"Bônus por carta especial no descarte."),"minimum_specials":p_int(1,1,"Mínimo de cartas especiais no descarte."),"max_bonus":p_int(2,2,"Teto do bônus concedido.")},"aliases":{"eco_arcano":{"bonus_per_special":2,"minimum_specials":1,"max_bonus":2},"echo_orb":{"bonus_per_special":1,"minimum_specials":1,"max_bonus":2}}},
    {"slug":"death_revenge","name":"Vingança","kind":"unit","timing":"on_death","duration":"immediate","stacking":"additive","targeting":"allied_units_same_row","handler":"resolve_death_revenge","template":"Ao ser removida, concede +{ally_bonus} às unidades aliadas restantes na mesma fileira.","params":{"ally_bonus":p_int(1,1,"Bônus concedido a cada aliado.")},"aliases":{"vinganca":{"ally_bonus":1}}},
    {"slug":"entry_shield","name":"Escudo de Ferro","kind":"unit","timing":"on_play","duration":"until_first_block","stacking":"replace","targeting":"self","handler":"resolve_entry_shield","template":"Entra com {shield_count} escudo(s), bloqueando a primeira remoção.","params":{"shield_count":p_int(1,1,"Quantidade de bloqueios.")},"aliases":{"escudo_ferro":{"shield_count":1}}},
    {"slug":"ally_sacrifice_power","name":"Sacrifício Devorador","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"weakest_allied_unit_same_row","handler":"resolve_ally_sacrifice_power","template":"Sacrifica o aliado elegível mais fraco na mesma fileira e recebe bônus conforme o poder dele, limitado a {gain_cap}; se não houver alvo, recebe {fallback_bonus}.","params":{"gain_cap":p_int(3,4,"Teto de bônus convertido do aliado sacrificado."),"fallback_bonus":p_int(0,1,"Bônus recebido sem alvo elegível."),"minimum_gain":p_int(1,1,"Bônus mínimo quando há sacrifício."),"target_selection":p_enum(["weakest_same_row"],"Regra de seleção do sacrifício.")},"aliases":{"devorar":{"gain_cap":4,"fallback_bonus":0,"minimum_gain":1,"target_selection":"weakest_same_row"},"v75_blood_price":{"gain_cap":3,"fallback_bonus":1,"minimum_gain":1,"target_selection":"weakest_same_row"}}},
    {"slug":"revive_from_discard","name":"Ressurgir","kind":"unit","timing":"on_play","duration":"immediate","stacking":"unique_card_instance","targeting":"strongest_eligible_unit_from_discard","handler":"resolve_revive_from_discard","template":"Traz ao campo a unidade mais forte do descarte com poder-base até {maximum_base_power}; ela entra sem bônus temporário.","params":{"maximum_base_power":p_int(5,5,"Poder-base máximo do alvo ressuscitado."),"target_selection":p_enum(["strongest_eligible"],"Regra automática de seleção."),"added_bonus":p_int(0,0,"Bônus inicial da unidade recuperada.")},"aliases":{"ressurgir":{"maximum_base_power":5,"target_selection":"strongest_eligible","added_bonus":0}}},
    {"slug":"round_victory_survivor","name":"Glória da Sobrevivência","kind":"unit","timing":"round_end","duration":"next_round_board_presence","stacking":"one_per_player","targeting":"strongest_tagged_unit","handler":"resolve_round_victory_survivor","template":"Se vencer a rodada, mantém no campo a unidade marcada mais forte; os demais aliados vão para o descarte. Bônus e estados temporários são removidos.","params":{"winner_only":p_bool("Só ativa quando o jogador vence a rodada."),"maximum_survivors":p_int(1,1,"Quantidade máxima de unidades que permanecem.")},"aliases":{"sobrevivente":{"winner_only":True,"maximum_survivors":1},"gloria":{"winner_only":True,"maximum_survivors":1}}},
    {"slug":"victory_draw","name":"Espólios","kind":"unit","timing":"round_end","duration":"immediate","stacking":"once_per_round","targeting":"owner_draw_pile","handler":"resolve_victory_draw","template":"Se vencer a rodada com esta unidade em campo, compra {draw_count} carta(s), se houver reserva.","params":{"draw_count":p_int(1,1,"Quantidade de cartas compradas.")},"aliases":{"espolios":{"draw_count":1}}},
    {"slug":"cross_row_presence_power","name":"Passos entre Fileiras","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_cross_row_presence_power","template":"Recebe bônus quando há aliados em outras fileiras, conforme o modo e o limite definidos.","params":{"mode":p_enum(["any_other_row","per_distinct_other_row"],"Modo de contagem de fileiras aliadas diferentes."),"bonus_per_row":p_int(1,2,"Bônus por condição/fileira."),"max_bonus":p_int(1,2,"Teto de bônus." )},"aliases":{"irmandade_veu":{"mode":"any_other_row","bonus_per_row":2,"max_bonus":2},"twin_dance":{"mode":"any_other_row","bonus_per_row":1,"max_bonus":1},"shadow_paths":{"mode":"per_distinct_other_row","bonus_per_row":1,"max_bonus":2},"v75_lunar_cartography":{"mode":"per_distinct_other_row","bonus_per_row":1,"max_bonus":2}}},
    {"slug":"formation_or_discard_power","name":"Círculo de Ressonância","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_formation_or_discard_power","template":"Se houver outro aliado na mesma fileira ou uma carta especial em seu descarte, recebe +{bonus}.","params":{"bonus":p_int(2,2,"Bônus fixo por uma das condições.")},"aliases":{"circulo_arcano":{"bonus":2}}},
    {"slug":"row_pair_blessing","name":"Bênção de Companheiros","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self_and_one_same_row_ally","handler":"resolve_row_pair_blessing","template":"Recebe +{self_bonus} e, se houver aliado na mesma fileira, concede +{ally_bonus} ao aliado selecionado.","params":{"self_bonus":p_int(0,1,"Bônus aplicado à própria unidade."),"ally_bonus":p_int(1,1,"Bônus aplicado ao aliado."),"ally_selection":p_enum(["first_same_row","weakest_same_row"],"Critério de seleção do aliado." )},"aliases":{"ash_guardian":{"self_bonus":1,"ally_bonus":1,"ally_selection":"first_same_row"},"v75_golden_vow":{"self_bonus":1,"ally_bonus":1,"ally_selection":"weakest_same_row"}}},
    {"slug":"discard_advantage_power","name":"Dízimo do Abismo","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_discard_advantage_power","template":"Recebe +{discard_bonus} se houver unidade em seu descarte; caso contrário, recebe +{fallback_bonus} se o adversário tiver mais unidades em campo.","params":{"discard_bonus":p_int(2,2,"Bônus com descarte não vazio."),"fallback_bonus":p_int(1,1,"Bônus alternativo."),"fallback_condition":p_enum(["opponent_has_more_units"],"Condição do bônus alternativo." )},"aliases":{"abyss_tithe":{"discard_bonus":2,"fallback_bonus":1,"fallback_condition":"opponent_has_more_units"}}},
    {"slug":"ruin_omen","name":"Presságio da Ruína","kind":"unit","timing":"on_play","duration":"persistent_until_changed","stacking":"capped","targeting":"strongest_enemy_and_self","handler":"resolve_ruin_omen","template":"Reduz em {enemy_bonus_reduction} o bônus do inimigo mais forte (limite {enemy_bonus_floor}) e, se estiver perdendo, recebe +{self_bonus_if_behind}.","params":{"enemy_bonus_reduction":p_int(1,1,"Redução no bônus do inimigo."),"enemy_bonus_floor":p_int(-2,-2,"Limite inferior do bônus inimigo."),"self_bonus_if_behind":p_int(1,1,"Bônus próprio se estiver atrás." )},"aliases":{"ruin_omen":{"enemy_bonus_reduction":1,"enemy_bonus_floor":-2,"self_bonus_if_behind":1}}},
    {"slug":"enemy_positive_bonus_power","name":"Eclipse Devorador","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self","handler":"resolve_enemy_positive_bonus_power","template":"Se algum inimigo tiver bônus positivo, recebe +{bonus}.","params":{"bonus":p_int(2,2,"Bônus fixo de absorção arcana." )},"aliases":{"devouring_eclipse":{"bonus":2}}},
    {"slug":"cross_row_support","name":"Aliança Lunar","kind":"unit","timing":"on_play","duration":"permanent_bonus","stacking":"additive","targeting":"self_and_weakest_ally_other_row","handler":"resolve_cross_row_support","template":"Recebe +{self_bonus} e concede +{ally_bonus} ao aliado mais fraco em outra fileira, se houver.","params":{"self_bonus":p_int(0,1,"Bônus próprio."),"ally_bonus":p_int(1,1,"Bônus ao aliado."),"ally_selection":p_enum(["weakest_other_row"],"Critério do aliado de suporte.")},"aliases":{"veiled_moon":{"self_bonus":1,"ally_bonus":1,"ally_selection":"weakest_other_row"},"covering_shot":{"self_bonus":0,"ally_bonus":1,"ally_selection":"weakest_other_row"}}},
    {"slug":"row_status_pressure","name":"Pressão de Estados","kind":"unit","timing":"on_play","duration":"until_round_end_or_threshold","stacking":"marks_up_to_cap","targeting":"enemy_units_same_row","handler":"resolve_row_status_pressure","template":"Aplica {status} na fileira inimiga; ao atingir {threshold_marks} marcas, executa a consequência configurada.","params":{"status":p_enum(["podrida","sangramento","geada"],"Estado aplicado."),"target_scope":p_enum(["all_enemies_same_row","strongest_enemy_same_row"],"Quais inimigos recebem o estado."),"marks_per_entry":p_int(1,2,"Marcas adicionadas por ativação."),"threshold_marks":p_int(2,2,"Quantidade de marcas para a consequência."),"threshold_bonus_loss":p_int(0,2,"Perda de bônus do alvo ao atingir o limiar."),"self_bonus_on_threshold":p_int(0,1,"Bônus próprio ao atingir o limiar, quando aplicável."),"reset_marks_on_threshold":p_bool("Se verdadeiro, as marcas são consumidas ao atingir o limiar.")},"aliases":{"scarlet_bloom":{"status":"podrida","target_scope":"all_enemies_same_row","marks_per_entry":1,"threshold_marks":2,"threshold_bonus_loss":1,"self_bonus_on_threshold":0,"reset_marks_on_threshold":False},"impaling_spear":{"status":"sangramento","target_scope":"all_enemies_same_row","marks_per_entry":1,"threshold_marks":2,"threshold_bonus_loss":2,"self_bonus_on_threshold":0,"reset_marks_on_threshold":True},"v75_blood_mark":{"status":"sangramento","target_scope":"strongest_enemy_same_row","marks_per_entry":1,"threshold_marks":2,"threshold_bonus_loss":2,"self_bonus_on_threshold":1,"reset_marks_on_threshold":True},"v75_frost_oracle":{"status":"geada","target_scope":"strongest_enemy_same_row","marks_per_entry":1,"threshold_marks":2,"threshold_bonus_loss":0,"self_bonus_on_threshold":1,"reset_marks_on_threshold":False}}},
    {"slug":"gravity_reposition","name":"Gravidade do Flagelo","kind":"unit","timing":"on_play","duration":"persistent_until_changed","stacking":"capped","targeting":"strongest_enemy","handler":"resolve_gravity_reposition","template":"Move o inimigo mais forte para a fileira desta unidade e reduz em {bonus_loss} o bônus dele, até -2.","params":{"bonus_loss":p_int(2,2,"Redução de bônus aplicada ao alvo."),"destination":p_enum(["this_card_row"],"Fileira de destino do alvo.")},"aliases":{"star_gravity":{"bonus_loss":2,"destination":"this_card_row"}}},
    {"slug":"frost_storm_momentum","name":"Tempestade do Tempo","kind":"unit","timing":"on_play","duration":"until_round_end","stacking":"marks_up_to_cap","targeting":"enemy_units_same_row_and_self","handler":"resolve_frost_storm_momentum","template":"Aplica uma marca de Geada aos inimigos da mesma fileira; recebe +1 por inimigo atingido, até +{self_bonus_cap}.","params":{"marks_per_enemy":p_int(1,1,"Marcas de Geada aplicadas por inimigo."),"max_marks":p_int(2,2,"Limite de marcas de Geada."),"self_bonus_per_target":p_int(1,1,"Bônus próprio por alvo atingido."),"self_bonus_cap":p_int(3,3,"Teto do bônus próprio." )},"aliases":{"time_storm":{"marks_per_enemy":1,"max_marks":2,"self_bonus_per_target":1,"self_bonus_cap":3}}},
    {"slug":"grace_purification","name":"Regressão Serena","kind":"unit","timing":"on_play","duration":"until_round_end","stacking":"purify_then_buff","targeting":"up_to_two_same_row_allies","handler":"resolve_grace_purification","template":"Purifica até {max_targets} aliados afetados na mesma fileira e concede +{bonus_per_purified}; se não houver alvos afetados, aplica o fallback descrito.","params":{"max_targets":p_int(2,2,"Máximo de aliados purificados."),"bonus_per_purified":p_int(1,1,"Bônus por aliado purificado."),"fallback":p_enum(["weakest_same_row_then_self"],"Comportamento sem alvos afetados.")},"aliases":{"v75_grace_mender":{"max_targets":2,"bonus_per_purified":1,"fallback":"weakest_same_row_then_self"}}},
    {"slug":"gravity_shear","name":"Cisalhamento Gravitacional","kind":"unit","timing":"on_play","duration":"persistent_until_changed","stacking":"capped","targeting":"up_to_two_positive_bonus_enemies_same_row","handler":"resolve_gravity_shear","template":"Reduz em {amount} o bônus de até {max_targets} inimigos com bônus positivo na mesma fileira; se atingir todos os alvos previstos, recebe +{self_bonus_when_full}.","params":{"amount":p_int(1,1,"Redução de bônus por alvo."),"max_targets":p_int(2,2,"Máximo de inimigos afetados."),"self_bonus_when_full":p_int(1,1,"Bônus próprio quando dois alvos são atingidos."),"bonus_floor":p_int(-2,-2,"Limite inferior do bônus inimigo.")},"aliases":{"v75_gravity_shear":{"amount":1,"max_targets":2,"self_bonus_when_full":1,"bonus_floor":-2}}},
    # Tactical specials
    {"slug":"weather_row","name":"Tempestade dos Picos","kind":"special","timing":"special_action","duration":"until_round_end","stacking":"replace_row_weather","targeting":"chosen_row_both_sides","handler":"resolve_weather_row","template":"Aplica clima severo à fileira escolhida; as unidades dos dois lados sofrem -{power_penalty} de poder efetivo enquanto durar.","params":{"power_penalty":p_int(1,1,"Penalidade de poder efetivo por unidade." )},"aliases":{"gwent_clima":{"power_penalty":1}}},
    {"slug":"apply_status_marks","name":"Aplicação de Estados","kind":"special","timing":"special_action","duration":"until_round_end_or_threshold","stacking":"marks_up_to_cap","targeting":"enemy_scope_from_params","handler":"resolve_apply_status_marks","template":"Aplica {marks} marca(s) de {status} ao escopo definido; ao atingir o limiar, executa {threshold_action}.","params":{"status":p_enum(["podrida","sangramento","geada","loucura"],"Estado aplicado."),"target_scope":p_enum(["chosen_enemy_row","all_enemies","enemy_siege_row"],"Escopo de inimigos afetados."),"marks":p_int(1,2,"Marcas tentadas por alvo."),"mark_cap":p_int(1,2,"Limite de marcas por alvo."),"threshold_marks":p_int(2,2,"Limiar para a consequência secundária."),"threshold_action":p_enum(["corrode_positive_bonus_1","reduce_bonus_2_and_reset","reduce_effective_power_per_mark","clear_positive_bonus","none"],"Consequência ao atingir o limiar."),"rarity_scaling":p_bool("Deve permanecer falso; raridade não amplia o efeito.")},"aliases":{"gwent_nevoa":{"status":"podrida","target_scope":"chosen_enemy_row","marks":1,"mark_cap":2,"threshold_marks":2,"threshold_action":"corrode_positive_bonus_1","rarity_scaling":False},"gwent_geada":{"status":"geada","target_scope":"all_enemies","marks":1,"mark_cap":2,"threshold_marks":2,"threshold_action":"reduce_effective_power_per_mark","rarity_scaling":False},"gwent_chuva":{"status":"sangramento","target_scope":"enemy_siege_row","marks":1,"mark_cap":2,"threshold_marks":2,"threshold_action":"reduce_bonus_2_and_reset","rarity_scaling":False},"gwent_sangramento":{"status":"sangramento","target_scope":"chosen_enemy_row","marks":1,"mark_cap":2,"threshold_marks":2,"threshold_action":"reduce_bonus_2_and_reset","rarity_scaling":False},"gwent_geada_cariana":{"status":"geada","target_scope":"chosen_enemy_row","marks":1,"mark_cap":2,"threshold_marks":2,"threshold_action":"reduce_effective_power_per_mark","rarity_scaling":False},"gwent_podrida":{"status":"podrida","target_scope":"chosen_enemy_row","marks":1,"mark_cap":2,"threshold_marks":2,"threshold_action":"corrode_positive_bonus_1","rarity_scaling":False},"gwent_loucura":{"status":"loucura","target_scope":"chosen_enemy_row","marks":1,"mark_cap":2,"threshold_marks":2,"threshold_action":"clear_positive_bonus","rarity_scaling":False}}},
    {"slug":"row_buff","name":"Bênção de Fileira","kind":"special","timing":"special_action","duration":"until_round_end","stacking":"additive","targeting":"allied_units_chosen_row","handler":"resolve_row_buff","template":"Concede +{bonus} às unidades aliadas na fileira escolhida; a condição exige ao menos {minimum_allies} unidade(s).","params":{"bonus":p_int(1,2,"Bônus concedido por unidade."),"minimum_allies":p_int(0,2,"Mínimo de unidades aliadas na fileira." )},"aliases":{"gwent_chifre":{"bonus":2,"minimum_allies":0},"gwent_muralha":{"bonus":1,"minimum_allies":0},"gwent_vinculo":{"bonus":2,"minimum_allies":2}}},
    {"slug":"return_unit_to_hand","name":"Lágrima Sagrada","kind":"special","timing":"special_action","duration":"immediate","stacking":"unique_card_instance","targeting":"own_discard_to_hand","handler":"resolve_return_unit_to_hand","template":"Devolve à mão uma unidade do descarte com poder-base até {maximum_base_power}.","params":{"maximum_base_power":p_int(4,4,"Poder-base máximo; sem aumento por raridade."),"target_selection":p_enum(["chosen_or_last_eligible"],"Regra de seleção do alvo." )},"aliases":{"gwent_medico":{"maximum_base_power":4,"target_selection":"chosen_or_last_eligible"}}},
    {"slug":"remove_units","name":"Remoção Tática","kind":"special","timing":"special_action","duration":"immediate","stacking":"once_per_action","targeting":"enemy_or_both_sides","handler":"resolve_remove_units","template":"Remove alvos conforme {target_scope}; escudos bloqueiam cada tentativa. O limite de poder, quando aplicável, é {power_limit}.","params":{"target_scope":p_enum(["strongest_unit_each_side","chosen_enemy_row_under_power_limit"],"Critério de seleção dos alvos."),"max_targets":p_int(1,2,"Máximo de alvos removidos."),"power_limit":p_int(0,6,"Poder efetivo máximo; zero significa sem limite."),"shield_blocks":p_bool("Se verdadeiro, escudo bloqueia remoção." )},"aliases":{"gwent_queima":{"target_scope":"strongest_unit_each_side","max_targets":2,"power_limit":0,"shield_blocks":True},"gwent_execucao":{"target_scope":"chosen_enemy_row_under_power_limit","max_targets":1,"power_limit":6,"shield_blocks":True}}},
    {"slug":"clear_weather","name":"Lei da Regressão","kind":"special","timing":"special_action","duration":"immediate","stacking":"clear_all","targeting":"all_weather_rows","handler":"resolve_clear_weather","template":"Remove todos os efeitos climáticos ativos.","params":{},"aliases":{"gwent_purificar":{}}},
    {"slug":"draw_cards","name":"Passo do Cão de Caça","kind":"special","timing":"special_action","duration":"immediate","stacking":"draw","targeting":"own_draw_pile","handler":"resolve_draw_cards","template":"Compra {count} carta(s) da reserva, se disponíveis.","params":{"count":p_int(1,1,"Quantidade fixa de cartas; sem aumento por raridade.")},"aliases":{"gwent_batedor":{"count":1}}},
    {"slug":"grant_shield","name":"Bênção da Árvore Áurea","kind":"special","timing":"special_action","duration":"until_first_block","stacking":"one_shield_per_unit","targeting":"one_allied_unit","handler":"resolve_grant_shield","template":"Concede {shield_count} escudo a uma unidade aliada sem escudo.","params":{"shield_count":p_int(1,1,"Quantidade de escudos por alvo."),"max_targets":p_int(1,1,"Máximo de alvos; não escala com raridade.")},"aliases":{"gwent_egide":{"shield_count":1,"max_targets":1}}},
    {"slug":"revive_to_board","name":"Chamado dos Mortos","kind":"special","timing":"special_action","duration":"immediate","stacking":"unique_card_instance","targeting":"own_discard_to_board","handler":"resolve_revive_to_board","template":"Traz ao campo uma unidade do descarte com poder-base até {maximum_base_power}; ela entra sem bônus temporários.","params":{"maximum_base_power":p_int(6,6,"Poder-base máximo; sem aumento por raridade."),"target_selection":p_enum(["chosen_or_strongest_eligible"],"Regra de seleção."),"added_bonus":p_int(0,0,"Bônus inicial da unidade ressuscitada.")},"aliases":{"gwent_requiem":{"maximum_base_power":6,"target_selection":"chosen_or_strongest_eligible","added_bonus":0}}},
    {"slug":"move_unit","name":"Passo do Lobo","kind":"special","timing":"special_action","duration":"persistent_until_changed","stacking":"move","targeting":"one_allied_unit_to_chosen_row","handler":"resolve_move_unit","template":"Move {max_targets} unidade(s) aliada(s) para a fileira escolhida.","params":{"max_targets":p_int(1,1,"Quantidade fixa; sem aumento por raridade."),"target_selection":p_enum(["chosen_or_weakest_movable"],"Regra de seleção do alvo." )},"aliases":{"gwent_passo":{"max_targets":1,"target_selection":"chosen_or_weakest_movable"}}},
    {"slug":"purify_frost_buff","name":"Chama do Gigante","kind":"special","timing":"special_action","duration":"until_round_end","stacking":"purify_then_buff","targeting":"allied_units_with_frost","handler":"resolve_purify_frost_buff","template":"Remove Geada de todas as unidades aliadas afetadas; cada unidade purificada recebe +{bonus_per_unit}.","params":{"bonus_per_unit":p_int(1,1,"Bônus por unidade purificada.")},"aliases":{"gwent_chama":{"bonus_per_unit":1}}},
    {"slug":"summon_wolves","name":"Cinzas dos Lobos Solitários","kind":"special","timing":"special_action","duration":"until_round_end_or_board_clear","stacking":"summon","targeting":"chosen_row","handler":"resolve_summon_wolves","template":"Invoca {count} unidade(s) de Lobos Espirituais com poder-base {power_base} na fileira escolhida.","params":{"count":p_int(1,1,"Quantidade fixa de invocações."),"power_base":p_int(3,3,"Poder-base fixo; sem aumento por raridade." )},"aliases":{"gwent_invocacao":{"count":1,"power_base":3}}},
    # Relics; they remain outside the 12-card deck slots.
    {"slug":"relic_godrick_rune","name":"Grande Runa de Godrick","kind":"relic","timing":"relic_action","duration":"persistent_until_changed","stacking":"additive","targeting":"all_allied_units","handler":"resolve_relic_godrick_rune","template":"Exige ao menos uma unidade aliada em campo e concede +{bonus} a todas elas.","params":{"bonus":p_int(1,1,"Bônus fixo da relíquia.")},"aliases":{"reliquia_godrick":{"bonus":1}}},
    {"slug":"relic_unborn_rune","name":"Grande Runa dos Não Nascidos","kind":"relic","timing":"relic_action","duration":"immediate","stacking":"purify_then_buff","targeting":"allied_units_with_frost_or_rot","handler":"resolve_relic_unborn_rune","template":"Remove Geada e Podridão dos aliados afetados; cada unidade purificada recebe +{bonus}.","params":{"bonus":p_int(1,1,"Bônus por unidade purificada.")},"aliases":{"reliquia_renala":{"bonus":1}}},
    {"slug":"relic_death_rune","name":"Runa da Morte","kind":"relic","timing":"relic_action","duration":"persistent_until_changed","stacking":"capped","targeting":"highest_positive_bonus_enemy_per_row","handler":"resolve_relic_death_rune","template":"Em cada fileira, reduz em até {amount} o bônus positivo do inimigo com maior bônus, sem criar bônus negativo.","params":{"amount":p_int(2,2,"Redução máxima de bônus por fileira."),"floor":p_int(0,0,"Limite mínimo de bônus após aplicação.")},"aliases":{"reliquia_morte":{"amount":2,"floor":0}}},
    {"slug":"relic_night_flame_sword","name":"Espada da Noite e da Chama","kind":"relic","timing":"relic_action","duration":"immediate","stacking":"stance_choice","targeting":"chosen_enemy_row","handler":"resolve_relic_night_flame_sword","template":"Na postura da Noite, aplica Geada à fileira escolhida; na postura da Chama, reduz poder-base em {base_power_loss} e bônus em {bonus_loss} do inimigo mais forte. Escudo bloqueia a Chama.","params":{"stance":p_enum(["night","flame"],"Postura escolhida."),"base_power_loss":p_int(1,1,"Redução do poder-base na postura da Chama."),"bonus_loss":p_int(2,2,"Redução do bônus na postura da Chama.")},"aliases":{"reliquia_noite_chama":{"stance":"night","base_power_loss":1,"bonus_loss":2}}},
    {"slug":"relic_black_blade","name":"Lâmina Negra","kind":"relic","timing":"relic_action","duration":"persistent_until_changed","stacking":"once_if_not_blocked","targeting":"one_enemy_in_chosen_row","handler":"resolve_relic_black_blade","template":"Reduz em {bonus_loss} o bônus de um inimigo na fileira escolhida; escudo bloqueia sem consumir a relíquia.","params":{"bonus_loss":p_int(3,3,"Redução fixa de bônus."),"shield_blocks_without_consumption":p_bool("A relíquia não é consumida quando escudo bloqueia.")},"aliases":{"reliquia_lamina_negra":{"bonus_loss":3,"shield_blocks_without_consumption":True}}},
    {"slug":"relic_margit_shackles","name":"Algemas de Margit","kind":"relic","timing":"relic_action","duration":"persistent_until_changed","stacking":"set_positive_to_zero","targeting":"one_enemy_in_chosen_row","handler":"resolve_relic_margit_shackles","template":"Zera o bônus positivo de um inimigo na fileira escolhida; bônus negativos permanecem inalterados.","params":{"target_selection":p_enum(["chosen_or_highest_bonus"],"Regra de seleção do alvo.")},"aliases":{"reliquia_algemas":{"target_selection":"chosen_or_highest_bonus"}}},
]

# Legacy-to-candidate map for additional identity branches that are no longer
# linked to an active card. Only safe semantic aliases are recorded; the rest
# stay archived and do not enter the candidate registry.
STALE_ALIAS_CANDIDATES = {
    "shadow_paths": ("effect.cross_row_presence_power", {"mode":"per_distinct_other_row","bonus_per_row":1,"max_bonus":2}),
    "grey_watch": ("effect.row_aura_bonus", {"bonus":1,"include_self":False}),
    "veil_shift": ("effect.sequence_power", {"reference_side":"own","row_relation":"different","requires_previous_play":True,"bonus":2}),
    "pilgrim_duel": ("effect.sequence_power", {"reference_side":"opponent","row_relation":"same","requires_previous_play":True,"bonus":2}),
    "forge_rhythm": ("effect.same_row_formation_power", {"mode":"per_ally","bonus_per_ally":1,"max_bonus":2,"minimum_allies":1,"faction_filter":"golden_order"}),
    "covering_shot": ("effect.cross_row_support", {"self_bonus":0,"ally_bonus":1,"ally_selection":"weakest_other_row"}),
    "mist_trail": ("effect.sequence_power", {"reference_side":"own","row_relation":"different","requires_previous_play":True,"bonus":1}),
    "echo_orb": ("effect.discard_special_power", {"bonus_per_special":1,"minimum_specials":1,"max_bonus":2}),
    "counterflame": ("effect.enemy_bonus_reduction", {"target_scope":"top_two_in_enemy_row","amount":1,"floor":-2,"only_positive":False}),
}

FACTION_ID_MAP = {
    "Ordem Áurea": "golden_order",
    "Véu Carmesim": "crimson_veil",
    "Lua Negra": "dark_moon",
    "Os Esquecidos": "the_forgotten",
}


def dump(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def build():
    effects = []
    alias_to_family: dict[str, tuple[str, dict, str]] = {}
    for family in FAMILIES:
        effect_id = "effect." + family["slug"]
        alias_items = family["aliases"].items()
        for legacy_id, params in alias_items:
            if legacy_id in alias_to_family:
                raise RuntimeError(f"legacy alias duplicado: {legacy_id}")
            alias_to_family[legacy_id] = (effect_id, params, family["kind"])
        effects.append({
            "effect_id": effect_id,
            "name": family["name"],
            "kind": family["kind"],
            "parameters": family["params"],
            "required_parameters": list(family["params"].keys()),
            "allow_additional_parameters": False,
            "rules_template": family["template"],
            "resolution_handler": family["handler"],
            "timing": family["timing"],
            "duration": family["duration"],
            "stacking": family["stacking"],
            "targeting": family["targeting"],
            "test_id": "candidate." + family["slug"],
        })

    # Add legacy IDs defined in HABILIDADES and assert all are migrated.
    generic_ids = set(legacy_cards.HABILIDADES)
    cards_by_skill: dict[str, list[str]] = defaultdict(list)
    for card_id, card in legacy_cards.CARTAS_POR_ID.items():
        skill_id = getattr(card, "habilidade", None)
        if isinstance(skill_id, str) and skill_id:
            cards_by_skill[skill_id].append(card_id)
    missing_legacy = sorted(generic_ids - set(alias_to_family))
    if missing_legacy:
        raise RuntimeError("HABILIDADES sem destino: " + ", ".join(missing_legacy))

    # Active identity effects are card-specific in the old runtime. They map
    # into the same one-effect-per-card registry, not a second hidden channel.
    identity_alias_to_family: dict[str, tuple[str, dict]] = {}
    for card_id, entry in legacy_engine.CARD_IDENTITY_ABILITIES.items():
        legacy_effect = entry["effect"]
        if legacy_effect in alias_to_family:
            effect_id, params, _kind = alias_to_family[legacy_effect]
            identity_alias_to_family[legacy_effect] = (effect_id, params)
        else:
            # Find the family by scanning aliases explicitly recorded above.
            family_target = None
            for family in FAMILIES:
                if legacy_effect in family["aliases"]:
                    family_target = ("effect." + family["slug"], family["aliases"][legacy_effect])
                    break
            if family_target is None:
                # Identity effect may be a distinct active candidate. It will
                # be added below only when explicitly described in this map.
                identity_alias_to_family[legacy_effect] = ("", {})
            else:
                identity_alias_to_family[legacy_effect] = family_target

    # `legacy_effect` is not necessarily an HABILIDADES key. Map the 22 active
    # identities explicitly to the semantic family selected by review.
    identity_targets = {
        "ash_guardian": ("effect.row_pair_blessing", {"self_bonus":1,"ally_bonus":1,"ally_selection":"first_same_row"}),
        "void_rend": ("effect.enemy_bonus_reduction", {"target_scope":"strongest_enemy","amount":2,"floor":-2,"only_positive":False}),
        "abyss_tithe": ("effect.discard_advantage_power", {"discard_bonus":2,"fallback_bonus":1,"fallback_condition":"opponent_has_more_units"}),
        "ruin_omen": ("effect.ruin_omen", {"enemy_bonus_reduction":1,"enemy_bonus_floor":-2,"self_bonus_if_behind":1}),
        "twin_dance": ("effect.cross_row_presence_power", {"mode":"any_other_row","bonus_per_row":1,"max_bonus":1}),
        "last_bell": ("effect.comeback_power", {"bonus":2}),
        "vigil_seal": ("effect.weather_ward_support", {"weather_resistance":1,"ally_bonus":1}),
        "hollow_thunder": ("effect.enemy_bonus_reduction", {"target_scope":"chosen_enemy_row","amount":1,"floor":-2,"only_positive":False}),
        "ancient_mist": ("effect.weather_affinity_power", {"weather_scope":"any_row_active","bonus":2}),
        "devouring_eclipse": ("effect.enemy_positive_bonus_power", {"bonus":2}),
        "veiled_moon": ("effect.cross_row_support", {"self_bonus":1,"ally_bonus":1,"ally_selection":"weakest_other_row"}),
        "scarlet_bloom": ("effect.row_status_pressure", {"status":"podrida","target_scope":"all_enemies_same_row","marks_per_entry":1,"threshold_marks":2,"threshold_bonus_loss":1,"self_bonus_on_threshold":0,"reset_marks_on_threshold":False}),
        "star_gravity": ("effect.gravity_reposition", {"bonus_loss":2,"destination":"this_card_row"}),
        "destined_death": ("effect.enemy_bonus_reduction", {"target_scope":"strongest_enemy","amount":2,"floor":-2,"only_positive":False}),
        "impaling_spear": ("effect.row_status_pressure", {"status":"sangramento","target_scope":"all_enemies_same_row","marks_per_entry":1,"threshold_marks":2,"threshold_bonus_loss":2,"self_bonus_on_threshold":0,"reset_marks_on_threshold":True}),
        "time_storm": ("effect.frost_storm_momentum", {"marks_per_enemy":1,"max_marks":2,"self_bonus_per_target":1,"self_bonus_cap":3}),
        "v75_golden_vow": ("effect.row_pair_blessing", {"self_bonus":1,"ally_bonus":1,"ally_selection":"weakest_same_row"}),
        "v75_grace_mender": ("effect.grace_purification", {"max_targets":2,"bonus_per_purified":1,"fallback":"weakest_same_row_then_self"}),
        "v75_blood_mark": ("effect.row_status_pressure", {"status":"sangramento","target_scope":"strongest_enemy_same_row","marks_per_entry":1,"threshold_marks":2,"threshold_bonus_loss":2,"self_bonus_on_threshold":1,"reset_marks_on_threshold":True}),
        "v75_blood_price": ("effect.ally_sacrifice_power", {"gain_cap":3,"fallback_bonus":1,"minimum_gain":1,"target_selection":"weakest_same_row"}),
        "v75_frost_oracle": ("effect.row_status_pressure", {"status":"geada","target_scope":"strongest_enemy_same_row","marks_per_entry":1,"threshold_marks":2,"threshold_bonus_loss":0,"self_bonus_on_threshold":1,"reset_marks_on_threshold":False}),
        "v75_gravity_shear": ("effect.gravity_shear", {"amount":1,"max_targets":2,"self_bonus_when_full":1,"bonus_floor":-2}),
    }
    for identity_effect_id, (canonical_id, params) in identity_targets.items():
        identity_alias_to_family[identity_effect_id] = (canonical_id, params)

    # Verify active identity effects are fully represented.
    active_identity_ids = {entry["effect"] for entry in legacy_engine.CARD_IDENTITY_ABILITIES.values()}
    if active_identity_ids != set(identity_targets):
        raise RuntimeError(f"Mapa de identidades incompleto: missing={sorted(active_identity_ids-set(identity_targets))}; extra={sorted(set(identity_targets)-active_identity_ids)}")

    # All combos are imported from the current, already-approved resolver policy.
    cards_by_id = legacy_cards.CARTAS_POR_ID
    tag_map = legacy_engine.CARD_SYNERGY_TAGS
    valid_tag_card_ids = {card_id for card_id in tag_map if card_id in cards_by_id}
    orphan_tag_card_ids = sorted(set(tag_map) - set(cards_by_id))
    combos = []
    combo_pair_evidence = []
    providers_by_tag: dict[str, list[str]] = defaultdict(list)
    for card_id in valid_tag_card_ids:
        for tag in tag_map[card_id]:
            providers_by_tag[tag].append(card_id)
    for combo_id, combo in sorted(legacy_engine.SYNERGY_COMBOS.items(), key=lambda kv: (kv[1]["priority"], kv[0])):
        required_tags = sorted(combo["tags"])
        possible_ids = sorted({cid for tag in required_tags for cid in providers_by_tag.get(tag, [])})
        valid_pair = None
        for left, right in combinations(possible_ids, 2):
            combined = set(tag_map[left]) | set(tag_map[right])
            if set(required_tags) <= combined:
                valid_pair = [left, right]
                break
        if valid_pair is None:
            raise RuntimeError(f"Combo sem par de participantes distintos: {combo_id}")
        minimum = int(combo.get("minimum", 2))
        if minimum < 2:
            raise RuntimeError(f"Combo viola mínimo aprovado: {combo_id}")
        combos.append({
            "combo_id": "combo." + combo_id,
            "name": combo["name"],
            "required_tags": required_tags,
            "minimum_participants": minimum,
            "priority": int(combo["priority"]),
            "individual_bonus": combo.get("bonus", 0),
            "team_bonus": combo.get("team_bonus", 0),
            "test_id": "combo." + combo_id,
        })
        combo_pair_evidence.append({
            "combo_id": combo_id,
            "required_tags": required_tags,
            "distinct_participant_example": valid_pair,
            "provider_counts": {tag: len(providers_by_tag.get(tag, [])) for tag in required_tags},
        })

    registry = {
        "schema_version": 1,
        "effects": effects,
        "combos": combos,
    }
    validation = validate_effect_registry(registry)
    if not validation.valid:
        raise RuntimeError("Registry candidate inválido: " + " | ".join(validation.errors))

    # Alias mapping for all 59 HABILIDADES entries.
    legacy_aliases = []
    for legacy_id in sorted(generic_ids):
        canonical_id, params, family_kind = alias_to_family[legacy_id]
        legacy_meta = legacy_cards.HABILIDADES[legacy_id]
        assigned_card_ids = sorted(cards_by_skill.get(legacy_id, []))
        migration_status = "PARAMETERIZED_ALIAS" if sum(1 for f in FAMILIES if len(f["aliases"]) > 1 and legacy_id in f["aliases"]) else "DIRECT_ALIAS"
        if legacy_id == "sobrevivente":
            proposed_disposition = "REDESIGN_AS_EXPLICIT_ROUND_END_EFFECT; NEW_HANDLER_REQUIRED"
        elif migration_status == "PARAMETERIZED_ALIAS":
            proposed_disposition = "MERGE_AS_PARAMETERIZED_FAMILY"
        else:
            proposed_disposition = "KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST"
        legacy_aliases.append({
            "legacy_id": legacy_id,
            "legacy_namespace": "HABILIDADES",
            "legacy_kind": "relic" if legacy_id.startswith("reliquia_") else "special" if legacy_id.startswith("gwent_") else "unit",
            "legacy_display_name": legacy_meta.get("nome", legacy_id),
            "legacy_description": legacy_meta.get("texto", ""),
            "assigned_card_ids": assigned_card_ids,
            "assigned_card_count": len(assigned_card_ids),
            "canonical_effect_id": canonical_id,
            "default_effect_params": params,
            "migration_status": migration_status,
            "proposed_disposition": proposed_disposition,
        })

    identity_aliases = []
    for card_id, entry in sorted(legacy_engine.CARD_IDENTITY_ABILITIES.items()):
        canonical_id, params = identity_targets[entry["effect"]]
        card = cards_by_id.get(card_id)
        complex_identity_effects = {"ruin_omen", "star_gravity", "time_storm", "v75_gravity_shear", "scarlet_bloom", "impaling_spear", "v75_blood_mark", "v75_frost_oracle", "v75_blood_price"}
        if entry["effect"] in complex_identity_effects:
            identity_disposition = "REDESIGN_OR_SPLIT_AFTER_BEHAVIOR_REVIEW"
        elif canonical_id in {"effect.comeback_power", "effect.enemy_bonus_reduction", "effect.weather_affinity_power", "effect.row_pair_blessing", "effect.cross_row_support", "effect.row_status_pressure"}:
            identity_disposition = "MERGE_AS_PARAMETERIZED_FAMILY"
        else:
            identity_disposition = "KEEP_AS_SINGLE_CARD_EFFECT_CANDIDATE"
        identity_aliases.append({
            "card_id": card_id,
            "legacy_identity_effect_id": entry["effect"],
            "legacy_display_name": entry["name"],
            "legacy_description": entry["text"],
            "legacy_generic_field_suppressed": bool(card and card.habilidade),
            "suppressed_generic_field": card.habilidade if card and card.habilidade else None,
            "canonical_effect_id": canonical_id,
            "default_effect_params": params,
            "migration_status": "IDENTITY_BECOMES_SINGLE_CANONICAL_EFFECT",
            "proposed_disposition": identity_disposition,
        })

    stale = json.loads((ROOT / "docs/card-game-stale-identity-disposition-v0.1.json").read_text(encoding="utf-8"))
    stale_v18 = stale.get("v18_filtered_identity_candidates", [])
    stale_v75 = stale.get("stale_v75_effect_candidates", [])
    unresolved_fields = stale.get("unmapped_legacy_field_effect_candidates", [])

    stale_decisions = []
    for item in stale_v18:
        effect_id = item["effect_id"]
        if effect_id in STALE_ALIAS_CANDIDATES:
            canonical_id, params = STALE_ALIAS_CANDIDATES[effect_id]
            disposition = "ARCHIVE_AS_OPTIONAL_ALIAS"
        else:
            canonical_id, params = None, {}
            disposition = "ARCHIVE_DO_NOT_REACTIVATE_AUTOMATICALLY"
        stale_decisions.append({
            "legacy_effect_id": effect_id,
            "card_id": item["card_id"],
            "card_name": item["card_name"],
            "current_tags": item.get("synergy_tags", []),
            "candidate_effect_id": canonical_id,
            "candidate_params": params,
            "disposition": disposition,
            "proposed_disposition": "REMOVE_FROM_NEW_RUNTIME; PRESERVE_OPTIONAL_ALIAS_METADATA" if disposition == "ARCHIVE_AS_OPTIONAL_ALIAS" else "REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED",
            "reason": "Definição filtrada pela transformação V18; reativação só poderá ocorrer por atribuição explícita no novo manifesto de cartas.",
        })
    for item in stale_v75:
        stale_decisions.append({
            "legacy_effect_id": item["effect_id"],
            "card_id": item["associated_current_card_id"],
            "card_name": item["card_name"],
            "current_tags": item.get("synergy_tags", []),
            "candidate_effect_id": None,
            "candidate_params": {},
            "disposition": "ARCHIVE_STALE_BRANCH",
            "proposed_disposition": "REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED",
            "reason": "A carta atual declara habilidade individual vazia; o efeito só aparece como ramo de identidade sem associação ativa.",
        })
    for legacy_id in unresolved_fields:
        stale_decisions.append({
            "legacy_effect_id": legacy_id,
            "card_id": None,
            "card_name": None,
            "current_tags": [],
            "candidate_effect_id": None,
            "candidate_params": {},
            "disposition": "ARCHIVE_UNREGISTERED_FIELD_EFFECT",
            "proposed_disposition": "REMOVE_UNREGISTERED_FIELD_EFFECT_FROM_NEW_RUNTIME",
            "reason": "Código legado sem entrada em HABILIDADES e sem associação de identidade ativa; os valores de campo não têm resolução genérica canônica.",
        })

    # Legacy generic field values on cards with active identities are not
    # migrated as a second effect. The card gets exactly one identity-derived
    # canonical effect as required by the new data contract.
    suppressed_overrides = [x for x in identity_aliases if x["legacy_generic_field_suppressed"]]

    # Five orphan tag keys are confirmed in the legacy map and excluded from
    # the new catalog until a real card definition is authored.
    orphan_ids = orphan_tag_card_ids

    leaders = []
    for leader_id, entry in sorted(legacy_engine.LEADERS.items()):
        leaders.append({
            "leader_id": leader_id,
            "name": entry["name"],
            "faction_id": FACTION_ID_MAP[entry["faction"]],
            "legacy_faction_name": entry["faction"],
            "legacy_effect_id": entry["effect"],
            "resolution_handler_candidate": "resolve_leader_" + entry["effect"],
            "description_current": entry["description"],
            "uses_per_match": 1,
            "status": "IMPLEMENTED_IN_LEGACY; NEW_HANDLER_NOT_IMPLEMENTED",
        })

    faction_passives = []
    for faction_name, archetype in sorted(legacy_engine.FACTION_ARCHETYPES.items()):
        faction_passives.append({
            "faction_id": FACTION_ID_MAP[faction_name],
            "legacy_faction_name": faction_name,
            "archetype_name_current": archetype["name"],
            "archetype_description_current": archetype["description"],
            "passive_id": "faction.first_unit_of_faction_each_round",
            "trigger": "first_unit_of_this_faction_played_each_round",
            "bonus": 1,
            "status": "LEGACY_GLOBAL_RULE; NEW_REGISTRY_CANDIDATE",
        })

    # All HABILIDADES IDs and active identities must have a valid canonical target.
    candidate_effect_ids = {e["effect_id"] for e in effects}
    assert len(legacy_aliases) == 59
    assert len(identity_aliases) == 22
    assert len(combos) == 27
    for alias in legacy_aliases:
        assert alias["canonical_effect_id"] in candidate_effect_ids, alias
    for alias in identity_aliases:
        assert alias["canonical_effect_id"] in candidate_effect_ids, alias
    for leader in leaders:
        assert leader["leader_id"] in legacy_engine.LEADERS

    aliases_payload = {
        "metadata": {
            "document": "Mapa de aliases do catálogo de efeitos legado para o candidato v0.1",
            "generated_at": date.today().isoformat(),
            "status": "PROPOSTA DE MIGRAÇÃO; NÃO ALTERA O RUNTIME",
            "source": "sistemas/cartas.py, sistemas/gwent.py e docs/card-game-card-traceability.json",
            "warning": "Os parâmetros são defaults de migração e precisam de teste/balanceamento antes de serem usados em cartas novas.",
        },
        "generic_and_special_aliases": legacy_aliases,
        "active_identity_card_overrides": identity_aliases,
        "identity_generic_suppression_count": len(suppressed_overrides),
        "inactive_identity_branch_decisions": stale_decisions,
        "hidden_lifecycle_aliases": [
            {"legacy_id":"gloria","source":"_resolve_round() in sistemas/gwent.py","assigned_card_ids":sorted(cards_by_skill.get("gloria", [])),"assigned_card_count":len(cards_by_skill.get("gloria", [])),"candidate_effect_id":"effect.round_victory_survivor","disposition":"REGISTER_EXPLICITLY; CURRENTLY HIDDEN OUTSIDE HABILIDADES","proposed_disposition":"REDESIGN_AS_EXPLICIT_ROUND_END_EFFECT; REVIEW_SOBREVIVENTE_DECLARATION_SEPARATELY"},
            {"legacy_id":"sobrevivente","source":"HABILIDADES in sistemas/cartas.py","assigned_card_ids":sorted(cards_by_skill.get("sobrevivente", [])),"assigned_card_count":len(cards_by_skill.get("sobrevivente", [])),"candidate_effect_id":"effect.round_victory_survivor","disposition":"ARCHIVE_UNIMPLEMENTED_TEXT; NO_AUTOMATIC_MIGRATION","proposed_disposition":"KEEP_AS_UNIMPLEMENTED_LEGACY_TEXT; DO_NOT_MIGRATE_WITHOUT_NEW_RULE_APPROVAL"},
        ],
        "orphan_synergy_card_ids": orphan_ids,
    }

    leaders_payload = {
        "schema_version": 1,
        "status": "CANDIDATE; NOT CONNECTED TO RUNTIME",
        "leaders": leaders,
    }
    factions_payload = {
        "schema_version": 1,
        "status": "CANDIDATE; PASSIVES ARE SEPARATE FROM CARD EFFECTS",
        "passives": faction_passives,
    }

    decisions = {
        "metadata": {
            "document": "Decisões de consolidação do catálogo de efeitos v0.1",
            "generated_at": date.today().isoformat(),
            "status": "CANDIDATE FOR REVIEW; NOT AN APPROVED FINAL GAME RULESET",
            "source_baseline": "soulsbo-main(1).zip; runtime modules sistemas/cartas.py and sistemas/gwent.py",
            "candidate_effect_family_count": len(effects),
            "legacy_generic_definition_count": len(legacy_aliases),
            "active_identity_count": len(identity_aliases),
            "combo_count": len(combos),
            "leader_count": len(leaders),
        },
        "counts": {
            "legacy_habilidades": len(legacy_cards.HABILIDADES),
            "legacy_unit_skill_definitions": sum(1 for k in legacy_cards.HABILIDADES if not k.startswith(("gwent_","reliquia_"))),
            "legacy_tactical_special_definitions": sum(1 for k in legacy_cards.HABILIDADES if k.startswith("gwent_")),
            "legacy_relic_definitions": sum(1 for k in legacy_cards.HABILIDADES if k.startswith("reliquia_")),
            "candidate_effect_families_by_kind": dict(Counter(effect["kind"] for effect in effects)),
            "active_identity_effects": len(identity_aliases),
            "identity_cards_with_suppressed_generic_field": len(suppressed_overrides),
            "filtered_identity_branches_v18": len(stale_v18),
            "stale_v75_identity_branches": len(stale_v75),
            "unregistered_field_effect_ids": len(unresolved_fields),
            "hidden_gloria_cards": 3,
            "declared_survivente_without_handler": True,
            "combos": len(combos),
            "combo_tag_card_ids": len(tag_map),
            "combo_tag_card_ids_with_catalog_entry": len(valid_tag_card_ids),
            "orphan_combo_card_ids": len(orphan_ids),
            "leaders": len(leaders),
            "faction_passives": len(faction_passives),
        },
        "recommendation_counts": {
            "generic_aliases": dict(Counter(item["proposed_disposition"] for item in legacy_aliases)),
            "identity_overrides": dict(Counter(item["proposed_disposition"] for item in identity_aliases)),
            "inactive_branches": dict(Counter(item["proposed_disposition"] for item in stale_decisions)),
        },
        "families": [
            {
                "effect_id":"effect."+f["slug"],
                "name":f["name"],
                "kind":f["kind"],
                "resolution_handler_candidate":f["handler"],
                "legacy_aliases":list(f["aliases"].keys()),
                "required_params":list(f["params"].keys()),
                "timing":f["timing"],
                "recommendation":"KEEP_OR_MERGE_INTO_CANONICAL_FAMILY",
            }
            for f in FAMILIES
        ],
        "generic_special_and_relic_aliases": legacy_aliases,
        "active_identity_card_overrides": identity_aliases,
        "inactive_identity_branch_decisions": stale_decisions,
        "combo_pair_evidence": combo_pair_evidence,
        "orphan_tag_card_ids": orphan_ids,
        "leader_registry": leaders,
        "faction_passives": faction_passives,
        "global_rule_decisions": [
            {"rule":"FACTION_BOOST","recommendation":"KEEP_AS_SEPARATE_FACTION_PASSIVE","reason":"O bônus de +1 na primeira unidade da facção por rodada não é efeito individual e não deve invalidar carta pura."},
            {"rule":"RARITY_EFFECT_BUDGET","recommendation":"REMOVE_FROM_NEW_RUNTIME_AFTER_MIGRATION","reason":"Amplificação automática por raridade cria uma segunda camada de poder não declarada. Poder, efeito e custo devem estar definidos na carta/compilação; raridade não deve alterar o handler silenciosamente."},
            {"rule":"CARD_IDENTITY_ABILITIES","recommendation":"REMOVE_AS_PARALLEL_LOOKUP_AFTER_MIGRATION","reason":"O novo card_id aponta para um único effect_id. Identidade não pode executar habilidade paralela escondida."},
            {"rule":"CARD_SYNERGY_TAGS","recommendation":"MOVE_TO_CANONICAL_CARD.combo_tags","reason":"Tags ficam declaradas junto da carta, não num mapa separado por ID."},
        ],
        "not_yet_approved_or_implemented": [
            "Pontuação EFP e pesos de balanceamento.",
            "Custo individual e orçamento de deck.",
            "Fórmula e faixas finais de raridade.",
            "Quais efeitos candidatos serão realmente atribuídos a cada uma das 137 cartas reescritas.",
            "Remoção física dos handlers legados, que só ocorrerá após migração e testes do novo motor.",
        ],
    }

    dump(OUT_REGISTRY, registry)
    dump(OUT_ALIASES, aliases_payload)
    dump(OUT_LEADERS, leaders_payload)
    dump(OUT_FACTIONS, factions_payload)
    dump(OUT_DECISIONS, decisions)

    # Human-readable report.
    lines = [
        "# Consolidação do catálogo de efeitos — candidato v0.1",
        "",
        f"**Estado:** proposta de migração, não aprovada como regra final e ainda não conectada ao runtime. Gerado em {date.today().isoformat()}.",
        "",
        "## 1. Resultado da extração",
        "",
        "| Registro | Quantidade |",
        "|---|---:|",
        f"| Definições em `HABILIDADES` | {len(legacy_cards.HABILIDADES)} |",
        f"| Efeitos genéricos de unidades | {decisions['counts']['legacy_unit_skill_definitions']} |",
        f"| Especiais táticas | {decisions['counts']['legacy_tactical_special_definitions']} |",
        f"| Relíquias | {decisions['counts']['legacy_relic_definitions']} |",
        f"| Identidades ativas | {len(identity_aliases)} |",
        f"| Combos | {len(combos)} |",
        f"| Líderes | {len(leaders)} |",
        f"| Famílias canônicas candidatas | {len(effects)} |",
        f"| Famílias de unidade | {sum(1 for effect in effects if effect['kind'] == 'unit')} |",
        f"| Famílias de especial | {sum(1 for effect in effects if effect['kind'] == 'special')} |",
        f"| Famílias de relíquia | {sum(1 for effect in effects if effect['kind'] == 'relic')} |",
        "",
        "A proposta reduz definições repetidas por parametrização, mas preserva os IDs antigos no mapa de migração. Nenhum efeito é removido do runtime nesta etapa.",
        "",
        "## 2. Famílias candidatas",
        "",
        "| Novo effect_id | Nome | Tipo | IDs legados absorvidos |",
        "|---|---|---|---|",
    ]
    for f in FAMILIES:
        lines.append(f"| `effect.{f['slug']}` | {f['name']} | {f['kind']} | {', '.join('`'+x+'`' for x in f['aliases'])} |")
    lines += [
        "",
        "## 3. Rastreabilidade de cada ID antigo",
        "",
        "| ID antigo | Nome legado | Cartas atualmente atribuídas | Efeito candidato | Decisão proposta |",
        "|---|---|---:|---|---|",
    ]
    for item in legacy_aliases:
        lines.append(f"| `{item['legacy_id']}` | {item['legacy_display_name']} | {item['assigned_card_count']} | `{item['canonical_effect_id']}` | `{item['proposed_disposition']}` |")
    lines += [
        "",
        "## 4. Tratamento das 16 cartas com identidade + habilidade genérica",
        "",
        f"Foram encontradas **{len(suppressed_overrides)}** cartas com campo genérico preenchido e identidade ativa. O motor suprime o campo genérico e executa só a identidade. Na migração, o `effect_id` de identidade vira o único efeito da carta; o valor genérico suprimido é arquivado, não somado.",
        "",
        "| card_id | campo genérico suprimido | efeito canônico único | decisão proposta |",
        "|---|---|---|---|",
    ]
    for item in suppressed_overrides:
        lines.append(f"| `{item['card_id']}` | `{item['suppressed_generic_field']}` | `{item['canonical_effect_id']}` | `{item['proposed_disposition']}` |")
    lines += [
        "",
        "## 5. Efeitos sem ligação, filtrados ou ocultos",
        "",
        "| ID | Referência atual | Classificação | Decisão proposta |",
        "|---|---|---|---|",
    ]
    for item in stale_decisions:
        ref = item.get("card_id") or "campo global"
        lines.append(f"| `{item['legacy_effect_id']}` | `{ref}` | `{item['disposition']}` | `{item['proposed_disposition']}` |")
    for item in aliases_payload["hidden_lifecycle_aliases"]:
        ref = ", ".join("`" + x + "`" for x in item["assigned_card_ids"]) or "declaração sem carta"
        lines.append(f"| `{item['legacy_id']}` | {ref} | `HOOK_DE_CICLO_DE_VIDA` | `{item['proposed_disposition']}` |")
    lines += [
        "",
        "## 6. Combos e tags",
        "",
        f"Os **{len(combos)} combos** atuais foram copiados com prioridade, tags, mínimo de participantes e bônus. Cada um tem pelo menos um par de IDs distintos do catálogo atual que cobre as tags exigidas. A regra aprovada de participação permanece: a carta que recebe o bônus tem de contribuir com tag exigida.",
        "",
        f"Existem {len(orphan_ids)} IDs órfãos em `CARD_SYNERGY_TAGS`; eles serão excluídos do novo catálogo até que uma carta real seja definida:",
        "",
    ]
    lines.extend(f"- `{x}`" for x in orphan_ids)
    lines += [
        "",
        "| Combo | Prioridade | Tags requeridas | Exemplo de dois participantes |",
        "|---|---:|---|---|",
    ]
    for c in combo_pair_evidence:
        lines.append(f"| `{c['combo_id']}` | {next(x['priority'] for x in combos if x['combo_id']=='combo.'+c['combo_id'])} | {', '.join('`'+x+'`' for x in c['required_tags'])} | {', '.join('`'+x+'`' for x in c['distinct_participant_example'])} |")
    lines += [
        "",
        "## 7. Líderes e passivas",
        "",
        "Os 10 líderes foram extraídos para `leader-registry-candidate.v1.json`. Líder não é carta do deck e continua em um slot próprio. As quatro passivas de facção são extraídas para `faction-passives-candidate.v1.json`; o +1 da primeira unidade da facção por rodada não desqualifica carta pura.",
        "",
        "## 8. Decisões estruturais importantes",
        "",
        "1. `CARD_IDENTITY_ABILITIES` deixa de existir como lookup paralelo: o ID da carta aponta para exatamente um `effect_id`.",
        "2. `CARD_SYNERGY_TAGS` migra para `combo_tags` no próprio registro da carta.",
        "3. `FACTION_BOOST` fica em registro de passivas globais, separado dos efeitos individuais.",
        "4. `RARITY_EFFECT_BUDGET` deve ser removido do novo runtime: raridade não pode ampliar efeitos silenciosamente.",
        "5. `gloria` é um hook legado funcional em `_resolve_round()`; `sobrevivente` é somente texto declarado e sem handler. Não migrar os dois como equivalentes. Se a nova base mantiver uma regra de sobrevivência, especificá-la como mecânica nova, aprovada e testada, e decidir separadamente se o comportamento histórico de `gloria` será preservado.",
        "6. Efeitos de status compartilham um sistema de marcas parametrizado, mas mantêm parâmetros distintos de status, alvo, limiar, expiração e consequência.",
        "",
        "## 9. Pendências antes de aprovar o registry",
        "",
        "- Rever efeitos compostos/fortes: `star_gravity`, `time_storm`, `v75_blood_price`, `ruin_omen` e `v75_gravity_shear`.",
        "- Rever status e duração de Geada, Podridão, Sangramento e Loucura numa especificação única.",
        "- Aprovar ou rejeitar cada família candidata e os aliases.",
        "- Calibrar EFP, custo e raridade com simulações de partidas; ainda não usar a fórmula v0.1.",
        "- Construir testes do novo resolver; `resolution_handler` neste registry é nome proposto, não função implementada.",
        "- Atribuir cada efeito a cartas novas somente depois da aprovação do manifesto de cartas e da quota de 30% puras.",
        "",
        "## 10. Reprodutibilidade e arquivos",
        "",
        "Gerar novamente:",
        "```bash",
        "python docs/scripts/build-effect-catalog-candidate-v0.1.py",
        "python docs/scripts/test-effect-catalog-candidate-v0.1.py",
        "python docs/scripts/audit-effect-semantic-groups-v0.1.py",
        "python docs/scripts/test-effect-semantic-audit-v0.1.py",
        "python docs/scripts/summarize-effect-catalog-candidate-v0.1.py",
        "```",
        "",
        "Arquivos gerados:",
        "- `data/card_game/effect-registry-candidate.v1.json` — definições de efeito e combos, validação do contrato v1.",
        "- `data/card_game/legacy-effect-aliases-v0.1.json` — mapa de migração por ID, com parâmetros default e supressões.",
        "- `data/card_game/leader-registry-candidate.v1.json` — líderes em slot separado.",
        "- `data/card_game/faction-passives-candidate.v1.json` — passivas por facção.",
        "- `docs/card-game-effect-catalog-decision-v0.1.json` — registro estruturado completo.",
        "- `docs/card-game-effect-semantic-audit-v0.1.md/.json` — branches AST, hooks, riscos e diferenças semânticas revisadas.",
        "",
        "**Limitação:** nenhuma função do motor legado foi alterada. As famílias e handlers são uma proposta de migração e precisam de aprovação e testes comportamentais antes de entrar em produção.",
    ]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "valid": True,
        "candidate_effect_families": len(effects),
        "generic_effect_aliases": len(legacy_aliases),
        "active_identity_aliases": len(identity_aliases),
        "identity_generic_suppressed": len(suppressed_overrides),
        "combos": len(combos),
        "combo_distinct_pair_coverage": len(combo_pair_evidence),
        "leaders": len(leaders),
        "faction_passives": len(faction_passives),
        "orphan_combo_card_ids": orphan_ids,
        "registry_errors": list(validation.errors),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    build()

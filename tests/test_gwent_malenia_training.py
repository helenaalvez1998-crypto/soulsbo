from __future__ import annotations

from copy import deepcopy

from sistemas.cartas import CUSTO_RARIDADE, FAIXA_PODER, get_carta
from sistemas.gwent import (
    CARD_IDENTITY_ABILITIES,
    AI_PLAYER_ID,
    _aplicar_habilidade_identidade,
    aplicar_jogada,
    executar_uma_jogada_ia,
    novo_estado,
    preparar_carta,
)
from sistemas.gwent_treino import (
    AI_THINK_DELAY_SECONDS,
    construir_deck_treino,
    perfil_treino,
)

MALENIA_ID = "chefe_malenia_lamina_miquella"


def _unit(unit_id: str, *, row: str = "melee", bonus: int = 0, podrida: int = 0) -> dict:
    return {
        "id": unit_id,
        "nome": unit_id,
        "categoria": "Unidade",
        "especial": False,
        "poder": 5,
        "bonus": bonus,
        "faccao": "Ordem Áurea",
        "row": row,
        "fileira": row,
        "weather_resist": 0,
        "escudo": 0,
        "sangramento": 0,
        "geada": 0,
        "podrida": podrida,
        "loucura": 0,
    }


def test_malenia_catalog_data_is_canonical_and_internally_consistent():
    card = get_carta(MALENIA_ID)
    assert card is not None
    data = card.para_dict()
    assert data["nome"] == "Malenia, Lâmina de Miquella"
    assert data["categoria"] == "Unidade"
    assert data["faccao"] == "Véu Carmesim"
    assert data["fileira"] == "melee"
    assert data["poder"] == 9
    assert data["raridade"] == "Primordial"
    assert data["custo"] == CUSTO_RARIDADE["Primordial"] == 6
    assert data["poder"] == FAIXA_PODER["Primordial"][1]
    assert data["habilidade"] == "scarlet_bloom"
    assert "Mão de Malenia" in data["descricao"]
    assert "Elphael" in data["descricao"]
    assert "Deusa da Podridão" in data["descricao"]


def test_prepared_malenia_payload_uses_same_name_cost_and_exact_rule_text():
    model = get_carta(MALENIA_ID)
    prepared = preparar_carta(model.para_dict())
    identity = CARD_IDENTITY_ABILITIES[MALENIA_ID]
    assert prepared["nome"] == model.nome
    assert prepared["poder"] == 9
    assert prepared["raridade"] == "Primordial"
    assert prepared["custo"] == 6
    assert prepared["habilidade"] == "scarlet_bloom"
    assert prepared["habilidade_nome"] == "Flor Escarlate"
    assert prepared["habilidade_texto"] == identity["text"]
    assert "até 3 alvos nessa transição" in prepared["habilidade_texto"]
    assert "raridade Primordial: reforça" not in prepared["habilidade_texto"].casefold()
    assert "antes de sua transformação" in prepared["descricao"].casefold()


def test_malenia_rule_text_fits_the_card_panel_without_truncation():
    from PIL import Image, ImageDraw
    from sistemas.arte_cartas import _font, _wrap

    prepared = preparar_carta(get_carta(MALENIA_ID).para_dict())
    draw = ImageDraw.Draw(Image.new("RGB", (800, 600)))
    lines = _wrap(draw, prepared["habilidade_texto"], _font(9), 342)
    assert len(lines) <= 4
    joined = " ".join(lines)
    assert "Ao atingir 2" in joined
    assert "bônus positivo" in joined
    assert "até 3" in joined
    assert "-2" in joined


def test_scarlet_bloom_applies_one_mark_and_threshold_corrosion_only_once():
    player = {"board": []}
    targets = [
        _unit("fresh"),
        _unit("threshold_1", bonus=3, podrida=1),
        _unit("threshold_2", bonus=1, podrida=1),
        _unit("negative_bonus", bonus=-1, podrida=1),
        _unit("already_capped", bonus=3, podrida=2),
        _unit("other_row", row="ranged", bonus=3, podrida=1),
    ]
    other = {"board": targets}
    card = {"id": MALENIA_ID, "nome": "Malenia", "poder": 9, "bonus": 0, "raridade": "Primordial"}

    _aplicar_habilidade_identidade(player, other, card, {"weather": {}}, "melee")

    assert targets[0]["podrida"] == 1
    assert targets[0]["bonus"] == 0
    assert targets[1]["podrida"] == 2
    assert targets[1]["bonus"] == 1  # +3 -> +2 base -> +1 Primordial
    assert targets[2]["podrida"] == 2
    assert targets[2]["bonus"] == -1  # +1 -> 0 base -> -1 Primordial
    assert targets[3]["podrida"] == 2
    assert targets[3]["bonus"] == -1  # bônus não positivo não sofre corrosão-base
    assert targets[4]["podrida"] == 2
    assert targets[4]["bonus"] == 3  # limite não repete consequência
    assert targets[5]["podrida"] == 1  # fileira diferente não é atingida
    assert targets[5]["bonus"] == 3


def test_scarlet_bloom_primordial_bonus_is_limited_to_three_corroded_targets():
    targets = [_unit(f"target_{i}", bonus=4, podrida=1) for i in range(4)]
    card = {"id": MALENIA_ID, "nome": "Malenia", "poder": 9, "bonus": 0, "raridade": "Primordial"}
    _aplicar_habilidade_identidade({"board": []}, {"board": targets}, card, {"weather": {}}, "melee")
    assert [unit["bonus"] for unit in targets] == [2, 2, 2, 3]
    assert all(unit["podrida"] == 2 for unit in targets)


def test_normal_match_resolver_applies_malenia_with_her_identity_once():
    malenia = preparar_carta(get_carta(MALENIA_ID).para_dict())
    fillers = [
        preparar_carta(get_carta("chefe_cervo_sombrio").para_dict()),
        preparar_carta(get_carta("chefe_cacador_sem_rosto").para_dict()),
        preparar_carta(get_carta("chefe_aparicao_veio").para_dict()),
        preparar_carta(get_carta("arma_lamina_peregrino").para_dict()),
        preparar_carta(get_carta("arma_arco_peregrino").para_dict()),
        preparar_carta(get_carta("gwent_v75_veu_acolito_sangue").para_dict()),
        preparar_carta(get_carta("gwent_v75_veu_devota_hemorragia").para_dict()),
        preparar_carta(get_carta("gwent_v75_veu_cacador_sangue").para_dict()),
        preparar_carta(get_carta("gwent_especial_medico").para_dict()),
        preparar_carta(get_carta("gwent_especial_batedor").para_dict()),
        preparar_carta(get_carta("elden_especial_podrida").para_dict()),
    ]
    ai_deck = construir_deck_treino("facil")
    state = novo_estado(99, 100, AI_PLAYER_ID, {"100": [malenia, *fillers], str(AI_PLAYER_ID): ai_deck})
    state["phase"] = "battle"
    state["turn"] = "100"
    state["players"]["100"]["mulligan_done"] = True
    state["players"][str(AI_PLAYER_ID)]["mulligan_done"] = True
    state["players"][str(AI_PLAYER_ID)]["board"] = [
        _unit("threshold", bonus=2, podrida=1),
        _unit("capped", bonus=3, podrida=2),
    ]

    result = aplicar_jogada(state, 100, MALENIA_ID, "play", "melee")
    assert "error" not in result
    after = result["state"]
    enemies = {unit["id"]: unit for unit in after["players"][str(AI_PLAYER_ID)]["board"]}
    assert enemies["threshold"]["podrida"] == 2
    assert enemies["threshold"]["bonus"] == 0  # +2 -> +1 base -> 0 Primordial; sem amplificador genérico extra
    assert enemies["capped"]["podrida"] == 2
    assert enemies["capped"]["bonus"] == 3
    played = next(unit for unit in after["players"]["100"]["board"] if unit["id"] == MALENIA_ID)
    assert played["poder"] == 9
    assert played["habilidade"] == "scarlet_bloom"


def test_three_training_decks_have_distinct_valid_builds_and_hard_deck_includes_malenia():
    decks = {key: construir_deck_treino(key) for key in ("facil", "normal", "dificil")}
    assert len({tuple(card["id"] for card in deck) for deck in decks.values()}) == 3
    for key, deck in decks.items():
        profile = perfil_treino(key)
        assert len(deck) == 12
        assert len([card for card in deck if not card["especial"]]) == 9
        assert len([card for card in deck if card["especial"]]) == 3
        assert {card["faccao"] for card in deck if not card["especial"]} == {profile["faction"]}
        assert profile["relic_id"] in {
            "reliquia_grande_runa_godrick", "reliquia_runa_nao_nascidos", "reliquia_runa_morte"
        }
        assert get_carta(profile["relic_id"]) is not None
    hard = {card["id"]: card for card in decks["dificil"]}
    assert MALENIA_ID in hard
    assert hard[MALENIA_ID]["poder"] == 9
    assert hard[MALENIA_ID]["raridade"] == "Primordial"
    assert hard[MALENIA_ID]["custo"] == 6
    assert hard[MALENIA_ID]["habilidade"] == "scarlet_bloom"


def test_ai_uses_one_normal_engine_action_per_decision_and_returns_turn_to_human():
    deck = construir_deck_treino("dificil")
    state = novo_estado(101, 100, AI_PLAYER_ID, {"100": deepcopy(deck), str(AI_PLAYER_ID): deepcopy(deck)})
    state["phase"] = "battle"
    state["turn"] = str(AI_PLAYER_ID)
    for player in state["players"].values():
        player["mulligan_done"] = True
    ai_before = state["players"][str(AI_PLAYER_ID)]
    hand_before = len(ai_before["hand"])
    board_before = len(ai_before["board"])

    after = executar_uma_jogada_ia(state, AI_PLAYER_ID, "dificil")

    ai_after = after["players"][str(AI_PLAYER_ID)]
    assert after["turn"] == "100"
    assert len(ai_after["hand"]) == hand_before - 1
    assert len(ai_after["board"]) == board_before + 1
    assert after["last_event"]


def test_ai_training_delay_is_between_three_and_five_seconds():
    assert AI_THINK_DELAY_SECONDS == (3.0, 5.0)


def test_each_nara_profile_equips_a_relic_that_resolves_through_the_normal_engine():
    relics = {
        "facil": ("reliquia_grande_runa_godrick", "Grande Runa de Godrick"),
        "normal": ("reliquia_runa_nao_nascidos", "Grande Runa dos Não Nascidos"),
        "dificil": ("reliquia_runa_morte", "Runa da Morte"),
    }
    for difficulty, (relic_id, relic_name) in relics.items():
        profile = perfil_treino(difficulty)
        assert profile["relic_id"] == relic_id
        assert profile["relic_name"] == relic_name
        configs = {
            "100": {"faction": "Ordem Áurea", "leader_id": "bastiao_ancestral"},
            str(AI_PLAYER_ID): {
                "faction": profile["faction"],
                "leader_id": profile["leader_id"],
                "relic_id": relic_id,
                "relic_owned": True,
            },
        }
        deck = construir_deck_treino(difficulty)
        state = novo_estado(103, 100, AI_PLAYER_ID, {"100": deepcopy(deck), str(AI_PLAYER_ID): deepcopy(deck)}, configs)
        state["phase"] = "battle"
        state["turn"] = str(AI_PLAYER_ID)
        ai = state["players"][str(AI_PLAYER_ID)]
        human = state["players"]["100"]
        for player in state["players"].values():
            player["mulligan_done"] = True
        ally = _unit(f"ally_{difficulty}", bonus=0)
        enemy = _unit(f"enemy_{difficulty}", bonus=2)
        if difficulty == "normal":
            ally["geada"] = 1
        ai["board"] = [ally]
        human["board"] = [enemy]

        result = aplicar_jogada(state, AI_PLAYER_ID, action="relic")
        assert "error" not in result, result.get("error")
        after = result["state"]
        ai_after = after["players"][str(AI_PLAYER_ID)]
        assert ai_after["relic_used"] is True
        assert ai_after["equipped_relic_id"] == relic_id
        if difficulty == "facil":
            assert ai_after["board"][0]["bonus"] == 1
        elif difficulty == "normal":
            assert ai_after["board"][0]["geada"] == 0
            assert ai_after["board"][0]["bonus"] == 1
        else:
            assert after["players"]["100"]["board"][0]["bonus"] == 0

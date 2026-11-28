from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from sistemas.cartas import (
    CARTAS_EXPANSAO_V77,
    CARTAS_PACOTE,
    CARTAS_POR_ID,
    CUSTO_RARIDADE,
    HABILIDADES,
)
from sistemas.catalogo_publico import montar_catalogo_publico_cartas
from sistemas.gwent import (
    FACTION_ARCHETYPES,
    HABILIDADES_ESPECIAIS_IMPLEMENTADAS,
    LEADERS,
    SPECIAL_EFFECT_ALIASES,
    aplicar_jogada,
    novo_estado,
    opcoes_de_alvo,
    preparar_carta,
)

FACCOES = {"Ordem Áurea", "Véu Carmesim", "Lua Negra", "Os Esquecidos"}


def _unit(uid: str, row: str = "melee", **extra) -> dict:
    unit = {
        "id": uid,
        "nome": uid,
        "categoria": "Unidade",
        "especial": False,
        "poder": 3,
        "bonus": 0,
        "faccao": "Os Esquecidos",
        "row": row,
        "fileira": row,
        "escudo": 0,
        "weather_resist": 0,
        "sangramento": 0,
        "geada": 0,
        "podrida": 0,
        "loucura": 0,
    }
    unit.update(extra)
    return unit


def _special_state(skill: str) -> dict:
    filler = _unit("filler")
    state = novo_estado(
        77001, 1001, 2002,
        {"1001": [dict(filler, id=f"p{i}") for i in range(12)],
         "2002": [dict(filler, id=f"e{i}") for i in range(12)]},
        {"1001": {"faction": "Os Esquecidos"}, "2002": {"faction": "Ordem Áurea"}},
    )
    state["phase"] = "battle"
    state["turn"] = "1001"
    for player in state["players"].values():
        player["mulligan_done"] = True
    card = {
        "id": "probe_special",
        "nome": "Especial de Teste",
        "categoria": "Especial",
        "especial": True,
        "poder": 0,
        "bonus": 0,
        "faccao": "Os Esquecidos",
        "raridade": "Comum",
        "custo": 1,
        "habilidade": skill,
        "row": "melee",
        "fileira": "melee",
    }
    state["players"]["1001"]["hand"] = [card]
    state["players"]["1001"]["board"] = [
        _unit("ally_melee", "melee", geada=1),
        _unit("ally_melee_2", "melee"),
        _unit("ally_ranged", "ranged"),
    ]
    state["players"]["1001"]["discard"] = [_unit("discard_unit")]
    state["players"]["1001"]["draw_pile"] = [_unit("draw_unit")]
    state["players"]["2002"]["board"] = [
        _unit("enemy_melee", "melee", faccao="Ordem Áurea", bonus=2),
        _unit("enemy_melee_2", "melee", faccao="Ordem Áurea", bonus=1),
        _unit("enemy_ranged", "ranged", faccao="Ordem Áurea", bonus=1),
    ]
    state["weather"] = {"melee": 1, "ranged": 1, "siege": 0}
    return state


def _apply_effect(skill: str) -> dict:
    state = _special_state(skill)
    target = {
        "gwent_egide": "ally_melee",
        "gwent_medico": "discard_unit",
        "gwent_passo": "ally_ranged",
        "gwent_execucao": "enemy_melee",
    }.get(SPECIAL_EFFECT_ALIASES.get(skill, skill))
    row = "melee"
    result = aplicar_jogada(state, 1001, "probe_special", "play", row, target_id=target)
    assert "error" not in result, (skill, result.get("error"))
    clean = result["state"]
    # O nome do handler canônico aparece em alguns textos históricos de evento;
    # a equivalência compara os efeitos de jogo, não a redação do log.
    clean.pop("last_event", None)
    clean.pop("event_log", None)
    return clean


def test_all_four_factions_have_equal_collection_size_and_three_leaders():
    units = Counter(c.faccao for c in CARTAS_PACOTE if c.categoria.casefold() != "especial")
    specials = Counter(c.faccao for c in CARTAS_PACOTE if c.categoria.casefold() == "especial")
    leaders = Counter(x["faction"] for x in LEADERS.values())
    assert units == {f: 30 for f in FACCOES}
    assert specials == {f: 11 for f in FACCOES}
    assert leaders == {f: 3 for f in FACCOES}
    assert all(FACTION_ARCHETYPES[f] for f in FACCOES)


def test_forgotten_expansion_adds_ten_special_cards_and_all_v77_cards_are_packaged():
    forgotten = [c for c in CARTAS_EXPANSAO_V77 if c.faccao == "Os Esquecidos"]
    assert len(forgotten) == 10
    assert len(CARTAS_EXPANSAO_V77) == 17
    package_ids = {c.id for c in CARTAS_PACOTE}
    assert {c.id for c in CARTAS_EXPANSAO_V77} <= package_ids


def test_every_v77_special_uses_a_catalogued_and_executable_canonical_handler():
    for model in CARTAS_EXPANSAO_V77:
        declared = str(model.habilidade)
        assert declared in HABILIDADES, (model.id, declared)
        assert declared in SPECIAL_EFFECT_ALIASES, (model.id, declared)
        effective = SPECIAL_EFFECT_ALIASES[declared]
        assert effective in HABILIDADES_ESPECIAIS_IMPLEMENTADAS, (model.id, effective)
        prepared = preparar_carta(model.para_dict())
        assert prepared["habilidade_id_declarada"] == declared
        assert prepared["habilidade_id_efetiva"] == effective
        assert prepared["row_label"] == "Carta especial"
        assert prepared["custo"] == CUSTO_RARIDADE[model.raridade]
        assert prepared["habilidade_texto"].strip()


def test_site_public_payload_publishes_v77_effects_names_and_special_row():
    payload = montar_catalogo_publico_cartas()
    assert payload["total_expansao_v77"] == 17
    by_id = {card["card_id"]: card for card in payload["cartas"]}
    for model in CARTAS_EXPANSAO_V77:
        item = by_id[model.id]
        assert item["nome"] == model.nome
        assert item["faccao"] == model.faccao
        assert item["fileira"] == "Carta especial"
        assert item["fileira_id"] == "special"
        assert item["habilidade_id"] == SPECIAL_EFFECT_ALIASES[model.habilidade]
        assert item["habilidade_id_declarada"] == model.habilidade
        assert item["habilidade_texto"]
        assert item["expansao_v77"] is True


def test_all_static_card_names_are_unique_compact_and_old_ids_remain_stable():
    names = [card.nome.strip().casefold() for card in CARTAS_POR_ID.values()]
    assert all(names)
    assert max(len(card.nome) for card in CARTAS_POR_ID.values()) <= 27
    assert len(names) == len(set(names))
    # IDs da expansão anterior são parte de snapshots e decks já salvos.
    for stable_id in (
        "gwent_v76_esq_peregrino_cinza",
        "gwent_v76_esq_cantor_hino",
        "gwent_v76_esq_guardiao_vitrais",
        "luterano_papa",
        "luterano_apostolo",
    ):
        assert stable_id in CARTAS_POR_ID


@pytest.mark.parametrize("alias", sorted(SPECIAL_EFFECT_ALIASES))
def test_v77_alias_executes_exactly_the_same_gameplay_as_its_canonical_handler(alias: str):
    canonical = SPECIAL_EFFECT_ALIASES[alias]
    alias_state = _apply_effect(alias)
    canonical_state = _apply_effect(canonical)
    assert alias_state["weather"] == canonical_state["weather"]
    for uid in ("1001", "2002"):
        alias_player = alias_state["players"][uid]
        canonical_player = canonical_state["players"][uid]
        assert alias_player["board"] == canonical_player["board"]
        assert [c["id"] for c in alias_player["hand"]] == [c["id"] for c in canonical_player["hand"]]
        assert [c["id"] for c in alias_player["discard"]] == [c["id"] for c in canonical_player["discard"]]
        assert [c["id"] for c in alias_player["draw_pile"]] == [c["id"] for c in canonical_player["draw_pile"]]


def test_alias_target_picker_uses_effective_handler_for_forgotten_specials():
    state = _special_state("gwent_v77_esq_medico")
    options = opcoes_de_alvo(state, 1001)
    assert "probe_special" in options
    assert [item["id"] for item in options["probe_special"]["opcoes"]] == ["discard_unit"]

    state = _special_state("gwent_v77_esq_egide")
    options = opcoes_de_alvo(state, 1001)
    assert "probe_special" in options
    assert {item["id"] for item in options["probe_special"]["opcoes"]} == {
        "ally_melee", "ally_melee_2", "ally_ranged"
    }


def test_global_name_review_is_applied_to_public_site_and_painting_archetypes():
    source = Path("sistemas/pintura_procedural.py").read_text(encoding="utf-8")
    assert "servo dos mortos" in source
    app = Path("site/app.js").read_text(encoding="utf-8")
    assert "fetch('/api/gwent/catalogo-cartas'" in app


def test_v77_specials_have_art_direction_specific_to_their_names_and_lore():
    from sistemas.pintura_procedural import analisar_direcao

    expected_subjects = {
        "gwent_v77_ord_egide": "protective blessing",
        "gwent_v77_ord_hino": "sacred choir",
        "gwent_v77_ord_silencio": "weather-cleansing blessing",
        "gwent_v77_veu_sangramento": "blood rite",
        "gwent_v77_veu_podrida": "scarlet rot mist",
        "gwent_v77_veu_loucura": "frenzied blood ritual",
        "gwent_v77_veu_execucao": "execution",
        "gwent_v77_esq_muralha": "fortification event",
        "gwent_v77_esq_chifre": "sacred choir",
        "gwent_v77_esq_medico": "last mercy and recovery",
        "gwent_v77_esq_egide": "protective blessing",
        "gwent_v77_esq_passo": "faithful procession",
        "gwent_v77_esq_chama": "frost-cleansing flame",
        "gwent_v77_esq_vinculo": "ancestral vow",
        "gwent_v77_esq_batedor": "pilgrim bell",
        "gwent_v77_esq_purificar": "weather-cleansing blessing",
        "gwent_v77_esq_clima": "sepulchral mist",
    }
    for card_id, subject in expected_subjects.items():
        model = CARTAS_POR_ID[card_id]
        direction = analisar_direcao(model.para_dict())
        assert direction.subject == subject, (card_id, direction.subject)
        assert direction.scene
        assert direction.action
        assert direction.material

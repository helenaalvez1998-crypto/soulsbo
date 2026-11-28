from __future__ import annotations

from collections import Counter
from pathlib import Path

from sistemas.cartas import CARTAS_PACOTE, CARTAS_POR_ID, PATENTES, carta_jogo, carta_patente, get_carta
from sistemas.decks_base import DECKS_BASE
from sistemas.gwent import (
    LEADERS,
    aplicar_jogada,
    contar_faccoes_deck,
    faction_for_card,
    novo_estado,
    preparar_carta,
    _resolve_round,
)


def _card(card_id: str) -> dict:
    model = get_carta(card_id)
    assert model is not None, card_id
    return preparar_carta(model.para_dict())


def _battle(leader_id: str) -> dict:
    forgotten = [
        _card(card.id)
        for card in CARTAS_PACOTE
        if card.faccao == "Os Esquecidos" and card.categoria != "Especial"
    ][:12]
    order = [
        _card(card.id)
        for card in CARTAS_PACOTE
        if card.faccao == "Ordem Áurea" and card.categoria != "Especial"
    ][:12]
    state = novo_estado(
        2026112801,
        1001,
        2002,
        {"1001": forgotten, "2002": order},
        {
            "1001": {"faction": "Os Esquecidos", "leader_id": leader_id},
            "2002": {"faction": "Ordem Áurea"},
        },
    )
    state["phase"] = "battle"
    state["turn"] = "1001"
    for player in state["players"].values():
        player["mulligan_done"] = True
    return state


def _with_status(card_id: str, row: str, **statuses) -> dict:
    card = _card(card_id)
    card.update({
        "row": row,
        "fileira": row,
        "bonus": 0,
        "escudo": 0,
        "sangramento": 0,
        "geada": 0,
        "podrida": 0,
        "loucura": 0,
    })
    card.update(statuses)
    return card


def test_all_four_factions_have_exactly_30_playable_units():
    counts = Counter(
        card.faccao
        for card in CARTAS_PACOTE
        if card.categoria.casefold() != "especial"
    )
    assert counts == {
        "Ordem Áurea": 30,
        "Véu Carmesim": 30,
        "Lua Negra": 30,
        "Os Esquecidos": 30,
    }


def test_all_luterano_ids_resolve_to_os_esquecidos_in_catalog_and_old_snapshots():
    old_wrong_assignments = {
        "luterano_apostolo", "luterano_profeta", "luterano_pastor",
        "luterano_vigia", "luterano_mistico", "luterano_anjo2",
    }
    all_luterano_ids = [card.id for card in CARTAS_PACOTE if card.id.startswith("luterano_")]
    assert len(all_luterano_ids) == 14
    for card_id in all_luterano_ids:
        model = get_carta(card_id)
        assert model is not None and model.faccao == "Os Esquecidos"
    for card_id in old_wrong_assignments:
        model = get_carta(card_id)
        assert model is not None and model.faccao == "Os Esquecidos"
        legacy_snapshot = {
            **model.para_dict(),
            "faccao": "Ordem Áurea",
            "nome": "Nome antigo armazenado",
            "descricao": "Lore antiga armazenada",
        }
        prepared = preparar_carta(legacy_snapshot)
        assert prepared["faccao"] == "Os Esquecidos"
        assert prepared["nome"] == model.nome
        assert prepared["descricao"] == model.descricao
        assert faction_for_card(legacy_snapshot) == "Os Esquecidos"


def test_card_titles_are_short_unique_and_all_dynamic_titles_follow_the_same_limit():
    names = [card.nome.casefold() for card in CARTAS_POR_ID.values()]
    assert all(card.nome.strip() and len(card.nome) <= 27 for card in CARTAS_POR_ID.values())
    assert len(names) == len(set(names))


def test_dynamic_game_and_patent_rewards_also_use_compact_titles():
    game_factions = set()
    generated_names = set()
    catalog_names = {card.nome.casefold() for card in CARTAS_POR_ID.values()}
    for index in range(100):
        for milestone in ("zerado", "platina"):
            card = carta_jogo(f"Jogo de Teste {index}", milestone)
            assert card.nome and len(card.nome) <= 27
            assert card.nome.casefold() not in catalog_names
            game_factions.add(card.faccao)
            if card.faccao not in generated_names:
                generated_names.add(card.nome.casefold())
    assert game_factions == {"Ordem Áurea", "Véu Carmesim", "Lua Negra", "Os Esquecidos"}
    patent_factions = set()
    for index, (level, title) in enumerate(PATENTES):
        card = carta_patente(index, level, title)
        assert card.nome == title
        assert len(card.nome) <= 27
        patent_factions.add(card.faccao)
    assert patent_factions == {"Ordem Áurea", "Véu Carmesim", "Lua Negra", "Os Esquecidos"}


def test_forgotten_leader_roster_matches_other_factions_and_is_published_to_site():
    by_faction = Counter(leader["faction"] for leader in LEADERS.values())
    assert by_faction == {
        "Ordem Áurea": 3,
        "Véu Carmesim": 3,
        "Lua Negra": 3,
        "Os Esquecidos": 3,
    }
    app = Path("site/app.js").read_text(encoding="utf-8")
    for leader_id in ("lider_papa_esquecido", "lider_abadessa_ruinas", "lider_martir_vigilia"):
        assert leader_id in app
    assert "maior poder efetivo" in LEADERS["lider_abadessa_ruinas"]["description"]
    assert "Sangramento, Geada, Podridão e Loucura" in app
    assert '"lider_abadessa_ruinas": "abadessa"' in Path("bot.py").read_text(encoding="utf-8")
    assert '"lider_martir_vigilia": "martir"' in Path("bot.py").read_text(encoding="utf-8")
    assert (Path("site/assets/leaders") / "abadessa.webp").is_file()
    assert (Path("site/assets/leaders") / "martir.webp").is_file()


def test_all_starter_decks_are_faction_consistent_and_use_the_same_structure():
    assert set(DECKS_BASE) == {"Ordem Áurea", "Véu Carmesim", "Lua Negra", "Os Esquecidos"}
    for faction, deck in DECKS_BASE.items():
        assert len(deck) == 10
        assert len(set(deck)) == 10
        for card_id in deck:
            model = get_carta(card_id)
            assert model is not None, card_id
            assert model.faccao == faction, (faction, card_id, model.faccao)
        assert sum(get_carta(card_id).categoria.casefold() != "especial" for card_id in deck) == 9
    assert "gwent_especial_requiem" in DECKS_BASE["Os Esquecidos"]


def test_abbess_leader_purifies_only_two_forgotten_allies_in_selected_row():
    state = _battle("lider_abadessa_ruinas")
    player = state["players"]["1001"]
    first = _with_status("luterano_pastor", "melee", sangramento=1, bonus=0)
    second = _with_status("luterano_mistico", "melee", geada=2, podrida=1, bonus=0)
    untouched = _with_status("luterano_diacon", "melee", loucura=1, bonus=0)
    foreign = _with_status("chefe_cervo_sombrio", "melee", sangramento=1, bonus=0)
    other_row = _with_status("luterano_sacerdote", "ranged", geada=1, bonus=0)
    player["board"] = [first, second, untouched, foreign, other_row]

    result = aplicar_jogada(state, 1001, action="leader", row="melee")
    assert "error" not in result, result.get("error")
    board = result["state"]["players"]["1001"]["board"]
    by_id = {unit["id"]: unit for unit in board}
    for unit in (by_id[first["id"]], by_id[second["id"]]):
        assert unit["sangramento"] == unit["geada"] == unit["podrida"] == unit["loucura"] == 0
        assert unit["bonus"] == 1
    assert by_id[untouched["id"]]["loucura"] == 1
    assert by_id[foreign["id"]]["sangramento"] == 1
    assert by_id[other_row["id"]]["geada"] == 1
    assert result["state"]["players"]["1001"]["leader_used"] is True


def test_martyr_leader_revives_strongest_eligible_forgotten_unit_with_clean_status():
    state = _battle("lider_martir_vigilia")
    player = state["players"]["1001"]
    strongest = _with_status(
        "luterano_missionario", "ranged", bonus=2, escudo=1,
        sangramento=1, geada=1, podrida=1, loucura=1,
    )
    smaller = _with_status("gwent_v76_esq_peregrino_cinza", "ranged")
    outsider = _with_status("chefe_cervo_sombrio", "melee")
    too_strong = _with_status("luterano_papa", "siege")
    player["discard"] = [strongest, smaller, outsider, too_strong]

    result = aplicar_jogada(state, 1001, action="leader", row="siege")
    assert "error" not in result, result.get("error")
    updated = result["state"]["players"]["1001"]
    revived = next(unit for unit in updated["board"] if unit["id"] == "luterano_missionario")
    assert revived["row"] == "siege" and revived["fileira"] == "siege"
    assert revived["bonus"] == 3
    assert not revived.get("escudo")
    assert all(revived[key] == 0 for key in ("sangramento", "geada", "podrida", "loucura"))
    assert "luterano_missionario" not in {unit["id"] for unit in updated["discard"]}
    assert {unit["id"] for unit in updated["discard"]} == {
        smaller["id"], outsider["id"], too_strong["id"]
    }
    assert updated["leader_used"] is True


def test_faction_counts_ignore_specials_so_the_new_requiem_does_not_distort_deck_faction():
    cards = [_card("luterano_cruzado"), _card("luterano_bispo"), _card("gwent_especial_requiem")]
    counts = contar_faccoes_deck(cards)
    assert counts["Os Esquecidos"] == 2
    assert sum(counts.values()) == 2


def test_new_forgotten_survivor_card_uses_the_existing_round_end_hook():
    state = _battle("lider_papa_esquecido")
    player = state["players"]["1001"]
    opponent = state["players"]["2002"]
    survivor = _card("gwent_v76_esq_cantor_hino")
    assert survivor["habilidade"] == "sobrevivente"
    player["board"] = [survivor]
    opponent["board"] = []

    _resolve_round(state)

    assert any(unit["id"] == survivor["id"] for unit in player["board"])
    assert not any(unit["id"] == survivor["id"] for unit in player["discard"])

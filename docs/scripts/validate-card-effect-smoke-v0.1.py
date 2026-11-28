#!/usr/bin/env python3
"""Runtime smoke audit of card effects against the current Gwent engine.

This is a diagnostic harness, not a balance simulation. It builds synthetic,
controlled match states and invokes the real `aplicar_jogada`, `_remover_unidade`
and `_resolve_round` functions. It does not modify production data or files.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sistemas import cartas, gwent

OUT = ROOT / "docs" / "card-game-effect-runtime-smoke-v0.1.json"


def unit(
    card_id: str,
    *,
    skill: str = "",
    power: int = 3,
    row: str = "melee",
    faction: str = "Ordem Áurea",
    bonus: int = 0,
    special: bool = False,
    rarity: str = "Comum",
    **extra: Any,
) -> dict[str, Any]:
    result = {
        "id": card_id,
        "nome": card_id,
        "categoria": "Especial" if special else "Unidade",
        "especial": special,
        "poder": power,
        "bonus": bonus,
        "faccao": faction,
        "habilidade": skill,
        "raridade": rarity,
        "row": row,
        "fileira": row,
        "weather_resist": 0,
        "escudo": 0,
        "sangramento": 0,
        "geada": 0,
        "podrida": 0,
        "loucura": 0,
    }
    result.update(extra)
    return result


def fixture(card: dict[str, Any], row: str) -> dict[str, Any]:
    allies = [
        unit("ally_melee_a", row="melee", faction="Ordem Áurea", power=3, bonus=0, geada=1),
        unit("ally_melee_b", row="melee", faction="Ordem Áurea", power=2, bonus=0),
        unit("ally_ranged", row="ranged", faction="Lua Negra", power=3, bonus=0),
        unit("ally_siege", row="siege", faction="Véu Carmesim", power=3, bonus=0, sangramento=1),
    ]
    enemies = [
        unit("enemy_melee_a", row="melee", faction="Véu Carmesim", power=4, bonus=2),
        unit("enemy_melee_b", row="melee", faction="Lua Negra", power=3, bonus=1),
        unit("enemy_ranged", row="ranged", faction="Lua Negra", power=4, bonus=2, geada=1),
        unit("enemy_siege", row="siege", faction="Véu Carmesim", power=4, bonus=2),
    ]
    own_draw = [unit("draw_unit", power=2)]
    own_discard = [
        unit("discard_unit_4", power=4),
        unit("discard_unit_3", power=3),
        unit("discard_special", special=True, skill="gwent_clima", power=0),
    ]
    other_draw = [unit("enemy_draw", power=2)]
    filler = [unit(f"filler_{i}") for i in range(12)]
    state = gwent.novo_estado(
        90001,
        1,
        2,
        {"1": [card, *filler], "2": [*filler]},
        {"1": {"faction": "Lua Negra"}, "2": {"faction": "Ordem Áurea"}},
    )
    state["phase"] = "battle"
    state["round"] = 1
    state["turn"] = "1"
    state["weather"] = {"melee": 0, "ranged": 0, "siege": 0}
    state["rounds"] = [{"round": 2, "winner_id": "2"}]
    p1, p2 = state["players"]["1"], state["players"]["2"]
    for player in (p1, p2):
        player["mulligan_done"] = True
        player["passed"] = False
    p1["faction"] = "Lua Negra"  # avoid the Order faction entry bonus in unit tests
    p2["faction"] = "Ordem Áurea"
    # Keep one reserve card so the engine does not auto-pass immediately after the test play.
    p1["hand"] = [card, unit("smoke_reserve_card", power=1)]
    p1["draw_pile"] = own_draw
    p1["discard"] = own_discard
    p1["board"] = allies
    p1["last_row"] = "ranged"
    p2["hand"] = [unit("enemy_hand")]
    p2["draw_pile"] = other_draw
    p2["discard"] = []
    p2["board"] = enemies
    p2["last_row"] = row
    p1["synergy_used"] = {}
    p1["faction_boost_used"] = True
    return state


def side_swing(player: dict[str, Any], other: dict[str, Any], weather: dict[str, int]) -> int:
    return gwent.pontuacao(player, weather) - gwent.pontuacao(other, weather)


def run_skill(skill_id: str) -> dict[str, Any]:
    is_special = skill_id.startswith(("gwent_", "reliquia_"))
    row = "ranged" if skill_id == "precisao" else "melee"
    card = unit(
        f"smoke_{skill_id}", skill=skill_id, special=is_special,
        faction="Véu Carmesim", row=row, power=4,
    )
    state = fixture(card, row)
    state["round"] = 3 if skill_id in {"ultimo_folego", "paradoxo_eterno"} else 1
    p1, p2 = state["players"]["1"], state["players"]["2"]

    # Tailor only the conditions needed to exercise the selected condition-gated skill.
    if skill_id in {"retaliacao", "contragolpe", "instinto", "fome_abismo"}:
        for enemy in p2["board"]:
            enemy["bonus"] = 3
        for ally in p1["board"]:
            ally["bonus"] = 0
    elif skill_id == "impeto":
        for ally in p1["board"]:
            ally["bonus"] = 5
        for enemy in p2["board"]:
            enemy["bonus"] = 0
    elif skill_id == "sangue_frio":
        for ally in p1["board"]:
            ally["bonus"] = 0
            ally["geada"] = 0
            ally["row"] = "melee"
        for enemy, power in zip(p2["board"], (3, 3, 3, 2)):
            enemy["bonus"] = 0
            enemy["geada"] = 0
            enemy["row"] = "melee"
            enemy["poder"] = power
        state["weather"] = {"melee": 0, "ranged": 0, "siege": 0}
    elif skill_id == "encadeamento":
        p1["last_row"] = row
    elif skill_id == "paradoxo_eterno":
        state["rounds"] = [{"round": 2, "winner_id": "2"}]
    elif skill_id in {"olho_tempestade", "resistencia_climatica"}:
        state["weather"][row] = 1
    elif skill_id == "gwent_purificar":
        state["weather"] = {"melee": 1, "ranged": 1, "siege": 1}
    elif skill_id == "cacador_solitario":
        p1["board"] = [u for u in p1["board"] if u["row"] != row]
    elif skill_id == "gwent_clima":
        state["weather"] = {"melee": 0, "ranged": 0, "siege": 0}
    elif skill_id == "gwent_nevoa":
        pass
    elif skill_id == "gwent_chuva":
        row = "siege"
    elif skill_id == "gwent_passo":
        row = "melee"
    elif skill_id == "reliquia_noite_chama":
        pass

    # Skills requiring a selected sub-mode/target.
    target_id = "noite" if skill_id == "reliquia_noite_chama" else None
    before_swing = side_swing(p1, p2, state["weather"])
    base_card_power = max(1, int(card["poder"]) - max(0, int(state["weather"].get(row, 0)) - int(card.get("weather_resist", 0)))) if not is_special else 0
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row=row, target_id=target_id)
    if "error" in result:
        return {"id": skill_id, "status": "error", "error": result["error"]}
    after = result["state"]
    ap1, ap2 = after["players"]["1"], after["players"]["2"]
    played = next((u for u in ap1["board"] if u["id"] == card["id"]), None)
    if is_special:
        played = next((u for u in ap1["discard"] if u["id"] == card["id"]), None)
    after_swing = side_swing(ap1, ap2, after.get("weather", {}))
    lifecycle_only = skill_id in {"vinganca", "espolios", "sobrevivente"}
    return {
        "id": skill_id,
        "status": ("lifecycle_hook_tested_separately" if played is not None and lifecycle_only else
                   "play_action_completed_not_full_branch_coverage" if played is not None else "card_location_unexpected"),
        "category": "special" if is_special else "unit",
        "played_card_found": played is not None,
        "immediate_field_swing_delta_excluding_base_power": (
            after_swing - before_swing - base_card_power
        ),
        "own_board_count_delta": len(ap1["board"]) - len(p1["board"]),
        "enemy_board_count_delta": len(ap2["board"]) - len(p2["board"]),
        "own_hand_delta": len(ap1["hand"]) - len(p1["hand"]),
        "own_discard_delta": len(ap1["discard"]) - len(p1["discard"]),
        "last_event": after.get("last_event", "")[:350],
    }


def run_identity(card_id: str) -> dict[str, Any]:
    model = cartas.get_carta(card_id)
    payload = model.para_dict()
    payload["raridade"] = "Comum"  # isolate identity from current rarity amplification
    card = payload
    row = str(card.get("fileira") or model.fileira or "melee")
    state = fixture(card, row)
    p1 = state["players"]["1"]
    p1["hand"].append(unit(f"identity_reserve_{card_id}"))  # prevent auto-pass after the test card is played
    if gwent.CARD_IDENTITY_ABILITIES[card_id]["effect"] in {"ancient_mist", "wandering_ember"}:
        state["weather"] = {"melee": 1, "ranged": 1, "siege": 0}
    before_swing = side_swing(p1, state["players"]["2"], state["weather"])
    base_card_power = max(1, int(card.get("poder", 1)) - max(0, int(state["weather"].get(row, 0)) - int(card.get("weather_resist", 0))))
    p1["faction"] = "Véu Carmesim" if card.get("faccao") != "Véu Carmesim" else "Ordem Áurea"
    result = gwent.aplicar_jogada(state, 1, card_id=card_id, action="play", row=row)
    if "error" in result:
        return {"card_id": card_id, "status": "error", "error": result["error"]}
    after_state = result["state"]
    after_p1, after_p2 = after_state["players"]["1"], after_state["players"]["2"]
    last_event = after_state.get("last_event", "")
    after_swing = side_swing(after_p1, after_p2, after_state.get("weather", {}))
    return {
        "card_id": card_id,
        "effect_id": gwent.CARD_IDENTITY_ABILITIES[card_id]["effect"],
        "status": "resolved" if "Habilidade ativada:" in last_event else "identity_event_missing",
        "immediate_field_swing_delta_excluding_base_power": after_swing - before_swing - base_card_power,
        "card_bonus_after": next((int(u.get("bonus", 0)) for u in after_p1["board"] if u.get("id") == card_id), None),
        "last_event": last_event[:350],
    }


def run_lifecycle_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    # Vingança is a death-trigger hook, so trigger it through the motor's single removal function.
    revenge = unit("lifecycle_revenge", skill="vinganca", row="melee")
    state = fixture(revenge, "melee")
    p1 = state["players"]["1"]
    result = gwent.aplicar_jogada(state, 1, card_id=revenge["id"], action="play", row="melee")
    if "error" in result:
        cases.append({"id": "vinganca", "status": "error", "error": result["error"]})
    else:
        state2 = result["state"]
        p = state2["players"]["1"]
        victim = next(u for u in p["board"] if u["id"] == revenge["id"])
        allies_before = [int(u.get("bonus", 0)) for u in p["board"] if u["row"] == "melee" and u is not victim]
        event = gwent._remover_unidade(p, victim, "remocao")
        allies_after = [int(u.get("bonus", 0)) for u in p["board"] if u["row"] == "melee"]
        cases.append({"id": "vinganca", "status": "resolved" if "Vingança" in event else "hook_not_triggered", "event": event, "ally_bonus_before": allies_before, "ally_bonus_after": allies_after})

    # Espólios is a round-end hook; Gloria is a hidden round-end hook; Sobrevivente is tested as declared.
    for skill_id in ("espolios", "gloria", "sobrevivente"):
        card = unit(f"lifecycle_{skill_id}", skill=skill_id, row="melee", power=8)
        state = fixture(card, "melee")
        p1, p2 = state["players"]["1"], state["players"]["2"]
        p1["board"] = [card, unit(f"lifecycle_ally_{skill_id}", row="ranged", power=8)]
        p2["board"] = [unit(f"lifecycle_enemy_{skill_id}", row="melee", power=1)]
        p1["draw_pile"] = [unit(f"draw_after_{skill_id}")]
        state["weather"] = {"melee": 0, "ranged": 0, "siege": 0}
        before_hand = len(p1["hand"])
        gwent._resolve_round(state)
        kept = any(u["id"] == card["id"] for u in p1["board"])
        in_discard = any(u["id"] == card["id"] for u in p1["discard"])
        drew = len(p1["hand"]) > before_hand
        if skill_id == "espolios":
            status = "resolved" if drew else "hook_not_triggered"
        elif skill_id == "gloria":
            status = "hidden_effect_executes" if kept else "not_kept"
        else:
            status = "missing_handler_confirmed" if in_discard and not kept else "unexpected_behavior"
        cases.append({"id": skill_id, "status": status, "kept_on_board": kept, "sent_to_discard": in_discard, "drew_card": drew})

    return cases


def main() -> None:
    generic = [run_skill(skill_id) for skill_id in cartas.HABILIDADES]
    identities = [run_identity(card_id) for card_id in gwent.CARD_IDENTITY_ABILITIES]
    lifecycle = run_lifecycle_cases()
    report = {
        "metadata": {
            "document": "Runtime smoke audit of card effects v0.1",
            "status": "DIAGNOSTIC ONLY; DOES NOT CHANGE GAME DATA OR RUNTIME",
            "engine": "sistemas.gwent.aplicar_jogada / _remover_unidade / _resolve_round",
            "method": "Controlled synthetic states; no player strategy, match win-rate, or production DB assumptions",
        },
        "generic_skill_smoke": generic,
        "generic_skill_counts": {
            "catalog_count": len(cartas.HABILIDADES),
            "play_action_completed_not_full_branch_coverage": sum(x["status"] == "play_action_completed_not_full_branch_coverage" for x in generic),
            "lifecycle_hook_tested_separately": sum(x["status"] == "lifecycle_hook_tested_separately" for x in generic),
            "errors": sum(x["status"] == "error" for x in generic),
            "unexpected_card_location": sum(x["status"] == "card_location_unexpected" for x in generic),
        },
        "identity_smoke": identities,
        "identity_counts": {
            "active_mapping_count": len(gwent.CARD_IDENTITY_ABILITIES),
            "resolved": sum(x["status"] == "resolved" for x in identities),
            "errors": sum(x["status"] == "error" for x in identities),
        },
        "lifecycle_cases": lifecycle,
        "notes": [
            "A successful play-action proves the engine accepted the card and completed the action in this fixture; it does not prove every conditional branch was entered.",
            "The encadeamento fixture now sets last_row equal to the played row; the sangue_frio fixture equalizes both pre-play board scores at 11.",
            "EFP values are not derived automatically from these observed deltas; effects with delayed/resource outcomes require separate valuation.",
            "The current rarity effect budget is set to Comum for smoke tests to isolate effect implementations.",
        ],
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["generic_skill_counts"], ensure_ascii=False))
    print("condition fixtures:", json.dumps({x["id"]: x["immediate_field_swing_delta_excluding_base_power"] for x in generic if x["id"] in {"encadeamento", "sangue_frio"}}, ensure_ascii=False))
    print(json.dumps(report["identity_counts"], ensure_ascii=False))
    print(json.dumps([{"id": x["id"], "status": x["status"]} for x in lifecycle], ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

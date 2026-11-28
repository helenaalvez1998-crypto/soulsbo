#!/usr/bin/env python3
"""Stateful end-to-end engine checks with JSON/SQLite snapshot round-trips.

These tests exercise the actual in-memory Gwent engine and its real card catalogue.
They do not instantiate the Discord bot or production HTTP/database services.
"""
from __future__ import annotations

import ast
import json
import sqlite3
import sys
import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sistemas import cartas, gwent  # noqa: E402

REPORT = ROOT / "docs/card-game-match-snapshot-integration-v0.1.json"
CASES: list[dict[str, Any]] = []


def check(name: str, fn):
    try:
        details = fn() or {}
        CASES.append({"case": name, "status": "passed", **details})
    except Exception as exc:  # keep running to collect all independent failures
        CASES.append({"case": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})


def snapshot(state: dict) -> dict:
    """Simulate the JSON encoding/decoding boundary used by state_json."""
    encoded = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
    decoded = json.loads(encoded)
    assert isinstance(decoded, dict)
    assert decoded.get("match_id") == state.get("match_id")
    return decoded


def synthetic_unit(uid: str, faction: str, power: int, row: str = "melee") -> dict:
    raw = {
        "id": uid,
        "nome": f"Unidade de teste {uid}",
        "categoria": "Unidade",
        "faccao": faction,
        "poder": int(power),
        "raridade": "Comum",
        "custo": 1,
        "habilidade": "",
        "descricao": "Fixture de teste; não é uma carta publicada.",
        "fileira": row,
        "row": row,
    }
    return gwent.preparar_carta(raw)


def real_card(card_id: str) -> dict:
    model = cartas.get_carta(card_id)
    assert model is not None, f"card missing from catalogue: {card_id}"
    return gwent.preparar_carta(model.para_dict())


def keep_both(state: dict, p1: int, p2: int) -> dict:
    for uid in (p1, p2):
        result = gwent.aplicar_jogada(state, uid, action="keep")
        assert "error" not in result, result.get("error")
        state = snapshot(result["state"])
    assert state["phase"] == "battle"
    assert state["turn"] == str(p1)
    return state


def play_power(state: dict, uid: int, power: int) -> dict:
    player = state["players"][str(uid)]
    card = next((item for item in player["hand"] if int(item.get("poder", -1)) == power), None)
    assert card is not None, f"player {uid}: power {power} not in hand"
    result = gwent.aplicar_jogada(state, uid, card_id=str(card["id"]), action="play", row=card.get("row"))
    assert "error" not in result, result.get("error")
    return snapshot(result["state"])


def pass_current_until_round_changes(state: dict, max_actions: int = 4) -> dict:
    initial_rounds = len(state.get("rounds", []))
    for _ in range(max_actions):
        if state["status"] != "active" or len(state.get("rounds", [])) > initial_rounds:
            break
        uid = int(state["turn"])
        result = gwent.aplicar_jogada(state, uid, action="pass")
        assert "error" not in result, result.get("error")
        state = snapshot(result["state"])
    assert state["status"] == "finished" or len(state.get("rounds", [])) > initial_rounds, "round did not resolve"
    return state


def make_full_deck(prefix: str, faction: str) -> list[dict]:
    rows = ("melee", "ranged", "siege")
    return [synthetic_unit(f"{prefix}_unit_{power:02d}", faction, power, rows[(power - 1) % 3])
            for power in range(1, 13)]


def test_complete_three_round_match(p1_faction: str, p2_faction: str, match_id: int) -> dict:
    p1, p2 = 11001 + match_id, 22002 + match_id
    decks = {
        str(p1): make_full_deck(f"p1_{match_id}", p1_faction),
        str(p2): make_full_deck(f"p2_{match_id}", p2_faction),
    }
    configs = {
        str(p1): {"faction": p1_faction, "leader_id": gwent.DEFAULT_LEADERS[p1_faction]},
        str(p2): {"faction": p2_faction, "leader_id": gwent.DEFAULT_LEADERS[p2_faction]},
    }
    state = snapshot(gwent.novo_estado(match_id, p1, p2, decks, configs))
    state = keep_both(state, p1, p2)

    # Every round: the scheduled winner plays a high-power unit and the loser a low one.
    schedules = [
        {str(p1): 10, str(p2): 1},
        {str(p2): 10, str(p1): 1},
        {str(p1): 9, str(p2): 2},
    ]
    expected_winners = [str(p1), str(p2), str(p1)]
    for index, schedule in enumerate(schedules, start=1):
        # Starter order alternates; the scheduled power is selected by the actual turn.
        for _ in range(2):
            uid = str(state["turn"])
            assert uid in schedule
            state = play_power(state, int(uid), schedule[uid])
        assert len(state["rounds"]) == index - 1
        state = pass_current_until_round_changes(state)
        assert len(state["rounds"]) == index
        actual_winner = state["rounds"][-1]["winner_id"]
        assert actual_winner == expected_winners[index - 1], (
            f"round {index}: expected {expected_winners[index - 1]}, got {actual_winner}"
        )
        # Snapshot boundary after every fully resolved round.
        state = snapshot(state)
        if index < 3:
            assert state["status"] == "active"
            assert state["round"] == index + 1
            assert state["weather"] == {row: 0 for row in gwent.ROWS}
            for side in state["players"].values():
                assert side["passed"] is False
                assert side["faction_boost_used"] is False
                assert side["synergy_used"] == {}

    assert state["status"] == "finished"
    assert state["phase"] == "finished"
    assert state["winner_id"] == str(p1)
    assert state["crowns"] == {str(p1): 2, str(p2): 1}
    return {
        "match_id": match_id,
        "p1_faction": p1_faction,
        "p2_faction": p2_faction,
        "round_winners": expected_winners,
        "crowns": state["crowns"],
        "winner_id": state["winner_id"],
        "round_count": len(state["rounds"]),
        "snapshots_round_tripped": True,
    }


for idx, (f1, f2) in enumerate([
    ("Ordem Áurea", "Véu Carmesim"),
    ("Véu Carmesim", "Lua Negra"),
    ("Lua Negra", "Os Esquecidos"),
    ("Os Esquecidos", "Ordem Áurea"),
], start=1):
    check(f"full_three_round_match_{idx}_{f1}_{f2}",
          lambda f1=f1, f2=f2, idx=idx: test_complete_three_round_match(f1, f2, 500 + idx))


def test_catalogue_card_payload_contract():
    required = {
        "id", "nome", "categoria", "especial", "poder", "raridade", "faccao",
        "fileira", "row", "habilidade", "habilidade_nome", "habilidade_texto",
        "sinergias", "combos_compativeis", "descricao", "image_url",
    }
    failures = []
    categories = {"Unidade": 0, "Especial": 0}
    for model in cartas.CARTAS_POR_ID.values():
        payload = gwent.preparar_carta(model.para_dict())
        missing = sorted(required - set(payload))
        if missing:
            failures.append({"card_id": model.id, "missing": missing})
        assert payload["id"] == model.id
        assert payload["categoria"] in categories
        categories[payload["categoria"]] += 1
        assert payload["row"] in gwent.ROWS
        assert payload["image_url"].startswith("/api/gwent/public-cards/")
        if payload["especial"]:
            assert payload["poder"] == 0
        else:
            assert 1 <= payload["poder"] <= 15
    assert not failures, failures[:5]
    return {
        "catalogue_models": len(cartas.CARTAS_POR_ID),
        "payloads_validated": len(cartas.CARTAS_POR_ID),
        "categories": categories,
        "required_payload_fields": sorted(required),
    }


check("all_catalogue_models_prepare_for_api_and_renderer_contract", test_catalogue_card_payload_contract)


def test_combo_activates_through_full_turn_and_survives_snapshot():
    p1, p2 = 31001, 31002
    p1_deck = [real_card("chefe_guardiao_cinzas"), real_card("gwent_unidade_baluarte")]
    p1_deck += [synthetic_unit(f"combo_fill_{n}", "Ordem Áurea", 4 + (n % 4)) for n in range(10)]
    p2_deck = make_full_deck("combo_opponent", "Véu Carmesim")
    state = snapshot(gwent.novo_estado(
        6101, p1, p2,
        {str(p1): p1_deck, str(p2): p2_deck},
        {str(p1): {"faction": "Ordem Áurea"}, str(p2): {"faction": "Véu Carmesim"}},
    ))
    state = keep_both(state, p1, p2)

    first = state["players"][str(p1)]["hand"][0]
    result = gwent.aplicar_jogada(state, p1, card_id=first["id"], action="play")
    assert "error" not in result, result.get("error")
    state = snapshot(result["state"])

    result = gwent.aplicar_jogada(state, p2, action="pass")
    assert "error" not in result, result.get("error")
    state = snapshot(result["state"])
    assert state["turn"] == str(p1)

    second = next(c for c in state["players"][str(p1)]["hand"] if c["id"] == "gwent_unidade_baluarte")
    result = gwent.aplicar_jogada(state, p1, card_id=second["id"], action="play")
    assert "error" not in result, result.get("error")
    state = snapshot(result["state"])
    activated = next(c for c in state["players"][str(p1)]["board"] if c["id"] == "gwent_unidade_baluarte")
    assert activated.get("combo_ativado") == "cinzas_fornalha"
    assert state["players"][str(p1)]["synergy_used"].get("cinzas_fornalha") is True
    assert int(activated.get("bonus", 0)) >= 2
    return {
        "combo_id": "cinzas_fornalha",
        "activating_card": activated["id"],
        "combo_bonus_persisted": int(activated["bonus"]),
        "synergy_used_persisted": True,
        "snapshot_round_trip": True,
    }


check("combo_activation_via_normal_turn_survives_json_snapshot", test_combo_activates_through_full_turn_and_survives_snapshot)


def test_leader_special_weather_and_round_reset():
    p1, p2 = 41001, 41002
    p1_deck = [synthetic_unit("weather_p1_unit", "Ordem Áurea", 7), real_card("gwent_especial_tempestade")]
    p1_deck += [synthetic_unit(f"weather_p1_fill_{n}", "Ordem Áurea", 4 + n % 3) for n in range(10)]
    p2_deck = [synthetic_unit(f"weather_p2_{n}", "Véu Carmesim", 7 + n % 2) for n in range(12)]
    state = snapshot(gwent.novo_estado(
        6201, p1, p2, {str(p1): p1_deck, str(p2): p2_deck},
        {str(p1): {"faction": "Ordem Áurea", "leader_id": "comandante_fornalha"},
         str(p2): {"faction": "Véu Carmesim"}},
    ))
    state = keep_both(state, p1, p2)
    state = play_power(state, p1, 7)
    state = play_power(state, p2, 7)

    result = gwent.aplicar_jogada(state, p1, action="leader", row="melee")
    assert "error" not in result, result.get("error")
    state = snapshot(result["state"])
    own_unit = next(u for u in state["players"][str(p1)]["board"] if u["id"] == "weather_p1_unit")
    assert own_unit["bonus"] >= 3  # +1 faction passive, +2 Godfrey
    assert state["players"][str(p1)]["leader_used"] is True

    result = gwent.aplicar_jogada(state, p2, action="pass")
    assert "error" not in result, result.get("error")
    state = snapshot(result["state"])
    special = next(c for c in state["players"][str(p1)]["hand"] if c["id"] == "gwent_especial_tempestade")
    result = gwent.aplicar_jogada(state, p1, card_id=special["id"], action="play", row="melee")
    assert "error" not in result, result.get("error")
    state = snapshot(result["state"])
    assert state["weather"]["melee"] == 1
    assert state["players"][str(p1)]["leader_used"] is True
    assert any(c["id"] == "gwent_especial_tempestade" for c in state["players"][str(p1)]["discard"])
    repeat_leader = gwent.aplicar_jogada(state, p1, action="leader", row="melee")
    assert repeat_leader.get("error") == "A habilidade de líder já foi usada."

    # Player 2 already passed; player 1's pass resolves the round and clears weather.
    result = gwent.aplicar_jogada(state, p1, action="pass")
    assert "error" not in result, result.get("error")
    state = snapshot(result["state"])
    assert len(state["rounds"]) == 1
    assert state["weather"] == {row: 0 for row in gwent.ROWS}
    assert state["players"][str(p1)]["leader_used"] is True  # once per match, not per round
    assert state["players"][str(p1)]["faction_boost_used"] is False
    return {
        "leader": "comandante_fornalha",
        "special": "gwent_especial_tempestade",
        "weather_applied_and_reset": True,
        "leader_use_persists_across_rounds": True,
        "second_leader_activation_rejected": True,
        "round_count": 1,
    }


check("leader_special_weather_snapshot_and_round_reset", test_leader_special_weather_and_round_reset)


def test_relic_action_is_snapshotted_and_consumed_once():
    p1, p2 = 51001, 51002
    p1_deck = [synthetic_unit("relic_owner_unit", "Ordem Áurea", 6)]
    p1_deck += [synthetic_unit(f"relic_owner_fill_{n}", "Ordem Áurea", 3 + n % 4) for n in range(11)]
    p2_deck = make_full_deck("relic_opponent", "Véu Carmesim")
    state = snapshot(gwent.novo_estado(
        6301, p1, p2, {str(p1): p1_deck, str(p2): p2_deck},
        {str(p1): {"faction": "Ordem Áurea", "relic_id": "reliquia_grande_runa_godrick", "relic_owned": True},
         str(p2): {"faction": "Véu Carmesim"}},
    ))
    state = keep_both(state, p1, p2)
    state = play_power(state, p1, 6)
    result = gwent.aplicar_jogada(state, p2, action="pass")
    assert "error" not in result, result.get("error")
    state = snapshot(result["state"])

    before = next(u for u in state["players"][str(p1)]["board"] if u["id"] == "relic_owner_unit")["bonus"]
    result = gwent.aplicar_jogada(state, p1, action="relic")
    assert "error" not in result, result.get("error")
    state = snapshot(result["state"])
    owner = next(u for u in state["players"][str(p1)]["board"] if u["id"] == "relic_owner_unit")
    assert owner["bonus"] == before + 1
    assert state["players"][str(p1)]["relic_used"] is True
    assert any(c["id"] == "reliquia_grande_runa_godrick" for c in state["players"][str(p1)]["discard"])

    result = gwent.aplicar_jogada(state, p1, action="relic")
    assert result.get("error") == "Sua Relíquia já foi ativada nesta partida."
    return {
        "relic_id": "reliquia_grande_runa_godrick",
        "ally_bonus_delta": 1,
        "relic_consumed_to_discard": True,
        "second_activation_rejected": True,
        "snapshot_round_trip": True,
    }


check("relic_action_persists_and_rejects_second_use", test_relic_action_is_snapshotted_and_consumed_once)


def test_manual_weather_action_once_per_match():
    p1, p2 = 61001, 61002
    decks = {str(p1): make_full_deck("manual_weather_p1", "Ordem Áurea"),
             str(p2): make_full_deck("manual_weather_p2", "Véu Carmesim")}
    state = snapshot(gwent.novo_estado(6351, p1, p2, decks))
    state = keep_both(state, p1, p2)
    result = gwent.aplicar_jogada(state, p1, action="weather", row="ranged")
    assert "error" not in result, result.get("error")
    state = snapshot(result["state"])
    assert state["weather"]["ranged"] == 1
    assert state["players"][str(p1)]["weather_used"] is True
    result = gwent.aplicar_jogada(state, p2, action="pass")
    assert "error" not in result, result.get("error")
    state = snapshot(result["state"])
    repeated = gwent.aplicar_jogada(state, p1, action="weather", row="ranged")
    assert repeated.get("error") == "Seu efeito climático já foi usado nesta partida."
    return {"first_weather_action_applied": True, "weather_used_persisted": True,
            "second_weather_action_rejected": True}


check("manual_weather_action_is_limited_and_snapshotted", test_manual_weather_action_once_per_match)


def test_http_frontend_contract_static():
    bot_source = (ROOT / "bot.py").read_text(encoding="utf-8")
    app_source = (ROOT / "site/app.js").read_text(encoding="utf-8")
    expected_routes = [
        'app.router.add_get("/api/gwent/cards", self._api_gwent_cards)',
        'app.router.add_post("/api/gwent/deck", self._api_gwent_deck_save)',
        'app.router.add_get("/api/gwent/matches/{match_id}", self._api_gwent_match_detail)',
        'app.router.add_post("/api/gwent/matches/{match_id}/action", self._api_gwent_match_action)',
    ]
    missing_routes = [route for route in expected_routes if route not in bot_source]
    assert not missing_routes, missing_routes
    assert "async def _api_gwent_cards" in bot_source
    assert "async def _api_gwent_match_detail" in bot_source
    assert "async def _api_gwent_match_action" in bot_source
    assert "fetch('/api/gwent/cards'" in app_source
    assert "data.catalog" in app_source and "data.cards" in app_source
    assert "habilidade_texto" in app_source and "combos_compativeis" in app_source
    assert "/api/gwent/matches/${matchId}/action" in app_source
    assert "card_id, row, card_ids, target_id" in app_source
    return {"routes_checked": len(expected_routes), "frontend_fields_checked":
            ["catalog", "cards", "habilidade_texto", "combos_compativeis", "image_url"],
            "classification": "static contract only; handler dispatch not executed"}


check("http_and_frontend_contract_static", test_http_frontend_contract_static)


def test_legacy_snapshot_defaults_and_error_immutability():
    p1, p2 = 71001, 71002
    decks = {str(p1): make_full_deck("legacy_p1", "Ordem Áurea"), str(p2): make_full_deck("legacy_p2", "Véu Carmesim")}
    state = gwent.novo_estado(6401, p1, p2, decks)
    state["phase"] = "battle"
    for key in ("weather", "event_log"):
        state.pop(key, None)
    for side in state["players"].values():
        for key in ("discard", "draw_pile", "faction_boost_used", "mulligan_done", "leader_used",
                    "relic_used", "weather_used", "last_row", "synergy_used", "baixas"):
            side.pop(key, None)
    result = gwent.aplicar_jogada(state, p1, action="pass")
    assert "error" not in result, result.get("error")
    recovered = snapshot(result["state"])
    assert recovered["weather"] == {row: 0 for row in gwent.ROWS}
    assert recovered["event_log"]
    for side in recovered["players"].values():
        assert "discard" in side and "draw_pile" in side and "synergy_used" in side
        assert "faction_boost_used" in side and "mulligan_done" in side

    before = snapshot(gwent.novo_estado(6402, p1, p2, decks))
    before["phase"] = "battle"
    for side in before["players"].values():
        side["mulligan_done"] = True
    before_blob = json.dumps(before, ensure_ascii=False, sort_keys=True)
    failure = gwent.aplicar_jogada(before, p1, card_id="does_not_exist", action="play")
    after_blob = json.dumps(before, ensure_ascii=False, sort_keys=True)
    assert failure.get("error") == "Essa carta não está na sua mão."
    assert before_blob == after_blob, "rejected action mutated input snapshot"
    return {"legacy_state_defaults_restored": True, "rejected_action_did_not_mutate_input": True}


check("legacy_snapshot_compatibility_and_rejected_action_immutability", test_legacy_snapshot_defaults_and_error_immutability)


def test_sqlite_state_json_roundtrip():
    p1, p2 = 81001, 81002
    state = gwent.novo_estado(
        6501, p1, p2,
        {str(p1): make_full_deck("sqlite_p1", "Ordem Áurea"),
         str(p2): make_full_deck("sqlite_p2", "Lua Negra")},
    )
    state = snapshot(state)
    # Execute the actual schema constants from database.py without importing
    # aiosqlite or opening the production database.
    schema_tree = ast.parse((ROOT / "database.py").read_text(encoding="utf-8"))
    schema_values = {}
    for node in schema_tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"SCHEMA", "SCHEMA_CARTAS"}:
                    schema_values[target.id] = ast.literal_eval(node.value)
    assert {"SCHEMA", "SCHEMA_CARTAS"}.issubset(schema_values)
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(schema_values["SCHEMA"])
    conn.executescript(schema_values["SCHEMA_CARTAS"])
    conn.execute("INSERT INTO users(user_id) VALUES (?)", (p1,))
    conn.execute("INSERT INTO users(user_id) VALUES (?)", (p2,))
    conn.execute(
        "INSERT INTO cartas_gwent_matches(creator_id,opponent_id,status,state_json) VALUES (?,?,?,?)",
        (p1, p2, state["status"], json.dumps(state, ensure_ascii=False)),
    )
    row = conn.execute("SELECT id,status,state_json FROM cartas_gwent_matches WHERE id=1").fetchone()
    loaded = json.loads(row[2])
    assert row[1] == loaded["status"] == "active"
    assert loaded["phase"] == "mulligan"
    assert list(loaded["players"]) == [str(p1), str(p2)]
    conn.execute(
        "UPDATE cartas_gwent_matches SET status=?,state_json=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
        ("active", json.dumps(loaded, ensure_ascii=False), row[0]),
    )
    reloaded = json.loads(conn.execute("SELECT state_json FROM cartas_gwent_matches WHERE id=1").fetchone()[0])
    assert reloaded["match_id"] == 6501
    assert len(reloaded["players"][str(p1)]["hand"]) == 10
    conn.close()
    return {"sqlite_table": "cartas_gwent_matches", "schema_source": "database.py: SCHEMA + SCHEMA_CARTAS", "state_json_insert_select_update": True, "foreign_keys_enabled": True, "opening_hand": 10, "reserve": 2}


check("sqlite_state_json_insert_update_read_roundtrip", test_sqlite_state_json_roundtrip)


total = len(CASES)
passed = sum(case["status"] == "passed" for case in CASES)
failed = total - passed
report = {
    "version": "v0.1",
    "status": "passed" if failed == 0 else "failed",
    "scope": "stateful in-memory engine, card preparation, JSON and SQLite state_json round-trips",
    "integration_limit": "Discord bot and HTTP handlers not instantiated; production DB/credentials are not part of the handoff ZIP",
    "environment": {
        "discord_module_present": importlib.util.find_spec("discord") is not None,
        "aiosqlite_module_present": importlib.util.find_spec("aiosqlite") is not None,
        "http_dispatch_executed": False,
        "database_wrapper_executed": False,
    },
    "checks": total,
    "passed": passed,
    "failed": failed,
    "cases": CASES,
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"checks": total, "passed": passed, "failed": failed, "report": str(REPORT)}, ensure_ascii=False))
if failed:
    raise SystemExit(1)

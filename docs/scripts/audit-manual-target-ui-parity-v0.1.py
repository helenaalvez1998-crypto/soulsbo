#!/usr/bin/env python3
"""Auditoria read-only da paridade entre seletor de alvos, UI e motor legado.

Executar da raiz do repositório:
    python docs/scripts/audit-manual-target-ui-parity-v0.1.py

As fixtures exercitam opcoes_de_alvo/aplicar_jogada reais e fazem verificações
estáticas pontuais do frontend. Não alteram runtime, catálogo ou dados de partida.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sistemas import cartas, gwent  # noqa: E402

SMOKE_PATH = ROOT / "docs" / "scripts" / "validate-card-effect-smoke-v0.1.py"
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("manual_target_smoke_helpers", SMOKE_PATH)
smoke = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(smoke)

OUT = ROOT / "docs" / "card-game-manual-target-ui-parity-audit-v0.1.json"
APP_JS = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
RESULTS: list[dict] = []


def special(skill: str, card_id: str = "audit_special", rarity: str = "Comum") -> dict:
    return smoke.unit(card_id, skill=skill, power=0, special=True, rarity=rarity)


def state_for(card: dict) -> dict:
    state = smoke.fixture(card, "melee")
    p1 = state["players"]["1"]
    p1["hand"] = [card, smoke.unit("audit_reserve", power=1)]
    p1["faction"] = "Lua Negra"
    p1["faction_boost_used"] = True
    return state


def check(case_id: str, title: str, fn: Callable[[], dict], expected_scope: str) -> None:
    try:
        detail = fn()
        RESULTS.append({"id": case_id, "title": title, "status": "PASS", "expected_scope": expected_scope, **detail})
    except Exception as exc:  # keep all cases visible even when one regresses
        RESULTS.append({"id": case_id, "title": title, "status": "FAIL", "expected_scope": expected_scope,
                        "error": f"{type(exc).__name__}: {exc}"})


def t01_target_summary_does_not_expose_instance_key() -> dict:
    card = special("gwent_execucao")
    state = state_for(card)
    state["players"]["2"]["board"] = [smoke.unit("enemy_a", power=4)]
    info = gwent.opcoes_de_alvo(state, 1)[card["id"]]
    option = info["opcoes"][0]
    expected = {"id", "nome", "poder", "bonus", "row", "escudo", "sangramento", "geada", "podrida", "loucura"}
    assert set(option) == expected, set(option)
    assert "instance_id" not in option and "exemplar_id" not in option
    return {"observed_fields": sorted(option), "note": "O contrato público da opção não carrega uma identidade física de exemplar."}


def t02_duplicate_ids_cannot_select_second_physical_copy() -> dict:
    card = special("gwent_execucao")
    state = state_for(card)
    first = smoke.unit("same-id", power=4, row="melee", nome="Cópia A")
    second = smoke.unit("same-id", power=5, row="melee", nome="Cópia B")
    state["players"]["2"]["board"] = [first, second]
    info = gwent.opcoes_de_alvo(state, 1)[card["id"]]
    assert len(info["opcoes"]) == 2
    assert [o["id"] for o in info["opcoes"]] == ["same-id", "same-id"]
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee", target_id="same-id")
    assert "error" not in result, result
    discarded = result["state"]["players"]["2"]["discard"]
    assert any(u.get("nome") == "Cópia A" for u in discarded)
    assert not any(u.get("nome") == "Cópia B" for u in discarded)
    return {"picker_options": [o["nome"] for o in info["opcoes"]], "submitted_target_id": "same-id",
            "resolved_copy": "Cópia A", "note": "O backend resolve o primeiro ID elegível na ordem do tabuleiro; não há como enviar uma das duas cópias de forma inequívoca."}


def t03_execution_ui_shows_raw_not_effective_power() -> dict:
    card = special("gwent_execucao")
    state = state_for(card)
    state["weather"] = {"melee": 3, "ranged": 0, "siege": 0}
    target = smoke.unit("enemy_weather", power=9, bonus=0, row="melee")
    state["players"]["2"]["board"] = [target]
    info = gwent.opcoes_de_alvo(state, 1)[card["id"]]
    assert info["opcoes"][0]["id"] == "enemy_weather"
    effective = gwent._poder_efetivo(target, state["weather"])
    raw = int(info["opcoes"][0]["poder"]) + int(info["opcoes"][0]["bonus"])
    assert effective == 6 and raw == 9
    assert "number(o.poder + o.bonus)" in APP_JS
    assert "Poder efetivo" not in APP_JS[APP_JS.find("function openGwentTargetPicker"):APP_JS.find("function replaceGwentArenaMarkup")]
    return {"eligibility_metric": "effective_power", "effective_power": effective, "picker_display_value": raw,
            "weather": 3, "note": "A unidade é elegível por poder efetivo 6, mas o seletor apresenta 9 (poder-base + bônus), sem explicitar o desconto climático/estados."}


def t04_frontend_applies_same_different_row_filter_but_server_revalidates() -> dict:
    card = special("gwent_execucao")
    state = state_for(card)
    state["players"]["2"]["board"] = [
        smoke.unit("melee_target", power=4, row="melee"),
        smoke.unit("ranged_target", power=4, row="ranged"),
    ]
    info = gwent.opcoes_de_alvo(state, 1)[card["id"]]
    assert {o["id"] for o in info["opcoes"]} == {"melee_target", "ranged_target"}
    assert "info.filtro_fileira === 'mesma' ? o.row === row" in APP_JS
    assert "info.filtro_fileira === 'diferente' ? o.row !== row" in APP_JS
    rejected = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee", target_id="ranged_target")
    assert "error" in rejected and "não está nessa fileira" in rejected["error"]
    return {"server_options_before_ui_filter": [o["id"] for o in info["opcoes"]],
            "client_row_filter": "same row for Execução; different row for Passo",
            "out_of_row_submission": rejected["error"],
            "note": "A filtragem visual é local no frontend; o motor repete a validação da fileira na submissão."}


def t05_medico_automatic_uses_last_eligible_discard_entry() -> dict:
    card = special("gwent_medico")
    state = state_for(card)
    p1 = state["players"]["1"]
    p1["discard"] = [smoke.unit("discard_first", power=2), smoke.unit("discard_second", power=4), smoke.unit("discard_last", power=3)]
    info = gwent.opcoes_de_alvo(state, 1)[card["id"]]
    assert [o["id"] for o in info["opcoes"]] == ["discard_first", "discard_second", "discard_last"]
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee", target_id="")
    assert "error" not in result, result
    hand_ids = [c["id"] for c in result["state"]["players"]["1"]["hand"]]
    assert "discard_last" in hand_ids and "discard_first" not in hand_ids and "discard_second" not in hand_ids
    assert "Automático" in APP_JS
    return {"eligible_in_discard_order": [o["id"] for o in info["opcoes"]], "automatic_choice": "discard_last",
            "note": "O botão Automático envia target_id vazio; para Lágrima Sagrada, o motor escolhe candidates[-1], não maior/menor poder."}


def t06_requiem_automatic_uses_highest_base_power() -> dict:
    card = special("gwent_requiem")
    state = state_for(card)
    p1 = state["players"]["1"]
    p1["discard"] = [smoke.unit("discard_weak", power=2), smoke.unit("discard_strong", power=6), smoke.unit("discard_mid", power=5)]
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee", target_id="")
    assert "error" not in result, result
    board_ids = [u["id"] for u in result["state"]["players"]["1"]["board"]]
    assert "discard_strong" in board_ids
    return {"automatic_choice": "discard_strong", "selection_metric": "highest base power",
            "note": "O automático do Réquiem usa maior poder-base; difere do automático da Lágrima Sagrada."}



def t07_base_power_eligibility_is_displayed_as_power_plus_bonus() -> dict:
    card = special("gwent_medico")
    state = state_for(card)
    target = smoke.unit("discard_with_bonus", power=4, bonus=5)
    state["players"]["1"]["discard"] = [target]
    info = gwent.opcoes_de_alvo(state, 1)[card["id"]]
    option = info["opcoes"][0]
    base_power = int(option["poder"])
    display_power = base_power + int(option["bonus"])
    assert base_power == 4 and display_power == 9
    assert "number(o.poder + o.bonus)" in APP_JS
    return {"eligibility_metric": "base_power", "base_power": base_power, "picker_display_value": display_power,
            "note": "Lágrima Sagrada testa poder-base <= 4, mas o seletor apresenta poder-base + bônus (9 neste caso), sem explicar qual métrica define a elegibilidade."}


def t07_egide_one_manual_choice_can_shield_multiple_targets() -> dict:
    card = special("gwent_egide", rarity="Rara")
    state = state_for(card)
    p1 = state["players"]["1"]
    p1["board"] = [
        smoke.unit("manual_low", power=2, row="melee"),
        smoke.unit("auto_high", power=10, row="melee"),
        smoke.unit("auto_mid", power=7, row="ranged"),
    ]
    info = gwent.opcoes_de_alvo(state, 1)[card["id"]]
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee", target_id="manual_low")
    assert "error" not in result, result
    board = result["state"]["players"]["1"]["board"]
    shielded = [u["id"] for u in board if int(u.get("escudo", 0)) > 0]
    assert shielded == ["manual_low", "auto_high"]
    assert "Escolha a unidade que receberá o escudo" in info["rotulo"]
    assert "protege até 2 unidades" in APP_JS or "gwent_egide" in APP_JS
    return {"picker_label": info["rotulo"], "manual_choice": "manual_low", "actually_shielded": shielded,
            "count": len(shielded), "note": "Rara protege duas: a escolhida primeiro e depois a maior elegível por poder efetivo. A UI só pede uma escolha manual."}


def t08_passo_one_manual_choice_moves_secondary_in_board_order() -> dict:
    card = special("gwent_passo", rarity="Rara")
    state = state_for(card)
    p1 = state["players"]["1"]
    p1["board"] = [
        smoke.unit("manual_low", power=1, row="ranged"),
        smoke.unit("first_in_board", power=2, row="siege"),
        smoke.unit("highest_power", power=14, row="siege"),
    ]
    info = gwent.opcoes_de_alvo(state, 1)[card["id"]]
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee", target_id="manual_low")
    assert "error" not in result, result
    board = result["state"]["players"]["1"]["board"]
    moved = [u["id"] for u in board if u["row"] == "melee"]
    assert moved == ["manual_low", "first_in_board"]
    assert "Escolha a unidade que será movida" in info["rotulo"]
    return {"picker_label": info["rotulo"], "manual_choice": "manual_low", "actually_moved": moved,
            "not_moved_despite_higher_power": "highest_power",
            "note": "Rara move duas: a unidade escolhida e depois a primeira elegível na ordem original do tabuleiro, não a segunda mais fraca/forte."}


def t09_relic_options_are_returned_by_api_but_not_consumed_by_frontend() -> dict:
    relic = gwent.opcoes_de_reliquia({"players": {"1": {"equipped_relic_id": "reliquia_lamina_negra"},
                                                        "2": {"board": [smoke.unit("enemy", power=5)]}}}, 1)
    assert relic["requires_row"] is True and relic["requires_target"] is True
    assert "relic_options" not in APP_JS
    assert "const targets = (enemy.board || []).filter(unit => unit.row === row)" in APP_JS
    return {"server_options_require_target": relic["requires_target"], "server_rows": relic["rows"],
            "frontend_reads_relic_options": False,
            "note": "O endpoint publica relic_options, mas app.js reconstrói a lista a partir de opponent.board e filtra a fileira localmente."}


def t10_lamina_negra_shield_blocks_without_consuming_relic() -> dict:
    card = gwent.cartas.get_carta("reliquia_lamina_negra") if hasattr(gwent, "cartas") else None
    if card is None:
        card = cartas.get_carta("reliquia_lamina_negra")
    assert card is not None, "Modelo reliquia_lamina_negra ausente do catálogo"
    state = state_for(smoke.unit("reserve_special", special=True, skill="gwent_clima"))
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["hand"] = [smoke.unit("reserve", power=1)]
    p1["equipped_relic_id"] = "reliquia_lamina_negra"
    p1["relic_card_owned"] = True
    p2["board"] = [smoke.unit("shielded_target", power=5, row="melee", escudo=1)]
    result = gwent.aplicar_jogada(state, 1, action="relic", row="melee", target_id="shielded_target")
    assert "error" not in result, result
    after = result["state"]["players"]["1"]
    target = result["state"]["players"]["2"]["board"][0]
    assert target["escudo"] == 0 and after["relic_used"] is False
    return {"shield_after": target["escudo"], "relic_used": after["relic_used"],
            "note": "Escudo é consumido; a Relíquia continua disponível. O seletor inclui alvo protegido e mostra o indicador de Escudo."}


def t11_algemas_can_be_spent_on_target_without_positive_bonus() -> dict:
    card = cartas.get_carta("reliquia_algemas_margit")
    assert card is not None, "Modelo reliquia_algemas_margit ausente do catálogo"
    state = state_for(smoke.unit("reserve_special", special=True, skill="gwent_clima"))
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["hand"] = [smoke.unit("reserve", power=1)]
    p1["equipped_relic_id"] = "reliquia_algemas_margit"
    p1["relic_card_owned"] = True
    p2["board"] = [smoke.unit("no_positive_bonus", power=5, row="melee", bonus=0)]
    options = gwent.opcoes_de_reliquia(state, 1)
    assert options["rows"]["melee"][0]["id"] == "no_positive_bonus"
    result = gwent.aplicar_jogada(state, 1, action="relic", row="melee", target_id="no_positive_bonus")
    assert "error" not in result, result
    after = result["state"]["players"]["1"]
    enemy = result["state"]["players"]["2"]["board"][0]
    assert enemy["bonus"] == 0 and after["relic_used"] is True
    return {"target_bonus_before_after": [0, enemy["bonus"]], "relic_used": after["relic_used"],
            "note": "Algemas aceita qualquer inimigo da fileira; com bônus zero, não muda o alvo, mas consome a Relíquia."}


check("TUI-001", "Resumo de alvo sem identidade física", t01_target_summary_does_not_expose_instance_key,
      "Contrato de serialização e identificação")
check("TUI-002", "IDs repetidos colapsam a seleção manual", t02_duplicate_ids_cannot_select_second_physical_copy,
      "Desambiguação de exemplar")
check("TUI-003", "Execução mostra valor bruto, valida poder efetivo", t03_execution_ui_shows_raw_not_effective_power,
      "Paridade semântica do seletor")
check("TUI-004", "Filtro de fileira no frontend e revalidação no motor", t04_frontend_applies_same_different_row_filter_but_server_revalidates,
      "Paridade de filtro UI/backend")
check("TUI-005", "Automático da Lágrima Sagrada usa último descarte elegível", t05_medico_automatic_uses_last_eligible_discard_entry,
      "Fallback automático")
check("TUI-006", "Automático do Réquiem usa maior poder-base", t06_requiem_automatic_uses_highest_base_power,
      "Fallback automático")
check("TUI-007", "Poder-base de elegibilidade é exibido como poder + bônus", t07_base_power_eligibility_is_displayed_as_power_plus_bonus,
      "Paridade semântica do seletor")
check("TUI-008", "Égide pede um alvo e protege múltiplos", t07_egide_one_manual_choice_can_shield_multiple_targets,
      "Alvo manual versus alvos secundários")
check("TUI-009", "Passo pede um alvo e move secundários por ordem do tabuleiro", t08_passo_one_manual_choice_moves_secondary_in_board_order,
      "Alvo manual versus alvos secundários")
check("TUI-010", "Opções de relíquia do servidor não são consumidas pelo frontend", t09_relic_options_are_returned_by_api_but_not_consumed_by_frontend,
      "Contrato API/frontend")
check("TUI-011", "Escudo bloqueia Lâmina Negra sem consumir a relíquia", t10_lamina_negra_shield_blocks_without_consuming_relic,
      "Proteção e custo de ativação")
check("TUI-012", "Algemas podem consumir-se sem reduzir bônus positivo", t11_algemas_can_be_spent_on_target_without_positive_bonus,
      "Elegibilidade e semântica de alvo")

passed = sum(x["status"] == "PASS" for x in RESULTS)
failed = len(RESULTS) - passed
payload = {
    "audit": "manual_target_ui_parity_v0.1",
    "date": "2026-11-27",
    "status": "READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED",
    "scope": "opcoes_de_alvo, target_id, UI picker, relic options and special-card resolution",
    "passed": passed,
    "failed": failed,
    "cases": RESULTS,
    "runtime_modified": False,
}
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
for item in RESULTS:
    marker = "PASS" if item["status"] == "PASS" else "FAIL"
    print(f"[{marker}] {item['id']} — {item['title']}")
    if item.get("error"):
        print(f"       {item['error']}")
print(f"Resultado: {passed}/{len(RESULTS)} aprovadas; {failed} falhas.")
print(f"JSON: {OUT.relative_to(ROOT)}")
if failed:
    raise SystemExit(1)

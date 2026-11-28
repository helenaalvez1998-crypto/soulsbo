#!/usr/bin/env python3
"""Auditoria read-only do Grupo D: seleção, fallback, outcomes e custos.

Executar da raiz do repositório:
    python docs/scripts/audit-card-game-selection-group-D-v0.1.py

Usa fixtures sintéticas e chama funções reais do runtime legado. Também faz
verificações estáticas pontuais de API/DB/frontend. Não altera runtime nem DB.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sistemas import cartas, gwent  # noqa: E402

SMOKE_PATH = ROOT / "docs" / "scripts" / "validate-card-effect-smoke-v0.1.py"
spec = importlib.util.spec_from_file_location("group_d_smoke_helpers", SMOKE_PATH)
smoke = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(smoke)

OUT = ROOT / "docs" / "card-game-selection-group-D-audit-v0.1.json"
APP_JS = (ROOT / "site" / "app.js").read_text(encoding="utf-8")
GWENT_PY = (ROOT / "sistemas" / "gwent.py").read_text(encoding="utf-8")
BOT_PY = (ROOT / "bot.py").read_text(encoding="utf-8")
DB_PY = (ROOT / "database.py").read_text(encoding="utf-8")
RESULTS: list[dict] = []


def special(skill: str, card_id: str | None = None, rarity: str = "Comum") -> dict:
    return smoke.unit(card_id or f"audit_{skill}", skill=skill, power=0, special=True, rarity=rarity)


def state_for(card: dict) -> dict:
    state = smoke.fixture(card, "melee")
    p1 = state["players"]["1"]
    p1["hand"] = [card, smoke.unit("audit_reserve", power=1)]
    p1["faction"] = "Lua Negra"
    p1["faction_boost_used"] = True
    return state


def success_state(result: dict) -> dict:
    assert "error" not in result, result
    assert isinstance(result.get("state"), dict), result
    return result["state"]


def check(case_id: str, title: str, fn: Callable[[], dict], scope: str) -> None:
    try:
        detail = fn()
        RESULTS.append({"id": case_id, "title": title, "status": "PASS", "scope": scope, **detail})
    except Exception as exc:  # retain the complete audit even if one case fails
        RESULTS.append({"id": case_id, "title": title, "status": "FAIL", "scope": scope,
                        "error": f"{type(exc).__name__}: {exc}"})


def t01_rejected_invalid_target_is_non_mutating() -> dict:
    card = special("gwent_execucao")
    state = state_for(card)
    state["players"]["2"]["board"] = [smoke.unit("valid_enemy", power=4, row="melee")]
    before = json.dumps(state, ensure_ascii=False, sort_keys=True)
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee", target_id="missing")
    after = json.dumps(state, ensure_ascii=False, sort_keys=True)
    assert "error" in result
    assert before == after
    assert any(c["id"] == card["id"] for c in state["players"]["1"]["hand"])
    return {"error": result["error"], "input_snapshot_unchanged": True,
            "source_card_still_in_hand": True, "turn_cost": "not committed"}


def t02_required_target_absence_rejects_without_consuming_source() -> dict:
    card = special("gwent_requiem")
    state = state_for(card)
    state["players"]["1"]["discard"] = []
    before = json.dumps(state, ensure_ascii=False, sort_keys=True)
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee")
    assert "error" in result
    assert json.dumps(state, ensure_ascii=False, sort_keys=True) == before
    assert any(c["id"] == card["id"] for c in state["players"]["1"]["hand"])
    return {"error": result["error"], "policy_observed": "reject", "source_consumed": False}


def t03_manual_target_is_revalidated_after_options_are_read() -> dict:
    card = special("gwent_execucao")
    state = state_for(card)
    state["players"]["2"]["board"] = [
        smoke.unit("melee_target", power=4, row="melee"),
        smoke.unit("ranged_target", power=4, row="ranged"),
    ]
    offers = gwent.opcoes_de_alvo(state, 1)[card["id"]]["opcoes"]
    assert {x["id"] for x in offers} == {"melee_target", "ranged_target"}
    before = json.dumps(state, ensure_ascii=False, sort_keys=True)
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee", target_id="ranged_target")
    assert "error" in result and "fileira" in result["error"].casefold()
    assert json.dumps(state, ensure_ascii=False, sort_keys=True) == before
    return {"offered_ids": [x["id"] for x in offers], "submitted_id": "ranged_target",
            "server_rejected_stale_or_out_of_scope_choice": True}


def t04_target_summary_is_not_physical_identity() -> dict:
    card = special("gwent_execucao")
    state = state_for(card)
    state["players"]["2"]["board"] = [smoke.unit("enemy", power=4)]
    option = gwent.opcoes_de_alvo(state, 1)[card["id"]]["opcoes"][0]
    assert "id" in option and "instance_id" not in option and "exemplar_id" not in option
    assert '"target_id"' in BOT_PY or "target_id = str(body.get" in BOT_PY
    return {"public_option_fields": sorted(option), "legacy_key": "id",
            "physical_instance_key_present": False}


def t05_auto_execution_uses_lowest_effective_power() -> dict:
    card = special("gwent_execucao")
    state = state_for(card)
    state["players"]["2"]["board"] = [
        smoke.unit("weak_effective", power=5, row="melee", geada=1),
        smoke.unit("strong_effective", power=5, bonus=1, row="melee"),
        smoke.unit("other_row", power=2, row="siege"),
    ]
    result = success_state(gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee", target_id=""))
    discard_ids = [x["id"] for x in result["players"]["2"]["discard"]]
    assert "weak_effective" in discard_ids and "strong_effective" not in discard_ids
    return {"automatic_policy": "min(effective_power) within selected current row",
            "removed_target": "weak_effective", "other_row_excluded": True}


def t06_auto_egide_uses_highest_effective_power() -> dict:
    card = special("gwent_egide")
    state = state_for(card)
    state["players"]["1"]["board"] = [
        smoke.unit("weak", power=2, row="melee"),
        smoke.unit("strong", power=10, row="ranged"),
    ]
    result = success_state(gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee", target_id=""))
    shields = [u["id"] for u in result["players"]["1"]["board"] if int(u.get("escudo", 0)) > 0]
    assert shields == ["strong"]
    return {"automatic_policy": "max(effective_power) among protectable allies",
            "selected_target": "strong"}


def t07_auto_passo_uses_lowest_effective_power() -> dict:
    card = special("gwent_passo")
    state = state_for(card)
    state["players"]["1"]["board"] = [
        smoke.unit("weak", power=2, row="ranged"),
        smoke.unit("strong", power=10, row="siege"),
    ]
    result = success_state(gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee", target_id=""))
    rows = {u["id"]: u["row"] for u in result["players"]["1"]["board"]}
    assert rows["weak"] == "melee" and rows["strong"] == "siege"
    return {"automatic_policy": "min(effective_power) among movable allies",
            "moved_target": "weak"}


def t08_egide_target_count_changes_with_rarity_in_legacy() -> dict:
    def run(rarity: str) -> list[str]:
        card = special("gwent_egide", f"egide_{rarity}", rarity)
        state = state_for(card)
        state["players"]["1"]["board"] = [
            smoke.unit("a", power=2), smoke.unit("b", power=8), smoke.unit("c", power=6)
        ]
        result = success_state(gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee", target_id="a"))
        return [u["id"] for u in result["players"]["1"]["board"] if int(u.get("escudo", 0)) > 0]
    common = run("Comum")
    rare = run("Rara")
    assert common == ["a"] and rare == ["a", "b"]
    return {"common_targets": common, "rare_targets": rare,
            "conflict": "target cardinality depends on rarity in legacy; incompatible with approved BUF-001"}


def t09_passo_target_count_changes_with_rarity_in_legacy() -> dict:
    def run(rarity: str) -> dict[str, str]:
        card = special("gwent_passo", f"passo_{rarity}", rarity)
        state = state_for(card)
        state["players"]["1"]["board"] = [
            smoke.unit("manual", power=1, row="ranged"),
            smoke.unit("secondary", power=2, row="siege"),
        ]
        result = success_state(gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee", target_id="manual"))
        return {u["id"]: u["row"] for u in result["players"]["1"]["board"]}
    common, rare = run("Comum"), run("Rara")
    assert common["manual"] == "melee" and common["secondary"] == "siege"
    assert rare["manual"] == "melee" and rare["secondary"] == "melee"
    return {"common_rows": common, "rare_rows": rare,
            "conflict": "secondary target count depends on rarity in legacy; incompatible with approved BUF-001"}


def t10_leader_up_to_two_allows_single_available_target() -> dict:
    from importlib.util import spec_from_file_location
    target_script = ROOT / "docs" / "scripts" / "audit-target-selection-row-scope-v0.1.py"
    target_spec = spec_from_file_location("group_d_target_helpers", target_script)
    target_mod = importlib.util.module_from_spec(target_spec)
    assert target_spec and target_spec.loader
    target_spec.loader.exec_module(target_mod)
    one_ally = target_mod.unit("single_ally", 7, row="melee")
    state = target_mod.leader_state("bastiao_ancestral", "Ordem Áurea", [one_ally], [], row="melee")
    result = success_state(gwent.aplicar_jogada(state, 1, action="leader", row="melee"))
    ally = result["players"]["1"]["board"][0]
    assert ally["escudo"] == 1 and ally["bonus"] == 1
    return {"leader": "Morgott", "maximum_targets": 2, "available_targets": 1,
            "outcome": "applied_to_available_target", "source": "synthetic fixture"}


def t11_empty_leader_scope_is_rejected_without_leader_cost() -> dict:
    from importlib.util import spec_from_file_location
    target_script = ROOT / "docs" / "scripts" / "audit-target-selection-row-scope-v0.1.py"
    target_spec = spec_from_file_location("group_d_target_helpers_empty", target_script)
    target_mod = importlib.util.module_from_spec(target_spec)
    assert target_spec and target_spec.loader
    target_spec.loader.exec_module(target_mod)
    state = target_mod.leader_state("bastiao_ancestral", "Ordem Áurea", [], [], row="melee")
    before = json.dumps(state, ensure_ascii=False, sort_keys=True)
    result = gwent.aplicar_jogada(state, 1, action="leader", row="melee")
    assert "error" in result and json.dumps(state, ensure_ascii=False, sort_keys=True) == before
    assert state["players"]["1"]["leader_used"] is False
    return {"outcome": "rejected", "leader_used": False, "input_snapshot_unchanged": True}


def t12_chama_with_no_geada_is_consumed_without_target_mutation() -> dict:
    card = special("gwent_chama")
    state = state_for(card)
    p1 = state["players"]["1"]
    for unit in p1["board"]:
        unit["geada"] = 0
    before = [(u["id"], u.get("bonus", 0), u.get("geada", 0)) for u in p1["board"]]
    result = success_state(gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee"))
    after = [(u["id"], u.get("bonus", 0), u.get("geada", 0)) for u in result["players"]["1"]["board"]]
    assert before == after
    assert card["id"] in [c["id"] for c in result["players"]["1"]["discard"]]
    return {"outcome": "consumed_no_effect", "source_card_consumed": True,
            "target_state_changed": False, "legacy_note": "No aliado tinha Geada; a especial ainda foi descartada."}


def t13_muralha_empty_selected_row_is_consumed_without_buff() -> dict:
    card = special("gwent_muralha")
    state = state_for(card)
    p1 = state["players"]["1"]
    for unit in p1["board"]:
        unit["row"] = "ranged"
    before = {u["id"]: int(u.get("bonus", 0)) for u in p1["board"]}
    result = success_state(gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee"))
    after = {u["id"]: int(u.get("bonus", 0)) for u in result["players"]["1"]["board"]}
    assert before == after and card["id"] in [c["id"] for c in result["players"]["1"]["discard"]]
    return {"outcome": "consumed_no_effect", "source_card_consumed": True,
            "target_state_changed": False, "empty_row": "melee"}


def relic_state(relic_id: str, enemy: dict) -> dict:
    state = state_for(special("gwent_clima", "reserve_special"))
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["hand"] = [smoke.unit("reserve", power=1)]
    p1["equipped_relic_id"] = relic_id
    p1["relic_card_owned"] = True
    p2["board"] = [enemy]
    return state


def t14_algemas_zero_bonus_is_consumed_no_effect() -> dict:
    state = relic_state("reliquia_algemas_margit", smoke.unit("zero_bonus", power=5, bonus=0, row="melee"))
    result = success_state(gwent.aplicar_jogada(state, 1, action="relic", row="melee", target_id="zero_bonus"))
    p1, target = result["players"]["1"], result["players"]["2"]["board"][0]
    assert target["bonus"] == 0 and p1["relic_used"] is True and result["turn"] == "2"
    return {"outcome": "consumed_no_effect", "bonus_before_after": [0, 0],
            "relic_activation_consumed": True, "turn_cost_consumed": True}


def t15_lamina_block_consumes_shield_but_not_relic_activation() -> dict:
    state = relic_state("reliquia_lamina_negra", smoke.unit("shielded", power=5, row="melee", escudo=1))
    result = success_state(gwent.aplicar_jogada(state, 1, action="relic", row="melee", target_id="shielded"))
    p1, target = result["players"]["1"], result["players"]["2"]["board"][0]
    assert target["escudo"] == 0 and p1["relic_used"] is False and result["turn"] == "2"
    return {"outcome": "blocked", "protection_charge_consumed": True,
            "relic_activation_consumed": False, "turn_cost_consumed": True}


def t16_noite_chama_block_consumes_shield_and_activation() -> dict:
    state = relic_state("reliquia_noite_chama", smoke.unit("shielded", power=5, row="melee", escudo=1))
    result = success_state(gwent.aplicar_jogada(state, 1, action="relic", row="melee", target_id="chama"))
    p1, target = result["players"]["1"], result["players"]["2"]["board"][0]
    assert target["escudo"] == 0 and p1["relic_used"] is True and result["turn"] == "2"
    return {"outcome": "blocked", "protection_charge_consumed": True,
            "relic_activation_consumed": True, "turn_cost_consumed": True}


def t17_execution_block_consumes_card_and_turn_but_not_target() -> dict:
    card = special("gwent_execucao")
    state = state_for(card)
    state["players"]["2"]["board"] = [smoke.unit("shielded_enemy", power=4, row="melee", escudo=1)]
    result = success_state(gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee", target_id="shielded_enemy"))
    p1, p2 = result["players"]["1"], result["players"]["2"]
    target = next(u for u in p2["board"] if u["id"] == "shielded_enemy")
    assert target["escudo"] == 0 and card["id"] in [c["id"] for c in p1["discard"]]
    assert result["turn"] == "2"
    return {"outcome": "blocked", "protection_charge_consumed": True,
            "source_card_consumed": True, "turn_cost_consumed": True, "target_zone_unchanged": True}


def t18_aoe_can_have_mixed_applied_and_blocked_targets() -> dict:
    card = special("gwent_queima")
    state = state_for(card)
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["board"] = [smoke.unit("p1_shielded_max", power=9, escudo=1), smoke.unit("p1_weak", power=2)]
    p2["board"] = [smoke.unit("p2_unshielded_max", power=8), smoke.unit("p2_weak", power=2)]
    result = success_state(gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee"))
    p1_after, p2_after = result["players"]["1"], result["players"]["2"]
    p1_max = next(u for u in p1_after["board"] if u["id"] == "p1_shielded_max")
    assert p1_max["escudo"] == 0
    assert "p2_unshielded_max" in [u["id"] for u in p2_after["discard"]]
    return {"outcome": "partial_mixed", "blocked_target": "p1_shielded_max",
            "applied_target_removed": "p2_unshielded_max", "source_card_consumed": True}


def t19_relic_target_mode_and_instance_are_overloaded_in_one_string() -> dict:
    segment = GWENT_PY[GWENT_PY.find('elif skill == "reliquia_noite_chama"'):GWENT_PY.find('elif skill == "reliquia_lamina_negra"')]
    assert 'target_id == "noite"' in segment
    assert 'else:' in segment and 'max(alvos,key=lambda u:_poder_efetivo' in segment
    assert "target_id: str | None" in GWENT_PY
    return {"same_field_usage": ["unit/model target id", "mode choice noite"],
            "recommended_split": ["selection.target_instance_id", "selection.choice_id"]}


def t20_relic_options_are_returned_but_frontend_rebuilds_candidates() -> dict:
    route = BOT_PY[BOT_PY.find('"relic_options": opcoes_de_reliquia'):BOT_PY.find('"equipped_relic_id"', BOT_PY.find('"relic_options": opcoes_de_reliquia'))]
    relic_picker = APP_JS[APP_JS.find("function openGwentRelicPicker"):APP_JS.find("function replaceGwentArenaMarkup")]
    assert "relic_options" not in relic_picker
    assert "(enemy.board || []).filter(unit => unit.row === row)" in relic_picker
    assert route
    return {"server_serializes_relic_options": True, "frontend_consumes_them": False,
            "frontend_source": "opponent.board + client-side row filter"}


def t21_api_persists_only_successful_resolver_result_inside_db_transaction() -> dict:
    start = BOT_PY.find("async def _api_gwent_match_action")
    end = BOT_PY.find("async def ", start + 10)
    handler = BOT_PY[start:end]
    assert "async with self.db.transaction() as tx:" in handler
    assert handler.find('if "error" in result:') < handler.find('UPDATE cartas_gwent_matches SET status=?,state_json=?')
    assert "BEGIN IMMEDIATE" in DB_PY
    return {"db_transaction": "BEGIN IMMEDIATE", "error_path_before_state_update": True,
            "state_update_after_successful_resolver_only": True,
            "scope_limit": "single current implementation path; does not prove cross-process idempotency"}


def t22_api_and_client_do_not_send_operation_id_or_expected_revision() -> dict:
    start = BOT_PY.find("async def _api_gwent_match_action")
    end = BOT_PY.find("async def ", start + 10)
    handler = BOT_PY[start:end]
    send_start = APP_JS.find("async function sendGwentAction")
    send_end = APP_JS.find("\n}", send_start) + 2
    sender = APP_JS[send_start:send_end]
    assert "operation_id" not in handler and "expected_revision" not in handler
    assert "operation_id" not in sender and "expected_revision" not in sender
    assert "gwentActionInFlight" in sender
    return {"operation_id_in_request": False, "expected_revision_in_request": False,
            "client_duplicate_click_guard": True,
            "classification": "Group E persistence/idempotency gap, not resolved by client guard"}


def t23_v4_protection_grants_have_no_selection_policy_field() -> dict:
    schema = json.loads((ROOT / "docs" / "schemas" / "card-game-card-instance-match.schema.v4.json").read_text(encoding="utf-8"))
    blob = json.dumps(schema, ensure_ascii=False)
    assert "protection_grants" in blob
    protection_section = blob[blob.find('"protection_grants"'):]
    # The v4 shape models grants but does not bind the choice among multiple compatible grants.
    assert "selection_policy_id" not in protection_section
    assert "priority" not in protection_section
    return {"protection_grants_exist": True, "grant_selection_order_defined": False,
            "group_C_gap_confirmed_for_group_D": True}


CASES = [
    ("DSEL-001", "Rejeição de alvo inválido sem mutação", t01_rejected_invalid_target_is_non_mutating, "Aplicar uma operação em working copy e descartar todo o plano quando a validação falha."),
    ("DSEL-002", "Ausência de alvo obrigatório rejeita sem consumir carta", t02_required_target_absence_rejects_without_consuming_source, "Sem alvo obrigatório, nenhuma carta, recurso ou turno é consumido."),
    ("DSEL-003", "Alvo é revalidado no servidor", t03_manual_target_is_revalidated_after_options_are_read, "A oferta visual não autoriza um alvo fora do escopo no momento da submissão."),
    ("DSEL-004", "Resumo público não carrega identidade física", t04_target_summary_is_not_physical_identity, "O legado usa id de modelo; o contrato futuro deve usar instance_id."),
    ("DSEL-005", "Fallback automático da Execução", t05_auto_execution_uses_lowest_effective_power, "A Execução automática escolhe o menor poder efetivo elegível na fileira."),
    ("DSEL-006", "Fallback automático da Égide", t06_auto_egide_uses_highest_effective_power, "A Égide automática escolhe o maior poder efetivo entre aliados protegíveis."),
    ("DSEL-007", "Fallback automático do Passo", t07_auto_passo_uses_lowest_effective_power, "O Passo automático escolhe o menor poder efetivo entre aliados móveis."),
    ("DSEL-008", "Quantidade de alvos da Égide depende de raridade no legado", t08_egide_target_count_changes_with_rarity_in_legacy, "Evidência de conflito com BUF-001; nova cardinalidade precisa ser parâmetro explícito, não raridade."),
    ("DSEL-009", "Quantidade de alvos do Passo depende de raridade no legado", t09_passo_target_count_changes_with_rarity_in_legacy, "Evidência de conflito com BUF-001; alvo secundário precisa ser declarado e mostrado."),
    ("DSEL-010", "Efeito de até dois alvos aceita um único alvo", t10_leader_up_to_two_allows_single_available_target, "Contagem máxima e mínima são conceitos separados; uma política up_to pode aceitar um alvo."),
    ("DSEL-011", "Líder sem alvo elegível é rejeitado", t11_empty_leader_scope_is_rejected_without_leader_cost, "Rejeição preserva uso do líder e snapshot de entrada."),
    ("DSEL-012", "Chama sem Geada é consumida sem efeito", t12_chama_with_no_geada_is_consumed_without_target_mutation, "Há efeitos legados de consumo válido sem mudança no alvo."),
    ("DSEL-013", "Muralha em fileira vazia é consumida sem efeito", t13_muralha_empty_selected_row_is_consumed_without_buff, "No-op pode ser aceito em alguns handlers; não é comportamento universal."),
    ("DSEL-014", "Algemas em bônus zero consome a relíquia", t14_algemas_zero_bonus_is_consumed_no_effect, "O legado aceita alvo sem bônus positivo e consome a ativação."),
    ("DSEL-015", "Lâmina Negra bloqueada separa escudo, relíquia e turno", t15_lamina_block_consumes_shield_but_not_relic_activation, "O escudo e o turno são consumidos; a ativação de uso único da relíquia não."),
    ("DSEL-016", "Noite/Chama bloqueada consome ativação", t16_noite_chama_block_consumes_shield_and_activation, "O escudo, o turno e a ativação são consumidos quando a Chama é bloqueada."),
    ("DSEL-017", "Execução bloqueada consome carta e turno", t17_execution_block_consumes_card_and_turn_but_not_target, "Bloqueio é resultado aceito da ação, não rejeição da operação."),
    ("DSEL-018", "Área pode produzir resultado misto", t18_aoe_can_have_mixed_applied_and_blocked_targets, "Resultados devem ser registrados por alvo; status global pode ser partial."),
    ("DSEL-019", "Campo target_id mistura identidade e escolha de modo", t19_relic_target_mode_and_instance_are_overloaded_in_one_string, "O novo request separa target_instance_id de choice_id/mode_id."),
    ("DSEL-020", "Frontend reconstrói opções de relíquia", t20_relic_options_are_returned_but_frontend_rebuilds_candidates, "A fonte de verdade de candidatos deve ser o servidor; cliente só apresenta."),
    ("DSEL-021", "A API só persiste resultado sem erro dentro de transação", t21_api_persists_only_successful_resolver_result_inside_db_transaction, "Há atomicidade local do update de snapshot no endpoint atual; replay/idempotência cross-process pertencem ao Grupo E."),
    ("DSEL-022", "API não envia operation_id nem expected_revision", t22_api_and_client_do_not_send_operation_id_or_expected_revision, "O bloqueio de clique no browser não substitui idempotência persistente nem revisão esperada."),
    ("DSEL-023", "V4 não declara desempate entre grants compatíveis", t23_v4_protection_grants_have_no_selection_policy_field, "A escolha de uma carga de proteção entre várias grants precisa de política versionada."),
]


def main() -> int:
    for case in CASES:
        check(*case)
    passed = sum(r["status"] == "PASS" for r in RESULTS)
    failed = len(RESULTS) - passed
    payload = {
        "audit": "card_game_selection_group_D",
        "version": "0.1",
        "date": "2026-11-27",
        "status": "READ_ONLY_LEGACY_AUDIT; RESOLUTIONS_CANDIDATE_NOT_APPROVED",
        "baseline": "soulsbo-main-continuity-2026-11-27-rev11.zip",
        "total": len(RESULTS),
        "passed": passed,
        "failed": failed,
        "cases": RESULTS,
        "scope_note": (
            "Fixtures chamam funções reais do runtime legado e verificações estáticas pontuais de frontend/API/DB. "
            "Não são testes de browser real, rede, banco concorrente, replay, integração nem produção. "
            "Casos de raridade registram conflito legado com BUF-001 aprovado; não aprovam esse comportamento."
        ),
        "runtime_modified": False,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for item in RESULTS:
        marker = "PASS" if item["status"] == "PASS" else "FAIL"
        print(f"[{marker}] {item['id']} — {item['title']}")
        if item.get("error"):
            print(f"       {item['error']}")
    print(f"\nResultado: {passed}/{len(RESULTS)}; {failed} falhas.")
    print(f"JSON: {OUT.relative_to(ROOT)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

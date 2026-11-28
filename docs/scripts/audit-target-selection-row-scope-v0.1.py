#!/usr/bin/env python3
"""Auditoria read-only de seleção de alvos e escopo de fileira no motor legado.

Executar da raiz do repositório:
    python docs/scripts/audit-target-selection-row-scope-v0.1.py

As fixtures chamam funções reais de sistemas.gwent. Nenhum arquivo funcional é alterado.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sistemas.gwent import (  # noqa: E402
    ROWS,
    CARD_IDENTITY_ABILITIES,
    _aplicar_habilidade_identidade,
    _poder_efetivo,
    aplicar_jogada,
)

RESULTS: list[dict] = []


def unit(uid: str, power: int, *, bonus: int = 0, row: str = "melee",
         fileira: str | None = None, shield: int = 0, **extra) -> dict:
    item = {
        "id": uid,
        "nome": uid,
        "categoria": "Unidade",
        "especial": False,
        "poder": power,
        "bonus": bonus,
        "row": row,
        "fileira": fileira if fileira is not None else row,
        "escudo": shield,
        "weather_resist": 0,
        "sangramento": 0,
        "geada": 0,
        "podrida": 0,
        "loucura": 0,
        "faccao": "Ordem Áurea",
    }
    item.update(extra)
    return item


def identity(card_id: str, allies: list[dict], enemies: list[dict], *, row: str = "melee",
             weather: dict | None = None, power: int = 1, bonus: int = 0) -> tuple[dict, dict, dict]:
    player = {"board": allies, "discard": [], "last_row": None}
    other = {"board": enemies, "discard": [], "last_row": None}
    card = {"id": card_id, "nome": card_id, "poder": power, "bonus": bonus, "faccao": "Ordem Áurea"}
    state = {"weather": weather or {r: 0 for r in ROWS}}
    if card_id not in CARD_IDENTITY_ABILITIES:
        raise AssertionError(f"{card_id} não possui vínculo de identidade ativo após o filtro V18")
    _aplicar_habilidade_identidade(player, other, card, state, row)
    return player, other, card


def leader_state(leader_id: str, faction: str, own_board: list[dict], enemy_board: list[dict], *, row: str) -> dict:
    """Cria estado mínimo válido para exercitar a ação real de líder."""
    return {
        "match_id": 9001,
        "status": "active",
        "phase": "battle",
        "round": 1,
        "turn": "1",
        "round_starter": "1",
        "weather": {r: 0 for r in ROWS},
        "crowns": {"1": 0, "2": 0},
        "rounds": [],
        "winner_id": None,
        "last_event": "",
        "event_log": [],
        "players": {
            "1": {
                "hand": [unit("filler", 1)], "draw_pile": [], "discard": [],
                "board": own_board, "passed": False, "leader_used": False,
                "weather_used": False, "faction": faction, "leader_id": leader_id,
                "leader_name": leader_id, "faction_boost_used": False,
                "mulligan_done": True, "last_row": None, "synergy_used": {},
                "baixas": 0, "relic_used": False,
            },
            "2": {
                "hand": [unit("enemy_filler", 1)], "draw_pile": [], "discard": [],
                "board": enemy_board, "passed": False, "leader_used": False,
                "weather_used": False, "faction": "Véu Carmesim", "leader_id": "mestre_veu",
                "leader_name": "Mohg", "faction_boost_used": False,
                "mulligan_done": True, "last_row": None, "synergy_used": {},
                "baixas": 0, "relic_used": False,
            },
        },
        "_requested_row": row,
    }


def case(case_id: str, title: str, fn: Callable[[], None], observation: str) -> None:
    try:
        fn()
        RESULTS.append({"id": case_id, "title": title, "status": "PASS", "observation": observation})
    except Exception as exc:  # pragma: no cover - relatório precisa capturar qualquer falha
        RESULTS.append({"id": case_id, "title": title, "status": "FAIL", "observation": observation,
                        "error": f"{type(exc).__name__}: {exc}"})


def test_effective_power_components():
    u = unit("calc", 8, bonus=2, row="melee", geada=1, podrida=1, loucura=1)
    assert _poder_efetivo(u, {"melee": 2}) == 5  # 8 + 2 - clima 2 - estados 3
    assert _poder_efetivo(u, {"melee": 9}) == 1  # piso mínimo


def test_global_strongest_uses_effective_power():
    a = unit("high-base", 10, row="melee")
    b = unit("effective-winner", 8, bonus=1, row="siege")
    _, _, _ = identity("chefe_dama_vazio", [], [a, b], weather={"melee": 5, "ranged": 0, "siege": 0})
    assert a["bonus"] == 0
    assert b["bonus"] == -1  # bônus inicial +1, reduzido em 2


def test_max_tie_uses_first_board_order():
    a = unit("first", 6)
    b = unit("second", 6)
    identity("chefe_dama_vazio", [], [a, b])
    assert a["bonus"] == -2 and b["bonus"] == 0


def test_golden_vow_chooses_weakest_effective_same_row():
    weakest_effective = unit("weakest-effective", 5, row="melee")
    stronger_effective = unit("stronger-effective", 6, row="melee")
    other_row = unit("other-row", 1, row="siege")
    identity("gwent_v75_ordem_veterano_juramento",
             [weakest_effective, stronger_effective, other_row], [], row="melee",
             weather={"melee": 3, "ranged": 0, "siege": 0})
    assert weakest_effective["bonus"] == 1
    assert stronger_effective["bonus"] == 0 and other_row["bonus"] == 0


def test_blood_mark_uses_current_row_and_effective_power():
    moved_out = unit("moved-out", 15, row="ranged", fileira="melee")
    moved_in = unit("moved-in", 7, bonus=2, row="melee", fileira="ranged")
    weaker = unit("weaker", 8, row="melee", fileira="melee", geada=2)
    identity("gwent_v75_veu_acolito_sangue", [], [moved_out, moved_in, weaker], row="melee")
    assert moved_in["sangramento"] == 1
    assert moved_out["sangramento"] == 0 and weaker["sangramento"] == 0


def test_gravity_shear_filters_positive_and_ranks_bonus():
    a = unit("bonus-4", 1, bonus=4)
    b = unit("bonus-3", 10, bonus=3)
    c = unit("high-power-no-bonus", 15, bonus=0)
    _, _, card = identity("gwent_v75_lua_graviturgista", [], [a, b, c])
    assert a["bonus"] == 3 and b["bonus"] == 2 and c["bonus"] == 0
    assert card["bonus"] == 1


def test_blood_price_chooses_weakest_effective_same_row_and_caps_gain():
    weakest = unit("weakest-effective", 8, bonus=0, row="melee", geada=1)
    stronger = unit("stronger", 10, row="melee")
    other_row = unit("other-row", 1, row="siege")
    player, _, card = identity("gwent_v75_veu_carrasco_preco", [weakest, stronger, other_row], [], row="melee")
    # Sacrifice removes only the selected weakest same-row unit; gain uses effective power.
    assert card["bonus"] == 3  # poder efetivo 7, ganho limitado a +3
    assert weakest not in player["board"]
    assert stronger in player["board"] and other_row in player["board"]


def test_grace_mender_filters_status_then_picks_two_weakest():
    weakest_marked = unit("weakest-marked", 4, row="melee", geada=1)
    second_marked = unit("second-marked", 6, row="melee", sangramento=1)
    third_marked = unit("third-marked", 8, row="melee", podrida=1)
    unmarked = unit("unmarked", 1, row="melee")
    identity("gwent_v75_ordem_confessora_graca",
             [weakest_marked, second_marked, third_marked, unmarked], [], row="melee")
    assert weakest_marked["geada"] == 0 and weakest_marked["bonus"] == 1
    assert second_marked["sangramento"] == 0 and second_marked["bonus"] == 1
    assert third_marked["podrida"] == 1 and third_marked["bonus"] == 0
    assert unmarked["bonus"] == 0


def test_grace_mender_fallback_chooses_weakest_when_no_status_target():
    weak = unit("weak", 2, row="melee")
    strong = unit("strong", 8, row="melee")
    identity("gwent_v75_ordem_confessora_graca", [weak, strong], [], row="melee")
    assert weak["bonus"] == 1 and strong["bonus"] == 0


def test_grace_mender_fallback_buffs_card_when_row_empty():
    _, _, card = identity("gwent_v75_ordem_confessora_graca", [], [], row="melee")
    assert card["bonus"] == 1


def test_star_gravity_selects_global_effective_max_and_changes_current_row():
    strongest = unit("strongest", 8, bonus=1, row="siege", fileira="siege")
    other = unit("other", 10, row="melee")
    _, _, _card = identity("chefe_radahn_flagelo_estrelas", [], [strongest, other], row="ranged",
                           weather={"melee": 5, "ranged": 0, "siege": 0})
    assert strongest["row"] == "ranged" and strongest["fileira"] == "siege"
    assert strongest["bonus"] == -1 and other["bonus"] == 0


def test_morgott_picks_two_strongest_unshielded_in_selected_current_row():
    own = [
        unit("shielded-strongest", 15, row="melee", shield=1),
        unit("first-eligible", 10, row="melee"),
        unit("second-eligible", 8, row="melee"),
        unit("other-row", 20, row="siege"),
    ]
    state = leader_state("bastiao_ancestral", "Ordem Áurea", own, [], row="melee")
    result = aplicar_jogada(state, 1, action="leader", row="melee")
    assert "error" not in result
    board = result["state"]["players"]["1"]["board"]
    assert board[1]["escudo"] == 1 and board[2]["escudo"] == 1
    assert board[0]["escudo"] == 1 and board[3]["escudo"] == 0


def test_mohg_picks_two_strongest_in_selected_row():
    enemies = [
        unit("ranged-strongest", 20, row="ranged"),
        unit("melee-first", 9, row="melee"),
        unit("melee-second", 8, row="melee"),
        unit("melee-third", 2, row="melee"),
    ]
    state = leader_state("mestre_veu", "Véu Carmesim", [], enemies, row="melee")
    result = aplicar_jogada(state, 1, action="leader", row="melee")
    assert "error" not in result
    board = result["state"]["players"]["2"]["board"]
    assert board[1]["sangramento"] == 1 and board[2]["sangramento"] == 1
    assert board[0]["sangramento"] == 0 and board[3]["sangramento"] == 0


def test_astel_caps_to_three_strongest_in_selected_row():
    enemies = [
        unit("wrong-row", 20, row="siege"),
        unit("melee-a", 10, row="melee"),
        unit("melee-b", 9, row="melee"),
        unit("melee-c", 8, row="melee"),
        unit("melee-d", 7, row="melee"),
    ]
    state = leader_state("mestre_eclipse", "Lua Negra", [], enemies, row="melee")
    # Use a Lua Negra player and retain a valid opposing player in the state.
    result = aplicar_jogada(state, 1, action="leader", row="melee")
    assert "error" not in result
    board = result["state"]["players"]["2"]["board"]
    assert [u["geada"] for u in board] == [0, 1, 1, 1, 0]


def test_loretta_picks_two_strongest_in_fixed_ranged_row():
    own = [unit("ranged-a", 9, row="ranged"), unit("ranged-b", 8, row="ranged"),
           unit("ranged-c", 1, row="ranged"), unit("melee-high", 20, row="melee")]
    state = leader_state("oraculo_tempestade", "Lua Negra", own, [], row="ranged")
    result = aplicar_jogada(state, 1, action="leader", row="ranged")
    assert "error" not in result
    board = result["state"]["players"]["1"]["board"]
    assert [u["bonus"] for u in board] == [2, 2, 0, 0]


CASES = [
    ("TGT-001", "Poder efetivo", test_effective_power_components, "Poder efetivo usa bônus, clima e estados; o cap agregado de estados é 3 e o piso é 1."),
    ("TGT-002", "Maior poder global", test_global_strongest_uses_effective_power, "Fenda do Vazio procura o maior poder efetivo em todo o campo inimigo, não apenas na fileira escolhida."),
    ("TGT-003", "Desempate de máximo", test_max_tie_uses_first_board_order, "Em empate de max(), vence a primeira instância na ordem atual do tabuleiro."),
    ("TGT-004", "Menor aliado na mesma fileira", test_golden_vow_chooses_weakest_effective_same_row, "Juramento Dourado filtra pela row corrente e escolhe o menor poder efetivo entre aliados dessa fileira."),
    ("TGT-005", "Marca por fileira corrente", test_blood_mark_uses_current_row_and_effective_power, "Marca da Dinastia usa row corrente, não fileira-base, e escolhe o maior poder efetivo."),
    ("TGT-006", "Cisalhamento por bônus", test_gravity_shear_filters_positive_and_ranks_bonus, "Cisalhamento filtra bônus positivo e ranqueia pelo bônus bruto, não pelo poder efetivo."),
    ("TGT-007", "Sacrifício pelo menor poder efetivo", test_blood_price_chooses_weakest_effective_same_row_and_caps_gain, "Preço em Sangue escolhe a unidade mais fraca por poder efetivo na fileira corrente e limita o ganho a +3."),
    ("TGT-008", "Purificação com seleção", test_grace_mender_filters_status_then_picks_two_weakest, "Regressão Serena filtra unidades com status na fileira e escolhe até duas de menor poder efetivo."),
    ("TGT-009", "Fallback da purificação", test_grace_mender_fallback_chooses_weakest_when_no_status_target, "Sem status elegível, Regressão Serena fortalece o aliado mais fraco da fileira corrente."),
    ("TGT-010", "Fallback sem aliados", test_grace_mender_fallback_buffs_card_when_row_empty, "Sem status elegível nem aliado na fileira, o próprio portador recebe +1."),
    ("TGT-011", "Gravidade e posição corrente", test_star_gravity_selects_global_effective_max_and_changes_current_row, "Gravidade do Flagelo seleciona o maior poder efetivo global, move a unidade e mantém a referência fileira-base separada."),
    ("TGT-012", "Alvos de Morgott", test_morgott_picks_two_strongest_unshielded_in_selected_current_row, "Morgott seleciona até dois aliados sem escudo na fileira escolhida em ordem decrescente de poder efetivo."),
    ("TGT-013", "Alvos de Mohg", test_mohg_picks_two_strongest_in_selected_row, "Mohg escolhe os dois inimigos mais fortes da fileira escolhida por poder efetivo."),
    ("TGT-014", "Alvos de Astel", test_astel_caps_to_three_strongest_in_selected_row, "Astel aplica Geada a no máximo três inimigos de maior poder efetivo na fileira escolhida."),
    ("TGT-015", "Alvos de Loretta", test_loretta_picks_two_strongest_in_fixed_ranged_row, "Loretta exige Longa Distância e fortalece as duas unidades de maior poder efetivo nessa fileira."),
]

def main() -> int:
    for item in CASES:
        case(*item)
    passed = sum(r["status"] == "PASS" for r in RESULTS)
    failed = len(RESULTS) - passed
    payload = {
        "audit": "target_selection_row_scope",
        "version": "0.1",
        "status": "READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED",
        "total": len(RESULTS),
        "passed": passed,
        "failed": failed,
        "cases": RESULTS,
        "scope_note": "Fixtures sintéticas chamam funções reais do motor; não validam partidas completas, UI, persistência ou balanceamento.",
    }
    root = ROOT
    out = root / "docs" / "card-game-target-selection-row-scope-audit-v0.1.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for result in RESULTS:
        marker = "PASS" if result["status"] == "PASS" else "FAIL"
        print(f"[{marker}] {result['id']} — {result['title']}")
        if result.get("error"):
            print(f"       {result['error']}")
    print(f"\nResultado: {passed}/{len(RESULTS)} aprovadas; {failed} falhas.")
    print(f"JSON: {out.relative_to(root)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

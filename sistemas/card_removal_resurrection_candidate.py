"""Resolvedor candidato de remoção, sacrifício e ressurreição.

Este módulo é uma especificação executável isolada para revisão. Não é importado
por `sistemas.gwent` e não altera partidas do runtime legado.

Os campos canônicos usados aqui são `kind`, `power_base`, `instance_id`,
`effect_ids`, `row`, `bonus`, `shield` e os quatro contadores de estado.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "card_game" / "removal-resurrection-registry-candidate.v1.json"
STATUS_FIELDS = ("sangramento", "geada", "podrida", "loucura")
REMOVAL_CAUSES = {"normal_removal", "execution", "sacrifice"}
VALID_ROWS = {"melee", "ranged", "siege"}


class RemovalResurrectionError(ValueError):
    """Dados de remoção/ressurreição inválidos ou ambíguos."""


@dataclass(frozen=True, slots=True)
class RemovalResult:
    removed: bool
    blocked_by_shield: bool
    cause: str
    unit_id: str | None
    vengeance_targets: int
    message: str


@dataclass(frozen=True, slots=True)
class ResurrectionResult:
    resurrected: dict[str, Any]
    removed_discard_index: int
    selected_by: str
    destination: str


def load_registry(path: Path | str = REGISTRY_PATH) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RemovalResurrectionError(f"Não foi possível carregar o registry: {exc}") from exc
    validate_registry(data)
    return data


def validate_registry(registry: Mapping[str, Any]) -> None:
    if not isinstance(registry, Mapping) or registry.get("schema_version") != 1:
        raise RemovalResurrectionError("schema_version deve ser 1")
    if registry.get("status") != "CANDIDATE_FOR_REVIEW_NOT_APPROVED":
        raise RemovalResurrectionError("O registry deve permanecer explicitamente candidato")
    policy = registry.get("removal_policy")
    if not isinstance(policy, Mapping):
        raise RemovalResurrectionError("removal_policy deve ser um objeto")
    causes = policy.get("causes")
    if not isinstance(causes, list):
        raise RemovalResurrectionError("removal_policy.causes deve ser uma lista")
    cause_ids = [item.get("cause_id") for item in causes if isinstance(item, Mapping)]
    if set(cause_ids) != REMOVAL_CAUSES or len(cause_ids) != len(REMOVAL_CAUSES):
        raise RemovalResurrectionError("Causas devem ser normal_removal, execution e sacrifice")
    assignments = registry.get("assignments")
    if not isinstance(assignments, list) or not assignments:
        raise RemovalResurrectionError("assignments deve ser uma lista não vazia")
    ids = [item.get("assignment_id") for item in assignments if isinstance(item, Mapping)]
    if len(ids) != len(assignments) or len(ids) != len(set(ids)):
        raise RemovalResurrectionError("assignment_id ausente, inválido ou duplicado")
    recommendations = registry.get("candidate_recommendations")
    if not isinstance(recommendations, Mapping):
        raise RemovalResurrectionError("candidate_recommendations deve ser um objeto")


def _card_identifier(unit: Mapping[str, Any]) -> str | None:
    value = unit.get("instance_id") or unit.get("id")
    return str(value) if value is not None else None


def _has_vengeance(unit: Mapping[str, Any]) -> bool:
    """Resolve Vingança pelo contrato canônico singular ou pelo alias legado."""
    effect_ids = unit.get("effect_ids") or []
    return (
        unit.get("effect_id") == "effect.vengeance_on_removal"
        or "effect.vengeance_on_removal" in effect_ids  # compatibilidade de fixture/alias antigo
        or unit.get("habilidade") == "vinganca"
    )


def attempt_removal(
    side: MutableMapping[str, Any],
    unit: MutableMapping[str, Any],
    cause: str,
) -> RemovalResult:
    """Tenta retirar uma unidade do campo segundo a política candidata.

    Remoção comum e execução consomem um escudo e falham; sacrifício ignora
    escudo. Uma remoção bem-sucedida limpa estados, vai ao descarte, incrementa
    `baixas` e dispara Vingança uma única vez.
    """
    if cause not in REMOVAL_CAUSES:
        raise RemovalResurrectionError(f"Causa de remoção desconhecida: {cause}")
    board = side.get("board")
    if not isinstance(side, MutableMapping) or not isinstance(unit, MutableMapping):
        raise RemovalResurrectionError("side e unit devem ser objetos mutáveis")
    if not isinstance(board, list):
        raise RemovalResurrectionError("side.board deve ser uma lista")
    discard = side.get("discard")
    if discard is None:
        discard = []
    if not isinstance(discard, list):
        raise RemovalResurrectionError("side.discard deve ser uma lista")
    index = next((i for i, candidate in enumerate(board) if candidate is unit), None)
    if index is None:
        return RemovalResult(False, False, cause, _card_identifier(unit), 0, "unit_not_on_board")

    shield = max(0, int(unit.get("shield", unit.get("escudo", 0)) or 0))
    if cause != "sacrifice" and shield > 0:
        if "shield" in unit:
            unit["shield"] = shield - 1
        else:
            unit["escudo"] = shield - 1
        return RemovalResult(False, True, cause, _card_identifier(unit), 0, "blocked_by_shield")

    removed_count = int(side.get("baixas", 0) or 0) + 1
    board.pop(index)
    unit.pop("shield", None)
    unit.pop("escudo", None)
    for field in STATUS_FIELDS:
        unit[field] = 0
    if "discard" not in side:
        side["discard"] = discard
    discard.append(unit)
    side["baixas"] = removed_count

    vengeance_targets = 0
    if _has_vengeance(unit):
        row = unit.get("row")
        for ally in board:
            if ally.get("row") == row:
                ally["bonus"] = int(ally.get("bonus", 0) or 0) + 1
                vengeance_targets += 1

    return RemovalResult(
        True,
        False,
        cause,
        _card_identifier(unit),
        vengeance_targets,
        "removed",
    )


def _power_base(card: Mapping[str, Any]) -> int:
    value = card.get("power_base", card.get("poder"))
    if isinstance(value, bool) or not isinstance(value, int):
        raise RemovalResurrectionError("Carta do descarte precisa ter poder-base inteiro")
    return value


def _is_canonical_unit(card: Mapping[str, Any]) -> bool:
    return card.get("kind") == "unit"


def _eligible_indices(discard: Sequence[Mapping[str, Any]], max_power: int) -> list[int]:
    return [
        index
        for index, card in enumerate(discard)
        if isinstance(card, Mapping)
        and _is_canonical_unit(card)
        and _power_base(card) <= max_power
    ]


def _resolve_selected_index(
    discard: Sequence[Mapping[str, Any]],
    eligible: list[int],
    *,
    target_instance_id: str | None,
    target_card_id: str | None,
    selection: str,
) -> tuple[int, str]:
    if target_instance_id is not None:
        matches = [i for i in eligible if str(discard[i].get("instance_id")) == str(target_instance_id)]
        if len(matches) != 1:
            raise RemovalResurrectionError("instance_id não identifica exatamente uma unidade elegível")
        return matches[0], "target_instance_id"
    if target_card_id is not None:
        matches = [i for i in eligible if str(discard[i].get("card_id", discard[i].get("id"))) == str(target_card_id)]
        if len(matches) != 1:
            raise RemovalResurrectionError("card_id é ambíguo ou não corresponde a uma unidade elegível")
        return matches[0], "unique_legacy_card_id"
    if not eligible:
        raise RemovalResurrectionError("Não existe unidade elegível no descarte")
    if selection == "strongest":
        chosen = max(eligible, key=lambda i: _power_base(discard[i]))
        return chosen, "strongest_first_tie_in_discard_order"
    if selection == "last":
        return eligible[-1], "last_eligible_in_discard_order"
    if selection == "first":
        return eligible[0], "first_eligible_in_discard_order"
    raise RemovalResurrectionError(f"Modo de seleção não suportado: {selection}")


def resurrect_from_discard(
    side: MutableMapping[str, Any],
    *,
    max_power: int,
    row: str,
    entry_bonus_mode: str = "reset_to_zero",
    row_mode: str = "preserve_if_valid_else_fallback",
    selection: str = "strongest",
    target_instance_id: str | None = None,
    target_card_id: str | None = None,
) -> ResurrectionResult:
    """Ressuscita uma unidade elegível removendo uma única cópia do descarte.

    A unidade devolvida não dispara on-play, passiva de facção ou combo ao
    entrar. Estado temporário e escudo são sempre normalizados.
    """
    if isinstance(max_power, bool) or not isinstance(max_power, int) or max_power < 1:
        raise RemovalResurrectionError("max_power deve ser inteiro positivo")
    if row not in VALID_ROWS:
        raise RemovalResurrectionError(f"row inválida: {row}")
    if entry_bonus_mode not in {"reset_to_zero", "add_one_to_existing_bonus", "preserve"}:
        raise RemovalResurrectionError(f"entry_bonus_mode não suportado: {entry_bonus_mode}")
    if row_mode not in {"preserve_if_valid_else_fallback", "force_selected_row"}:
        raise RemovalResurrectionError(f"row_mode não suportado: {row_mode}")
    discard = side.get("discard")
    board = side.get("board")
    if not isinstance(discard, list) or not isinstance(board, list):
        raise RemovalResurrectionError("side precisa conter listas discard e board")
    eligible = _eligible_indices(discard, max_power)
    chosen_index, selected_by = _resolve_selected_index(
        discard,
        eligible,
        target_instance_id=target_instance_id,
        target_card_id=target_card_id,
        selection=selection,
    )
    original = discard.pop(chosen_index)
    revived = deepcopy(original)

    old_bonus = int(revived.get("bonus", 0) or 0)
    if entry_bonus_mode == "reset_to_zero":
        revived["bonus"] = 0
    elif entry_bonus_mode == "add_one_to_existing_bonus":
        revived["bonus"] = old_bonus + 1
    else:
        revived["bonus"] = old_bonus

    revived.pop("shield", None)
    revived.pop("escudo", None)
    for field in STATUS_FIELDS:
        revived[field] = 0

    if row_mode == "force_selected_row":
        revived["row"] = row
    elif revived.get("row") not in VALID_ROWS:
        revived["row"] = row

    board.append(revived)
    return ResurrectionResult(
        resurrected=revived,
        removed_discard_index=chosen_index,
        selected_by=selected_by,
        destination="board",
    )


def recover_unit_to_hand(
    side: MutableMapping[str, Any],
    *,
    max_power: int,
    selection: str = "last",
    target_instance_id: str | None = None,
    target_card_id: str | None = None,
) -> dict[str, Any]:
    """Recupera uma unidade elegível para a mão sem normalizar seus campos.

    Mantém a semântica legada de retorno à mão: não é ressurreição e não
    limpa bônus/estados. O uso de ID físico evita remover cópias indevidas.
    """
    discard = side.get("discard")
    hand = side.get("hand")
    if not isinstance(discard, list) or not isinstance(hand, list):
        raise RemovalResurrectionError("side precisa conter listas discard e hand")
    eligible = _eligible_indices(discard, max_power)
    index, _selected_by = _resolve_selected_index(
        discard,
        eligible,
        target_instance_id=target_instance_id,
        target_card_id=target_card_id,
        selection=selection,
    )
    card = discard.pop(index)
    hand.append(card)
    return card

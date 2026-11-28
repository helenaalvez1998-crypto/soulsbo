"""Resolvedor de referência para os estados negativos do novo jogo de cartas.

Este módulo implementa a proposta candidata em
`data/card_game/status-registry-candidate.v1.json`.

IMPORTANTE: não é importado por `sistemas.gwent` e não altera partidas legadas.
A integração ao runtime só deve ocorrer após aprovação do registry e dos testes.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any, Mapping

REGISTRY_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "card_game"
    / "status-registry-candidate.v1.json"
)


class StatusRegistryError(ValueError):
    """Registry de estados inválido ou incompatível com o resolvedor candidato."""


@dataclass(frozen=True, slots=True)
class StatusApplicationResult:
    status_id: str
    marks_before: int
    marks_after: int
    marks_applied: int
    marks_wasted: int
    threshold_triggers: int
    bonus_before: int
    bonus_after: int


def load_registry(path: Path | str = REGISTRY_PATH) -> dict[str, Any]:
    """Carrega o registry candidato a partir do JSON versionado."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StatusRegistryError(f"Não foi possível carregar o registry: {exc}") from exc
    validate_registry(data)
    return data


def _status_index(registry: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    statuses = registry.get("statuses")
    if not isinstance(statuses, list):
        raise StatusRegistryError("registry.statuses deve ser uma lista")
    result: dict[str, Mapping[str, Any]] = {}
    for item in statuses:
        if not isinstance(item, Mapping):
            raise StatusRegistryError("Cada estado precisa ser um objeto")
        status_id = item.get("status_id")
        if not isinstance(status_id, str) or not status_id:
            raise StatusRegistryError("status_id inválido")
        if status_id in result:
            raise StatusRegistryError(f"status_id duplicado: {status_id}")
        result[status_id] = item
    return result


def validate_registry(registry: Mapping[str, Any]) -> None:
    """Valida as invariantes mecânicas exigidas pelo resolvedor candidato."""
    if not isinstance(registry, Mapping) or registry.get("schema_version") != 1:
        raise StatusRegistryError("schema_version deve ser 1")
    if registry.get("status") != "CANDIDATE_FOR_REVIEW_NOT_APPROVED":
        raise StatusRegistryError("O registry deve permanecer explicitamente candidato")
    statuses = _status_index(registry)
    expected = {
        "status.frost": ("geada", 1, "control_debuffs"),
        "status.scarlet_rot": ("podrida", 1, "control_debuffs"),
        "status.bleeding": ("sangramento", 0, None),
        "status.madness": ("loucura", 1, "control_debuffs"),
    }
    if set(statuses) != set(expected):
        raise StatusRegistryError("O registry deve declarar exatamente Geada, Podridão, Sangramento e Loucura")
    for status_id, (state_key, reduction, group) in expected.items():
        item = statuses[status_id]
        if item.get("state_key") != state_key:
            raise StatusRegistryError(f"{status_id}: state_key incompatível")
        if item.get("max_marks_per_unit") != 2:
            raise StatusRegistryError(f"{status_id}: máximo de marcas deve ser 2")
        power = item.get("effective_power", {})
        if power.get("per_mark_reduction") != reduction or power.get("reduction_group") != group:
            raise StatusRegistryError(f"{status_id}: regra de poder efetivo incompatível")
        threshold = item.get("threshold")
        if status_id == "status.frost":
            if threshold is not None:
                raise StatusRegistryError("Geada não possui consequência secundária no limiar")
        else:
            if not isinstance(threshold, Mapping) or threshold.get("marks") != 2:
                raise StatusRegistryError(f"{status_id}: limiar de duas marcas obrigatório")
            if threshold.get("trigger") != "on_transition_to_threshold":
                raise StatusRegistryError(f"{status_id}: a consequência precisa disparar na transição para duas marcas")
    global_rules = registry.get("global_rules", {})
    effective_power = global_rules.get("effective_power", {})
    if effective_power.get("control_status_keys") != ["geada", "podrida", "loucura"]:
        raise StatusRegistryError("A lista de estados que reduzem poder efetivo é inválida")
    if effective_power.get("control_status_penalty") != "min(3, sum(control_status_marks))":
        raise StatusRegistryError("O teto combinado de três pontos precisa ser explícito")
    if effective_power.get("bleeding_affects_effective_power") is not False:
        raise StatusRegistryError("Sangramento não pode reduzir poder efetivo por marca")
    if global_rules.get("rarity_scaling") is not False:
        raise StatusRegistryError("A proposta candidata não permite escala oculta por raridade")


def apply_status_marks(
    unit: dict[str, Any],
    registry: Mapping[str, Any],
    status_id: str,
    marks: int = 1,
) -> StatusApplicationResult:
    """Aplica marcas e executa a consequência somente ao cruzar o limiar.

    O resultado é mutável no dicionário `unit`, mas não altera outros sistemas.
    Marcas de Sangramento são consumidas ao atingir duas; os outros estados
    permanecem no limite até o encerramento da rodada ou purificação.
    """
    validate_registry(registry)
    if not isinstance(unit, dict):
        raise TypeError("unit deve ser um dicionário mutável")
    if isinstance(marks, bool) or not isinstance(marks, int) or marks < 0 or marks > 2:
        raise ValueError("marks deve ser inteiro entre 0 e 2")
    definitions = _status_index(registry)
    definition = definitions.get(status_id)
    if definition is None:
        raise StatusRegistryError(f"Estado desconhecido: {status_id}")

    key = str(definition["state_key"])
    maximum = int(definition["max_marks_per_unit"])
    before = max(0, min(maximum, int(unit.get(key, 0) or 0)))
    current = before
    bonus_before = int(unit.get("bonus", 0) or 0)
    bonus_after = bonus_before
    applied = 0
    wasted = 0
    trigger_count = 0
    threshold = definition.get("threshold")

    for _ in range(marks):
        if current >= maximum:
            wasted += 1
            continue
        current += 1
        applied += 1
        if isinstance(threshold, Mapping) and current == int(threshold["marks"]):
            trigger_count += 1
            action = threshold["action"]
            amount = int(threshold.get("amount") or 0)
            floor = int(threshold.get("floor") or 0)
            if action == "reduce_positive_bonus":
                if bonus_after > 0:
                    bonus_after = max(floor, bonus_after - amount)
            elif action == "reduce_bonus":
                bonus_after = max(floor, bonus_after - amount)
            elif action == "clear_positive_bonus":
                if bonus_after > 0:
                    bonus_after = 0
            else:
                raise StatusRegistryError(f"Ação de limiar não suportada: {action}")
            if bool(threshold.get("reset_marks")):
                current = 0

    unit[key] = current
    unit["bonus"] = bonus_after
    return StatusApplicationResult(
        status_id=status_id,
        marks_before=before,
        marks_after=current,
        marks_applied=applied,
        marks_wasted=wasted,
        threshold_triggers=trigger_count,
        bonus_before=bonus_before,
        bonus_after=bonus_after,
    )


def combined_control_penalty(unit: Mapping[str, Any], registry: Mapping[str, Any]) -> int:
    """Retorna a penalidade combinada de Geada, Podridão e Loucura, teto 3."""
    validate_registry(registry)
    rule = registry["global_rules"]["effective_power"]
    keys = rule["control_status_keys"]
    total = sum(max(0, int(unit.get(key, 0) or 0)) for key in keys)
    return min(int(rule["max_control_status_penalty"]), total)


def effective_power(
    unit: Mapping[str, Any],
    registry: Mapping[str, Any],
    *,
    weather_level: int = 0,
) -> int:
    """Calcula poder efetivo pelo contrato candidato (sem ler o motor legado)."""
    validate_registry(registry)
    if isinstance(weather_level, bool) or not isinstance(weather_level, int):
        raise ValueError("weather_level deve ser inteiro")
    weather_resist = max(0, int(unit.get("weather_resist", 0) or 0))
    climate_penalty = max(0, weather_level - weather_resist)
    control_penalty = combined_control_penalty(unit, registry)
    floor = int(registry["global_rules"]["effective_power"]["minimum_power"])
    return max(
        floor,
        int(unit.get("poder", unit.get("power_base", 0)) or 0)
        + int(unit.get("bonus", 0) or 0)
        - climate_penalty
        - control_penalty,
    )


def clear_statuses(
    unit: dict[str, Any], registry: Mapping[str, Any], status_ids: list[str] | None = None
) -> list[str]:
    """Limpa todos os estados ou apenas os IDs indicados; devolve os removidos."""
    validate_registry(registry)
    definitions = _status_index(registry)
    selected = list(definitions) if status_ids is None else status_ids
    removed: list[str] = []
    for status_id in selected:
        definition = definitions.get(status_id)
        if definition is None:
            raise StatusRegistryError(f"Estado desconhecido para purificação: {status_id}")
        key = str(definition["state_key"])
        if int(unit.get(key, 0) or 0) > 0:
            unit[key] = 0
            removed.append(status_id)
    return removed


def close_round_statuses(units: list[dict[str, Any]], registry: Mapping[str, Any]) -> int:
    """Expira todos os estados das unidades no fechamento da rodada."""
    count = 0
    for unit in units:
        count += len(clear_statuses(unit, registry))
    return count

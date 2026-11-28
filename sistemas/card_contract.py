"""Contrato canônico de dados do jogo de cartas (v1).

Este módulo é deliberadamente independente do motor legado (`sistemas.gwent`)
para que catálogo, API, deck builder e renderizador possam convergir para o mesmo
modelo sem importar efeitos ou estado de partida.

As regras numéricas de custo e raridade não são calculadas aqui: as fórmulas
propostas ainda não foram aprovadas. Este contrato valida apenas a estrutura e
as invariantes já confirmadas para a nova base.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
import re
from typing import Any, Iterable, Mapping

CARD_SCHEMA_VERSION = 1
MIN_PURE_RATIO = 0.30

FACTION_IDS = frozenset({
    "golden_order",
    "crimson_veil",
    "dark_moon",
    "the_forgotten",
})
CARD_KINDS = frozenset({"unit", "special", "relic"})
ROWS = frozenset({"melee", "ranged", "siege"})
RARITY_IDS = frozenset({
    "common", "rare", "epic", "legendary", "mythic", "primordial", "singular",
})
REQUIRED_CARD_FIELDS = frozenset({
    "schema_version", "card_id", "name", "title", "kind", "faction_id",
    "row", "power_base", "effect_id", "effect_params", "combo_tags",
    "lore", "art_version",
})
ALLOWED_CARD_FIELDS = REQUIRED_CARD_FIELDS | frozenset({"origin_id", "source_game"})


@dataclass(frozen=True, slots=True)
class CardContractResult:
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        return not self.errors


def is_pure_unit(card: Mapping[str, Any]) -> bool:
    """Carta pura não tem efeito individual nem participação em combo.

    A passiva global da facção não entra nesta classificação.
    """
    return (
        card.get("kind") == "unit"
        and card.get("effect_id") is None
        and card.get("effect_params") == {}
        and card.get("combo_tags") == []
    )


def minimum_pure_cards(model_count: int, ratio: float = MIN_PURE_RATIO) -> int:
    if isinstance(model_count, bool) or not isinstance(model_count, int) or model_count < 0:
        raise ValueError("model_count deve ser um inteiro não negativo")
    if not 0 < ratio <= 1:
        raise ValueError("ratio deve estar no intervalo (0, 1]")
    return ceil(model_count * ratio)


def _value_matches_parameter_type(value: Any, expected_type: str) -> bool:
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    return False


def _validate_effect_params(
    effect_params: Mapping[str, Any],
    effect_definition: Mapping[str, Any],
    *,
    prefix: str,
) -> list[str]:
    """Validate values against the parameter declarations of one effect."""
    errors: list[str] = []
    parameter_specs = effect_definition.get("parameters", {})
    required_parameters = effect_definition.get("required_parameters", [])
    allow_additional = effect_definition.get("allow_additional_parameters", False)

    if not isinstance(parameter_specs, Mapping):
        return [f"{prefix}: registry.parameters deve ser um objeto"]
    if not isinstance(required_parameters, list) or any(not isinstance(item, str) for item in required_parameters):
        return [f"{prefix}: registry.required_parameters deve ser lista de strings"]
    if not isinstance(allow_additional, bool):
        return [f"{prefix}: registry.allow_additional_parameters deve ser booleano"]

    unknown_required = sorted(set(required_parameters) - set(parameter_specs))
    if unknown_required:
        errors.append(f"{prefix}: parâmetros obrigatórios ausentes da declaração: {', '.join(unknown_required)}")

    missing = sorted(set(required_parameters) - set(effect_params))
    if missing:
        errors.append(f"{prefix}: parâmetros obrigatórios ausentes: {', '.join(missing)}")

    if not allow_additional:
        unknown = sorted(set(effect_params) - set(parameter_specs))
        if unknown:
            errors.append(f"{prefix}: parâmetros não declarados: {', '.join(unknown)}")

    for name, value in effect_params.items():
        spec = parameter_specs.get(name)
        if spec is None:
            continue
        if not isinstance(spec, Mapping):
            errors.append(f"{prefix}.{name}: spec do parâmetro deve ser objeto")
            continue
        expected_type = spec.get("type")
        if not isinstance(expected_type, str) or not _value_matches_parameter_type(value, expected_type):
            errors.append(f"{prefix}.{name}: tipo inválido; esperado {expected_type!r}")
            continue

        if expected_type in {"integer", "number"}:
            minimum = spec.get("minimum")
            maximum = spec.get("maximum")
            if isinstance(minimum, (int, float)) and not isinstance(minimum, bool) and value < minimum:
                errors.append(f"{prefix}.{name}: valor abaixo do mínimo {minimum}")
            if isinstance(maximum, (int, float)) and not isinstance(maximum, bool) and value > maximum:
                errors.append(f"{prefix}.{name}: valor acima do máximo {maximum}")
        elif expected_type == "string":
            min_length = spec.get("minLength")
            max_length = spec.get("maxLength")
            if isinstance(min_length, int) and len(value) < min_length:
                errors.append(f"{prefix}.{name}: string menor que {min_length} caracteres")
            if isinstance(max_length, int) and len(value) > max_length:
                errors.append(f"{prefix}.{name}: string maior que {max_length} caracteres")

        enum_values = spec.get("enum")
        if isinstance(enum_values, list) and value not in enum_values:
            errors.append(f"{prefix}.{name}: valor fora do enum permitido")

    return errors


def validate_effect_registry(registry: Mapping[str, Any]) -> CardContractResult:
    """Validate IDs, definitions and deterministic combo metadata in a registry."""
    errors: list[str] = []
    if not isinstance(registry, Mapping):
        return CardContractResult(("registry deve ser um objeto/dicionário",))

    version = registry.get("schema_version")
    if isinstance(version, bool) or not isinstance(version, int) or version != CARD_SCHEMA_VERSION:
        errors.append(f"registry.schema_version deve ser o inteiro {CARD_SCHEMA_VERSION}")

    effects = registry.get("effects")
    combos = registry.get("combos")
    if not isinstance(effects, list):
        errors.append("registry.effects deve ser uma lista")
        effects = []
    if not isinstance(combos, list):
        errors.append("registry.combos deve ser uma lista")
        combos = []

    seen_effects: set[str] = set()
    for index, effect in enumerate(effects):
        prefix = f"registry.effects[{index}]"
        if not isinstance(effect, Mapping):
            errors.append(f"{prefix}: efeito deve ser objeto")
            continue
        effect_id = effect.get("effect_id")
        if not isinstance(effect_id, str) or not re.fullmatch(r"effect\.[a-z0-9]+(?:_[a-z0-9]+)*", effect_id, flags=re.ASCII):
            errors.append(f"{prefix}.effect_id: use identificador effect.snake_case")
        elif effect_id in seen_effects:
            errors.append(f"effect_id duplicado: {effect_id}")
        else:
            seen_effects.add(effect_id)
        if not isinstance(effect.get("name"), str) or not effect.get("name", "").strip():
            errors.append(f"{prefix}.name: nome obrigatório")
        if not isinstance(effect.get("resolution_handler"), str) or not effect.get("resolution_handler", "").strip():
            errors.append(f"{prefix}.resolution_handler: handler obrigatório")
        if not isinstance(effect.get("timing"), str) or not effect.get("timing", "").strip():
            errors.append(f"{prefix}.timing: timing obrigatório")
        parameters = effect.get("parameters", {})
        if not isinstance(parameters, Mapping):
            errors.append(f"{prefix}.parameters deve ser objeto")
            continue
        required = effect.get("required_parameters", [])
        if not isinstance(required, list) or any(not isinstance(item, str) for item in required):
            errors.append(f"{prefix}.required_parameters deve ser lista de strings")
        elif len(required) != len(set(required)):
            errors.append(f"{prefix}.required_parameters não pode conter duplicatas")
        elif set(required) - set(parameters):
            errors.append(f"{prefix}.required_parameters referencia parâmetros inexistentes")
        if not isinstance(effect.get("allow_additional_parameters", False), bool):
            errors.append(f"{prefix}.allow_additional_parameters deve ser booleano")
        for param_name, spec in parameters.items():
            if not isinstance(param_name, str) or not isinstance(spec, Mapping):
                errors.append(f"{prefix}.parameters: cada declaração precisa de chave e objeto")
                continue
            param_type = spec.get("type")
            if not isinstance(param_type, str) or param_type not in {"integer", "number", "string", "boolean", "object", "array"}:
                errors.append(f"{prefix}.parameters.{param_name}: type não suportado")
                continue
            if param_type in {"integer", "number"}:
                for bound in ("minimum", "maximum"):
                    value = spec.get(bound)
                    if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
                        errors.append(f"{prefix}.parameters.{param_name}.{bound}: limite precisa ser numérico")
                minimum = spec.get("minimum")
                maximum = spec.get("maximum")
                if (
                    isinstance(minimum, (int, float)) and not isinstance(minimum, bool)
                    and isinstance(maximum, (int, float)) and not isinstance(maximum, bool)
                    and minimum > maximum
                ):
                    errors.append(f"{prefix}.parameters.{param_name}: mínimo maior que máximo")

    seen_combos: set[str] = set()
    priorities: set[int] = set()
    for index, combo in enumerate(combos):
        prefix = f"registry.combos[{index}]"
        if not isinstance(combo, Mapping):
            errors.append(f"{prefix}: combo deve ser objeto")
            continue
        combo_id = combo.get("combo_id")
        if not isinstance(combo_id, str) or not re.fullmatch(r"combo\.[a-z0-9]+(?:_[a-z0-9]+)*", combo_id, flags=re.ASCII):
            errors.append(f"{prefix}.combo_id: use identificador combo.snake_case")
        elif combo_id in seen_combos:
            errors.append(f"combo_id duplicado: {combo_id}")
        else:
            seen_combos.add(combo_id)
        if not isinstance(combo.get("name"), str) or not combo.get("name", "").strip():
            errors.append(f"{prefix}.name: nome obrigatório")
        tags = combo.get("required_tags")
        if not isinstance(tags, list) or not tags or any(not isinstance(tag, str) or not tag.strip() for tag in tags):
            errors.append(f"{prefix}.required_tags deve conter ao menos uma tag válida")
        elif len(tags) != len(set(tags)):
            errors.append(f"{prefix}.required_tags não pode conter duplicatas")
        minimum = combo.get("minimum_participants")
        if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 2:
            errors.append(f"{prefix}.minimum_participants deve ser inteiro >= 2")
        priority = combo.get("priority")
        if isinstance(priority, bool) or not isinstance(priority, int) or priority < 1:
            errors.append(f"{prefix}.priority deve ser inteiro positivo")
        elif priority in priorities:
            errors.append(f"priority duplicada: {priority}")
        else:
            priorities.add(priority)

    return CardContractResult(tuple(errors))


def validate_card_definition(
    card: Mapping[str, Any],
    *,
    known_effect_ids: Iterable[str] | None = None,
    known_combo_tags: Iterable[str] | None = None,
    effect_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> CardContractResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(card, Mapping):
        return CardContractResult(("card deve ser um objeto/dicionário",))

    missing = sorted(REQUIRED_CARD_FIELDS - set(card.keys()))
    unknown = sorted(set(card.keys()) - ALLOWED_CARD_FIELDS)
    if missing:
        errors.append(f"campos obrigatórios ausentes: {', '.join(missing)}")
    if unknown:
        errors.append(f"campos não reconhecidos: {', '.join(unknown)}")

    schema_version = card.get("schema_version")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int) or schema_version != CARD_SCHEMA_VERSION:
        errors.append(f"schema_version deve ser o inteiro {CARD_SCHEMA_VERSION}")

    card_id = card.get("card_id")
    if not isinstance(card_id, str) or not card_id or len(card_id) > 120:
        errors.append("card_id deve ser string não vazia de até 120 caracteres")
    elif not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", card_id, flags=re.ASCII):
        errors.append("card_id deve usar snake_case ASCII estável")

    name = card.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        errors.append("name deve ter entre 1 e 100 caracteres")

    title = card.get("title")
    if title is not None and (not isinstance(title, str) or len(title) > 80):
        errors.append("title deve ser null ou string de até 80 caracteres")

    kind = card.get("kind")
    kind_valid = isinstance(kind, str) and kind in CARD_KINDS
    if not kind_valid:
        errors.append(f"kind inválido; use um de: {', '.join(sorted(CARD_KINDS))}")

    faction_id = card.get("faction_id")
    if not isinstance(faction_id, str) or faction_id not in FACTION_IDS:
        errors.append(f"faction_id inválida; use um de: {', '.join(sorted(FACTION_IDS))}")

    row = card.get("row")
    power = card.get("power_base")
    if kind == "unit":
        if not isinstance(row, str) or row not in ROWS:
            errors.append("unidade precisa de row: melee, ranged ou siege")
        if isinstance(power, bool) or not isinstance(power, int) or not 1 <= power <= 15:
            errors.append("unidade precisa de power_base inteiro entre 1 e 15")
    elif isinstance(kind, str) and kind in {"special", "relic"}:
        if row is not None:
            errors.append("special/relic deve usar row=null")
        if power is not None:
            errors.append("special/relic deve usar power_base=null; não usar 0 como poder de combate")

    effect_id = card.get("effect_id")
    effect_params = card.get("effect_params")
    if effect_id is not None and (not isinstance(effect_id, str) or not effect_id.strip()):
        errors.append("effect_id deve ser null ou string não vazia")
    if not isinstance(effect_params, dict):
        errors.append("effect_params deve ser objeto/dicionário")
    elif effect_id is None and effect_params:
        errors.append("effect_params deve ser vazio quando effect_id=null")
    if isinstance(kind, str) and kind in {"special", "relic"} and effect_id is None:
        errors.append("special/relic precisa declarar effect_id")
    known_effect_id_set = set(known_effect_ids) if known_effect_ids is not None else None
    if isinstance(effect_id, str) and effect_id and known_effect_id_set is not None and effect_id not in known_effect_id_set:
        errors.append(f"effect_id sem definição no registry: {effect_id}")
    if isinstance(effect_id, str) and effect_id and effect_registry is not None:
        definition = effect_registry.get(effect_id)
        if definition is None:
            errors.append(f"effect_id sem definição de parâmetros: {effect_id}")
        elif isinstance(effect_params, dict):
            errors.extend(_validate_effect_params(effect_params, definition, prefix=f"effect_params[{effect_id}]"))

    tags = card.get("combo_tags")
    if not isinstance(tags, list) or any(not isinstance(tag, str) or not tag.strip() for tag in tags):
        errors.append("combo_tags deve ser lista de strings não vazias")
    elif len(tags) != len(set(tags)):
        errors.append("combo_tags não pode conter duplicatas")
    elif known_combo_tags is not None:
        unknown_tags = sorted(set(tags) - set(known_combo_tags))
        if unknown_tags:
            errors.append(f"combo_tags sem combo registrado: {', '.join(unknown_tags)}")

    lore = card.get("lore")
    if not isinstance(lore, str) or not lore.strip() or len(lore) > 600:
        errors.append("lore deve ter entre 1 e 600 caracteres")

    art_version = card.get("art_version")
    if isinstance(art_version, bool) or not isinstance(art_version, int) or art_version < 1:
        errors.append("art_version deve ser inteiro maior ou igual a 1")

    for field in ("origin_id", "source_game"):
        value = card.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"{field} deve ser string ou null")

    if kind == "unit" and effect_id is None and effect_params == {} and tags == []:
        pass  # Carta pura válida; a quota é validada no catálogo.
    elif kind == "unit" and effect_id is None and tags:
        warnings.append("unidade não é pura: participa de combo por tags")

    return CardContractResult(tuple(errors), tuple(warnings))


def validate_catalog(
    catalog: Mapping[str, Any],
    *,
    known_effect_ids: Iterable[str],
    known_combo_tags: Iterable[str],
    effect_registry: Mapping[str, Mapping[str, Any]] | None = None,
    pure_ratio: float = MIN_PURE_RATIO,
) -> CardContractResult:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(catalog, Mapping):
        return CardContractResult(("catalog deve ser um objeto/dicionário",))
    catalog_version = catalog.get("schema_version")
    if isinstance(catalog_version, bool) or not isinstance(catalog_version, int) or catalog_version != CARD_SCHEMA_VERSION:
        errors.append(f"catalog.schema_version deve ser o inteiro {CARD_SCHEMA_VERSION}")
    effect_ids = set(known_effect_ids)
    combo_tags = set(known_combo_tags)
    cards = catalog.get("cards")
    if not isinstance(cards, list) or not cards:
        return CardContractResult(tuple(errors + ["catalog.cards deve ser uma lista não vazia"]))

    seen: set[str] = set()
    pure_count = 0
    for index, card in enumerate(cards):
        result = validate_card_definition(
            card,
            known_effect_ids=effect_ids,
            known_combo_tags=combo_tags,
            effect_registry=effect_registry,
        )
        errors.extend(f"cards[{index}]: {item}" for item in result.errors)
        warnings.extend(f"cards[{index}]: {item}" for item in result.warnings)
        card_id = card.get("card_id") if isinstance(card, Mapping) else None
        if isinstance(card_id, str):
            if card_id in seen:
                errors.append(f"card_id duplicado: {card_id}")
            seen.add(card_id)
        if isinstance(card, Mapping) and is_pure_unit(card):
            pure_count += 1

    required_pure = minimum_pure_cards(len(cards), pure_ratio)
    if pure_count < required_pure:
        errors.append(
            f"quota de cartas puras não atingida: {pure_count}/{len(cards)}; mínimo {required_pure} ({pure_ratio:.0%})"
        )
    return CardContractResult(tuple(errors), tuple(warnings))

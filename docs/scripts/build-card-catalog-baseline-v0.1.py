#!/usr/bin/env python3
"""Rebuild a deterministic, read-only snapshot of the legacy 137-card catalogue.

Run from the repository root:
  python docs/scripts/build-card-catalog-baseline-v0.1.py

This script does not alter runtime modules, the database, images, or the live
catalogue. It writes data/card_game/catalog-legacy-baseline-v0.1.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sistemas.cartas import (  # noqa: E402
    CARTAS_EXPANSAO_V75,
    CARTAS_POR_ID,
    CARTAS_PRIMORDIAIS,
    CARTAS_PATENTE,
    CUSTO_RARIDADE,
    HABILIDADES,
    RARIDADES,
    VERSAO_ARTES,
)
from sistemas.gwent import (  # noqa: E402
    CARD_IDENTITY_ABILITIES,
    CARD_SYNERGY_TAGS,
    DEFAULT_LEADERS,
    FACTION_ARCHETYPES,
    FACTION_BOOST,
    LEADERS,
    RARITY_EFFECT_BUDGET,
    SYNERGY_COMBOS,
)

TRACEABILITY_PATH = ROOT / "docs/card-game-card-traceability.json"
OUTPUT_PATH = ROOT / "data/card_game/catalog-legacy-baseline-v0.1.json"
FACTION_IDS = {
    "Ordem Áurea": "golden_order",
    "Véu Carmesim": "crimson_veil",
    "Lua Negra": "dark_moon",
    "Os Esquecidos": "the_forgotten",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    traceability = json.loads(TRACEABILITY_PATH.read_text(encoding="utf-8"))
    trace_by_id = {item["card_id"]: item for item in traceability["cards"]}
    expansion_ids = {card.id for card in CARTAS_EXPANSAO_V75}
    primordial_ids = {card.id for card in CARTAS_PRIMORDIAIS}
    patent_ids = {card.id for card in CARTAS_PATENTE}

    cards = []
    for card_id in sorted(CARTAS_POR_ID):
        model = CARTAS_POR_ID[card_id]
        trace = trace_by_id.get(card_id, {})
        identity = CARD_IDENTITY_ABILITIES.get(card_id)
        tags = sorted(CARD_SYNERGY_TAGS.get(card_id, set()))
        is_unit = str(model.categoria).casefold() == "unidade"
        is_relic = card_id.startswith("reliquia_")
        kind = "unit" if is_unit else ("relic" if is_relic else "special")
        declared_skill = str(model.habilidade or "") or None
        if identity:
            effective_legacy_effect = str(identity.get("effect") or "") or None
            resolution_source = "card_identity"
        elif declared_skill and declared_skill in HABILIDADES:
            effective_legacy_effect = declared_skill
            resolution_source = "generic_catalog_skill"
        elif declared_skill:
            effective_legacy_effect = None
            resolution_source = "unresolved_or_lifecycle_legacy_id"
        else:
            effective_legacy_effect = None
            resolution_source = "none_or_combo_only"

        source_class = (
            "patent_level_generated" if card_id in patent_ids else
            "v75_expansion" if card_id in expansion_ids else
            "primordial" if card_id in primordial_ids else
            "legacy_static_catalog"
        )
        combo_tag_overlaps = []
        for combo_id, combo in sorted(SYNERGY_COMBOS.items()):
            overlap = sorted(set(tags) & set(combo.get("tags", set())))
            if overlap:
                combo_tag_overlaps.append({
                    "combo_id": combo_id,
                    "overlapping_tags": overlap,
                    "note": "Tag em comum não garante ativação; todas as tags, participantes mínimos e política do motor são necessários.",
                })

        cards.append({
            "card_id": card_id,
            "source_class": source_class,
            "legacy_kind": kind,
            "legacy_slot": "relic_slot" if is_relic else "deck_slot",
            "name_legacy": model.nome,
            "title_legacy": None,
            "faction_legacy": model.faccao,
            "faction_id_candidate": FACTION_IDS.get(model.faccao),
            "faction_review_status": "review_required" if trace.get("alerta_facção") else "not_reviewed",
            "faction_review_note": trace.get("alerta_facção") or None,
            "row_legacy": (model.fileira or trace.get("fileira_atual") or "melee") if is_unit else None,
            "power_base_legacy": int(model.poder) if is_unit else None,
            "power_raw_legacy": int(model.poder),
            "rarity_legacy": model.raridade,
            "deck_cost_legacy": int(model.custo),
            "rarity_cost_table_legacy": CUSTO_RARIDADE.get(model.raridade),
            "legacy_cost_mismatch": int(model.custo) != int(CUSTO_RARIDADE.get(model.raridade, model.custo)),
            "declared_generic_skill_id": declared_skill,
            "declared_generic_skill_name": HABILIDADES.get(declared_skill, {}).get("nome") if declared_skill else None,
            "declared_generic_skill_text": HABILIDADES.get(declared_skill, {}).get("texto") if declared_skill else None,
            "active_identity": ({
                "identity_key": card_id,
                "effect_id": identity.get("effect"),
                "name": identity.get("name"),
                "text": identity.get("text"),
            } if identity else None),
            "effective_legacy_effect_id": effective_legacy_effect,
            "legacy_resolution_source": resolution_source,
            "legacy_resolution_status_from_audit": trace.get("status_resolucao"),
            "legacy_combo_tags": tags,
            "legacy_combo_tag_overlaps": combo_tag_overlaps,
            "strictly_pure_legacy": bool(trace.get("carta_pura_estrita", False)),
            "legacy_description_raw": model.descricao,
            "legacy_art_version": VERSAO_ARTES,
            "pre_v18": {
                "declared_skill_id": trace.get("habilidade_declarada_pre_v18"),
                "power_base": trace.get("poder_declarado_pre_v18"),
                "deck_cost": trace.get("custo_declarado_pre_v18"),
                "changed_by_v18": bool(trace.get("declaracao_alterada_pela_transformacao_v18", False)),
            },
            "migration_status": "not_rebuilt",
        })

    generic_effects = [
        {"effect_id": effect_id, "name": value.get("nome", ""), "legacy_rules_text": value.get("texto", "")}
        for effect_id, value in sorted(HABILIDADES.items())
    ]
    identity_effects = [
        {
            "card_id": card_id,
            "effect_id": value.get("effect"),
            "name": value.get("name", ""),
            "legacy_rules_text": value.get("text", ""),
        }
        for card_id, value in sorted(CARD_IDENTITY_ABILITIES.items())
    ]
    combos = [
        {
            "combo_id": combo_id,
            "priority": int(value.get("priority", 0)),
            "name": value.get("name", ""),
            "required_tags": sorted(value.get("tags", set())),
            "minimum_participants": int(value.get("minimum", 2)),
            "bonus": int(value.get("bonus", 0)),
            "team_bonus": int(value.get("team_bonus", 0)),
            "legacy_rules_text": value.get("description", ""),
        }
        for combo_id, value in sorted(SYNERGY_COMBOS.items())
    ]
    leaders = [
        {"leader_id": leader_id, **value}
        for leader_id, value in sorted(LEADERS.items())
    ]
    faction_profiles = [
        {
            "faction_name_legacy": name,
            "faction_id_candidate": FACTION_IDS[name],
            "archetype_name_legacy": FACTION_ARCHETYPES.get(name, {}).get("name", ""),
            "archetype_text_legacy": FACTION_ARCHETYPES.get(name, {}).get("description", ""),
            "passive_bonus_legacy": int(FACTION_BOOST.get(name, 0)),
            "default_leader_id_legacy": DEFAULT_LEADERS.get(name),
        }
        for name in sorted(FACTION_IDS)
    ]

    source_files = [
        ROOT / "sistemas/cartas.py",
        ROOT / "sistemas/gwent.py",
        ROOT / "levels.py",
        TRACEABILITY_PATH,
    ]
    payload = {
        "snapshot_type": "legacy_catalog_baseline",
        "snapshot_version": "0.1",
        "schema_version": 1,
        "status": "historical_snapshot_not_runtime_source_of_truth",
        "source_package": "soulsbo-main-handoff.zip",
        "source_files_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in source_files},
        "counts": {
            "catalogue_models": len(cards),
            "units": sum(card["legacy_kind"] == "unit" for card in cards),
            "specials": sum(card["legacy_kind"] == "special" for card in cards),
            "relics": sum(card["legacy_kind"] == "relic" for card in cards),
            "strictly_pure_units": sum(card["strictly_pure_legacy"] for card in cards),
            "strictly_pure_percent_all_models": round(100 * sum(card["strictly_pure_legacy"] for card in cards) / len(cards), 2),
            "minimum_pure_units_at_30_percent": (len(cards) * 30 + 99) // 100,
            "generic_effect_definitions": len(generic_effects),
            "active_identity_definitions": len(identity_effects),
            "cards_with_active_identity": sum(bool(card["active_identity"]) for card in cards),
            "cards_with_combo_tags": sum(bool(card["legacy_combo_tags"]) for card in cards),
            "legacy_cost_mismatches": sum(card["legacy_cost_mismatch"] for card in cards),
            "faction_review_required": sum(card["faction_review_status"] == "review_required" for card in cards),
            "v18_transformed_cards": sum(card["pre_v18"]["changed_by_v18"] for card in cards),
            "combos": len(combos),
            "leaders": len(leaders),
        },
        "notes": [
            "Este arquivo é uma fotografia histórica dos modelos atuais; não deve ser importado pelo runtime novo.",
            "As relíquias são separadas das 12 posições de deck; não classificá-las como especiais táticas no modelo novo.",
            "Poder-base é capturado apenas para unidades. O valor zero antigo de especiais não é poder de combate.",
            "Identidade ativa substitui a habilidade genérica no resolvedor legado; ambas são preservadas no snapshot para rastreabilidade.",
            "Descrições antigas são preservadas literalmente e podem misturar lore e regras; não usar como texto mecânico canônico.",
            "Os dez modelos patente_N são saídas determinísticas de níveis; cartas de recompensa de jogos geradas dinamicamente não entram neste inventário fixo.",
            "Fórmulas de custo, EFP e raridade continuam propostas sem aprovação; os valores legados não são valores oficiais novos.",
        ],
        "cards": cards,
        "effect_registry_legacy": {
            "generic_effects": generic_effects,
            "identity_effects": identity_effects,
            "combos": combos,
            "leaders": leaders,
            "factions": faction_profiles,
            "rarity_effect_budget_legacy": RARITY_EFFECT_BUDGET,
        },
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT_PATH.relative_to(ROOT)), "counts": payload["counts"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

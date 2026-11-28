#!/usr/bin/env python3
"""Build a traceable report for the Card Engine v2 catalog alpha expansion."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sistemas.card_engine_v2.alpha_catalog import AlphaCatalog  # noqa: E402
from sistemas.card_engine_v2.entry_effects import SUPPORTED_ENTRY_EFFECTS  # noqa: E402

BASELINE = ROOT / "data/card_game/catalog-legacy-baseline-v0.1.json"
ALLOWLIST = ROOT / "data/card_game/card-engine-v2-alpha-catalog.v0.2.json"
EFFECTS = ROOT / "data/card_game/card-engine-v2-alpha-effects.v0.2.json"
STAGING = ROOT / "data/card_game/card-engine-v2-legacy-catalog-staging.v0.1.json"
TESTS = ROOT / "docs/card-engine-v2-playable-alpha-validation-v0.3.json"
MATCH = ROOT / "docs/card-engine-v2-playable-match-alpha-run.v0.2.json"
OUT_JSON = ROOT / "docs/card-engine-v2-catalog-expansion-report-v0.2.json"
OUT_MD = ROOT / "docs/card-engine-v2-catalog-expansion-report-v0.2.md"

ORIGINAL_ALPHA_IDS = {
    "arma_lanca_fornalha",
    "arma_cajado_marulho",
    "arma_martelo_fornalha",
    "chefe_vigia_cinzento",
    "gwent_v75_ordem_veterano_juramento",
    "gwent_unidade_herdeiro_portao",
    "gwent_especial_egide",
    "gwent_especial_execucao",
    "gwent_especial_tempestade",
    "elden_especial_geada",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> dict:
    catalog = AlphaCatalog()
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    tests = json.loads(TESTS.read_text(encoding="utf-8"))
    match = json.loads(MATCH.read_text(encoding="utf-8"))
    effects = json.loads(EFFECTS.read_text(encoding="utf-8"))
    allowlist = set(catalog.allowed_card_ids())
    definitions = [catalog.definition_for(card_id) for card_id in sorted(allowlist)]
    new_ids = sorted(allowlist - ORIGINAL_ALPHA_IDS)
    family_sources: dict[str, list[str]] = {}
    for card in definitions:
        effect_id = card.get("effect_id")
        if effect_id in SUPPORTED_ENTRY_EFFECTS:
            family_sources.setdefault(effect_id, []).append(card["card_id"])

    assert len(allowlist) == 24
    assert len(new_ids) == 14
    assert len(SUPPORTED_ENTRY_EFFECTS) == 12
    assert set(family_sources) == set(SUPPORTED_ENTRY_EFFECTS)
    assert staging["summary"]["historical_model_count"] == 137
    assert staging["summary"]["alpha_test_only_count"] == 24
    assert staging["summary"]["blocked_staging_only_count"] == 113
    assert tests["metadata"]["status"] == "PASS"
    assert match["status"] == "finished"

    report = {
        "artifact_type": "soulsbo_card_engine_v2_catalog_expansion_report",
        "version": "0.2",
        "status": "PASS_ALPHA_ONLY_NOT_RELEASE_APPROVED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "catalog_release": catalog.definition_manifest(),
        "summary": {
            "historical_model_count": 137,
            "alpha_allowed_card_count": len(allowlist),
            "newly_added_alpha_card_count": len(new_ids),
            "blocked_staging_only_count": 113,
            "implemented_new_entry_effect_family_count": len(SUPPORTED_ENTRY_EFFECTS),
            "all_historical_models_rebuilt": False,
            "production_catalog_ready": False,
        },
        "newly_added_alpha_card_ids": new_ids,
        "card_definitions": [
            {
                "card_id": item["card_id"],
                "kind": item["kind"],
                "printed_row": item["printed_row"],
                "power_base": item["power_base"],
                "effect_id": item["effect_id"],
                "effect_params": item["effect_params"],
                "definition_digest": item["definition_digest"],
            }
            for item in definitions
        ],
        "implemented_entry_effect_families": [
            {"effect_id": effect_id, "source_card_ids": sorted(card_ids)}
            for effect_id, card_ids in sorted(family_sources.items())
        ],
        "staging_summary": staging["summary"],
        "playable_match_regression": {
            "status": match["status"],
            "winner_player_id": match["winner_player_id"],
            "round_wins": match["round_wins"],
            "operation_count": len(match["actions"]),
            "event_count": match["event_count"],
            "sqlite_integrity": match["sqlite_integrity"],
        },
        "test_validation": tests["summary"],
        "source_artifacts": {
            path.name: sha256(path)
            for path in (BASELINE, ALLOWLIST, EFFECTS, STAGING, TESTS, MATCH)
        },
        "limitations": [
            "O arquivo com 137 cartas é um staging histórico para revisão, não um catálogo executável.",
            "Somente os 24 IDs explícitos são aceitos pela alpha isolada; os outros 113 permanecem bloqueados.",
            "Os 137 registros históricos continuam exigindo reconstrução de definição e revisão de facção conforme o snapshot de origem.",
            "Esta expansão não implementa as 54 famílias candidatas completas, 27 combos, líderes ou passivas de facção.",
            "Custos de deck, texto, atribuição de facção e status de publicação não são aprovados por esta allowlist alpha.",
            "Discord, HTTP, frontend, banco de produção, runtime legado e migração de produção permanecem desconectados e inalterados.",
        ],
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Card Engine v2 — expansão de catálogo alpha v0.2",
        "",
        f"**Status:** {report['status']}  ",
        f"**Gerado (UTC):** {report['generated_at_utc']}  ",
        f"**Cartas permitidas:** {len(allowlist)} (14 adicionadas nesta expansão)  ",
        f"**Famílias novas implementadas:** {len(SUPPORTED_ENTRY_EFFECTS)}  ",
        f"**Testes da suíte:** {tests['summary']['passed']}/{tests['summary']['tests']} aprovados",
        "",
        "## Escopo efetivamente habilitado",
        "",
        "O snapshot histórico tem 137 modelos. O runtime alpha permite somente 24 IDs explícitos; 113 continuam bloqueados. A lista permitida está versionada em `data/card_game/card-engine-v2-alpha-catalog.v0.2.json`, validada pelo `AlphaCatalog` e incluída por SHA-256 no `DefinitionManifest`.",
        "",
        "### 14 cartas adicionadas",
        "",
    ]
    lines.extend(f"- `{card_id}` — `{catalog.definition_for(card_id)['effect_id']}`" for card_id in new_ids)
    lines.extend(["", "### 12 famílias de efeito de entrada", ""])
    for effect_id, card_ids in sorted(family_sources.items()):
        lines.append(f"- `{effect_id}`: " + ", ".join(f"`{card_id}`" for card_id in sorted(card_ids)))
    lines.extend(
        [
            "",
            "## Staging histórico",
            "",
            "| Métrica | Quantidade |",
            "|---|---:|",
            "| Modelos históricos | 137 |",
            "| Permitidos somente na alpha | 24 |",
            "| Bloqueados no staging | 113 |",
            "| Ainda não reconstruídos | 137 |",
            "| Facções ainda sem revisão | 137 |",
            "| Divergências históricas de custo | 19 |",
            "",
            "O staging é rastreabilidade, não publicação. Não foram inferidos handlers para cartas bloqueadas apenas porque há texto ou alias semelhante.",
            "",
            "## Regressão da partida jogável",
            "",
            f"A partida de referência terminou com vencedor `{match['winner_player_id']}` e resultado de rodadas `{match['round_wins']}`. Foram persistidas {len(match['actions'])} operações e {match['event_count']} eventos; SQLite: `{match['sqlite_integrity']['integrity_check']}`.",
            "",
            "## Testes",
            "",
            f"A suíte completa registrou **{tests['summary']['passed']}/{tests['summary']['tests']} aprovados**, {tests['summary']['failed']} falhas e {tests['summary']['skipped']} ignorados.",
            "",
            "Validação adicional: `docs/scripts/validate-card-engine-v2-legacy-catalog-staging-v0.1.py` confirma hashes de origem, 137 IDs sem duplicidade, 24 IDs alpha e 113 bloqueados.",
            "",
            "## Limites",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Catalog expansion report: {report['summary']['alpha_allowed_card_count']} alpha cards, "
          f"{report['summary']['implemented_new_entry_effect_family_count']} effect families, "
          f"{tests['summary']['passed']}/{tests['summary']['tests']} tests")
    print(f"JSON: {OUT_JSON.relative_to(ROOT)}")
    print(f"Markdown: {OUT_MD.relative_to(ROOT)}")
    return report


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate and summarize the proposed legacy-to-canonical effect catalogue.

This is an audit/reporting tool. It does not edit any runtime module or approve
candidate mechanics. It runs the 23-test structural suite and the independent semantic-audit suite.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import sistemas.cartas as legacy_cards  # noqa: E402
import sistemas.gwent as legacy_engine  # noqa: E402
from sistemas.card_contract import validate_effect_registry  # noqa: E402

DATA = ROOT / "data/card_game"
DOCS = ROOT / "docs"
REGISTRY_PATH = DATA / "effect-registry-candidate.v1.json"
SCHEMA_PATH = DATA / "effect-registry.schema.v1.json"
ALIASES_PATH = DATA / "legacy-effect-aliases-v0.1.json"
LEADERS_PATH = DATA / "leader-registry-candidate.v1.json"
FACTIONS_PATH = DATA / "faction-passives-candidate.v1.json"
DECISION_PATH = DOCS / "card-game-effect-catalog-decision-v0.1.json"
TEST_PATH = DOCS / "scripts/test-effect-catalog-candidate-v0.1.py"
SEMANTIC_AUDIT_SCRIPT = DOCS / "scripts/audit-effect-semantic-groups-v0.1.py"
SEMANTIC_TEST_PATH = DOCS / "scripts/test-effect-semantic-audit-v0.1.py"
SEMANTIC_REPORT_JSON = DOCS / "card-game-effect-semantic-audit-v0.1.json"
OUT_JSON = DOCS / "card-game-effect-catalog-validation-v0.1.json"
OUT_MD = DOCS / "card-game-effect-catalog-validation-v0.1.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    registry = load(REGISTRY_PATH)
    schema = load(SCHEMA_PATH)
    aliases = load(ALIASES_PATH)
    leaders = load(LEADERS_PATH)
    factions = load(FACTIONS_PATH)
    decisions = load(DECISION_PATH)

    schema_errors = list(Draft202012Validator(schema).iter_errors(registry))
    contract_result = validate_effect_registry(registry)
    effect_by_id = {item["effect_id"]: item for item in registry["effects"]}
    generic = aliases["generic_and_special_aliases"]
    identities = aliases["active_identity_card_overrides"]
    kinds = Counter(item["legacy_kind"] for item in generic)
    family_kinds = Counter(item["kind"] for item in registry["effects"])
    zero_assigned = [item["legacy_id"] for item in generic if item["legacy_kind"] == "unit" and item["assigned_card_count"] == 0]
    stale_dispositions = Counter(item["disposition"] for item in aliases["inactive_identity_branch_decisions"])
    combo_evidence = decisions["combo_pair_evidence"]

    test_run = subprocess.run(
        [sys.executable, str(TEST_PATH)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    test_summary = re.search(r"Ran (\d+) tests?", test_run.stdout)
    test_count = int(test_summary.group(1)) if test_summary else 0
    test_passed = test_run.returncode == 0

    semantic_audit_run = subprocess.run(
        [sys.executable, str(SEMANTIC_AUDIT_SCRIPT)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    semantic_test_run = subprocess.run(
        [sys.executable, str(SEMANTIC_TEST_PATH)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    semantic_test_summary = re.search(r"Ran (\d+) tests?", semantic_test_run.stdout)
    semantic_test_count = int(semantic_test_summary.group(1)) if semantic_test_summary else 0
    semantic_audit_passed = semantic_audit_run.returncode == 0
    semantic_test_passed = semantic_test_run.returncode == 0
    semantic_report = load(SEMANTIC_REPORT_JSON) if SEMANTIC_REPORT_JSON.exists() else {"counts": {}}

    result = {
        "schema_version": 1,
        "status": "CANDIDATE_NOT_APPROVED_NOT_CONNECTED_TO_RUNTIME",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "validation": {
            "json_schema_draft_2020_12_valid": not schema_errors,
            "contract_validator_valid": contract_result.valid,
            "contract_errors": list(contract_result.errors),
            "structural_tests": test_count,
            "structural_tests_passed": test_count if test_passed else None,
            "structural_tests_failed": 0 if test_passed else None,
            "test_command_exit_code": test_run.returncode,
            "test_output_tail": test_run.stdout[-4000:],
            "semantic_audit_script_exit_code": semantic_audit_run.returncode,
            "semantic_audit_script_passed": semantic_audit_passed,
            "semantic_audit_output_tail": semantic_audit_run.stdout[-3000:],
            "semantic_audit_tests": semantic_test_count,
            "semantic_audit_tests_passed": semantic_test_count if semantic_test_passed else None,
            "semantic_audit_tests_failed": 0 if semantic_test_passed else None,
            "semantic_audit_test_exit_code": semantic_test_run.returncode,
            "semantic_audit_test_output_tail": semantic_test_run.stdout[-3000:],
        },
        "counts": {
            "candidate_effect_families": len(registry["effects"]),
            "candidate_unit_effect_families": family_kinds["unit"],
            "candidate_special_effect_families": family_kinds["special"],
            "candidate_relic_effect_families": family_kinds["relic"],
            "legacy_habilidades_total": len(legacy_cards.HABILIDADES),
            "legacy_unit_skill_definitions": kinds["unit"],
            "legacy_tactical_special_definitions": kinds["special"],
            "legacy_relic_definitions": kinds["relic"],
            "generic_special_relic_aliases_mapped": len(generic),
            "parameterized_aliases": sum(item["migration_status"] == "PARAMETERIZED_ALIAS" for item in generic),
            "direct_aliases": sum(item["migration_status"] == "DIRECT_ALIAS" for item in generic),
            "generic_unit_effects_without_current_card_assignment": len(zero_assigned),
            "active_identity_overrides": len(identities),
            "identity_cards_with_suppressed_generic_field": aliases["identity_generic_suppression_count"],
            "hidden_gloria_cards": next(item["assigned_card_count"] for item in aliases["hidden_lifecycle_aliases"] if item["legacy_id"] == "gloria"),
            "filtered_v18_identity_branches": len([x for x in aliases["inactive_identity_branch_decisions"] if x["reason"].startswith("Definição filtrada pela transformação V18")]),
            "stale_v75_identity_branches": len([x for x in aliases["inactive_identity_branch_decisions"] if x["disposition"] == "ARCHIVE_STALE_BRANCH"]),
            "unregistered_legacy_field_effects": stale_dispositions["ARCHIVE_UNREGISTERED_FIELD_EFFECT"],
            "combos": len(registry["combos"]),
            "combo_pair_evidence": len(combo_evidence),
            "orphan_combo_card_ids": len(aliases["orphan_synergy_card_ids"]),
            "leaders": len(leaders["leaders"]),
            "faction_passives": len(factions["passives"]),
            "semantic_audit_candidate_families": semantic_report.get("counts", {}).get("candidate_families"),
            "semantic_audit_high_risk_families": semantic_report.get("counts", {}).get("high_risk_families"),
            "semantic_audit_medium_risk_families": semantic_report.get("counts", {}).get("medium_risk_families"),
            "semantic_audit_low_risk_families": semantic_report.get("counts", {}).get("low_risk_families"),
            "semantic_audit_generic_direct_handlers": semantic_report.get("counts", {}).get("direct_play_branch_aliases"),
            "semantic_audit_generic_lifecycle_hooks": semantic_report.get("counts", {}).get("lifecycle_hook_aliases"),
            "semantic_audit_generic_missing_handlers": semantic_report.get("counts", {}).get("generic_aliases_without_handler"),
        },
        "unassigned_unit_effect_ids": zero_assigned,
        "stale_disposition_counts": dict(stale_dispositions),
        "recommendation_counts": decisions["recommendation_counts"],
        "scope": {
            "runtime_files_changed": False,
            "new_handlers_implemented": False,
            "card_assignments_in_new_catalog_approved": False,
            "efp_cost_rarity_approved": False,
            "combo_policy_imported_from_approved_current_runtime": True,
            "source_catalog_card_count": len(legacy_cards.CARTAS_POR_ID),
            "active_identity_source_count": len(legacy_engine.CARD_IDENTITY_ABILITIES),
        },
        "sha256": {
            "registry": sha256(REGISTRY_PATH),
            "alias_map": sha256(ALIASES_PATH),
            "decision_json": sha256(DECISION_PATH),
            "builder_script": sha256(DOCS / "scripts/build-effect-catalog-candidate-v0.1.py"),
            "test_script": sha256(TEST_PATH),
            "semantic_audit_script": sha256(SEMANTIC_AUDIT_SCRIPT),
            "semantic_audit_test_script": sha256(SEMANTIC_TEST_PATH),
            "semantic_audit_json": sha256(SEMANTIC_REPORT_JSON) if SEMANTIC_REPORT_JSON.exists() else None,
        },
    }

    all_ok = (
        result["validation"]["json_schema_draft_2020_12_valid"]
        and result["validation"]["contract_validator_valid"]
        and test_passed
    )
    result["validation"]["all_checks_passed"] = all_ok
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    c = result["counts"]
    lines = [
        "# Validação do catálogo de efeitos candidato v0.1",
        "",
        "**Estado:** candidato para revisão; não aprovado e não conectado ao runtime.",
        "",
        "## Resultado",
        "",
        f"- JSON Schema Draft 2020-12: {'APROVADO' if result['validation']['json_schema_draft_2020_12_valid'] else 'FALHOU'}.",
        f"- Validador `validate_effect_registry()`: {'APROVADO' if result['validation']['contract_validator_valid'] else 'FALHOU'}.",
        f"- Suite estrutural: **{result['validation']['structural_tests_passed'] or 0}/{test_count}** testes aprovados.",
        f"- Auditoria semântica AST: {'APROVADA' if semantic_audit_passed else 'FALHOU'}; suite de regressão semântica: **{result['validation']['semantic_audit_tests_passed'] or 0}/{semantic_test_count}**.",
        f"- Resultado global: **{'APROVADO' if all_ok else 'FALHOU'}** para integridade estrutural do candidato.",
        "",
        "## Inventário consolidado",
        "",
        "| Registro | Quantidade |",
        "|---|---:|",
        f"| Famílias de efeito canônicas candidatas | {c['candidate_effect_families']} |",
        f"| Famílias de unidades | {c['candidate_unit_effect_families']} |",
        f"| Famílias de especiais | {c['candidate_special_effect_families']} |",
        f"| Famílias de relíquias | {c['candidate_relic_effect_families']} |",
        f"| IDs de `HABILIDADES` cobertos por alias | {c['generic_special_relic_aliases_mapped']} |",
        f"| Habilidades genéricas de unidade | {c['legacy_unit_skill_definitions']} |",
        f"| Especiais táticas | {c['legacy_tactical_special_definitions']} |",
        f"| Relíquias | {c['legacy_relic_definitions']} |",
        f"| Aliases parametrizados | {c['parameterized_aliases']} |",
        f"| Aliases diretos | {c['direct_aliases']} |",
        f"| Identidades ativas mapeadas | {c['active_identity_overrides']} |",
        f"| Cartas com habilidade genérica suprimida por identidade | {c['identity_cards_with_suppressed_generic_field']} |",
        f"| Combos com prova de par de IDs distintos | {c['combo_pair_evidence']} |",
        f"| Líderes | {c['leaders']} |",
        f"| Passivas de facção separadas | {c['faction_passives']} |",
        f"| Famílias com prioridade alta/média/baixa de revisão | {c['semantic_audit_high_risk_families']}/{c['semantic_audit_medium_risk_families']}/{c['semantic_audit_low_risk_families']} |",
        f"| Habilidades genéricas com handler direto / hook / sem handler | {c['semantic_audit_generic_direct_handlers']}/{c['semantic_audit_generic_lifecycle_hooks']}/{c['semantic_audit_generic_missing_handlers']} |",
        f"| IDs órfãos de cartas associados a tags | {c['orphan_combo_card_ids']} |",
        "",
        "## Habilidades unitárias sem atribuição atual",
        "",
        f"Há **{c['generic_unit_effects_without_current_card_assignment']}** definições de unidade no catálogo antigo sem carta atualmente atribuída: " + ", ".join(f"`{x}`" for x in zero_assigned) + ". Elas foram preservadas como aliases de migração, mas não serão atribuídas automaticamente a cartas novas.",
        "",
        "## Disposições de migração propostas (não aprovadas)",
        "",
        "| Origem | Disposição | Quantidade |",
        "|---|---|---:|",
        *[f"| HABILIDADES | `{k}` | {v} |" for k, v in sorted(decisions["recommendation_counts"]["generic_aliases"].items())],
        *[f"| Identidades ativas | `{k}` | {v} |" for k, v in sorted(decisions["recommendation_counts"]["identity_overrides"].items())],
        *[f"| Ramos sem associação | `{k}` | {v} |" for k, v in sorted(decisions["recommendation_counts"]["inactive_branches"].items())],
        "",
        "As disposições significam manter como candidato, fundir por parâmetros, redesenhar/dividir após revisão ou remover do novo runtime. Não são autorização para apagar imediatamente o código legado.",
        "",
        "## Limites e decisões pendentes",
        "",
        "- Os 54 `resolution_handler` são nomes propostos; nenhum novo handler foi implementado nesta etapa.",
        "- Os parâmetros default são traduções estruturais das regras legadas, não valores balanceados.",
        "- Os efeitos compostos (`ruin_omen`, `time_storm`, `gravity_reposition`, `row_status_pressure` e sacrifícios) precisam de testes detalhados antes de aprovação.",
        "- Os grupos de status compartilham um modelo, mas Geada, Podridão, Sangramento e Loucura não devem ser tratados como idênticos: limiar, consequência, reset e duração são parâmetros distintos.",
        "- Os 27 combos foram preservados da política atual aprovada; precisam ser reavaliados depois de reescrever as facções e o catálogo de tags.",
        "- EFP, custo, raridade e orçamento de deck seguem não aprovados. Não atribuir efeitos às 137 cartas novas com base apenas neste candidato.",
        "- O código legado e os seus dados não foram apagados ou alterados.",
        "",
        "## Reproduzir",
        "",
        "```bash",
        "python docs/scripts/build-effect-catalog-candidate-v0.1.py",
        "python docs/scripts/test-effect-catalog-candidate-v0.1.py",
        "python docs/scripts/audit-effect-semantic-groups-v0.1.py",
        "python docs/scripts/test-effect-semantic-audit-v0.1.py",
        "python docs/scripts/summarize-effect-catalog-candidate-v0.1.py",
        "```",
        "",
        "O JSON desta validação inclui hashes SHA-256 dos artefatos principais, a suite estrutural e a auditoria semântica. A prioridade alta/média/baixa é heurística de revisão, não decisão automática de equivalência ou aprovação.",
        "",
        "Consulte `docs/card-game-effect-semantic-audit-v0.1.md/.json` para evidências AST por família, localização de handlers, ganchos de ciclo de vida, ramos não mapeados e revisão semântica manual.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"all_checks_passed": all_ok, "families": c["candidate_effect_families"], "aliases": c["generic_special_relic_aliases_mapped"], "identities": c["active_identity_overrides"], "tests": test_count, "semantic_tests": semantic_test_count, "semantic_audit_passed": semantic_audit_passed, "report": str(OUT_JSON)}, ensure_ascii=False, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

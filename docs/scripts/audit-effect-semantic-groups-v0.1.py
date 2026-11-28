#!/usr/bin/env python3
"""Build a read-only semantic audit of candidate effect families against legacy source."""
from __future__ import annotations

import ast
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
DATA = ROOT / "data/card_game"
SOURCE_CARDS = ROOT / "sistemas/cartas.py"
SOURCE_ENGINE = ROOT / "sistemas/gwent.py"
ALIASES_PATH = DATA / "legacy-effect-aliases-v0.1.json"
REGISTRY_PATH = DATA / "effect-registry-candidate.v1.json"
DECISION_PATH = DOCS / "card-game-effect-catalog-decision-v0.1.json"
STALE_PATH = DOCS / "card-game-stale-identity-disposition-v0.1.json"
OUT_JSON = DOCS / "card-game-effect-semantic-audit-v0.1.json"
OUT_MD = DOCS / "card-game-effect-semantic-audit-v0.1.md"

ALIASES = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
REGISTRY = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
DECISIONS = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
STALE = json.loads(STALE_PATH.read_text(encoding="utf-8"))
ENGINE_TEXT = SOURCE_ENGINE.read_text(encoding="utf-8")
ENGINE_TREE = ast.parse(ENGINE_TEXT)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function_nodes(tree: ast.AST) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


FUNCTIONS = function_nodes(ENGINE_TREE)


def str_constants(node: ast.AST) -> set[str]:
    return {n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)}


def names(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def skill_branch_lines(function_name: str, identifiers: set[str], variable: str = "skill") -> dict[str, list[int]]:
    result: dict[str, list[int]] = defaultdict(list)
    fn = FUNCTIONS.get(function_name)
    if not fn:
        return result
    for node in ast.walk(fn):
        if isinstance(node, ast.If) and variable in names(node.test):
            found = str_constants(node.test) & identifiers
            for item in found:
                result[item].append(node.lineno)
    return {key: sorted(set(value)) for key, value in result.items()}


def constant_lines(function_name: str, identifiers: set[str]) -> dict[str, list[int]]:
    result: dict[str, list[int]] = defaultdict(list)
    fn = FUNCTIONS.get(function_name)
    if not fn:
        return result
    for node in ast.walk(fn):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in identifiers:
            result[node.value].append(node.lineno)
    return {key: sorted(set(value)) for key, value in result.items()}


def active_identity_effect_map() -> dict[str, str]:
    for node in ENGINE_TREE.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CARD_IDENTITY_ABILITIES" for t in node.targets):
            mapping = {}
            if isinstance(node.value, ast.Dict):
                for key_node, value_node in zip(node.value.keys, node.value.values):
                    if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str) or not isinstance(value_node, ast.Dict):
                        continue
                    fields = {
                        k.value: v.value
                        for k, v in zip(value_node.keys, value_node.values)
                        if isinstance(k, ast.Constant) and isinstance(k.value, str) and isinstance(v, ast.Constant)
                    }
                    effect = fields.get("effect")
                    if isinstance(effect, str):
                        mapping[key_node.value] = effect
            return mapping
    return {}


IDENTITY_MAP_SOURCE = active_identity_effect_map()
# The runtime filters the initial identity map through _CARTAS_SEM_EFEITO_IDS.
# Use the active keys imported from the alias artifact to match the effective map.
ACTIVE_IDENTITY_CARD_IDS = {entry["card_id"] for entry in ALIASES["active_identity_card_overrides"]}
def identity_branch_lines_all() -> dict[str, list[int]]:
    result: dict[str, list[int]] = defaultdict(list)
    fn = FUNCTIONS.get("_aplicar_habilidade_identidade")
    if not fn:
        return result
    for node in ast.walk(fn):
        if isinstance(node, ast.If) and "effect" in names(node.test):
            for value in str_constants(node.test):
                result[value].append(node.lineno)
    return {key: sorted(set(value)) for key, value in result.items()}


IDENTITY_BRANCH_LINES = identity_branch_lines_all()
GENERIC_IDS = {entry["legacy_id"] for entry in ALIASES["generic_and_special_aliases"]}
GENERIC_BRANCH_LINES = skill_branch_lines("aplicar_jogada", GENERIC_IDS, "skill")
LIFECYCLE_VINGANCA = constant_lines("_remover_unidade", {"vinganca"})
LIFECYCLE_ROUND_END = constant_lines("_resolve_round", {"gloria", "espolios"})

# Candidate entries are combined only for review; this does not imply equivalence.
by_family: dict[str, list[dict]] = defaultdict(list)
for entry in ALIASES["generic_and_special_aliases"]:
    by_family[entry["canonical_effect_id"]].append({
        "source_type": "HABILIDADES",
        "legacy_id": entry["legacy_id"],
        "label": entry["legacy_display_name"],
        "card_ids": entry["assigned_card_ids"],
        "params": entry["default_effect_params"],
        "source_path": "sistemas/cartas.py",
        "handler_path": "sistemas/gwent.py",
        "handler_function": "aplicar_jogada",
        "handler_lines": GENERIC_BRANCH_LINES.get(entry["legacy_id"], []),
    })

for entry in ALIASES["active_identity_card_overrides"]:
    family = entry["canonical_effect_id"]
    effect_key = IDENTITY_MAP_SOURCE.get(entry["card_id"])
    by_family[family].append({
        "source_type": "CARD_IDENTITY_ABILITIES",
        "legacy_id": entry["legacy_identity_effect_id"],
        "label": entry["legacy_display_name"],
        "card_ids": [entry["card_id"]],
        "params": entry["default_effect_params"],
        "source_path": "sistemas/gwent.py:CARD_IDENTITY_ABILITIES",
        "handler_path": "sistemas/gwent.py",
        "handler_function": "_aplicar_habilidade_identidade",
        "handler_lines": IDENTITY_BRANCH_LINES.get(effect_key, []) if effect_key else [],
    })

for entry in ALIASES.get("inactive_identity_branch_decisions", []):
    family = entry.get("candidate_effect_id")
    if not family:
        continue
    by_family[family].append({
        "source_type": "ARCHIVED_IDENTITY_BRANCH_CANDIDATE",
        "legacy_id": entry["legacy_effect_id"],
        "label": entry.get("card_name") or entry["legacy_effect_id"],
        "card_ids": [entry["card_id"]] if entry.get("card_id") else [],
        "params": entry.get("candidate_params", {}),
        "source_path": "sistemas/gwent.py:CARD_IDENTITY_ABILITIES (filtered/inactive)",
        "handler_path": "sistemas/gwent.py",
        "handler_function": "_aplicar_habilidade_identidade",
        "handler_lines": IDENTITY_BRANCH_LINES.get(entry["legacy_effect_id"], []),
    })

for entry in ALIASES.get("hidden_lifecycle_aliases", []):
    if entry["legacy_id"] != "gloria":
        continue
    by_family[entry["candidate_effect_id"]].append({
        "source_type": "HIDDEN_LIFECYCLE_HOOK",
        "legacy_id": entry["legacy_id"],
        "label": "Glória (hook de fim de rodada)",
        "card_ids": entry["assigned_card_ids"],
        "params": {"winner_only": True, "maximum_survivors": 1},
        "source_path": "sistemas/cartas.py:card.habilidade",
        "handler_path": "sistemas/gwent.py",
        "handler_function": "_resolve_round",
        "handler_lines": LIFECYCLE_ROUND_END.get("gloria", []),
    })

# Review priority is intentionally conservative and is not an automated keep/merge decision.
HIGH_RISK = {
    "effect.apply_status_marks", "effect.row_status_pressure", "effect.remove_units",
    "effect.enemy_bonus_reduction", "effect.ally_sacrifice_power", "effect.sequence_power",
    "effect.same_row_formation_power", "effect.cross_row_presence_power", "effect.cross_row_support",
    "effect.row_pair_blessing", "effect.discard_special_power", "effect.weather_affinity_power",
    "effect.gravity_reposition", "effect.frost_storm_momentum", "effect.ruin_omen",
    "effect.relic_night_flame_sword", "effect.relic_black_blade", "effect.relic_margit_shackles",
}
MEDIUM_RISK = {"effect.row_buff", "effect.weather_ward_support", "effect.grace_purification", "effect.revive_from_discard", "effect.revive_to_board", "effect.round_victory_survivor"}

families = []
for effect in REGISTRY["effects"]:
    effect_id = effect["effect_id"]
    entries = by_family.get(effect_id, [])
    distinct_param_shapes = sorted({tuple(sorted(item["params"].keys())) for item in entries})
    sensitive_keys = {"status", "target_scope", "threshold_action", "row_relation", "reference_side", "faction_filter", "ally_selection", "mode", "fallback", "target_selection", "maximum_base_power", "power_limit"}
    varying_sensitive = []
    all_param_keys = set().union(*(set(item["params"]) for item in entries)) if entries else set()
    for key in sorted(all_param_keys & sensitive_keys):
        values = {json.dumps(item["params"].get(key), sort_keys=True, ensure_ascii=False) for item in entries if key in item["params"]}
        if len(values) > 1:
            varying_sensitive.append(key)
    if effect_id in HIGH_RISK:
        risk = "HIGH"
    elif effect_id in MEDIUM_RISK or varying_sensitive or len(distinct_param_shapes) > 1:
        risk = "MEDIUM"
    else:
        risk = "LOW"
    families.append({
        "effect_id": effect_id,
        "candidate_name": effect["name"],
        "kind": effect["kind"],
        "candidate_resolution_handler_name_only": effect["resolution_handler"],
        "timing": effect["timing"],
        "duration": effect["duration"],
        "targeting": effect["targeting"],
        "legacy_alias_count": len(entries),
        "distinct_parameter_shapes": [list(x) for x in distinct_param_shapes],
        "varying_semantic_parameters": varying_sensitive,
        "review_priority": risk,
        "aliases": entries,
        "candidate_warning": "O nome de handler é proposta; não há implementação nova associada.",
    })

# Generic skill dispatch coverage: direct play branch, lifecycle hook, or no current handler.
execution_coverage = []
for entry in ALIASES["generic_and_special_aliases"]:
    legacy_id = entry["legacy_id"]
    direct_lines = GENERIC_BRANCH_LINES.get(legacy_id, [])
    lifecycle = []
    if legacy_id == "vinganca":
        lifecycle = LIFECYCLE_VINGANCA.get("vinganca", [])
    elif legacy_id == "espolios":
        lifecycle = LIFECYCLE_ROUND_END.get("espolios", [])
    elif legacy_id == "sobrevivente":
        lifecycle = []
    if direct_lines:
        classification = "DIRECT_PLAY_BRANCH"
        refs = [{"file": "sistemas/gwent.py", "function": "aplicar_jogada", "lines": direct_lines}]
    elif lifecycle:
        classification = "LIFECYCLE_HOOK"
        function = "_remover_unidade" if legacy_id == "vinganca" else "_resolve_round"
        refs = [{"file": "sistemas/gwent.py", "function": function, "lines": lifecycle}]
    else:
        classification = "NO_CURRENT_HANDLER_FOUND"
        refs = []
    execution_coverage.append({"legacy_id": legacy_id, "assigned_card_ids": entry["assigned_card_ids"], "classification": classification, "evidence": refs})

identity_coverage = []
for entry in ALIASES["active_identity_card_overrides"]:
    card_id = entry["card_id"]
    identity_key = IDENTITY_MAP_SOURCE.get(card_id)
    branch_lines = IDENTITY_BRANCH_LINES.get(identity_key, []) if identity_key else []
    identity_coverage.append({
        "card_id": card_id,
        "identity_effect_id": entry["legacy_identity_effect_id"],
        "resolver_effect_key": identity_key,
        "classification": "ACTIVE_IDENTITY_BRANCH_FOUND" if branch_lines else "MISSING_IDENTITY_BRANCH",
        "evidence": [{"file": "sistemas/gwent.py", "function": "_aplicar_habilidade_identidade", "lines": branch_lines}] if branch_lines else [],
        "generic_field_suppressed": entry["legacy_generic_field_suppressed"],
    })

hidden_lifecycle = []
for item in ALIASES["hidden_lifecycle_aliases"]:
    key = item["legacy_id"]
    line_map = LIFECYCLE_ROUND_END if key in {"gloria", "espolios"} else {}
    hidden_lifecycle.append({
        **item,
        "source_evidence": line_map.get(key, []),
        "implementation_status": "HOOK_IMPLEMENTED" if line_map.get(key) else "DECLARED_WITHOUT_HOOK",
    })

unmapped_fields = []
for field_id, item in STALE.get("unmapped_legacy_field_effect_candidates", {}).items():
    branch_lines = IDENTITY_BRANCH_LINES.get(field_id, [])
    unmapped_fields.append({
        "legacy_field_id": field_id,
        "source_card_ids": item.get("card_ids", item.get("associated_current_card_ids", [])),
        "identity_resolver_branch_lines": branch_lines,
        "current_card_identity_binding": False,
        "classification": "BRANCH_EXISTS_BUT_NO_ACTIVE_CARD_IDENTITY_BINDING" if branch_lines else "NO_RESOLVER_BRANCH_OR_BINDING",
        "source_reason": item.get("reason", ""),
    })

manual_findings = [
    {
        "finding_id": "SEM-001",
        "priority": "HIGH",
        "subject": "effect.sequence_power",
        "finding": "O bônus só deve ocorrer quando existe uma referência de jogada anterior válida. O registry v0.1 não expressava essa pré-condição.",
        "source_evidence": "sistemas/gwent.py:aplicar_jogada — encadeamento/adaptacao/quebra_ritmo; _aplicar_habilidade_identidade — veil_shift/pilgrim_duel/mist_trail",
        "candidate_change": "Adicionado requires_previous_play:boolean obrigatório e verdadeiro em todos os aliases; texto agora explicita que é necessária uma jogada anterior.",
        "status": "FIXED_IN_CANDIDATE_V0.1; NOT_RUNTIME",
    },
    {
        "finding_id": "SEM-002",
        "priority": "HIGH",
        "subject": "effect.apply_status_marks / effect.row_status_pressure",
        "finding": "O nome de família comum não significa efeito idêntico. Geada, Podridão, Sangramento e Loucura têm escopo, limiar, ação secundária, reset e duração diferentes.",
        "source_evidence": "sistemas/gwent.py:aplicar_jogada e _aplicar_habilidade_identidade; params preservam status/target_scope/threshold_action/reset",
        "candidate_change": "Manter só como abstração técnica parametrizada; cada combinação de status e consequência exige teste específico e texto próprio.",
        "status": "OPEN_REQUIRES_BEHAVIOR_TESTS",
    },
    {
        "finding_id": "SEM-003",
        "priority": "HIGH",
        "subject": "effect.remove_units",
        "finding": "Chama Negra seleciona a unidade mais forte de cada lado; Execução escolhe alvo inimigo na fileira com limite de poder. Não são a mesma regra de seleção.",
        "source_evidence": "sistemas/gwent.py:aplicar_jogada special dispatch; _remover_unidade centraliza escudo/remoção",
        "candidate_change": "Exigir escopo de seleção, lado, limite e política de escudo explícitos no futuro handler; remover sentinela ambígua power_limit=0 ou declarar flag `has_power_limit`.",
        "status": "OPEN_REQUIRES_HANDLER_DESIGN",
    },
    {
        "finding_id": "SEM-004",
        "priority": "HIGH",
        "subject": "effect.ally_sacrifice_power",
        "finding": "Devorar e Preço em Sangue diferem no teto do ganho e no bônus de fallback quando não há vítima. Sacrifício também ignora escudo por escolha do helper legado.",
        "source_evidence": "sistemas/gwent.py:aplicar_jogada; _remover_unidade(causa='sacrificio')",
        "candidate_change": "Manter parâmetros gain_cap/fallback_bonus/minimum_gain; criar teste explícito para escudo, gatilho de Vingança e descarte da vítima.",
        "status": "OPEN_REQUIRES_BEHAVIOR_TESTS",
    },
    {
        "finding_id": "SEM-005",
        "priority": "HIGH",
        "subject": "effect.cross_row_support / effect.row_pair_blessing",
        "finding": "Efeitos de suporte variam entre fortalecer apenas aliado e fortalecer a própria carta mais um aliado; seleção varia entre primeiro aliado e aliado mais fraco.",
        "source_evidence": "sistemas/gwent.py:_aplicar_habilidade_identidade",
        "candidate_change": "Manter self_bonus, ally_bonus e ally_selection explícitos; ordem dos empates para alvo mais fraco deve ser determinística e documentada.",
        "status": "OPEN_REQUIRES_TARGETING_RULE",
    },
    {
        "finding_id": "SEM-006",
        "priority": "MEDIUM",
        "subject": "effect.round_victory_survivor",
        "finding": "Glória tem hook funcional: se o jogador vencer uma rodada não final, conserva no campo a mais forte entre as cartas com habilidade gloria; bônus/escudo/status são limpos. Sobrevivente só tem texto declarado, sem handler e sem carta atribuída no snapshot efetivo.",
        "source_evidence": "sistemas/gwent.py:_resolve_round; sistemas/cartas.py:HABILIDADES['sobrevivente']",
        "candidate_change": "Não declarar os dois como comportamento equivalente comprovado. Desenhar uma única regra nova explicitamente e decidir se mantém a retenção da mais forte.",
        "status": "REQUIRES_PRODUCT_RULE_APPROVAL",
    },
    {
        "finding_id": "SEM-007",
        "priority": "HIGH",
        "subject": "effect.sequence_power",
        "finding": "As variantes própria/mesma, própria/diferente e adversária/mesma usam referências distintas; o estado last_row é reiniciado ao fim de cada rodada.",
        "source_evidence": "sistemas/gwent.py:aplicar_jogada e _resolve_round",
        "candidate_change": "`reference_side`, `row_relation` e `requires_previous_play` devem ser obrigatórios; nenhum handler deve inferir referência de valor nulo.",
        "status": "FIXED_IN_CANDIDATE_V0.1; NOT_RUNTIME",
    },
]

report = {
    "metadata": {
        "document": "Auditoria de equivalência semântica do catálogo candidato v0.1",
        "status": "READ_ONLY_SOURCE_AUDIT; CANDIDATE NOT APPROVED; NOT CONNECTED TO RUNTIME",
        "generated_at": "2026-11-27",
        "sources": {
            str(SOURCE_CARDS.relative_to(ROOT)): sha256(SOURCE_CARDS),
            str(SOURCE_ENGINE.relative_to(ROOT)): sha256(SOURCE_ENGINE),
            str(ALIASES_PATH.relative_to(ROOT)): sha256(ALIASES_PATH),
            str(REGISTRY_PATH.relative_to(ROOT)): sha256(REGISTRY_PATH),
        },
    },
    "counts": {
        "candidate_families": len(families),
        "generic_aliases": len(execution_coverage),
        "direct_play_branch_aliases": sum(x["classification"] == "DIRECT_PLAY_BRANCH" for x in execution_coverage),
        "lifecycle_hook_aliases": sum(x["classification"] == "LIFECYCLE_HOOK" for x in execution_coverage),
        "generic_aliases_without_handler": sum(x["classification"] == "NO_CURRENT_HANDLER_FOUND" for x in execution_coverage),
        "active_identity_overrides": len(identity_coverage),
        "active_identity_branches_found": sum(x["classification"] == "ACTIVE_IDENTITY_BRANCH_FOUND" for x in identity_coverage),
        "high_risk_families": sum(x["review_priority"] == "HIGH" for x in families),
        "medium_risk_families": sum(x["review_priority"] == "MEDIUM" for x in families),
        "low_risk_families": sum(x["review_priority"] == "LOW" for x in families),
    },
    "families": families,
    "generic_execution_coverage": execution_coverage,
    "identity_execution_coverage": identity_coverage,
    "hidden_lifecycle_aliases": hidden_lifecycle,
    "unmapped_fields": unmapped_fields,
    "manual_findings": manual_findings,
    "limitations": [
        "Os números de linha são evidência de localização no código-fonte atual e mudam se o arquivo for editado.",
        "A classificação de risco é uma prioridade de revisão, não prova automática de equivalência semântica.",
        "O relatório não executa partidas nem handlers novos; o registry candidato ainda não tem implementação runtime.",
        "Os nomes de resolution_handler são rótulos propostos, não funções presentes no código.",
    ],
}
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

lines = [
    "# Auditoria semântica das famílias de efeito — v0.1",
    "",
    "**Estado:** auditoria read-only do código legado e do registry candidato. Não aprova automaticamente fusões e não altera o runtime.",
    "",
    "## 1. Resultado da rastreabilidade",
    "",
    f"- Famílias candidatas: **{report['counts']['candidate_families']}**.",
    f"- Aliases genéricos: **{report['counts']['generic_aliases']}**; branches diretos: **{report['counts']['direct_play_branch_aliases']}**; hooks de ciclo de vida: **{report['counts']['lifecycle_hook_aliases']}**; sem handler encontrado: **{report['counts']['generic_aliases_without_handler']}**.",
    f"- Identidades ativas: **{report['counts']['active_identity_overrides']}**; branches de identidade encontrados: **{report['counts']['active_identity_branches_found']}**.",
    f"- Prioridade de revisão (heurística): alta **{report['counts']['high_risk_families']}**, média **{report['counts']['medium_risk_families']}**, baixa **{report['counts']['low_risk_families']}**.",
    "",
    "Os branches diretos são identificados por comparações de `skill` no `aplicar_jogada()`. Hooks são verificados separadamente em `_remover_unidade()` e `_resolve_round()`. As identidades ativas são cruzadas entre `CARD_IDENTITY_ABILITIES` e `_aplicar_habilidade_identidade()`. O mapa por família inclui também aliases candidatos arquivados quando a auditoria os vincula explicitamente a uma família; isso não os reativa.",
    "",
    "## 2. Mapa das 54 famílias",
    "",
    "| Família | Tipo | Aliases legados | Risco de revisão | Parâmetros semânticos variáveis |",
    "|---|---|---:|---|---|",
]
for f in families:
    aliases_text = ", ".join("`" + x["legacy_id"] + "`" for x in f["aliases"]) or "—"
    varying = ", ".join(f["varying_semantic_parameters"]) or "—"
    lines.append(f"| `{f['effect_id']}` | {f['kind']} | {f['legacy_alias_count']} — {aliases_text} | **{f['review_priority']}** | {varying} |")
lines += ["", "## 3. Achados semânticos prioritários", "", "| ID | Prioridade | Família | Achado e tratamento | Estado |", "|---|---|---|---|---|"]
for item in manual_findings:
    lines.append(f"| {item['finding_id']} | {item['priority']} | `{item['subject']}` | {item['finding']} **Proposta:** {item['candidate_change']} | `{item['status']}` |")
lines += ["", "## 4. Cobertura de cada alias genérico", "", "| ID | Cartas atuais | Classificação | Evidência |", "|---|---|---|---|"]
for item in execution_coverage:
    cards = ", ".join(f"`{x}`" for x in item["assigned_card_ids"]) or "—"
    refs = "; ".join(f"{e['function']}:{','.join(map(str, e['lines']))}" for e in item["evidence"]) or "—"
    lines.append(f"| `{item['legacy_id']}` | {cards} | `{item['classification']}` | `{refs}` |")
lines += ["", "## 5. Identidades ativas", "", "| Carta | Efeito identidade | Handler encontrado | Campo genérico suprimido |", "|---|---|---|---|"]
for item in identity_coverage:
    lines_ref = ",".join(str(n) for e in item["evidence"] for n in e["lines"]) or "—"
    lines.append(f"| `{item['card_id']}` | `{item['identity_effect_id']}` | `{item['classification']}` ({lines_ref}) | {item['generic_field_suppressed']} |")
lines += ["", "## 6. Hooks ocultos e campos sem vínculo", "", "### Hooks de ciclo de vida", "", "| ID | Cartas atribuídas no catálogo efetivo | Implementação | Linhas |", "|---|---|---|---:|"]
for item in hidden_lifecycle:
    cards = ", ".join(f"`{x}`" for x in item["assigned_card_ids"]) or "—"
    lines.append(f"| `{item['legacy_id']}` | {cards} | `{item['implementation_status']}` | {', '.join(map(str,item['source_evidence'])) or '—'} |")
lines += ["", "### Campos não mapeados", "", "| Campo | Branch do resolver | Vínculo ativo | Conclusão |", "|---|---:|---|---|"]
for item in unmapped_fields:
    lines.append(f"| `{item['legacy_field_id']}` | {', '.join(map(str,item['identity_resolver_branch_lines'])) or '—'} | {item['current_card_identity_binding']} | `{item['classification']}` |")
lines += ["", "## 7. Regras de interpretação", "", "1. Compartilhar `effect_id` significa compartilhar uma estrutura de resolver, não necessariamente o mesmo resultado. Alvo, condição, quantidade, limites, duração, reset, prioridade e efeitos colaterais devem ser parâmetros explícitos.", "2. O nível de risco é triagem conservadora; não é decisão `keep/merge/remove`.", "3. `gloria` está implementada no fim da rodada; `sobrevivente` tem descrição, mas nenhum hook identificado. Não afirmar equivalência implementada.", "4. Os campos `legado`, `devoto`, `escolha_ritmo` e `sinergia_faccao` têm ramos escritos dentro do resolver de identidade, mas não possuem vínculo ativo em `CARD_IDENTITY_ABILITIES`; não os tratar como habilidade genérica executável.", "5. O novo registry não está conectado ao motor antigo. Nenhum efeito foi apagado ou atribuído a carta nova.", "", "## 8. Reproduzir", "", "```bash", "python docs/scripts/build-effect-catalog-candidate-v0.1.py", "python docs/scripts/test-effect-catalog-candidate-v0.1.py", "python docs/scripts/audit-effect-semantic-groups-v0.1.py", "python docs/scripts/test-effect-semantic-audit-v0.1.py", "python docs/scripts/summarize-effect-catalog-candidate-v0.1.py", "```", "", "O JSON ao lado contém os mesmos achados, hashes das fontes, linhas de evidência e o inventário por família.", ""]
OUT_MD.write_text("\n".join(lines), encoding="utf-8")

print(json.dumps({"ok": True, "counts": report["counts"], "report": str(OUT_MD.relative_to(ROOT))}, ensure_ascii=False, indent=2))

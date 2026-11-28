#!/usr/bin/env python3
"""Static route/handler/frontend contract inventory for the Gwent HTTP API.

This tool parses source files only. It does not import bot.py, instantiate aiohttp,
connect to Discord, or execute database handlers.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BOT = ROOT / "bot.py"
JS = ROOT / "site/app.js"
ENGINE = ROOT / "sistemas/gwent.py"
OUT_JSON = ROOT / "docs/card-game-http-contract-map-v0.1.json"
OUT_MD = ROOT / "docs/card-game-http-contract-map-v0.1.md"

KEY_HANDLERS = {
    "_api_gwent_cards",
    "_api_gwent_deck",
    "_api_gwent_deck_save",
    "_api_gwent_deck_reset",
    "_api_gwent_matches",
    "_api_gwent_match_create",
    "_api_gwent_match_create_solo",
    "_api_gwent_match_respond",
    "_api_gwent_match_detail",
    "_api_gwent_match_action",
    "_api_gwent_public_card_image",
    "_api_gwent_card_image",
}

FRONTEND_SIGNALS = {
    "_api_gwent_cards": ["/api/gwent/cards"],
    "_api_gwent_deck": ["/api/gwent/deck"],
    "_api_gwent_deck_save": ["/api/gwent/deck"],
    "_api_gwent_deck_reset": ["/api/gwent/deck/reset"],
    "_api_gwent_matches": ["/api/gwent/matches"],
    "_api_gwent_match_create": ["/api/gwent/matches"],
    "_api_gwent_match_create_solo": ["/api/gwent/matches/solo"],
    "_api_gwent_match_respond": ["/respond"],
    "_api_gwent_match_detail": ["/api/gwent/matches/${matchId}"],
    "_api_gwent_match_action": ["/action"],
    "_api_gwent_public_card_image": ["card.image_url", "/api/gwent/public-cards/"],
    "_api_gwent_card_image": ["/api/gwent/cards/", "image"],
}


def attr_chain(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = attr_chain(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Subscript):
        return attr_chain(node.value)
    return ""


def literal_dict_keys(node: ast.AST) -> list[str]:
    if not isinstance(node, ast.Dict):
        return []
    out = []
    for key in node.keys:
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            out.append(key.value)
    return sorted(set(out))


def handler_contract(fn: ast.AsyncFunctionDef | ast.FunctionDef, js_text: str) -> dict[str, Any]:
    nodes = list(ast.walk(fn))
    body_fields = set()
    match_info = set()
    db_calls = set()
    response_keys = set()
    auth = False
    origin_guard = False
    transaction = False
    engine_calls = set()

    for node in nodes:
        if isinstance(node, ast.Call):
            f = node.func
            chain = attr_chain(f)
            if isinstance(f, ast.Attribute) and f.attr == "get" and attr_chain(f.value) == "body":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    body_fields.add(node.args[0].value)
            if isinstance(f, ast.Attribute) and f.attr == "execute" and attr_chain(f.value).startswith("tx.conn"):
                transaction = True
            if isinstance(f, ast.Attribute):
                if chain.startswith("self.db."):
                    db_calls.add(chain.removeprefix("self.db."))
                elif chain.startswith("tx."):
                    db_calls.add(chain)
                if chain in {"self._api_user_id", "self._api_origin_ok"}:
                    auth |= chain == "self._api_user_id"
                    origin_guard |= chain == "self._api_origin_ok"
                if chain.startswith("gwent."):
                    engine_calls.add(chain)
                if chain == "web.json_response" and node.args:
                    response_keys.update(literal_dict_keys(node.args[0]))
            elif isinstance(f, ast.Name) and chain in {"aplicar_jogada", "novo_estado", "executar_turno_ia", "preparar_carta"}:
                engine_calls.add(chain)
        if isinstance(node, ast.Subscript) and attr_chain(node.value) == "request.match_info":
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                match_info.add(node.slice.value)

    refs = FRONTEND_SIGNALS.get(fn.name, [])
    js_hits = [ref for ref in refs if ref in js_text]
    return {
        "handler": fn.name,
        "handler_lines": [fn.lineno, getattr(fn, "end_lineno", fn.lineno)],
        "auth_guard_detected": auth,
        "origin_guard_detected": origin_guard,
        "request_body_fields_detected": sorted(body_fields),
        "route_parameters_detected": sorted(match_info),
        "response_keys_detected": sorted(response_keys),
        "database_calls_detected": sorted(db_calls),
        "engine_calls_detected": sorted(engine_calls),
        "transaction_execute_detected": transaction,
        "frontend_signal_literals_found": js_hits,
        "frontend_signal_expected": refs,
    }


def main() -> None:
    bot_text = BOT.read_text(encoding="utf-8")
    js_text = JS.read_text(encoding="utf-8")
    bot_tree = ast.parse(bot_text)
    engine_tree = ast.parse(ENGINE.read_text(encoding="utf-8"))

    funcs: dict[str, ast.AsyncFunctionDef | ast.FunctionDef] = {}
    for node in ast.walk(bot_tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            funcs[node.name] = node

    routes = []
    for node in ast.walk(bot_tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"add_get", "add_post", "add_delete", "add_put", "add_patch"}:
            continue
        if attr_chain(node.func.value).split(".")[-1] != "router":
            continue
        if len(node.args) < 2 or not isinstance(node.args[0], ast.Constant):
            continue
        path = node.args[0].value
        handler = attr_chain(node.args[1]).split(".")[-1]
        if not isinstance(path, str) or not path.startswith("/api/gwent/") or handler not in KEY_HANDLERS:
            continue
        fn = funcs.get(handler)
        route = {
            "method": node.func.attr.removeprefix("add_").upper(),
            "path": path,
            "registration_line": node.lineno,
            "handler": handler,
            "handler_contract": handler_contract(fn, js_text) if fn else None,
        }
        routes.append(route)

    routes.sort(key=lambda x: (x["path"], x["method"]))

    prep_fn = next((n for n in ast.walk(engine_tree)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "preparar_carta"), None)
    prep_return_keys = set()
    if prep_fn:
        for node in ast.walk(prep_fn):
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
                prep_return_keys.update(literal_dict_keys(node.value))

    save_fn = funcs.get("_api_gwent_deck_save")
    save_text = "" if save_fn is None else ast.get_source_segment(bot_text, save_fn) or ""
    deck_save_checks = {
        "exactly_12_models": "len(entries) != 12" in save_text,
        "unique_card_models": "len(set(ids)) != 12" in save_text,
        "minimum_8_units": "unit_count < 8" in save_text,
        "maximum_4_specials": "special_count > 4" in save_text,
        "faction_validation": "validar_faccao_deck" in save_text,
        "leader_faction_validation": "LEADERS[leader_id][\"faction\"] != faction" in save_text,
        "relic_ownership_validation": "coliseu_listar_exemplares" in save_text,
        "deck_cost_sum_or_budget": bool(re.search(r"\b(total_cost|deck_cost|budget|orcamento|custo_total)\b", save_text, re.I)),
    }

    payload = {
        "version": "v0.1",
        "status": "static_source_audit_only",
        "source_files": {
            "bot.py": "route registration and async handler bodies parsed with Python AST",
            "site/app.js": "frontend request literals searched statically",
            "sistemas/gwent.py": "preparar_carta return dictionary inspected with Python AST",
        },
        "runtime_http_executed": False,
        "dependencies_missing_in_audit_environment": ["discord.py", "aiosqlite"],
        "routes": routes,
        "deck_save_validation": deck_save_checks,
        "preparar_carta_return_keys": sorted(prep_return_keys),
        "findings": [
            "The deck-save handler validates 12 unique card models, at least 8 units, at most 4 specials, faction predominance, leader/faction compatibility, and relic ownership; it does not sum deck cost or enforce a budget.",
            "Deck/catalog API code assigns payload['custo'] before calling preparar_carta(), but preparar_carta() returns an explicit dictionary that does not include 'custo'. The final prepared card payload therefore drops the assigned cost.",
            "The frontend posts cards as {card_id, exemplar_id} plus faction, leader_id and relic_id. Match actions post action, card_id, row, card_ids and target_id, then refresh the match detail endpoint.",
            "The action endpoint returns {ok: true}; the frontend refreshes GET /api/gwent/matches/{match_id} to retrieve the updated public state.",
            "Pending invitations are answered through the separate /respond endpoint; match detail returns status-only for pending rows and full state for active/finished rows.",
            "Human-vs-human invitation creation stores deck/config snapshots; acceptance revalidates relic ownership, shuffles snapshots and creates the initial game state.",
            "Solo creation mirrors the player's saved deck/config for NARA; the action handler executes the AI turn server-side and uses a pass fallback if AI execution raises.",
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# Mapa estático de contratos HTTP Gwent — v0.1",
        "",
        "> Auditoria por AST/inspeção de fonte. Não importa `bot.py`, não instancia `aiohttp`, não executa handlers, Discord nem o wrapper `Database`.",
        "",
        "## Rotas principais",
        "",
        "| Método | Rota | Handler | Linhas do handler | Autenticação | Checagem de origem | Uso pelo frontend |",
        "|---|---|---|---:|---|---|---|",
    ]
    for r in routes:
        c = r["handler_contract"] or {}
        lines = c.get("handler_lines", [None, None])
        md.append(
            f"| {r['method']} | `{r['path']}` | `{r['handler']}` | {lines[0]}–{lines[1]} | "
            f"{'sim' if c.get('auth_guard_detected') else 'não detectada'} | "
            f"{'sim' if c.get('origin_guard_detected') else 'não detectada'} | "
            f"{', '.join(c.get('frontend_signal_literals_found', [])) or 'sem literal confirmado'} |"
        )
    md += [
        "",
        "## Contrato de deck e custo",
        "",
        "O frontend envia `cards: [{card_id, exemplar_id}]`, `faction`, `leader_id` e `relic_id` em `POST /api/gwent/deck`. O handler exige 12 modelos únicos, facção válida/predominante, líder da facção, relíquia permitida e possuída, mínimo de oito unidades e máximo de quatro especiais. O estado da implementação não contém soma de custo nem teto de orçamento.",
        "",
        f"A função `preparar_carta()` retorna estas chaves: `{', '.join(sorted(prep_return_keys))}`. **`custo` não está na lista.** As rotas `/api/gwent/cards` e `/api/gwent/deck` atribuem `payload['custo']` antes de chamar `preparar_carta()`, mas a preparação explícita descarta esse campo. Assim, o custo pode existir no modelo/base payload e ainda não chegar ao consumidor final desse contrato.",
        "",
        "## Contrato de partidas",
        "",
        "- `GET /api/gwent/matches`: lista partidas/ranking/leaderboard do usuário autenticado.",
        "- `POST /api/gwent/matches`: recebe `opponent_id`; valida guild/decks, limite de três partidas pendentes/ativas e posse de relíquias; salva snapshot de deck/config em `state_json` com status `pending`.",
        "- `POST /api/gwent/matches/{match_id}/respond`: recebe `action` (`accept`, `decline`, `cancel`); somente o convidado aceita/recusa e somente o criador cancela. Na aceitação, revalida relíquias, embaralha snapshots e cria `novo_estado()`.",
        "- `POST /api/gwent/matches/solo`: cria partida contra NARA com cópia do deck/config do usuário; a API informa `rewards: false`.",
        "- `GET /api/gwent/matches/{match_id}`: para `pending`, retorna somente `match_id/status`; para `active/finished`, retorna estado público, mão, placar, alvos, clima, líder, relíquia, histórico e recompensa.",
        "- `POST /api/gwent/matches/{match_id}/action`: recebe `action`, `card_id`, `row`, `card_ids`, `target_id`; aplica `aplicar_jogada()` dentro de transação e executa turno NARA no servidor quando necessário. Retorna `{ok: true}`; o frontend busca novamente o detalhe para obter o estado novo.",
        "",
        "## Achados relevantes para a reconstrução",
        "",
        "1. **Custo não é uma regra de deck.** O handler de gravação não calcula soma de custo nem compara com orçamento.",
        "2. **Custo não chega no payload preparado.** `preparar_carta()` não inclui `custo` no dicionário retornado, mesmo quando rotas anteriores calcularam `payload['custo']`.",
        "3. **Ações são refetch-based.** O POST de ação devolve apenas sucesso; o frontend chama `refreshGwentMatch()` e `GET /api/gwent/matches/{id}`.",
        "4. **Convite é snapshot-based.** O deck/config enviado é guardado no convite; a aceitação revalida posse de relíquia, depois embaralha e inicializa a partida.",
        "5. **NARA atua no servidor.** A ação humana pode ser seguida por `executar_turno_ia()` no mesmo handler; em exceção, o backend tenta `pass` como fallback.",
        "",
        "## Limites e próximo passo",
        "",
        "Todas as conclusões são estáticas. Não foi possível executar HTTP porque `discord.py` e `aiosqlite` não estão instalados; tentativa de instalação temporária foi bloqueada por DNS. Não usar esta auditoria como prova de respostas reais, autenticação, transações, race conditions, integração do browser ou DB.",
        "",
        "Próxima execução: em ambiente com as dependências de `requirements.txt`, construir testes `aiohttp.TestClient` para cada rota de leitura/escrita, autenticação (401), origem (403), ownership, status (400/403/404/409), transação/rollback e refetch da UI. Em seguida, corrigir o contrato do custo junto da especificação aprovada — não antes de definir o schema/custo oficial.",
        "",
        "## Reprodução",
        "",
        "```bash",
        "python docs/scripts/audit-gwent-http-contracts-v0.1.py",
        "```",
        "",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print(json.dumps({"routes": len(routes), "report_json": str(OUT_JSON), "report_markdown": str(OUT_MD),
                      "deck_cost_budget_enforced": deck_save_checks["deck_cost_sum_or_budget"],
                      "prepared_payload_includes_cost": "custo" in prep_return_keys}, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Authenticated HTTP API and page for the Card Engine v2 alpha.

Uses the site's signed Discord session and CSRF origin check. The player ID is
always derived from the server session, never from request JSON or query text.
The v2 repositories remain separate from the legacy Soulsbo database.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from aiohttp import web

from sistemas.card_engine_v2.application import AlphaGameApplication, AsyncAlphaGameApplication
from sistemas.card_engine_v2.discord_gateway import CardEngineV2DiscordGateway
from sistemas.card_engine_v2.errors import IdempotencyConflict, InvalidOperation, MatchNotFound, PersistenceConflict


_ROOT = Path(__file__).resolve().parent
_SITE = _ROOT / "site"
_ALLOWED_ACTIONS: dict[str, set[str]] = {
    "pass_turn": {"expected_revision", "operation_id"},
    "play_unit": {"instance_id", "expected_revision", "operation_id"},
    "play_special": {"source_instance_id", "selected_row", "selection", "expected_revision", "operation_id"},
    "sacrifice_unit": {"target_instance_id", "expected_revision", "operation_id"},
    "activate_leader": {"selected_row", "expected_revision", "operation_id"},
    "activate_card_ability": {"source_instance_id", "ability_id", "selection", "selected_row", "target_row", "expected_revision", "operation_id"},
}


def _gateway(bot: Any) -> CardEngineV2DiscordGateway:
    gateway = getattr(bot, "card_engine_v2_shared_gateway", None)
    if gateway is not None:
        return gateway
    service = getattr(bot, "card_engine_v2_discord_service", None)
    if service is not None:
        gateway = service.gateway
    else:
        import config
        data_root = Path(config.get_data_dir()).expanduser().resolve() / "card_engine_v2"
        data_root.mkdir(parents=True, exist_ok=True)
        application = AlphaGameApplication(
            match_database_path=data_root / "matches.sqlite3",
            deck_database_path=data_root / "decks.sqlite3",
        )
        gateway = CardEngineV2DiscordGateway(
            database=bot.db,
            application=AsyncAlphaGameApplication(application),
        )
    setattr(bot, "card_engine_v2_shared_gateway", gateway)
    return gateway


def _player_id(bot: Any, request: web.Request) -> int | None:
    value = bot._api_user_id(request)
    if value is None:
        return None
    try:
        uid = int(value)
    except (TypeError, ValueError):
        return None
    return uid if uid > 0 else None


def _json_error(message: str, status: int) -> web.Response:
    return web.json_response({"error": message}, status=status, headers={"Cache-Control": "no-store"})


async def _body(request: web.Request) -> dict[str, Any] | None:
    # Enforce the same bound for fixed-length and chunked requests. aiohttp's
    # default client_max_size is a broader safety net, not this API contract.
    try:
        raw = await request.read()
        if len(raw) > 32_768:
            return None
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, web.HTTPException):
        return None
    return value if isinstance(value, dict) else None


def _card_summary(gateway: CardEngineV2DiscordGateway, card_id: str) -> dict[str, Any]:
    definition = gateway.catalog.definition_for(card_id)
    return {
        "card_id": card_id,
        "name": gateway.catalog.display_name(card_id),
        "kind": definition.get("kind"),
        "faction_id": definition.get("faction_id"),
        "row": definition.get("printed_row"),
        "base_power": definition.get("power_base"),
        "energy_cost": gateway.catalog.energy_cost_for_card(card_id),
        "effect_id": definition.get("effect_id"),
    }


def registrar_rotas(bot: Any, app: web.Application) -> None:
    """Register the private Card Engine v2 website and authenticated API."""

    async def page(request: web.Request) -> web.Response:
        uid = _player_id(bot, request)
        if uid is None:
            raise web.HTTPFound("/auth/discord/login?next=%2Fcard-engine-v2")
        path = _SITE / "card-engine-v2.html"
        if not path.is_file():
            return web.Response(text="Interface do Card Engine v2 indisponível.", status=503)
        return web.FileResponse(path, headers={"Cache-Control": "private, no-store"})

    async def bootstrap(request: web.Request) -> web.Response:
        uid = _player_id(bot, request)
        if uid is None:
            return _json_error("Autenticação necessária.", 401)
        try:
            gateway = _gateway(bot)
            inventory, decks, matches = await __import__("asyncio").gather(
                gateway.collection_for_player(uid), gateway.list_decks(uid), gateway.list_matches(uid, limit=50)
            )
            cards = [_card_summary(gateway, card_id) for card_id in gateway.catalog.allowed_card_ids()]
            physical = []
            for exemplar_id, item in sorted(inventory.items()):
                card = _card_summary(gateway, str(item["card_id"]))
                physical.append({
                    "exemplar_id": int(exemplar_id),
                    "card_id": str(item["card_id"]),
                    "name": card["name"],
                    "rarity": str(item.get("rarity") or ""),
                    "power": item.get("power"),
                    "energy_cost": card["energy_cost"],
                    "kind": card["kind"],
                    "faction_id": card["faction_id"],
                    "row": card["row"],
                })
            leaders = [
                {
                    "leader_id": str(leader_id),
                    "name": str(definition.get("name") or leader_id),
                    "faction_id": str(definition.get("faction_id") or ""),
                    "description": str(definition.get("description_current") or ""),
                    "energy_cost": gateway.catalog.energy_cost_for_leader(str(leader_id)),
                }
                for leader_id, definition in sorted(gateway.catalog.leader_registry.items())
            ]
            data = {
                "player_id": str(uid),
                "release_id": "alpha-test-only.ruleset.v0.5",
                "cards": cards,
                "leaders": leaders,
                "inventory": physical,
                "decks": decks,
                "matches": matches,
                "rules": {"deck_size": 30, "max_copies_per_model": 3, "opening_hand": 4},
            }
            return web.json_response(data, headers={"Cache-Control": "private, no-store"})
        except Exception:
            import logging
            logging.getLogger("site_card_engine_v2").exception("Card Engine v2 bootstrap failed")
            return _json_error("Não foi possível carregar seus dados do Card Engine v2.", 503)

    async def deck_save(request: web.Request) -> web.Response:
        uid = _player_id(bot, request)
        if uid is None:
            return _json_error("Autenticação necessária.", 401)
        if not bot._api_origin_ok(request):
            return _json_error("Origem não autorizada.", 403)
        body = await _body(request)
        if body is None:
            return _json_error("Corpo JSON inválido ou muito grande.", 400)
        allowed = {"name", "card_ids", "exemplar_ids", "leader_id"}
        if set(body) - allowed:
            return _json_error("A requisição contém campos não permitidos.", 400)
        name = body.get("name")
        card_ids = body.get("card_ids")
        exemplar_ids = body.get("exemplar_ids")
        leader_id = body.get("leader_id")
        if not isinstance(name, str) or not isinstance(card_ids, list) or not isinstance(exemplar_ids, list) or not isinstance(leader_id, str):
            return _json_error("Dados do deck inválidos.", 400)
        gateway = _gateway(bot)
        leader = gateway.catalog.leader_registry.get(leader_id)
        if leader is None:
            return _json_error("Líder não permitido na alpha.", 400)
        try:
            saved = await gateway.save_deck(
                authenticated_player_id=uid,
                deck_id=f"web-{uuid.uuid4().hex}",
                name=name,
                card_ids=card_ids,
                exemplar_ids=exemplar_ids,
                faction_id=str(leader.get("faction_id") or ""),
                leader_id=leader_id,
            )
            return web.json_response({"deck": saved}, status=201, headers={"Cache-Control": "no-store"})
        except InvalidOperation as exc:
            return _json_error("Deck inválido: verifique tamanho, cópias, líder e coleção.", 400)
        except PersistenceConflict:
            return _json_error("Conflito ao salvar o deck. Atualize a página e tente novamente.", 409)
        except Exception:
            import logging
            logging.getLogger("site_card_engine_v2").exception("Deck create failed")
            return _json_error("Não foi possível salvar o deck.", 503)

    async def deck_update(request: web.Request) -> web.Response:
        uid = _player_id(bot, request)
        if uid is None:
            return _json_error("Autenticação necessária.", 401)
        if not bot._api_origin_ok(request):
            return _json_error("Origem não autorizada.", 403)
        body = await _body(request)
        if body is None:
            return _json_error("Corpo JSON inválido ou muito grande.", 400)
        if set(body) != {"name", "card_ids", "exemplar_ids", "leader_id", "expected_version"}:
            return _json_error("Campos do deck ou versão esperada inválidos.", 400)
        expected_version = body.get("expected_version")
        if (not isinstance(expected_version, int) or isinstance(expected_version, bool)
                or expected_version < 1):
            return _json_error("Versão esperada inválida.", 400)
        gateway = _gateway(bot)
        leader_id = body.get("leader_id")
        leader = gateway.catalog.leader_registry.get(leader_id) if isinstance(leader_id, str) else None
        if leader is None:
            return _json_error("Líder não permitido na alpha.", 400)
        try:
            saved = await gateway.save_deck(
                authenticated_player_id=uid,
                deck_id=request.match_info["deck_id"],
                name=body["name"], card_ids=body["card_ids"], exemplar_ids=body["exemplar_ids"],
                faction_id=str(leader.get("faction_id") or ""), leader_id=leader_id,
                expected_version=expected_version,
            )
            return web.json_response({"deck": saved}, headers={"Cache-Control": "no-store"})
        except PersistenceConflict:
            return _json_error("O deck foi alterado em outra sessão. Recarregue antes de salvar.", 409)
        except InvalidOperation:
            return _json_error("Deck inválido ou exemplares não pertencem mais à sua coleção.", 400)
        except Exception:
            import logging
            logging.getLogger("site_card_engine_v2").exception("Deck update failed")
            return _json_error("Não foi possível atualizar o deck.", 503)

    async def deck_delete(request: web.Request) -> web.Response:
        uid = _player_id(bot, request)
        if uid is None:
            return _json_error("Autenticação necessária.", 401)
        if not bot._api_origin_ok(request):
            return _json_error("Origem não autorizada.", 403)
        body = await _body(request)
        if body is None or set(body) != {"expected_version"}:
            return _json_error("Versão esperada inválida.", 400)
        expected_version = body["expected_version"]
        if (not isinstance(expected_version, int) or isinstance(expected_version, bool)
                or expected_version < 1):
            return _json_error("Versão esperada inválida.", 400)
        try:
            deleted = await _gateway(bot).delete_deck(
                authenticated_player_id=uid,
                deck_id=request.match_info["deck_id"],
                expected_version=expected_version,
            )
            if not deleted:
                return _json_error("Deck não encontrado ou versão desatualizada.", 409)
            return web.json_response({"deleted": True}, headers={"Cache-Control": "no-store"})
        except PersistenceConflict:
            return _json_error("O deck foi alterado em outra sessão. Recarregue antes de excluir.", 409)
        except Exception:
            import logging
            logging.getLogger("site_card_engine_v2").exception("Deck delete failed")
            return _json_error("Não foi possível excluir o deck.", 503)

    async def matches_list(request: web.Request) -> web.Response:
        uid = _player_id(bot, request)
        if uid is None:
            return _json_error("Autenticação necessária.", 401)
        try:
            rows = await _gateway(bot).list_matches(uid, limit=50)
            return web.json_response({"matches": rows}, headers={"Cache-Control": "private, no-store"})
        except Exception:
            return _json_error("Não foi possível consultar suas partidas.", 503)

    async def match_get(request: web.Request) -> web.Response:
        uid = _player_id(bot, request)
        if uid is None:
            return _json_error("Autenticação necessária.", 401)
        try:
            match_id = int(request.match_info["match_id"])
            cursor = int(request.query.get("after", "0"))
            if match_id <= 0 or cursor < 0:
                raise ValueError
            view = await _gateway(bot).player_view(match_id=match_id, authenticated_player_id=uid)
            history = await _gateway(bot).match_history(
                match_id=match_id, authenticated_player_id=uid, after_sequence=cursor, limit=50
            )
            return web.json_response({"view": view, "history": history}, headers={"Cache-Control": "private, no-store"})
        except (ValueError, TypeError):
            return _json_error("Identificador ou cursor inválido.", 400)
        except (InvalidOperation, MatchNotFound):
            return _json_error("Partida não encontrada ou indisponível para sua conta.", 404)
        except Exception:
            return _json_error("Não foi possível abrir a partida.", 503)

    async def match_action(request: web.Request) -> web.Response:
        uid = _player_id(bot, request)
        if uid is None:
            return _json_error("Autenticação necessária.", 401)
        if not bot._api_origin_ok(request):
            return _json_error("Origem não autorizada.", 403)
        body = await _body(request)
        if body is None:
            return _json_error("Corpo JSON inválido ou muito grande.", 400)
        action = body.get("action")
        payload = body.get("payload")
        if (set(body) != {"action", "payload"} or not isinstance(action, str)
                or action not in _ALLOWED_ACTIONS or not isinstance(payload, dict)):
            return _json_error("Ação não permitida.", 400)
        if set(payload) - _ALLOWED_ACTIONS[action]:
            return _json_error("A ação contém campos não permitidos.", 400)
        if (not isinstance(payload.get("expected_revision"), int)
                or isinstance(payload.get("expected_revision"), bool)
                or payload.get("expected_revision", -1) < 0):
            return _json_error("A revisão do estado é obrigatória.", 400)
        operation_id = payload.get("operation_id")
        try:
            parsed_operation = uuid.UUID(str(operation_id))
            if parsed_operation.version != 4 or str(parsed_operation) != str(operation_id).lower():
                raise ValueError
        except (ValueError, TypeError, AttributeError):
            return _json_error("operation_id UUIDv4 é obrigatório para idempotência.", 400)
        try:
            match_id = int(request.match_info["match_id"])
            if match_id <= 0:
                raise ValueError
            receipt = await _gateway(bot).execute_action(
                match_id=match_id,
                authenticated_player_id=uid,
                action=str(action),
                **payload,
            )
            raw_result = getattr(receipt, "result", receipt)
            raw_result = raw_result if isinstance(raw_result, dict) else {}
            safe_result = {
                key: raw_result[key] for key in ("outcome", "reason_code", "costs")
                if key in raw_result
            }
            replayed = bool(getattr(receipt, "replayed", False))
            new_view = await _gateway(bot).player_view(
                match_id=match_id, authenticated_player_id=uid
            )
            return web.json_response({"result": safe_result, "replayed": replayed, "view": new_view}, headers={"Cache-Control": "private, no-store"})
        except (ValueError, TypeError):
            return _json_error("Identificador de partida inválido.", 400)
        except (InvalidOperation, MatchNotFound):
            return _json_error("Ação recusada pelas regras atuais ou partida indisponível.", 409)
        except (PersistenceConflict, IdempotencyConflict):
            return _json_error("A partida mudou em outra sessão. Atualize e tente novamente.", 409)
        except Exception:
            import logging
            logging.getLogger("site_card_engine_v2").exception("Match action failed")
            return _json_error("Não foi possível executar a ação.", 503)

    async def target_offer(request: web.Request) -> web.Response:
        uid = _player_id(bot, request)
        if uid is None:
            return _json_error("Autenticação necessária.", 401)
        if not bot._api_origin_ok(request):
            return _json_error("Origem não autorizada.", 403)
        body = await _body(request)
        if body is None or set(body) - {"source_instance_id", "selected_row"} or not isinstance(body.get("source_instance_id"), str):
            return _json_error("Carta de origem inválida.", 400)
        selected_row = body.get("selected_row")
        if selected_row is not None and not isinstance(selected_row, str):
            return _json_error("Fileira selecionada inválida.", 400)
        try:
            match_id = int(request.match_info["match_id"])
            if match_id <= 0:
                raise ValueError
            offer = await _gateway(bot).target_offer(
                match_id=match_id, authenticated_player_id=uid,
                source_instance_id=body["source_instance_id"], selected_row=selected_row,
            )
            return web.json_response(offer, headers={"Cache-Control": "private, no-store"})
        except (ValueError, TypeError):
            return _json_error("Identificador de partida inválido.", 400)
        except (InvalidOperation, MatchNotFound):
            return _json_error("Ação indisponível para esta partida.", 409)
        except Exception:
            import logging
            logging.getLogger("site_card_engine_v2").exception("Target offer failed")
            return _json_error("Não foi possível calcular os alvos desta ação.", 503)

    async def sacrifice_offer(request: web.Request) -> web.Response:
        uid = _player_id(bot, request)
        if uid is None:
            return _json_error("Autenticação necessária.", 401)
        if not bot._api_origin_ok(request):
            return _json_error("Origem não autorizada.", 403)
        body = await _body(request)
        if body != {}:
            return _json_error("A oferta de sacrifício não aceita parâmetros do cliente.", 400)
        try:
            match_id = int(request.match_info["match_id"])
            if match_id <= 0:
                raise ValueError
            offer = await _gateway(bot).sacrifice_offer(
                match_id=match_id, authenticated_player_id=uid
            )
            return web.json_response(offer, headers={"Cache-Control": "private, no-store"})
        except (ValueError, TypeError):
            return _json_error("Identificador de partida inválido.", 400)
        except (InvalidOperation, MatchNotFound):
            return _json_error("Ação indisponível para esta partida.", 409)
        except Exception:
            import logging
            logging.getLogger("site_card_engine_v2").exception("Sacrifice offer failed")
            return _json_error("Não foi possível calcular os alvos de sacrifício.", 503)

    app.router.add_get("/card-engine-v2", page)
    app.router.add_get("/api/card-engine-v2/bootstrap", bootstrap)
    app.router.add_post("/api/card-engine-v2/decks", deck_save)
    app.router.add_put("/api/card-engine-v2/decks/{deck_id}", deck_update)
    app.router.add_delete("/api/card-engine-v2/decks/{deck_id}", deck_delete)
    app.router.add_get("/api/card-engine-v2/matches", matches_list)
    app.router.add_get("/api/card-engine-v2/matches/{match_id}", match_get)
    app.router.add_post("/api/card-engine-v2/matches/{match_id}/actions", match_action)
    app.router.add_post("/api/card-engine-v2/matches/{match_id}/target-offer", target_offer)
    app.router.add_post("/api/card-engine-v2/matches/{match_id}/sacrifice-offer", sacrifice_offer)


__all__ = ["registrar_rotas"]

"""Conquistas derivadas de registros autoritativos do Soulsbo.

O navegador nunca pode informar progresso. As métricas são calculadas no servidor
com o inventário e os registros de partida, e os desbloqueios são persistidos de
forma monotônica em `cartas_conquistas`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


ACHIEVEMENTS: tuple[dict[str, Any], ...] = (
    {
        "key": "first_blood",
        "name": "Primeiro Sangue",
        "description": "Vença sua primeira partida de cartas.",
        "metric": "wins",
        "target": 1,
        "category": "Competição",
    },
    {
        "key": "collector",
        "name": "Colecionador",
        "description": "Tenha 50 exemplares físicos na coleção.",
        "metric": "exemplars",
        "target": 50,
        "category": "Coleção",
    },
    {
        "key": "forger",
        "name": "Forjador",
        "description": "Faça ascensão de raridade em 10 exemplares distintos.",
        "metric": "forged_exemplars",
        "target": 10,
        "category": "Progressão",
    },
    {
        "key": "apostador",
        "name": "Apostador",
        "description": "Leve cinco cartas ao nível máximo de evolução.",
        "metric": None,
        "target": None,
        "category": "Progressão",
        "pending_reason": "O nível individual de evolução ainda não é persistido no inventário.",
    },
    {
        "key": "legend",
        "name": "Lenda",
        "description": "Obtenha um exemplar de raridade Singular.",
        "metric": "singular_exemplars",
        "target": 1,
        "category": "Coleção",
    },
    {
        "key": "survivor",
        "name": "Sobrevivente",
        "description": "Fracasse em três evoluções e preserve sua coleção.",
        "metric": None,
        "target": None,
        "category": "Progressão",
        "pending_reason": "As tentativas e falhas da evolução com risco ainda não são registradas.",
    },
    {
        "key": "perfectionist",
        "name": "Perfeccionista",
        "description": "Colecione todos os modelos de raridade Comum do catálogo oficial.",
        "metric": "common_models_owned",
        "target_metric": "common_models_total",
        "category": "Coleção",
    },
    {
        "key": "dedicado",
        "name": "Dedicado",
        "description": "Conclua 100 partidas de cartas.",
        "metric": "matches_played",
        "target": 100,
        "category": "Competição",
    },
)


def evaluate_achievement_cards(metrics: Mapping[str, int]) -> list[dict[str, Any]]:
    """Pure projection of metrics into user-facing cards; no persistence or writes."""
    results: list[dict[str, Any]] = []
    for definition in ACHIEVEMENTS:
        metric_key = definition.get("metric")
        if metric_key is None:
            results.append({
                **definition,
                "progress": None,
                "total": None,
                "unlocked": False,
                "status": "tracking_pending",
                "pending_reason": definition["pending_reason"],
            })
            continue
        progress = max(0, int(metrics.get(metric_key, 0) or 0))
        target = (
            max(0, int(metrics.get(definition["target_metric"], 0) or 0))
            if definition.get("target_metric")
            else max(1, int(definition["target"]))
        )
        if target <= 0:
            results.append({
                "key": definition["key"],
                "name": definition["name"],
                "description": definition["description"],
                "category": definition["category"],
                "progress": None,
                "total": None,
                "unlocked": False,
                "status": "tracking_pending",
                "pending_reason": "O catálogo atual ainda não possui modelos comuns para calcular esta meta.",
            })
            continue
        progress = min(progress, target)
        results.append({
            "key": definition["key"],
            "name": definition["name"],
            "description": definition["description"],
            "category": definition["category"],
            "progress": progress,
            "total": target,
            "unlocked": bool(target > 0 and progress >= target),
            "status": "unlocked" if target > 0 and progress >= target else "in_progress",
        })
    return results


async def load_user_achievement_metrics(database: Any, user_id: int) -> dict[str, int]:
    """Read only canonical legacy records and derive achievement metrics."""
    uid = int(user_id)
    if uid <= 0:
        raise ValueError("invalid_user_id")

    async def scalar(sql: str, args: tuple[Any, ...] = (), column: str = "total") -> int:
        row = await database._one(sql, args)
        return max(0, int(row[column] or 0)) if row else 0

    exemplars = await scalar(
        "SELECT COUNT(*) AS total FROM cartas_exemplares WHERE user_id=?", (uid,)
    )
    singular = await scalar(
        "SELECT COUNT(*) AS total FROM cartas_exemplares WHERE user_id=? AND rarity='Singular'",
        (uid,),
    )
    forged = await scalar(
        "SELECT COUNT(DISTINCT exemplar_id) AS total FROM cartas_movimentacoes "
        "WHERE user_id=? AND action='evolucao' AND exemplar_id IS NOT NULL",
        (uid,),
    )

    owned_rows = await database._all(
        "SELECT DISTINCT card_id FROM cartas_exemplares WHERE user_id=?", (uid,)
    )
    owned_card_ids = {str(row[0]) for row in owned_rows}
    from sistemas.cartas import CARTAS_POR_ID

    common_model_ids = {
        str(card.id)
        for card in CARTAS_POR_ID.values()
        if str(getattr(card, "raridade", "")).casefold() in {"comum", "common"}
    }
    common_owned = len(owned_card_ids.intersection(common_model_ids))

    ranking = await database._one(
        "SELECT COALESCE(wins,0) AS wins, COALESCE(losses,0) AS losses, "
        "COALESCE(draws,0) AS draws FROM cartas_gwent_rankings WHERE user_id=?",
        (uid,),
    )
    legacy_wins = max(0, int(ranking["wins"] or 0)) if ranking else 0
    legacy_losses = max(0, int(ranking["losses"] or 0)) if ranking else 0
    legacy_draws = max(0, int(ranking["draws"] or 0)) if ranking else 0

    return {
        "exemplars": exemplars,
        "singular_exemplars": singular,
        "forged_exemplars": forged,
        "common_models_owned": common_owned,
        "common_models_total": len(common_model_ids),
        "legacy_wins": legacy_wins,
        "legacy_matches_played": legacy_wins + legacy_losses + legacy_draws,
    }


async def persist_achievement_progress(
    database: Any,
    user_id: int,
    cards: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Persist progress and permanent unlocks idempotently under BEGIN IMMEDIATE."""
    uid = int(user_id)
    updated: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).date().isoformat()
    async with database.transaction() as tx:
        for card in cards:
            if card.get("status") == "tracking_pending":
                updated.append(dict(card))
                continue
            key = str(card["key"])
            row = await tx._one(
                "SELECT id,progresso,total,desbloqueada_em FROM cartas_conquistas "
                "WHERE user_id=? AND conquista=? ORDER BY id DESC LIMIT 1",
                (uid, key),
            )
            current_progress = int(card.get("progress") or 0)
            total = int(card.get("total") or 0)
            was_unlocked = bool(row and int(row["progresso"] or 0) >= max(1, int(row["total"] or 0)))
            is_unlocked = was_unlocked or (total > 0 and current_progress >= total)
            if was_unlocked and row:
                current_progress = max(current_progress, int(row["total"] or total))
            unlocked_at = (
                str(row["desbloqueada_em"] or now)
                if was_unlocked and row
                else (now if is_unlocked else "")
            )
            if row:
                await tx.conn.execute(
                    "UPDATE cartas_conquistas SET progresso=?,total=?,desbloqueada_em=? WHERE id=?",
                    (current_progress, total, unlocked_at, int(row["id"])),
                )
            else:
                await tx.conn.execute(
                    "INSERT INTO cartas_conquistas(user_id,conquista,progresso,total,desbloqueada_em) "
                    "VALUES(?,?,?,?,?)",
                    (uid, key, current_progress, total, unlocked_at),
                )
            result = dict(card)
            result.update({
                "progress": current_progress,
                "unlocked": is_unlocked,
                "status": "unlocked" if is_unlocked else "in_progress",
                "unlocked_at": unlocked_at or None,
            })
            updated.append(result)
    return updated


async def get_user_achievements(
    database: Any,
    user_id: int,
    *,
    v2_match_stats: Mapping[str, int] | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    metrics = await load_user_achievement_metrics(database, user_id)
    v2 = dict(v2_match_stats or {})
    metrics["wins"] = metrics["legacy_wins"] + max(0, int(v2.get("wins", 0) or 0))
    metrics["matches_played"] = metrics["legacy_matches_played"] + max(0, int(v2.get("played", 0) or 0))
    cards = evaluate_achievement_cards(metrics)
    if persist:
        persisted = await persist_achievement_progress(database, user_id, cards)
    else:
        stored_rows = await database._all(
            "SELECT conquista,progresso,total,desbloqueada_em FROM cartas_conquistas WHERE user_id=?",
            (int(user_id),),
        )
        stored = {str(row["conquista"]): row for row in stored_rows}
        persisted = []
        for card in cards:
            old = stored.get(str(card["key"]))
            was_unlocked = bool(
                old and int(old["total"] or 0) > 0
                and int(old["progresso"] or 0) >= int(old["total"] or 0)
            )
            result = dict(card)
            if was_unlocked:
                result["progress"] = max(int(card.get("progress") or 0), int(old["total"]))
                result["unlocked"] = True
                result["status"] = "unlocked"
                result["unlocked_at"] = str(old["desbloqueada_em"] or "") or None
            persisted.append(result)
    unlocked = sum(1 for item in persisted if item.get("unlocked"))
    trackable = sum(1 for item in persisted if item.get("status") != "tracking_pending")
    return {
        "achievements": persisted,
        "summary": {"unlocked": unlocked, "total": len(persisted), "trackable": trackable},
        "metrics": {
            "completed_matches": metrics["matches_played"],
            "wins": metrics["wins"],
            "physical_exemplars": metrics["exemplars"],
        },
    }

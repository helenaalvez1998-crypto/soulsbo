"""Fila de pesquisas do Caçador de Troféus.

Garante que um pedido de pesquisa nunca se perca nem se duplique:

* Existe no máximo UM pedido ativo por jogo (índice único parcial em `dedupe_key`).
  Repetir a busca, clicar duas vezes ou dois membros pedirem o mesmo jogo reaproveita o registro.
* Falhas de provedor (quota, rede, chave ausente) deixam o pedido em `waiting_provider`,
  com o motivo técnico para o administrador, e podem ser retomadas sem criar outro registro.
* Pesquisas interrompidas por reinício do bot são reconciliadas como `interrupted`.

Ciclo de vida:  queued -> researching -> review -> published | rejected
                          \\-> waiting_provider / failed / interrupted -> (retentar) researching
"""
from __future__ import annotations

import asyncio
import json
import logging

from trofeus_service import normalizar_texto

log = logging.getLogger("nara.trofeus.fila")

TERMINAIS = ("published", "rejected", "resolved")
REINICIAVEIS = ("queued", "waiting_provider", "failed", "interrupted", "needs_review")
_TERMINAIS_SQL = "('published','rejected','resolved')"

ROTULOS = {
    "queued": "na fila", "researching": "pesquisando", "review": "em revisão",
    "waiting_provider": "aguardando provedor", "failed": "falhou", "interrupted": "interrompida",
    "needs_review": "precisa de revisão", "published": "publicado", "rejected": "rejeitado",
    "resolved": "resolvido",
}


def chave_consulta(texto: str) -> str:
    """Chave para pedidos ainda sem título confirmado (só o texto digitado)."""
    return "q:" + normalizar_texto(texto)[:100]


def chave_jogo(slug: str) -> str:
    """Chave para pedidos com título oficial confirmado."""
    return "g:" + str(slug)[:100]


async def abrir_job(db, user_id: int, game_name: str, *, chave: str, status: str = "queued",
                    candidate: dict | None = None, details: str = "") -> tuple[int, bool, str]:
    """Cria o pedido ou devolve o ativo existente. Retorna (job_id, criado, status_atual)."""
    nome = " ".join(str(game_name or "").split())[:160] or "Jogo sem nome"
    candidato = json.dumps(candidate, ensure_ascii=False) if candidate else ""
    async with db.transaction() as tx:
        existente = await tx._one(
            f"SELECT id,status FROM catalog_import_jobs WHERE dedupe_key=? AND status NOT IN {_TERMINAIS_SQL}",
            (chave,),
        )
        if existente:
            if candidato:
                await tx.conn.execute(
                    "UPDATE catalog_import_jobs SET candidate_json=? WHERE id=? AND candidate_json=''",
                    (candidato, existente["id"]),
                )
            return int(existente["id"]), False, str(existente["status"])
        cur = await tx.conn.execute(
            """INSERT INTO catalog_import_jobs(requested_by,game_name,status,progress,details,
                                               candidate_json,dedupe_key,updated_at)
               VALUES (?,?,?,0,?,?,?,CURRENT_TIMESTAMP)""",
            (int(user_id), nome, status, str(details)[:1500], candidato, chave),
        )
        return int(cur.lastrowid), True, status


async def obter_job(db, job_id: int):
    return await db._one("SELECT * FROM catalog_import_jobs WHERE id=?", (int(job_id),))


async def promover_para_jogo(db, job_id: int, slug: str, game_name: str, candidate: dict) -> int:
    """Um pedido de texto livre virou jogo confirmado: troca a chave e guarda o candidato.

    Se já houver outro pedido ativo para o mesmo jogo, o pedido de texto é encerrado como
    `resolved` e o id do pedido existente é devolvido (evita dois registros do mesmo jogo).
    """
    chave = chave_jogo(slug)
    async with db.transaction() as tx:
        outro = await tx._one(
            f"SELECT id FROM catalog_import_jobs WHERE dedupe_key=? AND status NOT IN {_TERMINAIS_SQL} AND id<>?",
            (chave, int(job_id)),
        )
        if outro:
            await tx.conn.execute(
                "UPDATE catalog_import_jobs SET status='resolved', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (int(job_id),),
            )
            return int(outro["id"])
        await tx.conn.execute(
            """UPDATE catalog_import_jobs SET dedupe_key=?, game_name=?, candidate_json=?,
                   updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (chave, " ".join(str(game_name).split())[:160],
             json.dumps(candidate, ensure_ascii=False), int(job_id)),
        )
        return int(job_id)


async def encerrar_consulta(db, chave: str, exceto_id: int) -> None:
    """Pedidos de texto livre (`q:`) viram `resolved` quando o jogo confirmado ganha seu próprio pedido."""
    await db.conn.execute(
        f"""UPDATE catalog_import_jobs SET status='resolved', updated_at=CURRENT_TIMESTAMP
            WHERE dedupe_key=? AND id<>? AND status NOT IN {_TERMINAIS_SQL}""",
        (chave, int(exceto_id)),
    )
    await db.conn.commit()


async def marcar_pesquisando(db, job_id: int, *, expira_minutos: int = 10) -> bool:
    """Reserva o pedido para UMA execução. False se outra execução já está em andamento."""
    expira_minutos = max(1, int(expira_minutos))
    async with db.transaction() as tx:
        cur = await tx.conn.execute(
            """UPDATE catalog_import_jobs
               SET status='researching', progress=5, attempts=attempts+1, last_error='',
                   updated_at=CURRENT_TIMESTAMP
               WHERE id=? AND (status IN ('queued','waiting_provider','failed','interrupted','needs_review')
                               OR (status='researching' AND updated_at < datetime('now', ?)))""",
            (int(job_id), f"-{expira_minutos} minutes"),
        )
        return cur.rowcount == 1


async def adiar_job(db, job_id: int, motivo: str) -> None:
    """Devolve o pedido à fila (sem tentativa gasta) quando a pesquisa não pôde nem começar."""
    await db.conn.execute(
        """UPDATE catalog_import_jobs SET status='queued', progress=0, attempts=MAX(0,attempts-1),
               last_error=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
        (str(motivo)[:1500], int(job_id)),
    )
    await db.conn.commit()


async def concluir_job(db, job_id: int, game_id: int, details: dict) -> None:
    await db.conn.execute(
        """UPDATE catalog_import_jobs SET status='review', progress=100, game_id=?, details=?,
               last_error='', updated_at=CURRENT_TIMESTAMP WHERE id=?""",
        (int(game_id), json.dumps(details, ensure_ascii=False)[:60000], int(job_id)),
    )
    await db.conn.commit()


def classificar_erro(exc: BaseException) -> tuple[bool, str, str]:
    """Retorna (transitoria, mensagem_admin, mensagem_usuario).

    Transitória = vale tentar de novo depois (quota, rede, chave ausente corrigível).
    A mensagem do usuário nunca expõe detalhes técnicos.
    """
    admin = getattr(exc, "admin_message", None)
    user = getattr(exc, "user_message", None)
    if admin or user:
        tecnico = getattr(exc, "technical_message", "")
        detalhe = f"{admin or user}" + (f" Detalhe: {tecnico}" if tecnico and tecnico not in str(admin) else "")
        return True, detalhe[:1800], str(user or admin)[:400]
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError, ConnectionError)):
        return True, f"Tempo esgotado ou conexão perdida: {type(exc).__name__}", (
            "O serviço de pesquisa demorou demais para responder.")
    if isinstance(exc, (ValueError, RuntimeError)) and str(exc).strip():
        texto = str(exc).strip()[:400]
        return False, f"{type(exc).__name__}: {texto}", texto
    return False, f"{type(exc).__name__}: {str(exc)[:600]}", "Ocorreu um erro inesperado ao pesquisar este jogo."


async def registrar_falha(db, job_id: int, exc: BaseException) -> tuple[bool, str]:
    """Grava a falha preservando o pedido. Retorna (transitoria, mensagem_para_o_usuario)."""
    transitoria, admin_msg, user_msg = classificar_erro(exc)
    await db.conn.execute(
        """UPDATE catalog_import_jobs SET status=?, last_error=?, details=?, updated_at=CURRENT_TIMESTAMP
           WHERE id=?""",
        ("waiting_provider" if transitoria else "failed", admin_msg[:1800], admin_msg[:1500], int(job_id)),
    )
    await db.conn.commit()
    return transitoria, user_msg


async def reconciliar_orfaos(db, minutos: int = 5) -> int:
    """Marca como `interrupted` pesquisas 'researching' paradas. Na partida use minutos=0."""
    minutos = max(0, int(minutos))
    cur = await db.conn.execute(
        """UPDATE catalog_import_jobs SET status='interrupted',
               last_error='Pesquisa interrompida (reinício ou tempo esgotado). Use /catalogo_retentar.',
               updated_at=CURRENT_TIMESTAMP
           WHERE status='researching' AND updated_at <= datetime('now', ?)""",
        (f"-{minutos} minutes",),
    )
    await db.conn.commit()
    return cur.rowcount or 0


async def encerrar_jobs_do_jogo(db, game_id: int, status: str) -> None:
    """Fecha pedidos ligados ao jogo quando o catálogo é publicado ou rejeitado."""
    await db.conn.execute(
        f"UPDATE catalog_import_jobs SET status=?, updated_at=CURRENT_TIMESTAMP WHERE game_id=? AND status NOT IN {_TERMINAIS_SQL}",
        (status, int(game_id)),
    )
    await db.conn.commit()


async def listar_fila(db, limite: int = 15, *, somente_pendentes: bool = False):
    limite = max(1, min(25, int(limite)))
    filtro = f"WHERE status NOT IN {_TERMINAIS_SQL}" if somente_pendentes else ""
    return await db._all(
        f"""SELECT id,game_name,requested_by,status,attempts,last_error,details,created_at,updated_at,
                   candidate_json<>'' AS tem_candidato
            FROM catalog_import_jobs {filtro} ORDER BY id DESC LIMIT ?""",
        (limite,),
    )


def resumo_job(row) -> str:
    """Uma linha legível para a fila administrativa."""
    erro = str(row["last_error"] or "").strip()
    if erro:
        return erro
    detalhe = str(row["details"] or "").strip()
    try:
        dados = json.loads(detalhe)
        if isinstance(dados, dict):
            if dados.get("coverage_notes"):
                return str(dados["coverage_notes"])
            if dados.get("items") is not None:
                return f"{dados.get('items', 0)} itens, {dados.get('trophies', 0)} troféus coletados."
            return ""
    except (ValueError, TypeError):
        pass
    return detalhe

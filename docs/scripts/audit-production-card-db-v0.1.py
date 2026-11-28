#!/usr/bin/env python3
"""Exporta inventário agregado/sanitizado do SQLite de cartas (somente leitura).

Não exporta user_id, reviewer_id, prompt_text, rejection_reason, image_data,
BLOBs, segredos nem conteúdo de partidas. image_key é convertido em SHA-256;
assim, pode ser correlacionado com o inventário R2 sem expor caminhos/IDs de usuário.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

TABLES = (
    "cartas_colecao", "cartas_exemplares", "cartas_gwent_decks",
    "cartas_gwent_matches", "cartas_atelie_sessoes", "cartas_atelie_artes",
    "cartas_atelie_submissoes", "cartas_gwent_lideres_artes",
    "cartas_geradas", "cartas_geradas_artes", "cartas_geradas_habilidades",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _outside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(_repo_root())
        return False
    except ValueError:
        return True


def _hash_key(value: object) -> str | None:
    key = str(value or "").strip()
    if not key:
        return None
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _key_namespace(value: object) -> str:
    key = str(value or "").strip().lstrip("/")
    parts = [p for p in key.split("/") if p]
    if len(parts) >= 2 and parts[0] == "atelier" and parts[1] == "submissions":
        return "atelier/submissions"
    if parts and parts[0] == "cards":
        return "cards"
    return parts[0] if parts else "empty"


def _columns(conn: sqlite3.Connection, table: str) -> list[dict]:
    rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    return [
        {"name": row[1], "type": row[2], "notnull": bool(row[3]), "primary_key": bool(row[5])}
        for row in rows
    ]


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def _row_count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])


def _group_counts(conn: sqlite3.Connection, table: str, column: str) -> dict[str, int]:
    allowed = {c["name"] for c in _columns(conn, table)}
    if column not in allowed:
        return {}
    rows = conn.execute(
        f"""SELECT COALESCE(CAST("{column}" AS TEXT), '<NULL>') AS k, COUNT(*) AS n """
        f'FROM "{table}" GROUP BY "{column}" ORDER BY n DESC, k'
    ).fetchall()
    return {str(row[0]): int(row[1]) for row in rows}


def _path_kind(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "empty"
    if "://" in raw:
        return "uri"
    if raw.startswith(("/", "\\")) or (len(raw) > 2 and raw[1:3] == ":\\"):
        return "absolute_path"
    return "relative_path"


def build_report(db_path: Path, *, verify_local_generated_art: bool = False, data_dir: Path | None = None) -> dict:
    db_path = db_path.expanduser().resolve()
    if not db_path.is_file():
        raise FileNotFoundError(f"Banco não encontrado: {db_path}")
    uri = f"file:{quote(str(db_path), safe='/')}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA query_only = ON")
        conn.execute("BEGIN")
        quick = [r[0] for r in conn.execute("PRAGMA quick_check")]
        if quick != ["ok"]:
            raise RuntimeError(f"PRAGMA quick_check falhou: {quick[:10]}")

        tables: dict[str, dict] = {}
        for table in TABLES:
            exists = _table_exists(conn, table)
            tables[table] = {
                "exists": exists,
                "row_count": _row_count(conn, table) if exists else None,
                "columns": _columns(conn, table) if exists else [],
            }

        report: dict = {
            "schema": "card-game-production-db-audit/v0.1",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": {
                "basename": db_path.name,
                "bytes": db_path.stat().st_size,
                "read_only": True,
                "query_only": True,
                "quick_check": "ok",
                "journal_mode": str(conn.execute("PRAGMA journal_mode").fetchone()[0]),
                "schema_version": int(conn.execute("PRAGMA schema_version").fetchone()[0]),
                "user_version": int(conn.execute("PRAGMA user_version").fetchone()[0]),
            },
            "tables": tables,
            "inventory": {},
            "atelier": {},
            "art_storage": {},
            "matches": {},
            "privacy": {
                "user_ids_exported": False,
                "reviewer_ids_exported": False,
                "prompt_text_exported": False,
                "rejection_reasons_exported": False,
                "image_bytes_exported": False,
                "image_keys_exported": False,
                "image_key_hashes_exported": True,
                "match_state_exported": False,
            },
        }

        # Coleção agregada por modelo, sem qualquer identificador de jogador.
        if tables["cartas_colecao"]["exists"]:
            report["inventory"]["collection"] = {
                "rows": tables["cartas_colecao"]["row_count"],
                "models": int(conn.execute("SELECT COUNT(DISTINCT card_id) FROM cartas_colecao").fetchone()[0]),
                "total_quantity": int(conn.execute("SELECT COALESCE(SUM(quantidade),0) FROM cartas_colecao").fetchone()[0]),
                "by_card_id": [
                    {"card_id": str(r[0]), "quantity": int(r[1])}
                    for r in conn.execute("SELECT card_id,SUM(quantidade) FROM cartas_colecao GROUP BY card_id ORDER BY card_id")
                ],
            }
        if tables["cartas_exemplares"]["exists"]:
            report["inventory"]["exemplars"] = {
                "rows": tables["cartas_exemplares"]["row_count"],
                "by_card_rarity_power_source": [
                    {"card_id": str(r[0]), "rarity": str(r[1]), "power": int(r[2]), "source": str(r[3]), "count": int(r[4])}
                    for r in conn.execute(
                        "SELECT card_id,rarity,power,source,COUNT(*) FROM cartas_exemplares "
                        "GROUP BY card_id,rarity,power,source ORDER BY card_id,rarity,power,source"
                    )
                ],
            }
        if tables["cartas_gwent_decks"]["exists"]:
            deck_columns = {c["name"] for c in tables["cartas_gwent_decks"]["columns"]}
            deck_select = []
            for column, fallback in (
                ("card_ids_json", "'[]'"), ("exemplar_ids_json", "'[]'"),
                ("faction", "''"), ("leader_id", "''"), ("relic_id", "''"),
            ):
                deck_select.append(f'"{column}"' if column in deck_columns else f'{fallback} AS "{column}"')
            deck_rows = conn.execute(
                "SELECT " + ",".join(deck_select) + " FROM cartas_gwent_decks"
            ).fetchall()
            usage: Counter[str] = Counter()
            shape = Counter()
            malformed_card_json = 0
            malformed_exemplar_json = 0
            for row in deck_rows:
                try:
                    card_ids = json.loads(row["card_ids_json"] or "[]")
                    if not isinstance(card_ids, list):
                        raise ValueError("card_ids_json não é array")
                    for item in card_ids:
                        if isinstance(item, dict):
                            value = item.get("card_id") or item.get("id")
                        else:
                            value = item
                        if value:
                            usage[str(value)] += 1
                except (TypeError, ValueError, json.JSONDecodeError):
                    malformed_card_json += 1
                    card_ids = []
                try:
                    exemplar_ids = json.loads(row["exemplar_ids_json"] or "[]")
                    if not isinstance(exemplar_ids, list):
                        raise ValueError("exemplar_ids_json não é array")
                except (TypeError, ValueError, json.JSONDecodeError):
                    malformed_exemplar_json += 1
                    exemplar_ids = []
                shape[(str(row["faction"] or ""), str(row["leader_id"] or ""), str(row["relic_id"] or ""))] += 1
            report["inventory"]["decks"] = {
                "rows": len(deck_rows),
                "malformed_card_ids_json": malformed_card_json,
                "malformed_exemplar_ids_json": malformed_exemplar_json,
                "by_faction_leader_relic": [
                    {"faction": k[0], "leader_id": k[1], "relic_id": k[2], "deck_count": n}
                    for k, n in sorted(shape.items())
                ],
                "card_model_usage": [{"card_id": k, "deck_occurrences": v} for k, v in sorted(usage.items())],
            }

        # Partidas: apenas contagens/status e presença de campos de snapshot; nunca state_json.
        if tables["cartas_gwent_matches"]["exists"]:
            status_counts = _group_counts(conn, "cartas_gwent_matches", "status")
            snapshot_fields = Counter()
            invalid_snapshots = 0
            for row in conn.execute("SELECT state_json FROM cartas_gwent_matches"):
                try:
                    state = json.loads(row[0] or "{}")
                    if isinstance(state, dict):
                        snapshot_fields.update(state.keys())
                except (TypeError, ValueError, json.JSONDecodeError):
                    invalid_snapshots += 1
            report["matches"] = {
                "rows": tables["cartas_gwent_matches"]["row_count"],
                "by_status": status_counts,
                "invalid_state_json_rows": invalid_snapshots,
                "top_level_snapshot_key_presence_counts": dict(sorted(snapshot_fields.items())),
                "state_payload_exported": False,
            }

        # Submissões R2/SQLite do Ateliê: hash da key em vez do caminho bruto.
        if tables["cartas_atelie_submissoes"]["exists"]:
            cols = {c["name"] for c in tables["cartas_atelie_submissoes"]["columns"]}
            wanted = [c for c in (
                "id", "card_id", "exemplar_id", "full_card", "status", "mime_type",
                "created_at", "reviewed_at", "image_key", "image_data",
            ) if c in cols]
            rows = conn.execute(
                "SELECT " + ",".join(f'"{c}"' for c in wanted) + " FROM cartas_atelie_submissoes ORDER BY id"
            ).fetchall()
            submissions = []
            status = Counter()
            source_by_status = Counter()
            approved_no_source = 0
            approved_duplicates = Counter()
            for row in rows:
                d = dict(row)
                key = str(d.get("image_key") or "")
                blob_bytes = len(d.get("image_data") or b"")
                st = str(d.get("status") or "<NULL>")
                status[st] += 1
                source = "r2_key" if key else ("legacy_sqlite_blob" if blob_bytes else "missing")
                source_by_status[(st, source)] += 1
                if st == "approved":
                    if source == "missing":
                        approved_no_source += 1
                    approved_duplicates[(str(d.get("card_id") or ""), str(d.get("exemplar_id") or "<NULL>"))] += 1
                submissions.append({
                    "submission_id": int(d["id"]),
                    "card_id": str(d.get("card_id") or ""),
                    "exemplar_id": d.get("exemplar_id"),
                    "full_card": bool(d.get("full_card") or 0),
                    "status": st,
                    "mime_type": str(d.get("mime_type") or ""),
                    "created_at": d.get("created_at"),
                    "reviewed_at": d.get("reviewed_at"),
                    "image_source": source,
                    "image_data_bytes": blob_bytes,
                    "image_key_sha256": _hash_key(key),
                    "image_key_namespace": _key_namespace(key) if key else None,
                })
            duplicate_approved_keys = [
                {"card_id": card_id, "exemplar_id": exemplar_id, "approved_rows": n}
                for (card_id, exemplar_id), n in sorted(approved_duplicates.items()) if n > 1
            ]
            report["atelier"]["submissions"] = {
                "rows": len(rows), "by_status": dict(status),
                "by_status_and_image_source": [
                    {"status": k[0], "image_source": k[1], "count": v}
                    for k, v in sorted(source_by_status.items())
                ],
                "approved_without_any_image_source": approved_no_source,
                "duplicate_approved_card_exemplar_pairs": duplicate_approved_keys,
                "records": submissions,
            }

        # Fluxo antigo com anexo Discord: não se deve esperar imagem no R2.
        if tables["cartas_atelie_artes"]["exists"]:
            cols = {c["name"] for c in tables["cartas_atelie_artes"]["columns"]}
            wanted = [c for c in ("id", "card_id", "status", "channel_id", "message_id", "attachment_id", "created_at", "reviewed_at") if c in cols]
            rows = conn.execute("SELECT " + ",".join(f'"{c}"' for c in wanted) + " FROM cartas_atelie_artes ORDER BY id").fetchall()
            status = Counter()
            details = []
            for row in rows:
                d = dict(row)
                st = str(d.get("status") or "<NULL>")
                status[st] += 1
                has_attachment = bool(d.get("attachment_id") or d.get("message_id"))
                details.append({
                    "request_id": int(d["id"]), "card_id": str(d.get("card_id") or ""),
                    "status": st, "discord_attachment_reference_present": has_attachment,
                    "created_at": d.get("created_at"), "reviewed_at": d.get("reviewed_at"),
                })
            report["atelier"]["discord_attachment_requests"] = {
                "rows": len(rows), "by_status": dict(status), "records": details,
                "note": "Este fluxo referencia anexos do Discord; não é inventário R2.",
            }

        if tables["cartas_atelie_sessoes"]["exists"]:
            report["atelier"]["sessions"] = {
                "rows": tables["cartas_atelie_sessoes"]["row_count"],
                "by_status": _group_counts(conn, "cartas_atelie_sessoes", "status"),
            }

        if tables["cartas_gwent_lideres_artes"]["exists"]:
            cols = {c["name"] for c in tables["cartas_gwent_lideres_artes"]["columns"]}
            selected = [c for c in ("leader_id", "mime_type", "revision", "created_at", "updated_at", "image_data") if c in cols]
            rows = conn.execute("SELECT " + ",".join(f'"{c}"' for c in selected) + " FROM cartas_gwent_lideres_artes ORDER BY leader_id").fetchall()
            report["art_storage"]["leader_art_blobs"] = {
                "rows": len(rows),
                "records": [{
                    "leader_id": str(r["leader_id"]),
                    "mime_type": str(r["mime_type"] or ""),
                    "revision": str(r["revision"] or ""),
                    "image_data_bytes": len(r["image_data"] or b""),
                    "created_at": r["created_at"], "updated_at": r["updated_at"],
                } for r in rows],
                "note": "As artes de líder desta tabela ficam em BLOB no SQLite; não são objetos R2.",
            }

        if tables["cartas_geradas"]["exists"]:
            cols = {c["name"] for c in tables["cartas_geradas"]["columns"]}
            wanted = [c for c in ("card_id", "rarity", "faction", "power", "art_path", "art_status", "status", "generator_version", "created_at") if c in cols]
            rows = conn.execute("SELECT " + ",".join(f'"{c}"' for c in wanted) + " FROM cartas_geradas ORDER BY card_id").fetchall()
            status = Counter()
            records = []
            for row in rows:
                d = dict(row)
                status[(str(d.get("status") or ""), str(d.get("art_status") or ""))] += 1
                records.append({
                    "card_id": str(d.get("card_id") or ""), "rarity": str(d.get("rarity") or ""),
                    "faction": str(d.get("faction") or ""), "power": d.get("power"),
                    "status": str(d.get("status") or ""), "art_status": str(d.get("art_status") or ""),
                    "art_path_kind": _path_kind(d.get("art_path")),
                    "generator_version": str(d.get("generator_version") or ""), "created_at": d.get("created_at"),
                })
            if verify_local_generated_art:
                for record, raw_row in zip(records, rows):
                    raw_path = str(raw_row["art_path"] or "")
                    candidate = Path(raw_path).expanduser() if raw_path else None
                    candidates = []
                    if candidate is not None:
                        if candidate.is_absolute():
                            candidates.append(candidate)
                        else:
                            candidates.append(candidate.resolve())
                            if data_dir is not None:
                                candidates.append((data_dir.expanduser().resolve() / candidate).resolve())
                    actual = next((p for p in candidates if p.is_file()), None)
                    record["art_path_local_file_check"] = {
                        "checked": True, "exists": actual is not None,
                        "bytes": actual.stat().st_size if actual is not None else None,
                    }
            report["art_storage"]["generated_cards"] = {
                "rows": len(rows),
                "by_card_status_and_art_status": [
                    {"card_status": k[0], "art_status": k[1], "count": v} for k, v in sorted(status.items())
                ],
                "local_file_verification_performed": bool(verify_local_generated_art),
                "records": records,
            }

        if tables["cartas_geradas_artes"]["exists"]:
            cols = {c["name"] for c in tables["cartas_geradas_artes"]["columns"]}
            wanted = [c for c in ("generated_card_id", "storage_path", "content_hash", "width", "height", "status", "created_at") if c in cols]
            rows = conn.execute("SELECT " + ",".join(f'"{c}"' for c in wanted) + " FROM cartas_geradas_artes ORDER BY generated_card_id").fetchall()
            generated_art_records = []
            for r in rows:
                raw_path = str(r["storage_path"] or "")
                record = {
                    "card_id": str(r["generated_card_id"] or ""), "content_hash": str(r["content_hash"] or ""),
                    "width": int(r["width"] or 0), "height": int(r["height"] or 0),
                    "status": str(r["status"] or ""), "storage_path_kind": _path_kind(raw_path),
                    "created_at": r["created_at"],
                }
                if verify_local_generated_art:
                    candidate = Path(raw_path).expanduser() if raw_path else None
                    candidates = []
                    if candidate is not None:
                        if candidate.is_absolute():
                            candidates.append(candidate)
                        else:
                            candidates.append(candidate.resolve())
                            if data_dir is not None:
                                candidates.append((data_dir.expanduser().resolve() / candidate).resolve())
                    actual = next((p for p in candidates if p.is_file()), None)
                    actual_hash = None
                    actual_size = None
                    if actual is not None:
                        digest = hashlib.sha256()
                        with actual.open("rb") as asset_file:
                            for chunk in iter(lambda: asset_file.read(1024 * 1024), b""):
                                digest.update(chunk)
                        actual_hash = digest.hexdigest()
                        actual_size = actual.stat().st_size
                    expected_hash = str(r["content_hash"] or "").strip().lower()
                    record["local_file_check"] = {
                        "checked": True,
                        "exists": actual is not None,
                        "bytes": actual_size,
                        "actual_sha256_matches_db": bool(actual_hash and expected_hash and actual_hash == expected_hash),
                    }
                generated_art_records.append(record)
            report["art_storage"]["generated_art_records"] = {
                "rows": len(rows),
                "by_status": _group_counts(conn, "cartas_geradas_artes", "status"),
                "local_file_verification_performed": bool(verify_local_generated_art),
                "records": generated_art_records,
            }

        report["notes"] = [
            "Relatório agregado; não contém IDs de usuário/revisor, prompts, razões de rejeição, BLOBs ou state_json.",
            "image_key é representada por SHA-256 e namespace; usar o reconciliador local para cruzar com o inventário R2.",
            "cartas_atelie_artes representa referências de anexo Discord; cartas_atelie_submissoes.image_key representa o caminho R2 do Ateliê novo.",
            "artes de líder são BLOB SQLite; artes de cartas geradas usam caminhos locais e/ou tabela cartas_geradas_artes.",
        ]
        return report
    finally:
        try:
            conn.rollback()
        except sqlite3.Error:
            pass
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, type=Path, help="SQLite de produção ou snapshot consistente")
    parser.add_argument("--output", required=True, type=Path, help="JSON sanitizado, fora do repositório")
    parser.add_argument("--verify-local-generated-art", action="store_true", help="Verifica existência/hash de artes locais sem exportar caminhos")
    parser.add_argument("--data-dir", type=Path, help="DATA_DIR de produção; usado como fallback para caminhos relativos")
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if not _outside_repo(output):
        print("ERRO: relatórios de produção devem ficar fora do repositório.", file=sys.stderr)
        return 2
    try:
        report = build_report(args.db, verify_local_generated_art=args.verify_local_generated_art, data_dir=args.data_dir)
        output.parent.mkdir(parents=True, exist_ok=True)
        temp = output.with_name(output.name + ".tmp")
        temp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.chmod(temp, 0o600)
        temp.replace(output)
    except Exception as exc:
        print(f"ERRO: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    sub = report.get("atelier", {}).get("submissions", {})
    print(f"Relatório salvo: {output}")
    print(f"Tabelas verificadas: {sum(1 for x in report['tables'].values() if x['exists'])}/{len(TABLES)}")
    print(f"Submissões Ateliê: {sub.get('rows', 0)}; sem origem de imagem aprovada: {sub.get('approved_without_any_image_source', 0)}")
    print("Relatório não contém user_id, prompt, image bytes, imagem nem state_json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

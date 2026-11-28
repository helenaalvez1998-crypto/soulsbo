#!/usr/bin/env python3
"""Reconcilia hashes image_key SQLite vs. inventário R2, sem revelar object keys."""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone


def reconcile(db_report: dict, r2_report: dict) -> dict:
    if db_report.get("schema") != "card-game-production-db-audit/v0.1":
        raise ValueError("Formato inesperado do relatório DB.")
    if r2_report.get("schema") != "cloudflare-r2-object-inventory/v0.1":
        raise ValueError("Formato inesperado do inventário R2.")
    if not r2_report.get("complete"):
        raise ValueError("Inventário R2 incompleto/truncado; não é possível classificar referências ausentes.")
    if not r2_report.get("scope", {}).get("all_objects"):
        raise ValueError("Inventário R2 filtrado por prefixo; a reconciliação exige todos os objetos do bucket primário.")

    db_sub = db_report.get("atelier", {}).get("submissions", {})
    records = db_sub.get("records", [])
    db_by_hash = {}
    status_refs = Counter()
    for row in records:
        key_hash = row.get("image_key_sha256")
        if key_hash:
            db_by_hash.setdefault(key_hash, []).append(row)
            status_refs[str(row.get("status") or "<NULL>")] += 1

    r2_primary_by_hash = {}
    r2_namespace = Counter()
    r2_size_namespace = Counter()
    primary_bucket_seen = False
    for bucket in r2_report.get("buckets", []):
        is_primary = bucket.get("alias") == "primary"
        primary_bucket_seen = primary_bucket_seen or is_primary
        for obj in bucket.get("objects", []):
            key_hash = obj.get("key_sha256")
            if not key_hash:
                continue
            namespace = str(obj.get("namespace") or "<unknown>")
            r2_namespace[namespace] += 1
            r2_size_namespace[namespace] += int(obj.get("size", 0))
            if is_primary:
                r2_primary_by_hash.setdefault(key_hash, []).append({
                    "bucket_alias": bucket.get("alias"),
                    "bucket": bucket.get("bucket"),
                    "namespace": namespace,
                    "size": int(obj.get("size", 0)),
                })
    if not primary_bucket_seen:
        raise ValueError("Inventário não contém bucket alias='primary', usado para uploads do Ateliê.")

    missing_by_status = Counter()
    approved_r2_missing_without_blob = 0
    approved_legacy_blob = 0
    missing_records = []
    wrong_namespace_by_status = Counter()
    for row in records:
        key_hash = row.get("image_key_sha256")
        if key_hash and key_hash in r2_primary_by_hash and row.get("image_key_namespace") != "atelier/submissions":
            wrong_namespace_by_status[str(row.get("status") or "<NULL>")] += 1
        if key_hash and key_hash not in r2_primary_by_hash:
            status = str(row.get("status") or "<NULL>")
            missing_by_status[status] += 1
            if status == "approved" and int(row.get("image_data_bytes") or 0) == 0:
                approved_r2_missing_without_blob += 1
            missing_records.append({
                "submission_id": row.get("submission_id"),
                "card_id": row.get("card_id"),
                "exemplar_id": row.get("exemplar_id"),
                "status": status,
                "image_data_bytes": int(row.get("image_data_bytes") or 0),
            })
        if row.get("status") == "approved" and row.get("image_source") == "legacy_sqlite_blob":
            approved_legacy_blob += 1

    r2_atelier_hashes = {
        key_hash for key_hash, entries in r2_primary_by_hash.items()
        if any(entry["namespace"] == "atelier/submissions" for entry in entries)
    }
    db_atelier_hashes = {
        key_hash for key_hash, rows_for_key in db_by_hash.items()
        if any(str(row.get("image_key_namespace")) == "atelier/submissions" for row in rows_for_key)
    }
    candidate_unlinked = r2_atelier_hashes - db_atelier_hashes

    return {
        "schema": "card-game-production-assets-reconciliation/v0.1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "db_report_schema": db_report.get("schema"),
            "r2_report_schema": r2_report.get("schema"),
            "r2_inventory_complete": True,
            "r2_inventory_scope_all_objects": True,
            "r2_primary_bucket": next(b.get("bucket") for b in r2_report.get("buckets", []) if b.get("alias") == "primary"),
            "r2_objects": int(r2_report.get("total_objects", 0)),
        },
        "database_references": {
            "atelier_submission_rows": len(records),
            "rows_with_r2_key": len(db_by_hash),
            "r2_references_by_status": dict(status_refs),
            "approved_legacy_blob_rows": approved_legacy_blob,
        },
        "r2_inventory": {
            "objects_by_namespace_across_inventoried_buckets": dict(r2_namespace),
            "primary_bucket_atelier_objects": sum(
                1 for entries in r2_primary_by_hash.values()
                if any(entry["namespace"] == "atelier/submissions" for entry in entries)
            ),
            "bytes_by_namespace": dict(r2_size_namespace),
        },
        "reconciliation": {
            "db_key_hashes_missing_from_r2_by_status": dict(missing_by_status),
            "db_key_hashes_found_but_wrong_namespace_by_status": dict(wrong_namespace_by_status),
            "approved_r2_refs_missing_and_without_legacy_blob": approved_r2_missing_without_blob,
            "unlinked_atelier_r2_objects_candidate_count": len(candidate_unlinked),
            "unlinked_atelier_object_key_hashes": sorted(candidate_unlinked),
            "missing_db_reference_records": missing_records,
            "public_cards_prefix_is_cache_not_direct_atelier_reference": True,
        },
        "safety": {
            "raw_object_keys_exported": False,
            "user_ids_exported": False,
            "images_downloaded": False,
            "objects_modified_or_deleted": False,
            "unlinked_objects_are_candidates_only": True,
            "automatic_cleanup_performed": False,
        },
        "interpretation": [
            "Approved R2 reference missing from a complete inventory is a high-priority broken-art candidate, but confirm correct bucket/credentials and backup age first.",
            "Unlinked atelier/submissions objects are candidates only; could be uploads not yet committed, deleted database history, or DB/R2 snapshot timing differences. Never delete automatically.",
            "The cards namespace contains public CDN cache variants and is not expected to have a one-to-one row in the Ateliê submission table.",
            "Discord attachment requests, leader-art BLOBs, and generated local art are separate pipelines; they are not expected in the R2 atelier namespace.",
        ],
    }


def _outside_repo(path: Path) -> bool:
    repo_root = Path(__file__).resolve().parents[2]
    try:
        path.resolve().relative_to(repo_root)
        return False
    except ValueError:
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-audit", required=True, type=Path)
    parser.add_argument("--r2-inventory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if not _outside_repo(output):
        print("ERRO: relatórios operacionais devem ficar fora do repositório.", file=sys.stderr)
        return 2
    try:
        db_report = json.loads(args.db_audit.read_text(encoding="utf-8"))
        r2_report = json.loads(args.r2_inventory.read_text(encoding="utf-8"))
        report = reconcile(db_report, r2_report)
        output.parent.mkdir(parents=True, exist_ok=True)
        temp = output.with_name(output.name + ".tmp")
        temp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.chmod(temp, 0o600)
        temp.replace(output)
    except Exception as exc:
        print(f"ERRO: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    rec = report["reconciliation"]
    print(f"Reconciliação salva: {output}")
    print(f"Referências R2 ausentes: {sum(rec['db_key_hashes_missing_from_r2_by_status'].values())}")
    print(f"Referências aprovadas ausentes sem BLOB legado: {rec['approved_r2_refs_missing_and_without_legacy_blob']}")
    print(f"Objetos atelier/submissions sem referência DB (candidatos): {rec['unlinked_atelier_r2_objects_candidate_count']}")
    print("Nenhum objeto foi excluído ou modificado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

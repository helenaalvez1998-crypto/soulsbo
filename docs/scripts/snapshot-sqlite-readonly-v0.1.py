#!/usr/bin/env python3
"""Cria snapshot consistente do SQLite sem abrir conexão de escrita na origem.

A origem é aberta com mode=ro e query_only. O SQLite Backup API lê uma visão
consistente inclusive quando o banco usa WAL. O destino é um arquivo sensível;
este script se recusa a gravá-lo dentro do repositório.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _outside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(_repo_root())
        return False
    except ValueError:
        return True


def create_snapshot(source_path: Path, output_path: Path) -> dict:
    source_path = source_path.expanduser().resolve()
    output_path = output_path.expanduser().resolve()

    if not source_path.is_file():
        raise FileNotFoundError(f"Banco de origem não encontrado: {source_path}")
    if source_path == output_path:
        raise ValueError("Origem e destino não podem ser o mesmo arquivo.")
    if not _outside_repo(output_path):
        raise ValueError("O snapshot contém dados de produção; grave-o fora do repositório.")
    if output_path.exists():
        raise FileExistsError(f"O destino já existe; não será sobrescrito: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Reserva o destino em modo exclusivo para evitar sobrescrever arquivo existente.
    with output_path.open("xb"):
        pass
    os.chmod(output_path, 0o600)

    uri = f"file:{quote(str(source_path), safe='/')}?mode=ro"
    source = None
    target = None
    try:
        source = sqlite3.connect(uri, uri=True, timeout=30)
        source.execute("PRAGMA query_only = ON")
        source.execute("BEGIN")
        quick_check = [row[0] for row in source.execute("PRAGMA quick_check")]
        if quick_check != ["ok"]:
            raise RuntimeError(f"PRAGMA quick_check da origem retornou: {quick_check[:10]}")

        target = sqlite3.connect(str(output_path), timeout=30)
        source.backup(target, pages=256, sleep=0.1)
        target.commit()
        dest_check = [row[0] for row in target.execute("PRAGMA quick_check")]
        if dest_check != ["ok"]:
            raise RuntimeError(f"PRAGMA quick_check do snapshot retornou: {dest_check[:10]}")
        table_count = int(target.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0])
        page_count = int(target.execute("PRAGMA page_count").fetchone()[0])
        page_size = int(target.execute("PRAGMA page_size").fetchone()[0])
        return {
            "source_basename": source_path.name,
            "snapshot_basename": output_path.name,
            "snapshot_bytes": output_path.stat().st_size,
            "table_count": table_count,
            "page_count": page_count,
            "page_size": page_size,
            "source_open_mode": "read-only (mode=ro)",
            "source_query_only": True,
            "backup_method": "sqlite3.Connection.backup",
            "source_quick_check": "ok",
            "snapshot_quick_check": "ok",
        }
    except Exception:
        if target is not None:
            target.close()
            target = None
        if source is not None:
            source.close()
            source = None
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    finally:
        if target is not None:
            target.close()
        if source is not None:
            try:
                source.rollback()
            except sqlite3.Error:
                pass
            source.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Caminho do SQLite de produção")
    parser.add_argument("--output", required=True, type=Path, help="Destino do snapshot, fora do repositório")
    args = parser.parse_args()
    try:
        result = create_snapshot(args.source, args.output)
    except Exception as exc:
        print(f"ERRO: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    for key, value in result.items():
        print(f"{key}: {value}")
    print("A origem foi aberta somente para leitura; o snapshot contém dados sensíveis e não deve ser commitado ou enviado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

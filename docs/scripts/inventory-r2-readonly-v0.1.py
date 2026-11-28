#!/usr/bin/env python3
"""Lista objetos Cloudflare R2 via S3 ListObjectsV2, sem baixar ou modificar dados.

Lê credenciais apenas do ambiente do processo. O relatório não guarda chaves S3,
IDs de conta nem object keys em texto: usa SHA-256 de cada chave para permitir
reconciliação local com image_key do SQLite. Não chama Get/Put/Delete/Copy/Head.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import boto3
    from botocore.config import Config
except ImportError:  # permite --help e compilação em ambientes sem boto3
    boto3 = None
    Config = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _outside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(_repo_root())
        return False
    except ValueError:
        return True


def _namespace(key: str) -> str:
    parts = [part for part in str(key or "").lstrip("/").split("/") if part]
    if len(parts) >= 2 and parts[:2] == ["atelier", "submissions"]:
        return "atelier/submissions"
    if parts and parts[0] == "cards":
        return "cards"
    return parts[0] if parts else "empty"


def _bucket_configs() -> list[dict[str, str]]:
    base = {
        "account_id": os.getenv("R2_ACCOUNT_ID", "").strip(),
        "access_key_id": os.getenv("R2_ACCESS_KEY_ID", "").strip(),
        "secret_access_key": os.getenv("R2_SECRET_ACCESS_KEY", "").strip(),
        "bucket": os.getenv("R2_BUCKET_NAME", "").strip(),
    }
    if not all(base.values()):
        missing = [k for k, v in base.items() if not v]
        raise ValueError("Variáveis R2_* ausentes no ambiente: " + ", ".join(missing))
    configs = [{"alias": "primary", **base}]

    public_bucket = os.getenv("R2_PUBLIC_CARDS_BUCKET_NAME", "").strip() or base["bucket"]
    if public_bucket != base["bucket"]:
        public = {
            "account_id": os.getenv("R2_PUBLIC_CARDS_ACCOUNT_ID", "").strip() or base["account_id"],
            "access_key_id": os.getenv("R2_PUBLIC_CARDS_ACCESS_KEY_ID", "").strip() or base["access_key_id"],
            "secret_access_key": os.getenv("R2_PUBLIC_CARDS_SECRET_ACCESS_KEY", "").strip() or base["secret_access_key"],
            "bucket": public_bucket,
        }
        if not all(public.values()):
            raise ValueError("Configuração incompleta do bucket R2_PUBLIC_CARDS_*.")
        configs.append({"alias": "public_cards", **public})
    return configs


def _client(config: dict[str, str]):
    if boto3 is None or Config is None:
        raise RuntimeError("Dependência boto3 ausente. Instale conforme requirements.txt.")
    return boto3.client(
        "s3",
        endpoint_url=f"https://{config['account_id']}.r2.cloudflarestorage.com",
        aws_access_key_id=config["access_key_id"],
        aws_secret_access_key=config["secret_access_key"],
        region_name="auto",
        config=Config(
            signature_version="s3v4", connect_timeout=5, read_timeout=30,
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    )


def write_inventory(output: Path, prefixes: list[str] | None = None, max_objects: int = 0) -> dict:
    output = output.expanduser().resolve()
    if not _outside_repo(output):
        raise ValueError("O inventário R2 deve ser gravado fora do repositório.")
    if output.exists():
        raise FileExistsError(f"O arquivo de saída já existe; não será sobrescrito: {output}")
    configs = _bucket_configs()
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name + ".tmp")
    temp.unlink(missing_ok=True)

    bucket_summaries = []
    total_objects = 0
    complete = True
    try:
        with temp.open("w", encoding="utf-8") as stream:
            stream.write('{"schema":"cloudflare-r2-object-inventory/v0.1",')
            stream.write(f'"created_at_utc":{json.dumps(datetime.now(timezone.utc).isoformat())},')
            stream.write('"read_only":true,"operations_used":["ListObjectsV2"],')
            stream.write('"scope":' + json.dumps({"all_objects": not bool(prefixes), "prefixes": prefixes or []}, ensure_ascii=False) + ',"buckets":[')
            for index, config in enumerate(configs):
                if index:
                    stream.write(",")
                stream.write("{")
                stream.write('"alias":' + json.dumps(config["alias"]) + ",")
                stream.write('"bucket":' + json.dumps(config["bucket"]) + ",")
                stream.write('"objects":[')
                client = _client(config)
                paginator = client.get_paginator("list_objects_v2")
                first = True
                count = 0
                namespace_counts: dict[str, int] = {}
                for prefix in (prefixes or [None]):
                    kwargs = {"Bucket": config["bucket"]}
                    if prefix:
                        kwargs["Prefix"] = prefix
                    for page in paginator.paginate(**kwargs, PaginationConfig={"PageSize": 1000}):
                        for item in page.get("Contents", []):
                            if max_objects and total_objects >= max_objects:
                                complete = False
                                break
                            key = str(item.get("Key", ""))
                            record = {
                                "key_sha256": hashlib.sha256(key.encode("utf-8")).hexdigest(),
                                "namespace": _namespace(key),
                                "size": int(item.get("Size", 0)),
                                "last_modified": item.get("LastModified").isoformat() if item.get("LastModified") else None,
                                "etag": str(item.get("ETag", "")).strip('"'),
                                "storage_class": str(item.get("StorageClass", "STANDARD")),
                            }
                            if not first:
                                stream.write(",")
                            stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
                            first = False
                            count += 1
                            total_objects += 1
                            namespace_counts[record["namespace"]] = namespace_counts.get(record["namespace"], 0) + 1
                        if max_objects and total_objects >= max_objects:
                            break
                    if max_objects and total_objects >= max_objects:
                        break
                stream.write('],"object_count":' + str(count) + ',')
                stream.write('"namespace_counts":' + json.dumps(namespace_counts, ensure_ascii=False) + "}")
                bucket_summaries.append({"alias": config["alias"], "bucket": config["bucket"], "object_count": count, "namespace_counts": namespace_counts})
            stream.write('],"complete":' + str(complete).lower() + ',"total_objects":' + str(total_objects) + "}\n")
        os.chmod(temp, 0o600)
        temp.replace(output)
    except Exception:
        temp.unlink(missing_ok=True)
        raise

    return {
        "output": str(output), "total_objects": total_objects, "complete": complete,
        "buckets": bucket_summaries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="JSON com hashes das chaves, fora do repositório")
    parser.add_argument("--prefix", action="append", default=[], help="Prefixo opcional; repetir para vários prefixos. Sem este parâmetro lista tudo.")
    parser.add_argument("--max-objects", type=int, default=0, help="Limite opcional; 0 = sem limite (inventário truncado não pode reconciliar ausência).")
    args = parser.parse_args()
    if args.max_objects < 0:
        parser.error("--max-objects deve ser >= 0")
    try:
        result = write_inventory(args.output, args.prefix, args.max_objects)
    except Exception as exc:
        print(f"ERRO: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(f"Inventário salvo: {result['output']}")
    print(f"Objetos listados: {result['total_objects']}; completo: {result['complete']}")
    for bucket in result["buckets"]:
        print(f"{bucket['alias']} ({bucket['bucket']}): {bucket['object_count']} objetos; namespaces={bucket['namespace_counts']}")
    print("Operação exclusivamente ListObjectsV2; nenhuma imagem foi baixada e nenhum objeto foi alterado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

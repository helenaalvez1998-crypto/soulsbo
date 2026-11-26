"""Armazenamento de imagens no Cloudflare R2 (API compatível com S3).

Configuração por variáveis de ambiente:
R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
R2_BUCKET_NAME e R2_PUBLIC_BASE_URL.

Nunca coloque credenciais no frontend ou no repositório.
"""
from __future__ import annotations

import os
from urllib.parse import quote

import boto3
from botocore.config import Config


class R2NotConfigured(RuntimeError):
    """Configuração do R2 ausente ou incompleta."""


def _settings() -> dict[str, str]:
    values = {
        "account_id": os.getenv("R2_ACCOUNT_ID", "").strip(),
        "access_key_id": os.getenv("R2_ACCESS_KEY_ID", "").strip(),
        "secret_access_key": os.getenv("R2_SECRET_ACCESS_KEY", "").strip(),
        "bucket": os.getenv("R2_BUCKET_NAME", "").strip(),
        "public_base_url": os.getenv("R2_PUBLIC_BASE_URL", "").strip().rstrip("/"),
    }
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise R2NotConfigured(
            "R2 não configurado. Variáveis ausentes: " + ", ".join(missing)
        )
    return values


def _client(settings: dict[str, str]):
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings['account_id']}.r2.cloudflarestorage.com",
        aws_access_key_id=settings["access_key_id"],
        aws_secret_access_key=settings["secret_access_key"],
        region_name="auto",
        config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
    )


def upload_image(object_key: str, image_bytes: bytes, content_type: str = "image/png") -> dict:
    """Envia bytes ao bucket e retorna a chave e URL pública."""
    if not object_key or object_key.startswith("/") or ".." in object_key.split("/"):
        raise ValueError("Chave de armazenamento inválida.")
    if not image_bytes:
        raise ValueError("Não é possível enviar um arquivo vazio.")
    settings = _settings()
    _client(settings).put_object(
        Bucket=settings["bucket"],
        Key=object_key,
        Body=image_bytes,
        ContentType=content_type,
        CacheControl="public, max-age=31536000, immutable",
    )
    encoded_key = quote(object_key, safe="/")
    return {
        "storage_key": object_key,
        "public_url": f"{settings['public_base_url']}/{encoded_key}",
    }


def public_url_for_key(object_key: str) -> str:
    """Converte uma chave R2 já armazenada em URL pública."""
    settings = _settings()
    return f"{settings['public_base_url']}/{quote(str(object_key).lstrip('/'), safe='/')}"

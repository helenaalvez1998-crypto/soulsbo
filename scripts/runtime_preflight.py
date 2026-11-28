#!/usr/bin/env python3
"""Preflight executado antes do bot em Docker/staging/produção.

Não imprime segredos e nunca cria schema ou migra banco. Use --probe-discord para
validar o token com GET /users/@me; a chamada não altera o Discord.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import re
import sqlite3
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Mapping
from urllib.parse import quote, urlsplit

EXACT_DISTRIBUTIONS = {
    "discord.py": "2.7.1",
    "aiosqlite": "0.22.1",
    "python-dotenv": "1.2.4",
    "aiohttp": "3.14.5",
    "tzdata": "2026.6",
    "google-genai": "2.34.0",
    "requests": "2.34.2",
    "beautifulsoup4": "4.15.0",
    "Pillow": "13.0.0",
}
RANGED_DISTRIBUTIONS = {
    "boto3": ((1, 34), (2, 0)),
    "reportlab": ((4, 2), (5, 0)),
}
_PLACEHOLDER_MARKERS = (
    "change-me", "changeme", "your-token", "your-domain", "seu-dominio",
    "example.com", "placeholder", "replace-me", "todo",
)


REQUIRED_ENV = (
    "DISCORD_TOKEN",
    "DISCORD_OAUTH_CLIENT_ID",
    "DISCORD_OAUTH_CLIENT_SECRET",
    "DISCORD_OAUTH_REDIRECT_URI",
    "SOULSBOT_WEB_SESSION_SECRET",
    "SOULSBOT_PUBLIC_URL",
    "DATA_DIR",
)


def _version_tuple(value: str) -> tuple[int, ...]:
    match = re.match(r"^(\d+(?:\.\d+){1,3})", str(value))
    if not match:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def validate_runtime(
    project_root: Path,
    environ: Mapping[str, str],
    *,
    distribution_versions: Mapping[str, str] | None = None,
) -> list[dict[str, str]]:
    """Return structured checks; injectable versions keep unit tests offline."""
    root = Path(project_root).resolve()
    checks: list[dict[str, str]] = []

    def add(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    def env(name: str) -> str:
        return str(environ.get(name, "")).strip()

    if sys.version_info >= (3, 11):
        add("python", "pass", f"Python {sys.version_info.major}.{sys.version_info.minor}")
    else:
        add("python", "block", "Python 3.11 ou superior é obrigatório")

    versions = dict(distribution_versions or {})
    if distribution_versions is None:
        for name in (*EXACT_DISTRIBUTIONS.keys(), *RANGED_DISTRIBUTIONS.keys()):
            try:
                versions[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                versions[name] = ""

    for name, expected in EXACT_DISTRIBUTIONS.items():
        actual = versions.get(name, "")
        if actual == expected:
            add(f"dependency:{name}", "pass", f"versão {expected}")
        else:
            add(f"dependency:{name}", "block", f"esperado {expected}; encontrado {actual or 'ausente'}")

    for name, (lower, upper) in RANGED_DISTRIBUTIONS.items():
        actual = versions.get(name, "")
        parsed = _version_tuple(actual)
        valid = bool(parsed) and parsed >= lower and parsed < upper
        add(
            f"dependency:{name}",
            "pass" if valid else "block",
            f"versão {actual}" if valid else f"esperado >= {'.'.join(map(str, lower))} e < {'.'.join(map(str, upper))}; encontrado {actual or 'ausente'}",
        )

    for relative in ("bot.py", "requirements.txt", "site_hub.py", "site_card_engine_v2.py", "cogs/card_engine_v2_ui.py"):
        exists = (root / relative).is_file()
        add(f"file:{relative}", "pass" if exists else "block", "presente" if exists else "arquivo obrigatório ausente")

    faq_candidates = (root / "dados" / "nara_faq.json", root / "nara" / "nara_faq.json")
    faq_path = next((candidate for candidate in faq_candidates if candidate.is_file()), None)
    if faq_path is None:
        add("nara_faq_asset", "block", "nara_faq.json ausente em dados/ e nara/; inclua o arquivo no deploy")
    else:
        try:
            with faq_path.open("r", encoding="utf-8") as faq_file:
                faq_data = json.load(faq_file)
            faq_valid = isinstance(faq_data, dict) and isinstance(faq_data.get("intents"), list) and bool(faq_data["intents"])
            add("nara_faq_asset", "pass" if faq_valid else "block",
                f"FAQ válida: {len(faq_data.get('intents', []))} intenções ({faq_path.relative_to(root)})" if faq_valid
                else f"JSON da FAQ inválido ou sem intenções ({faq_path.relative_to(root)})")
        except (OSError, json.JSONDecodeError) as exc:
            add("nara_faq_asset", "block", f"não foi possível ler a FAQ: {type(exc).__name__}")

    for name in REQUIRED_ENV:
        value = env(name)
        folded = value.casefold()
        looks_placeholder = any(marker in folded for marker in _PLACEHOLDER_MARKERS)
        add(f"env:{name}", "pass" if value and not looks_placeholder else "block",
            "configurado" if value and not looks_placeholder else "variável ausente ou com placeholder")

    token = env("DISCORD_TOKEN")
    client_secret = env("DISCORD_OAUTH_CLIENT_SECRET")
    session_secret = env("SOULSBOT_WEB_SESSION_SECRET")
    secret_ok = len(session_secret) >= 32 and session_secret not in {token, client_secret}
    add("session_secret", "pass" if secret_ok else "block",
        "chave independente com pelo menos 32 caracteres" if secret_ok else "use uma chave aleatória, independente, com pelo menos 32 caracteres")

    public_url = env("SOULSBOT_PUBLIC_URL").rstrip("/")
    redirect = env("DISCORD_OAUTH_REDIRECT_URI")
    parsed_public_url = urlsplit(public_url)
    host = (parsed_public_url.hostname or "").casefold()
    host_is_placeholder = not host or any(marker in host for marker in _PLACEHOLDER_MARKERS)
    valid_scheme = parsed_public_url.scheme == "https" or (
        parsed_public_url.scheme == "http" and host in {"localhost", "127.0.0.1"}
    )
    try:
        explicit_port = parsed_public_url.port
        valid_port = explicit_port is None or 1 <= explicit_port <= 65535
    except ValueError:
        valid_port = False
    valid_url = bool(
        parsed_public_url.netloc and valid_scheme and valid_port and not host_is_placeholder
        and not parsed_public_url.username and not parsed_public_url.password
        and parsed_public_url.path in {"", "/"} and not parsed_public_url.query
        and not parsed_public_url.fragment
    )
    add("public_url", "pass" if valid_url else "block",
        "URL HTTPS válida (HTTP permitido somente para localhost)" if valid_url else "URL pública deve usar HTTPS; HTTP só é permitido em localhost")
    expected_redirect = f"{public_url}/auth/discord/callback" if public_url else ""
    redirect_ok = bool(valid_url and redirect and redirect == expected_redirect)
    add("oauth_redirect", "pass" if redirect_ok else "block",
        "callback corresponde à URL pública" if redirect_ok else "callback precisa ser exatamente SOULSBOT_PUBLIC_URL/auth/discord/callback")

    try:
        port = int(env("PORT") or "8080")
        port_ok = 1 <= port <= 65535
    except ValueError:
        port_ok = False
    add("port", "pass" if port_ok else "block", "porta válida" if port_ok else "PORT precisa ser um inteiro entre 1 e 65535")

    data_raw = env("DATA_DIR")
    db_raw = env("DB_PATH") or (str(Path(data_raw) / "colizeu.db") if data_raw else "")
    data_path = Path(data_raw).expanduser() if data_raw else None
    db_path = Path(db_raw).expanduser() if db_raw else None
    allow_empty = env("SOULSBOT_ALLOW_EMPTY_DATABASE").casefold() in {"1", "true", "yes", "sim"}
    if data_path is None:
        add("data_dir", "block", "DATA_DIR não configurado")
    else:
        try:
            data_path.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(prefix=".soulsbo-preflight-", dir=data_path, delete=True):
                pass
            add("data_dir", "pass", "diretório gravável; isso não prova persistência após redeploy")
        except OSError:
            add("data_dir", "block", "DATA_DIR não pode ser criado ou gravado")

    if db_path is None:
        add("database_persistence", "block", "DB_PATH não pode ser resolvido")
        add("legacy_database", "block", "DB_PATH não pode ser resolvido")
    elif data_path is not None:
        try:
            db_path.resolve().relative_to(data_path.resolve())
            add("database_persistence", "pass", "DB_PATH está dentro do DATA_DIR persistente")
        except ValueError:
            add("database_persistence", "block", "DB_PATH precisa ficar dentro de DATA_DIR para sobreviver à recriação do contêiner")
        if not db_path.is_file():
            status = "warn" if allow_empty else "block"
            detail = "banco ainda não existe; o bot criará schema vazio por configuração explícita" if allow_empty else "banco legado ausente; restaure o banco ou defina SOULSBOT_ALLOW_EMPTY_DATABASE=true apenas para instalação nova"
            add("legacy_database", status, detail)
        else:
            try:
                uri = f"file:{quote(str(db_path.resolve()))}?mode=ro"
                conn = sqlite3.connect(uri, uri=True, timeout=3)
                try:
                    conn.execute("PRAGMA query_only=ON")
                    quick = conn.execute("PRAGMA quick_check").fetchone()
                    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                    if not quick or quick[0] != "ok":
                        raise sqlite3.DatabaseError("quick_check não retornou ok")
                    if not {"users", "cartas_exemplares", "cartas_colecao"}.issubset(tables):
                        raise sqlite3.DatabaseError("schema users/cartas_exemplares/cartas_colecao incompleto")
                    columns = {row[1] for row in conn.execute("PRAGMA table_info(cartas_exemplares)")}
                    if not {"id", "user_id", "card_id", "rarity", "power"}.issubset(columns):
                        raise sqlite3.DatabaseError("colunas essenciais de cartas_exemplares ausentes")
                finally:
                    conn.close()
                add("legacy_database", "pass", "SQLite íntegro; schema de coleção verificado em modo somente leitura")
            except (OSError, sqlite3.Error):
                add("legacy_database", "block", "SQLite ilegível, corrompido ou incompatível com o schema esperado")
    else:
        add("database_persistence", "block", "DATA_DIR precisa estar configurado para validar persistência")
        if not db_path.is_file():
            status = "warn" if allow_empty else "block"
            detail = "banco ainda não existe; o bot criará schema vazio por configuração explícita" if allow_empty else "banco legado ausente; restaure o banco ou defina SOULSBOT_ALLOW_EMPTY_DATABASE=true apenas para instalação nova"
            add("legacy_database", status, detail)
        else:
            add("legacy_database", "block", "não foi possível validar o banco sem DATA_DIR")

    return checks


def probe_discord(token: str, timeout: float = 8.0) -> tuple[bool, str]:
    if not token:
        return False, "token ausente"
    request = urllib.request.Request(
        "https://discord.com/api/v10/users/@me",
        headers={"Authorization": f"Bot {token}", "User-Agent": "Soulsbo-Staging-Preflight/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status == 200, "token aceito pelo endpoint de identidade"
    except urllib.error.HTTPError as exc:
        return False, f"Discord respondeu HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError):
        return False, "não foi possível alcançar a API do Discord"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--probe-discord", action="store_true")
    args = parser.parse_args()
    checks = validate_runtime(args.project_root, os.environ)
    if args.probe_discord:
        ok, detail = probe_discord(os.environ.get("DISCORD_TOKEN", "").strip())
        checks.append({"name": "discord_token_probe", "status": "pass" if ok else "block", "detail": detail})
    blocks = sum(item["status"] == "block" for item in checks)
    summary = {
        "project_root": str(args.project_root.resolve()),
        "status": "ready" if blocks == 0 else "blocked",
        "passed": sum(item["status"] == "pass" for item in checks),
        "warnings": sum(item["status"] == "warn" for item in checks),
        "blocked": blocks,
        "checks": checks,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if blocks == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

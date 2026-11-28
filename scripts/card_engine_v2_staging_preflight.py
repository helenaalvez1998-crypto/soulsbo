#!/usr/bin/env python3
"""Read-only operational preflight for the Card Engine v2 staging host.

The script never prints credentials or user identifiers. It performs a read-only
SQLite inspection and, optionally, validates the Discord bot token with one GET
request to /users/@me. OAuth cannot be completed without an interactive browser
login and is therefore checked for configuration consistency only.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

EXPECTED_PACKAGES = {
    "discord.py": "2.7.1",
    "aiosqlite": "0.22.1",
    "aiohttp": "3.14.5",
    "python-dotenv": "1.2.4",
}
REQUIRED_EXEMPLAR_COLUMNS = {
    "id",
    "user_id",
    "card_id",
    "rarity",
    "power",
    "source",
    "origin_type",
    "origin_card_id",
    "is_sacrificable",
    "obtained_at",
}
PROJECT_FILES = (
    "bot.py",
    "database.py",
    "site_hub.py",
    "site_card_engine_v2.py",
    "cogs/painel_jogo.py",
    "cogs/card_engine_v2_ui.py",
    "sistemas/card_engine_v2/discord_gateway.py",
    "site/card-engine-v2.html",
    "site/assets/card-engine-v2.js",
)


def _package_versions(overrides: Mapping[str, str] | None = None) -> dict[str, str | None]:
    if overrides is not None:
        return {name: overrides.get(name) for name in EXPECTED_PACKAGES}
    result: dict[str, str | None] = {}
    for name in EXPECTED_PACKAGES:
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def _data_dir(project_root: Path, env: Mapping[str, str]) -> Path:
    configured = str(env.get("DATA_DIR", "") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    persistent = Path("/data")
    if persistent.is_dir():
        return persistent.resolve()
    return (project_root / "data").resolve()


def _valid_absolute_url(
    value: str, *, allow_local_http: bool = True, expected_path: str | None = None
) -> bool:
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname:
            return False
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            return False
        if expected_path is None:
            if parsed.path not in {"", "/"}:
                return False
        elif parsed.path != expected_path:
            return False
        if parsed.scheme == "http":
            host = parsed.hostname.casefold()
            if not allow_local_http or host not in {"localhost", "127.0.0.1", "::1"}:
                return False
        _ = parsed.port  # validates malformed ports
        return True
    except (TypeError, ValueError):
        return False


def _add(checks: list[dict[str, str]], name: str, status: str, detail: str) -> None:
    checks.append({"name": name, "status": status, "detail": detail})


def _write_probe(directory: Path) -> bool:
    """Create and remove a tiny unique file to verify actual write/delete access."""
    try:
        directory.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            prefix=".card-engine-v2-preflight-", suffix=".tmp", dir=directory, delete=False
        )
        path = Path(handle.name)
        handle.close()
        path.unlink()
        return True
    except OSError:
        try:
            if "path" in locals():
                path.unlink(missing_ok=True)
        except OSError:
            pass
        return False


def _inspect_database(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, "arquivo SQLite não encontrado no caminho configurado"
    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=5)
        try:
            connection.execute("PRAGMA query_only=ON")
            result = connection.execute("PRAGMA quick_check").fetchone()
            if not result or str(result[0]).casefold() != "ok":
                return False, "quick_check do SQLite não retornou ok"
            table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='cartas_exemplares'"
            ).fetchone()
            if not table:
                return False, "tabela cartas_exemplares ausente"
            columns = {
                str(row[1])
                for row in connection.execute("PRAGMA table_info(cartas_exemplares)").fetchall()
            }
            missing = sorted(REQUIRED_EXEMPLAR_COLUMNS - columns)
            if missing:
                return False, "schema de cartas_exemplares incompleto: " + ", ".join(missing)
            id_info = next(
                row for row in connection.execute("PRAGMA table_info(cartas_exemplares)")
                if str(row[1]) == "id"
            )
            if int(id_info[5] or 0) != 1:
                return False, "cartas_exemplares.id não está declarado como chave primária"
            has_rows = connection.execute(
                "SELECT 1 FROM cartas_exemplares LIMIT 1"
            ).fetchone() is not None
            suffix = "; existem exemplares" if has_rows else "; inventário ainda sem exemplares"
            return True, "SQLite íntegro; schema de exemplares compatível" + suffix
        finally:
            connection.close()
    except (OSError, sqlite3.Error, StopIteration, ValueError) as exc:
        return False, f"falha de leitura SQLite ({type(exc).__name__})"


def run_preflight(
    project_root: str | Path,
    *,
    environ: Mapping[str, str] | None = None,
    installed_versions: Mapping[str, str] | None = None,
    discord_probe: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    env = os.environ if environ is None else environ
    checks: list[dict[str, str]] = []

    if sys.version_info >= (3, 11):
        _add(checks, "python", "pass", f"Python {sys.version_info.major}.{sys.version_info.minor} atende ao mínimo 3.11")
    else:
        _add(checks, "python", "block", "Python 3.11 ou superior é obrigatório")

    versions = _package_versions(installed_versions)
    for package, expected in EXPECTED_PACKAGES.items():
        actual = versions.get(package)
        if actual == expected:
            _add(checks, f"dependency:{package}", "pass", f"versão {expected} instalada")
        elif actual is None:
            _add(checks, f"dependency:{package}", "block", f"pacote ausente; requirements exige {expected}")
        else:
            _add(checks, f"dependency:{package}", "block", f"versão {actual} encontrada; requirements exige {expected}")

    for relative in PROJECT_FILES:
        if (root / relative).is_file():
            _add(checks, f"file:{relative}", "pass", "arquivo presente")
        else:
            _add(checks, f"file:{relative}", "block", "arquivo obrigatório ausente")

    # Static wiring checks ensure the runtime entrypoints still reference v2.
    static_checks = {
        "bot_extension_panel": (root / "bot.py", '"cogs.painel_jogo"'),
        "site_v2_entry": (root / "cogs/painel_jogo.py", "/card-engine-v2"),
        "site_v2_routes": (root / "site_hub.py", "registrar_card_engine_v2"),
        "oauth_callback": (root / "bot.py", '"/auth/discord/callback"'),
    }
    for name, (path, marker) in static_checks.items():
        try:
            found = marker in path.read_text(encoding="utf-8")
        except OSError:
            found = False
        _add(checks, f"wiring:{name}", "pass" if found else "block", "referência de integração presente" if found else "referência de integração ausente")

    token = str(env.get("DISCORD_TOKEN", "") or "").strip()
    client_id = str(env.get("DISCORD_OAUTH_CLIENT_ID", "") or "").strip()
    client_secret = str(env.get("DISCORD_OAUTH_CLIENT_SECRET", "") or "").strip()
    redirect_uri = str(env.get("DISCORD_OAUTH_REDIRECT_URI", "") or "").strip()
    session_secret = str(env.get("SOULSBOT_WEB_SESSION_SECRET", "") or "")
    public_url = str(env.get("SOULSBOT_PUBLIC_URL", "") or "").strip().rstrip("/")

    _add(checks, "secret:DISCORD_TOKEN", "pass" if token else "block", "token configurado" if token else "token não configurado")
    _add(checks, "secret:DISCORD_OAUTH_CLIENT_ID", "pass" if client_id.isdigit() else "block", "client ID numérico configurado" if client_id.isdigit() else "client ID OAuth ausente ou inválido")
    _add(checks, "secret:DISCORD_OAUTH_CLIENT_SECRET", "pass" if client_secret else "block", "client secret configurado" if client_secret else "client secret OAuth não configurado")
    _add(checks, "secret:SOULSBOT_WEB_SESSION_SECRET", "pass" if len(session_secret) >= 32 else "block", "chave de sessão com comprimento suficiente" if len(session_secret) >= 32 else "chave de sessão ausente ou menor que 32 caracteres")
    if session_secret and (session_secret == token or session_secret == client_secret):
        _add(checks, "secret:session_key_separation", "block", "chave de sessão precisa ser independente dos demais segredos")
    else:
        _add(checks, "secret:session_key_separation", "pass", "chave de sessão separada dos demais segredos")

    if _valid_absolute_url(public_url):
        _add(checks, "url:SOULSBOT_PUBLIC_URL", "pass", "URL pública absoluta e segura")
    else:
        _add(checks, "url:SOULSBOT_PUBLIC_URL", "block", "URL pública ausente ou inválida; use HTTPS (HTTP só em localhost)")
    expected_redirect = f"{public_url}/auth/discord/callback" if public_url else ""
    if redirect_uri and _valid_absolute_url(redirect_uri, expected_path="/auth/discord/callback") and redirect_uri == expected_redirect:
        _add(checks, "url:DISCORD_OAUTH_REDIRECT_URI", "pass", "callback OAuth corresponde à URL pública")
    else:
        _add(checks, "url:DISCORD_OAUTH_REDIRECT_URI", "block", "callback precisa ser exatamente SOULSBOT_PUBLIC_URL/auth/discord/callback e estar registrada no Discord Developer Portal")

    data_dir = _data_dir(root, env)
    if data_dir.is_dir() and _write_probe(data_dir):
        _add(checks, "storage:DATA_DIR", "pass", "diretório persistente existe e passou teste de escrita/remoção")
    elif data_dir.is_dir():
        _add(checks, "storage:DATA_DIR", "block", "diretório existe, mas não permite criar/remover arquivo temporário")
    else:
        _add(checks, "storage:DATA_DIR", "block", "diretório de dados não existe; configure/crie DATA_DIR no volume persistente")

    v2_dir = data_dir / "card_engine_v2"
    if v2_dir.is_dir():
        if os.access(v2_dir, os.W_OK | os.X_OK):
            _add(checks, "storage:card_engine_v2", "pass", "diretório dedicado v2 existe e é gravável")
        else:
            _add(checks, "storage:card_engine_v2", "block", "diretório dedicado v2 não é gravável")
    elif data_dir.is_dir() and os.access(data_dir, os.W_OK | os.X_OK):
        _add(checks, "storage:card_engine_v2", "warn", "diretório v2 será criado na primeira inicialização")
    else:
        _add(checks, "storage:card_engine_v2", "block", "não é possível criar o diretório dedicado v2")

    db_value = str(env.get("DB_PATH", "") or "").strip()
    db_path = Path(db_value).expanduser() if db_value else data_dir / "colizeu.db"
    db_ok, db_detail = _inspect_database(db_path)
    _add(checks, "database:collection_schema", "pass" if db_ok else "block", db_detail)

    # This is intentionally a warning: filesystem permissions cannot prove that
    # the host volume survives a redeploy. That must be confirmed in the host panel.
    _add(checks, "storage:persistence_across_redeploy", "warn", "confirmar no painel da hospedagem que DATA_DIR está montado em volume persistente; teste local não prova retenção após deploy")

    if discord_probe is None:
        if env.get("DISCORD_TOKEN"):
            _add(checks, "discord:token_probe", "warn", "token não consultado; use --probe-discord para validar /users/@me")
        else:
            _add(checks, "discord:token_probe", "block", "não há token para validar a conexão Discord")
    elif bool(discord_probe.get("ok")):
        _add(checks, "discord:token_probe", "pass", "Discord aceitou o token do bot")
    else:
        _add(checks, "discord:token_probe", "block", "Discord recusou o token ou a conexão de rede falhou")

    privileged_intents = (
        (root / "bot.py").is_file()
        and all(
            marker in (root / "bot.py").read_text(encoding="utf-8")
            for marker in ("intents.message_content = True", "intents.members = True", "intents.presences = True")
        )
    )
    _add(
        checks,
        "discord:privileged_intents_code",
        "pass" if privileged_intents else "block",
        "código solicita message_content, members e presences; habilitar os três intents no Developer Portal",
    )

    blockers = sum(check["status"] == "block" for check in checks)
    warnings = sum(check["status"] == "warn" for check in checks)
    return {
        "tool": "card_engine_v2_staging_preflight",
        "version": "0.1",
        "ready": blockers == 0,
        "summary": {"passed": sum(c["status"] == "pass" for c in checks), "warnings": warnings, "blockers": blockers},
        "database": {"path_configured": bool(db_value), "read_only_schema_check": db_detail},
        "checks": checks,
        "security": {
            "secrets_printed": False,
            "database_opened_read_only": True,
            "database_rows_or_user_ids_exported": False,
            "writes_to_application_database": False,
        },
    }


async def _probe_discord_token(token: str) -> dict[str, Any]:
    try:
        import aiohttp
    except ImportError:
        return {"ok": False, "reason": "aiohttp ausente"}
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                "https://discord.com/api/v10/users/@me",
                headers={"Authorization": f"Bot {token}"},
            ) as response:
                return {"ok": response.status == 200, "http_status": int(response.status)}
    except Exception as exc:  # never serialize URL headers or exception arguments
        return {"ok": False, "reason": type(exc).__name__}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--probe-discord", action="store_true", help="validar DISCORD_TOKEN via GET /users/@me")
    args = parser.parse_args(argv)
    probe = None
    if args.probe_discord:
        token = str(os.getenv("DISCORD_TOKEN", "") or "").strip()
        probe = asyncio.run(_probe_discord_token(token)) if token else {"ok": False, "reason": "token ausente"}
    report = run_preflight(args.project_root, discord_probe=probe)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

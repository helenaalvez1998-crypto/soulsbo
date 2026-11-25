"""Sistema de Apostas — Aposta das Almas.

Apostas com Cartas (Wager) e Denários para partidas rankeadas, casuais e PvE.
Inspirado em sistemas de apostas de jogos competitivos e
mecânicas de risco/recompensa de Elden Ring/Dark Souls.

Tabelas necessárias no banco (ver add_schema_below):
- apostas_partidas: registro de apostas em partidas
- apostas_cartas: cartas apostadas em cada partida
- apostas_torneio: apostas de espectadores em torneios
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import hashlib
import secrets


# ── Taxas e Limites ────────────────────────────────────────────────────────────
APOSTA_TAXA_CASA = 0.05  # 5% comissão da casa para o Tesouro da Fogueira

LIMITE_DIARIO_DENARIOS = 10_000
COOLDOWN_APOSTA_ARRISCADA_SEGUNDOS = 300  # 5 minutos

# Multiplicador de Denários por tipo de aposta
MULTIPLICADORES_APOSTA = {
    "rankeada": 1.8,
    "casual": 1.5,
    "torneio": 2.5,
    "pve_chefe": 3.0,
}

APOSTA_MIN_DENARIOS = {
    "rankeada": 50,
    "casual": 10,
    "torneio": 500,
    "pve_chefe": 100,
}

APOSTA_MAX_DENARIOS = {
    "rankeada": 5_000,
    "casual": 500,
    "torneio": 50_000,
    "pve_chefe": 10_000,
}

# Diferença máxima de raridade permitida em apostas de cartas (níveis)
MAX_DIFF_RARIDADE_APOSTA = 1


RARIDADE_NIVEL = {
    "Comum": 1, "Rara": 2, "Épica": 3,
    "Lendária": 4, "Mítica": 5, "Primordial": 6, "Singular": 7,
}


@dataclass
class ApostaResultado:
    vencedor_id: int
    perdedor_id: int
    ganho_cartas: list[str]  # IDs de cartas ganhas
    perda_cartas: list[str]  # IDs de cartas perdidas
    ganho_denarios: int
    perda_denarios: int
    taxa_casa: int
    mensagem: str
    efeito_visual: str = ""


def validar_aposta_cartas(carta_a: dict, carta_b: dict) -> dict | None:
    """Valida se duas cartas podem ser apostadas uma contra a outra."""
    nivel_a = RARIDADE_NIVEL.get(str(carta_a.get("rarity") or "Comum"), 1)
    nivel_b = RARIDADE_NIVEL.get(str(carta_b.get("rarity") or "Comum"), 1)

    if abs(nivel_a - nivel_b) > MAX_DIFF_RARIDADE_APOSTA:
        return {
            "valido": False,
            "motivo": (
                f"Raridades muito distantes para aposta: "
                f"{carta_a.get('rarity')} (nível {nivel_a}) vs "
                f"{carta_b.get('rarity')} (nível {nivel_b}). "
                f"Diferença máxima permitida: {MAX_DIFF_RARIDADE_APOSTA}."
            ),
        }

    return {"valido": True}


def calcular_ganho_denarios(valor_aposta: int, tipo: str, vantagem_mmr: float = 0.0) -> int:
    """Calcula denários ganhos com base na aposta, tipo e diferença de MMR."""
    mult = MULTIPLICADORES_APOSTA.get(tipo, 1.5)
    # Ajuste por MMR: jogador menor favorito recebe mais
    mmr_adj = 1.0 + (vantagem_mmr / 100.0)
    ganho = int(round(valor_aposta * mult * mmr_adj * (1 - APOSTA_TAXA_CASA)))
    return max(0, ganho)


def criar_chave_aposta(user_id: int, oponente_id: int, tipo: str) -> str:
    """Gera chave única para evitar apostas duplicadas."""
    raw = f"{int(user_id)}:{int(oponente_id)}:{tipo}:{secrets.token_hex(8)}"
    return "aposta_" + hashlib.sha256(raw.encode()).hexdigest()


def pode_apostar_diario(usuario: dict, valor: int) -> dict:
    """Verifica se o usuário pode apostar valor dentro do limite diário."""
    hoje = __import__("datetime").date.today().isoformat()
    apostado_hoje = int(usuario.get(f"apostas_denarios_{hoje}", 0))

    if apostado_hoje + valor > LIMITE_DIARIO_DENARIOS:
        return {
            "permitido": False,
            "motivo": (
                f"Limite diário de {LIMITE_DIARIO_DENARIOS:,} Denários excedido. "
                f"Apostado hoje: {apostado_hoje:,}."
            ),
            "restante": max(0, LIMITE_DIARIO_DENARIOS - apostado_hoje),
        }
    return {"permitido": True, "restante": LIMITE_DIARIO_DENARIOS - apostado_hoje - valor}


def limite_aposta_por_tipo(tipo: str) -> tuple[int, int]:
    return APOSTA_MIN_DENARIOS.get(tipo, 10), APOSTA_MAX_DENARIOS.get(tipo, 500)


# ── Schema SQL para adicionar ao banco ────────────────────────────────────────
SCHEMA_APOSTAS = """
CREATE TABLE IF NOT EXISTS apostas_partidas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chave           TEXT UNIQUE NOT NULL,
    jogador_a       INTEGER NOT NULL,
    jogador_b       INTEGER NOT NULL,
    vencedor_id     INTEGER,
    tipo            TEXT NOT NULL DEFAULT 'casual',
    valor_denarios  INTEGER NOT NULL DEFAULT 0,
    carta_a_id      INTEGER,
    carta_b_id      INTEGER,
    status          TEXT NOT NULL DEFAULT 'pendente',  -- pendente | concluida | cancelada | reembolsada
    criado_em       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    concluido_em    TEXT,
    FOREIGN KEY(jogador_a) REFERENCES users(user_id),
    FOREIGN KEY(jogador_b) REFERENCES users(user_id),
    FOREIGN KEY(vencedor_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS apostas_cartas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    aposta_id       INTEGER NOT NULL,
    jogador_id      INTEGER NOT NULL,
    carta_id        INTEGER NOT NULL,  -- cartas_exemplares.id
    carta_nome      TEXT NOT NULL,
    carta_raridade  TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'apostada',  -- apostada | ganha | perdida | devolvida
    FOREIGN KEY(aposta_id) REFERENCES apostas_partidas(id),
    FOREIGN KEY(jogador_id) REFERENCES users(user_id),
    FOREIGN KEY(carta_id) REFERENCES cartas_exemplares(id)
);

CREATE TABLE IF NOT EXISTS apostas_torneio (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    torneio_id      TEXT NOT NULL,
    usuario_id      INTEGER NOT NULL,
    participante_id TEXT NOT NULL,  -- nome ou ID do participante
    valor_denarios  INTEGER NOT NULL,
    odd             REAL NOT NULL DEFAULT 2.0,
    status          TEXT NOT NULL DEFAULT 'aberta',  -- aberta | ganha | perdida | cancelada
    criado_em       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(usuario_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS users_aposta_cache (
    user_id   INTEGER PRIMARY KEY,
    data      TEXT NOT NULL DEFAULT (date('now')),
    total_dia INTEGER NOT NULL DEFAULT 0,
    ultimo_cooldown_risco TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
"""

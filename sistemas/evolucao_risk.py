"""Sistema de Evolução com Risco — Forja das Almas.

Cada nível de evolução aumenta o poder da carta, mas:
- Chance de sucesso diminui progressivamente
- Falha = carta REGREDIDA (volta ao nível anterior), não destruída
- Amuleto de proteção pode prevenir regressão (consumível, raro)

Inspirado em Elden Ring/Dark Souls: cada evolução é um ritual arriscado
que pode abençoar ou consumir a alma da carta.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Configuração de Níveis de Evolução ────────────────────────────────────────
# Ganho de poder ADITIVO (proporcional ao risco) em vez de multiplicativo.
# Risco de perda limitado a 50% máximo para manter o jogo justo.
EVOLUTION_LEVELS = {
    1: {
        "success_rate": 85.0,
        "power_gain": 5,          # +5 poder fixo
        "risk_regress": False,    # sem risco de perder nível
        "cost_fragmentos": 10,
        "cost_denarios": 80,
        "name": "Despertar",
    },
    2: {
        "success_rate": 75.0,
        "power_gain": 7,          # +7 poder
        "risk_regress": True,     # 25% chance de regredir 1 nível
        "cost_fragmentos": 20,
        "cost_denarios": 200,
        "name": "Ascensão",
    },
    3: {
        "success_rate": 65.0,
        "power_gain": 10,         # +10 poder
        "risk_regress": True,     # 35% chance de regredir 1 nível
        "cost_fragmentos": 35,
        "cost_denarios": 400,
        "name": "Transmutação",
    },
    4: {
        "success_rate": 55.0,
        "power_gain": 15,         # +15 poder
        "risk_regress": True,     # 45% chance de regredir 1 nível
        "cost_fragmentos": 60,
        "cost_denarios": 900,
        "name": "Evolução",
    },
    5: {
        "success_rate": 40.0,
        "power_gain": 22,         # +22 poder — salto massivo
        "risk_regress": True,     # 60% chance de regredir 1 nível
        "cost_fragmentos": 100,
        "cost_denarios": 2000,
        "name": "Ascensão Suprema",
    },
}

# ── Proteção com Amuleto ──────────────────────────────────────────────────────
AMULETO_PROTECAO = {
    "id": "amuleto_roteiro",
    "nome": "Roteiro Protetor",
    "descricao": "Protege uma carta da regressão em caso de falha na evolução.",
    "consumivel": True,
    "chance_ativacao": 100.0,  # Sempre ativa quando consumido
}


# ── Funções Auxiliares ───────────────────────────────────────────────────────
def get_evolution_config(level: int) -> dict | None:
    """Retorna a configuração de um nível de evolução."""
    return EVOLUTION_LEVELS.get(level)


def get_max_level_for_rarity(rarity: str) -> int:
    """Retorna o nível máximo permitido para cada raridade.

    - Comum: nível 3 (limitado)
    - Rara: nível 4
    - Épica/Lendária: nível 5
    - Mítica e acima: nível 5
    """
    limites = {
        "Comum": 3,
        "Rara": 4,
        "Épica": 5,
        "Lendária": 5,
        "Mítica": 5,
        "Primordial": 5,
        "Singular": 5,
    }
    return limites.get(rarity, 3)


def can_evolve(card_rarity: str, current_level: int) -> bool:
    """Verifica se a carta pode evoluir mais um nível."""
    return current_level < get_max_level_for_rarity(card_rarity)


def calculate_evolved_power(card: Any, target_level: int) -> int:
    """Calcula o poder da carta após evolução ao nível alvo.

    Fórmula ADITIVA: poder_base + soma dos ganhos de cada nível até o alvo.
    Isso torna o ganho proporcional ao risco em vez de exponencial.
    """
    base_power = card.poder
    current_level = int(getattr(card, 'evolution_level', 0) or 0)
    levels_to_apply = max(0, target_level - current_level)
    total_gain = 0
    for lvl in range(current_level + 1, target_level + 1):
        cfg = EVOLUTION_LEVELS.get(lvl)
        if cfg:
            total_gain += cfg["power_gain"]
    return base_power + total_gain


def get_evolution_info(card_rarity: str, current_level: int) -> dict:
    """Retorna informações completas sobre a evolução da carta."""
    max_level = get_max_level_for_rarity(card_rarity)
    next_level = current_level + 1 if current_level < max_level else None
    next_config = get_evolution_config(next_level) if next_level else None
    current_config = get_evolution_config(current_level) if current_level > 0 else None

    return {
        "current_level": current_level,
        "max_level": max_level,
        "can_evolve": current_level < max_level,
        "current_config": current_config,
        "next_level_name": next_config["name"] if next_config else None,
        "next_success_rate": next_config["success_rate"] if next_config else None,
        "next_risk_regress": next_config["risk_regress"] if next_config else False,
        "next_power_gain": next_config["power_gain"] if next_config else 0,
        "costs": next_config and {
            "fragmentos": next_config["cost_fragmentos"],
            "denarios": next_config["cost_denarios"],
        },
    }


# ── Simulação de Evolução (teste offline) ───────────────────────────────────
import random


def simulate_evolution_roll(success_rate: float) -> bool:
    """Simula o rolamento de dados para determinar sucesso/falha.

    success_rate em porcentagem (0-100)
    Retorna True para sucesso, False para falha.
    """
    return random.random() * 100 < success_rate


def execute_evolucao(card: Any, target_level: int, use_amulet: bool = False) -> dict:
    """Executa uma tentativa de evolução (simulação, sem persistência).

    Retorna dict com: success, card, level, power, amulet_used, regressed
    """
    current_level = int(getattr(card, 'evolution_level', 0) or 0)
    if not can_evolve(card.rarity if hasattr(card, 'rarity') else 'Comum', current_level):
        return {"error": "Carta no nível máximo"}

    cfg = get_evolution_config(target_level)
    if not cfg:
        return {"error": "Nível inválido"}

    success = simulate_evolution_roll(cfg["success_rate"])

    if success:
        new_power = calculate_evolved_power(card, target_level)
        return {
            "success": True,
            "power": new_power,
            "level": target_level,
            "amulet_used": False,
            "regressed": False,
            "message": f"Evolução bem-sucedida! Poder: {new_power}",
        }

    # Falha
    if cfg["risk_regress"]:
        if use_amulet:
            # Amuleto previne regressão, mas é consumido
            return {
                "success": False,
                "power": card.poder,
                "level": current_level,
                "amulet_used": True,
                "regressed": False,
                "message": "Amuleto consumido! Carta preservada no nível atual.",
            }
        else:
            # Regredir 1 nível (mínimo 0)
            new_level = max(0, current_level - 1)
            # Recalcular poder para o nível regresso
            regressed_power = card.poder
            if new_level < current_level:
                # Perde o ganho do nível que falhou (e possivelmente do anterior)
                regressed_card = type('obj', (object,), {'poder': card.poder, 'evolution_level': new_level})()
                regressed_power = calculate_evolved_power(regressed_card, new_level)
            return {
                "success": False,
                "power": regressed_power,
                "level": new_level,
                "amulet_used": False,
                "regressed": True,
                "message": f"Falha! Carta regrediu para nível {new_level}.",
            }
    else:
        # Sem risco, falha apenas não evolui
        return {
            "success": False,
            "power": card.poder,
            "level": current_level,
            "amulet_used": False,
            "regressed": False,
            "message": "Falha na evolução. Carta permanece no nível atual.",
        }


# ── Histórico e Análise ─────────────────────────────────────────────────────
def analyze_evolution_history(attempts: list[dict]) -> dict:
    """Analisa histórico de tentativas de evolução.

    Lista de dicts com: {success, risk_lost, level, rarity}
    """
    if not attempts:
        return {"total": 0, "success_rate": 0, "losses": 0, "avg_level": 0}

    total = len(attempts)
    successes = sum(1 for a in attempts if a.get("success"))
    losses = sum(1 for a in attempts if not a.get("success") and a.get("risk_lost"))
    avg_level = sum(a.get("level", 0) for a in attempts) / total

    return {
        "total": total,
        "success_rate": round(successes / total * 100, 1) if total else 0,
        "losses": losses,
        "avg_level": round(avg_level, 1),
    }


if __name__ == "__main__":
    print("=== Teste de Evolução com Risco Equilibrado ===")
    print(f"Níveis disponíveis: {len(EVOLUTION_LEVELS)}")

    for nivel, cfg in EVOLUTION_LEVELS.items():
        print(f"  Nv {nivel}: {cfg['name']}")
        print(f"    Sucesso: {cfg['success_rate']}% | Ganho: +{cfg['power_gain']} poder")
        print(f"    Custo: {cfg['cost_denarios']}D / {cfg['cost_fragmentos']}F")
        if cfg['risk_regress']:
            print(f"    Risco: {100 - cfg['success_rate']:.0f}% de regredir 1 nível")
        print()

    print("=== Simulação 10 tentativas nível 3 (55% sucesso) ===")
    for i in range(10):
        r = simulate_evolution_roll(55.0)
        print(f"  {i+1}: {'✅' if r else '❌'}")
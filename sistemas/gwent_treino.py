"""Decks oficiais e perfis de dificuldade do modo de treino da NARA.

Os três decks são snapshots determinísticos do catálogo oficial. Cada perfil
mantém 9 unidades e 3 especiais, sem depender da coleção do usuário.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from sistemas.cartas import get_carta
from sistemas.gwent import preparar_carta

# A NARA sempre aguarda dentro deste intervalo antes de cada ação do turno.
AI_THINK_DELAY_SECONDS = (3.0, 5.0)


TREINO_PERFIS: dict[str, dict[str, Any]] = {
    "facil": {
        "key": "facil",
        "label": "Aprendiz",
        "deck_name": "Formação da Árvore Áurea",
        "faction": "Ordem Áurea",
        "leader_id": "bastiao_ancestral",
        "relic_id": "reliquia_grande_runa_godrick",
        "relic_name": "Grande Runa de Godrick",
        "description": "Formação defensiva, unidades acessíveis e efeitos fáceis de acompanhar.",
        "ai_style": "jogadas menos precisas; não calcula quando conservar a mão antes de o jogador passar.",
        "cards": [
            "chefe_vigia_cinzento",
            "arma_lanca_fornalha",
            "covenant_irmandade_ferro",
            "gwent_unidade_baluarte",
            "gwent_unidade_portaestandarte",
            "gwent_unidade_sentinela_rubra",
            "gwent_v75_ordem_veterano_juramento",
            "gwent_v75_ordem_guardiao_crisol",
            "covenant_filhos_brasa",
            "gwent_especial_muralha",
            "gwent_especial_egide",
            "gwent_especial_vinculo",
        ],
    },
    "normal": {
        "key": "normal",
        "label": "Estrategista",
        "deck_name": "Observatório Cariano",
        "faction": "Lua Negra",
        "leader_id": "mestre_eclipse",
        "relic_id": "reliquia_runa_nao_nascidos",
        "relic_name": "Grande Runa dos Não Nascidos",
        "description": "Controle de fileira, geada e respostas mágicas com curva intermediária.",
        "ai_style": "avalia o valor imediato da jogada e conserva recursos quando a vantagem já é suficiente.",
        "cards": [
            "chefe_dama_vazio",
            "arma_cajado_marulho",
            "arma_agulha_astro",
            "magia_nevoa_antiga",
            "magia_fagulha",
            "magia_orbe_eco",
            "covenant_sentinelas",
            "gwent_v75_lua_oraculo_geada",
            "gwent_unidade_cavaleira",
            "gwent_especial_tempestade",
            "gwent_especial_geada",
            "gwent_especial_purificar",
        ],
    },
    "dificil": {
        "key": "dificil",
        "label": "Lendária",
        "deck_name": "Flor Escarlate — Malenia",
        "faction": "Véu Carmesim",
        "leader_id": "voz_caidos",
        "relic_id": "reliquia_runa_morte",
        "relic_name": "Runa da Morte",
        "description": "Malenia lidera uma formação de pressão gradual, Podridão Escarlate, marcas e recuperação tática.",
        "ai_style": "prioriza alvos, calcula melhor a conservação de recursos e aproveita as janelas de vantagem.",
        "cards": [
            "chefe_malenia_lamina_miquella",
            "chefe_cervo_sombrio",
            "chefe_cacador_sem_rosto",
            "chefe_aparicao_veio",
            "arma_lamina_peregrino",
            "arma_arco_peregrino",
            "gwent_v75_veu_acolito_sangue",
            "gwent_v75_veu_devota_hemorragia",
            "gwent_v75_veu_cacador_sangue",
            "elden_especial_podrida",
            "gwent_especial_medico",
            "gwent_especial_batedor",
        ],
    },
}


def perfil_treino(difficulty: str) -> dict[str, Any]:
    key = str(difficulty or "normal").strip().casefold()
    if key not in TREINO_PERFIS:
        key = "normal"
    return deepcopy(TREINO_PERFIS[key])


def construir_deck_treino(difficulty: str = "normal") -> list[dict[str, Any]]:
    """Retorna um deck válido de 12 cartas no formato esperado pelo Gwent."""
    profile = perfil_treino(difficulty)
    deck: list[dict[str, Any]] = []
    seen: set[str] = set()
    for card_id in profile["cards"]:
        if card_id in seen:
            raise ValueError(f"Carta repetida no deck de treino: {card_id}")
        seen.add(card_id)
        model = get_carta(card_id)
        if model is None:
            raise ValueError(f"Carta inexistente no catálogo de treino: {card_id}")
        payload = preparar_carta(model.para_dict())
        deck.append(payload)

    units = [card for card in deck if not card.get("especial")]
    specials = [card for card in deck if card.get("especial")]
    unit_factions = {str(card.get("faccao", "")) for card in units}
    if len(deck) != 12 or len(units) != 9 or len(specials) != 3:
        raise ValueError(f"Deck {profile['key']} precisa ter 9 unidades e 3 especiais.")
    if unit_factions != {profile["faction"]}:
        raise ValueError(f"As unidades do deck {profile['key']} não pertencem à mesma facção.")
    if profile["leader_id"] not in {
        "bastiao_ancestral", "mestre_eclipse", "voz_caidos"
    }:
        raise ValueError(f"Líder inválido no deck de treino: {profile['leader_id']}")
    return deck


def listar_perfis_treino() -> list[dict[str, str]]:
    """Metadados seguros para a interface; não expõe a ordem de compra."""
    return [
        {
            "key": item["key"],
            "label": item["label"],
            "deck_name": item["deck_name"],
            "faction": item["faction"],
            "leader_id": item["leader_id"],
            "relic_id": item["relic_id"],
            "relic_name": item["relic_name"],
            "description": item["description"],
        }
        for item in TREINO_PERFIS.values()
    ]

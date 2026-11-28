from __future__ import annotations

import ast
from pathlib import Path

import pytest

from sistemas.cartas import CARTAS_POR_ID, HABILIDADES, get_carta
from sistemas.gwent import (
    CARD_IDENTITY_ABILITIES,
    HABILIDADES_ESPECIAIS_IMPLEMENTADAS,
    HABILIDADES_UNIDADE_IMPLEMENTADAS,
    aplicar_jogada,
    novo_estado,
    preparar_carta,
)
from sistemas.auditoria_efeitos import gerar_relatorio_fidelidade_cartas


def _unit(uid: str, faction: str, row: str) -> dict:
    return {
        "id": uid,
        "nome": uid,
        "categoria": "Unidade",
        "especial": False,
        "poder": 4,
        "bonus": 0,
        "faccao": faction,
        "row": row,
        "fileira": row,
        "escudo": 0,
        "weather_resist": 0,
        "sangramento": 0,
        "geada": 0,
        "podrida": 0,
        "loucura": 0,
    }


def _play_catalog_unit(card_id: str, *, same_faction_allies: int = 0, previous_round_won: bool = False) -> dict:
    model = get_carta(card_id)
    assert model is not None
    card = model.para_dict()
    card.update({"bonus": 0, "escudo": 0, "weather_resist": 0})
    row = preparar_carta(card)["fileira"]
    filler = _unit("filler", model.faccao, row)
    decks = {
        "100": [card] + [dict(filler, id=f"filler_{i}") for i in range(11)],
        "200": [dict(filler, id=f"enemy_{i}") for i in range(12)],
    }
    state = novo_estado(
        701, 100, 200, decks,
        {"100": {"faction": model.faccao}, "200": {"faction": model.faccao}},
    )
    state["phase"] = "battle"
    state["turn"] = "100"
    player = state["players"]["100"]
    player["hand"] = [card]
    player["mulligan_done"] = True
    player["faction_boost_used"] = True  # isola o efeito próprio da carta
    player["legado_vitoria"] = previous_round_won
    player["board"] = [
        _unit(f"ally_{index}", model.faccao, row)
        for index in range(same_faction_allies)
    ]
    state["players"]["200"]["mulligan_done"] = True
    result = aplicar_jogada(state, 100, card_id, "play", row)
    assert "error" not in result, result.get("error")
    played = next(
        unit for unit in result["state"]["players"]["100"]["board"]
        if unit.get("id") == card_id
    )
    return played


def test_complete_catalog_matches_runtime_site_and_physical_card_text():
    report = gerar_relatorio_fidelidade_cartas()
    assert report["total_cartas"] == 137
    assert report["total_publicadas_site"] == 137
    assert report["total_erros"] == 0, report["erros"]
    assert report["status"] == "OK"
    assert len(report["cartas"]) == len(CARTAS_POR_ID)


def test_all_catalog_skill_ids_have_catalog_definitions_and_runtime_contracts():
    for model in CARTAS_POR_ID.values():
        skill = str(model.habilidade or "")
        if not skill:
            continue
        if model.categoria.casefold() == "especial":
            assert skill in HABILIDADES, (model.id, skill)
            assert skill in HABILIDADES_ESPECIAIS_IMPLEMENTADAS, (model.id, skill)
        elif model.id in CARD_IDENTITY_ABILITIES:
            assert CARD_IDENTITY_ABILITIES[model.id]["effect"]
        else:
            assert skill in HABILIDADES, (model.id, skill)
            assert skill in HABILIDADES_UNIDADE_IMPLEMENTADAS, (model.id, skill)


def test_all_identity_effects_have_an_explicit_runtime_branch():
    source = Path("sistemas/gwent.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    handler = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_aplicar_habilidade_identidade"
    )
    effects: set[str] = set()
    for node in ast.walk(handler):
        if isinstance(node, ast.Compare):
            compared = [node.left, *node.comparators]
            if any(isinstance(item, ast.Name) and item.id == "effect" for item in compared):
                for item in compared:
                    if isinstance(item, ast.Constant) and isinstance(item.value, str):
                        effects.add(item.value)
    expected = {data["effect"] for data in CARD_IDENTITY_ABILITIES.values()}
    assert expected <= effects, sorted(expected - effects)


@pytest.mark.parametrize(
    ("card_id", "allies", "previous_win", "minimum_bonus"),
    [
        ("luterano_pastor", 0, True, 2),
        ("luterano_bispo", 2, False, 1),
        ("luterano_mistico", 2, False, 1),
        ("luterano_cruzado", 2, False, 2),
        ("luterano_papa", 2, False, 2),
        ("luterano_profeta", 2, False, 2),
    ],
)
def test_generic_faith_skills_are_actually_applied_in_normal_gameplay(
    card_id: str, allies: int, previous_win: bool, minimum_bonus: int
):
    played = _play_catalog_unit(
        card_id,
        same_faction_allies=allies,
        previous_round_won=previous_win,
    )
    assert int(played["bonus"]) >= minimum_bonus


def test_devotion_does_not_activate_with_fewer_than_two_other_faction_allies():
    played = _play_catalog_unit("luterano_bispo", same_faction_allies=1)
    assert int(played["bonus"]) == 0


def test_legado_does_not_activate_when_previous_round_was_not_won():
    played = _play_catalog_unit("luterano_pastor", previous_round_won=False)
    assert int(played["bonus"]) == 0


def test_every_static_card_has_a_nonempty_canonical_effect_field():
    for model in CARTAS_POR_ID.values():
        prepared = preparar_carta(model.para_dict())
        assert prepared["habilidade_nome"].strip(), model.id
        assert prepared["habilidade_texto"].strip(), model.id
        if model.id in CARD_IDENTITY_ABILITIES:
            assert prepared["habilidade_id_efetiva"] == CARD_IDENTITY_ABILITIES[model.id]["effect"]
        else:
            assert prepared["habilidade_id_efetiva"] == (model.habilidade or "")


def test_generated_reward_skill_pool_is_fully_present_in_runtime_and_catalog():
    from sistemas.cartas import HABILIDADES_COMUNS

    for skill in HABILIDADES_COMUNS:
        assert skill in HABILIDADES, skill
        assert skill in HABILIDADES_UNIDADE_IMPLEMENTADAS, skill


def test_main_effect_compendium_and_relic_preview_read_from_the_canonical_api():
    index = Path('site/index.html').read_text(encoding='utf-8')
    app = Path('site/app.js').read_text(encoding='utf-8')
    assert 'id="effect-library-dynamic"' in index
    assert "fetch('/api/gwent/catalogo-cartas'" in index
    assert "fetch('/api/gwent/catalogo-cartas'" in app
    assert 'entry[2] = card.habilidade_texto' in app
    assert 'Aplica clima -2 à fileira escolhida' not in index
    assert 'Chuva de Estrelas</h4>' not in index


def test_every_effect_registry_entry_has_a_runtime_or_identity_handler():
    from sistemas.auditoria_efeitos import gerar_relatorio_efeitos

    report = gerar_relatorio_efeitos()
    assert report["status"] == "ok"
    assert report["habilidades_sem_cobertura"] == []
    assert report["especiais_motor_sem_texto_catalogo"] == []
    assert report["identidades_sem_definicao_completa"] == []



def test_long_effect_is_not_double_appended_when_rendering_base_card():
    from sistemas.arte_cartas import (
        _dados_habilidade_visual, _draw_card, preparar_payload_carta_base,
    )

    model = get_carta("gwent_especial_execucao")
    assert model is not None
    payload = preparar_payload_carta_base(model)
    expected = (payload["habilidade_nome"], payload["habilidade_texto"])
    assert _dados_habilidade_visual(payload) == expected
    rendered = _draw_card(payload)
    assert rendered.size == (420, 620)


def test_full_card_atelier_art_is_recomposed_with_canonical_game_text():
    from PIL import Image, ImageDraw
    import io
    from sistemas.arte_cartas import (
        _dados_habilidade_visual, preparar_payload_carta_base, renderizar_carta_com_arte_completa,
    )

    model = get_carta("chefe_malenia_lamina_miquella")
    assert model is not None
    source = preparar_payload_carta_base(model)
    full = Image.new("RGB", (840, 1240), (24, 28, 36))
    draw = ImageDraw.Draw(full)
    # A janela central representa a pintura; faixas externas simulam texto antigo.
    draw.rectangle((56, 256, 783, 845), fill=(116, 46, 54))
    draw.rectangle((40, 960, 800, 1180), fill=(235, 226, 207))
    original = io.BytesIO()
    full.save(original, format="PNG")

    rendered = renderizar_carta_com_arte_completa(source, original.getvalue())
    assert rendered.size == (420, 620)
    assert source["habilidade_texto"] in _dados_habilidade_visual(source)


def test_full_card_image_endpoints_never_serve_text_baked_into_old_art():
    source = Path("bot.py").read_text(encoding="utf-8")
    assert "renderizar_carta_com_arte_completa(" in source
    assert "extrair_ilustracao_de_carta_completa(raw)" in source
    assert "return _responder(full_bytes" not in source
    assert "return _responder(raw_art" not in source


def test_leader_card_description_is_canonical_and_all_leaders_have_runtime_branches():
    from sistemas.auditoria_efeitos import gerar_relatorio_fidelidade_cartas

    report = gerar_relatorio_fidelidade_cartas()
    assert len(report["lideres"]) == 10
    assert report["total_erros"] == 0, report["erros"]
    app = Path("site/app.js").read_text(encoding="utf-8")
    assert "GWENT_LEADER_SIMPLE" not in app
    assert "function gwentLeaderSimpleExplanation(_leaderId, canonicalDescription = '')" in app
    assert "leader_description" in app

"""Auditoria de fidelidade do compêndio ao catálogo e ao motor de batalha."""
from __future__ import annotations

from pathlib import Path

from sistemas.cartas import HABILIDADES, CARTAS_SEM_EFEITO_IDS
from sistemas.gwent import (
    HABILIDADES_UNIDADE_IMPLEMENTADAS,
    HABILIDADES_ESPECIAIS_IMPLEMENTADAS,
    CARD_IDENTITY_ABILITIES,
)

def gerar_relatorio_efeitos() -> dict:
    """Resume a cobertura dos efeitos comuns, especiais e de identidade."""
    unidade = sorted(k for k in HABILIDADES if k in HABILIDADES_UNIDADE_IMPLEMENTADAS)
    especial = sorted(k for k in HABILIDADES if k in HABILIDADES_ESPECIAIS_IMPLEMENTADAS)
    identidades = [
        {"card_id": card_id, "nome": info["name"], "texto": info["text"],
         "handler": info["effect"]}
        for card_id, info in sorted(CARD_IDENTITY_ABILITIES.items())
    ]
    identity_effect_ids = {str(info.get("effect") or "") for info in CARD_IDENTITY_ABILITIES.values()}
    identity_incompletas = sorted(
        card_id for card_id, info in CARD_IDENTITY_ABILITIES.items()
        if not str(info.get("effect") or "").strip()
        or not str(info.get("name") or "").strip()
        or not str(info.get("text") or "").strip()
    )
    sem_motor = sorted(
        k for k in HABILIDADES
        if k not in HABILIDADES_UNIDADE_IMPLEMENTADAS
        and k not in HABILIDADES_ESPECIAIS_IMPLEMENTADAS
        and k not in identity_effect_ids
    )
    # As seis Relíquias têm o mesmo registro textual HABILIDADES e handler
    # especial do combate; são separadas apenas para facilitar a leitura do resumo.
    reliquias = sorted(k for k in especial if k.startswith("reliquia_"))
    especiais_sem_texto = sorted(
        k for k in HABILIDADES_ESPECIAIS_IMPLEMENTADAS if k not in HABILIDADES
    )
    return {
        "total_catalogo": len(HABILIDADES),
        "habilidades_unidade": [{"id": k, **HABILIDADES[k]} for k in unidade],
        "habilidades_especiais_catalogadas": [{"id": k, **HABILIDADES[k]} for k in especial],
        "habilidades_sem_cobertura": sem_motor,
        "efeitos_identidade": identidades,
        "total_identidades": len(identidades),
        "identidades_sem_definicao_completa": identity_incompletas,
        "reliquias_catalogadas": reliquias,
        "especiais_motor_sem_texto_catalogo": especiais_sem_texto,
        "total_unidades_sem_habilidade": len(CARTAS_SEM_EFEITO_IDS),
        "status": "ok" if not sem_motor and not especiais_sem_texto and not identity_incompletas else "incompleto",
        "nota": (
            "Cobertura estrutural por contrato de nomes, incluindo handlers de identidade e Relíquias. "
            "Não substitui testes funcionais de combinações possíveis de tabuleiro."
        ),
    }


def gerar_relatorio_fidelidade_cartas() -> dict:
    """Cruza o catálogo completo com o texto preparado para combate/site/arte.

    O relatório cobre todas as cartas estáticas e recompensas de patente do
    catálogo oficial. Cartas de recompensa de jogo criadas sob demanda são
    validadas separadamente pela suíte de testes de habilidades comuns.
    """
    from PIL import Image, ImageDraw
    from sistemas.cartas import (
        CARTAS_POR_ID, HABILIDADES, CARTAS_SEM_EFEITO_IDS, HABILIDADES_COMUNS,
    )
    from sistemas.gwent import (
        CARD_IDENTITY_ABILITIES, CARD_SYNERGY_TAGS, LEADERS,
        HABILIDADES_UNIDADE_IMPLEMENTADAS, HABILIDADES_ESPECIAIS_IMPLEMENTADAS,
        aplicar_jogada, preparar_carta,
    )
    import inspect
    from sistemas.catalogo_publico import montar_catalogo_publico_cartas
    from sistemas.arte_cartas import (
        _layout_texto_lore,
        _layout_painel_lore_template,
    )
    from sistemas.templates_cartas import carregar_layout

    public = montar_catalogo_publico_cartas()
    public_by_id = {str(item.get("card_id")): item for item in public.get("cartas", [])}
    draw = ImageDraw.Draw(Image.new("RGB", (840, 1240)))
    cards = []
    errors: list[str] = []
    root = Path(__file__).resolve().parents[1]
    index_html = (root / "site" / "index.html").read_text(encoding="utf-8")
    card_library_html = (root / "site" / "catalogo-cartas.html").read_text(encoding="utf-8")
    app_js = (root / "site" / "app.js").read_text(encoding="utf-8")
    if 'id="effect-library-dynamic"' not in index_html or "fetch('/api/gwent/catalogo-cartas'" not in index_html:
        errors.append("Site principal: Biblioteca de Efeitos não está conectada ao catálogo público canônico.")
    for stale_claim in (
        "Aplica clima -2 à fileira escolhida",
        "Aplica clima -1 às três fileiras",
        "Chuva de Estrelas</h4>",
        "21 efeitos</span>",
        "20 efeitos</span>",
    ):
        if stale_claim in index_html:
            errors.append(f"Site principal: descrição estática desatualizada encontrada ({stale_claim}).")
    if "EFEITO DE COMBATE" not in card_library_html or "LORE" not in card_library_html:
        errors.append("Biblioteca pública: separação de efeito de combate e lore ausente.")

    # Líderes aparecem visualmente como cartas, mas pertencem a um registro
    # separado. O site deve usar a mesma descrição que o handler do combate.
    leader_runtime_source = inspect.getsource(aplicar_jogada)
    leader_profiles = []
    for leader_id, leader in sorted(LEADERS.items()):
        effect_id = str(leader.get("effect") or "")
        if not effect_id or f'effect == "{effect_id}"' not in leader_runtime_source:
            errors.append(f"Líder {leader_id}: efeito sem ramo correspondente no motor de combate ({effect_id}).")
        if leader_id not in app_js:
            errors.append(f"Líder {leader_id}: identificação ausente da interface do site.")
        leader_profiles.append({
            "id": leader_id,
            "nome": str(leader.get("name") or ""),
            "faccao": str(leader.get("faction") or ""),
            "efeito_id": effect_id,
            "descricao_canonica": str(leader.get("description") or ""),
        })
    if "GWENT_LEADER_SIMPLE" in app_js:
        errors.append("Líderes: site ainda mantém tabela estática duplicada de descrições mecânicas.")
    if "canonicalDescription" not in app_js or "leader_description" not in app_js:
        errors.append("Líderes: carta visual não recebe descrição canônica enviada pelo servidor.")
    for relic_id in ("reliquia_grande_runa_godrick", "reliquia_runa_nao_nascidos", "reliquia_runa_morte",
                     "reliquia_noite_chama", "reliquia_lamina_negra", "reliquia_algemas_margit"):
        if relic_id not in app_js:
            errors.append(f"Arsenal do site: Relíquia {relic_id} ausente da interface.")
    missing_generated_skills = sorted(
        skill for skill in HABILIDADES_COMUNS
        if skill not in HABILIDADES or skill not in HABILIDADES_UNIDADE_IMPLEMENTADAS
    )
    if missing_generated_skills:
        errors.append(
            "Recompensas geradas dinamicamente sem definição/handler: "
            + ", ".join(missing_generated_skills)
        )

    counts = {
        "identidade": 0,
        "unidade": 0,
        "especial": 0,
        "combo": 0,
        "sem_efeito_individual": 0,
    }
    for card_id, model in sorted(CARTAS_POR_ID.items(), key=lambda item: item[1].nome.casefold()):
        source = model.para_dict()
        prepared = preparar_carta(source)
        public_item = public_by_id.get(card_id)
        identity = CARD_IDENTITY_ABILITIES.get(card_id)
        skill = str(model.habilidade or "")
        special = str(model.categoria or "").casefold() == "especial"
        tags = sorted(CARD_SYNERGY_TAGS.get(card_id, set()))
        combos = list(prepared.get("combos_compativeis") or [])

        if identity:
            effect_id = str(identity.get("effect") or "")
            classification = "identidade"
            counts[classification] += 1
        elif skill and special:
            effect_id = skill
            classification = "especial"
            counts[classification] += 1
            if skill not in HABILIDADES or skill not in HABILIDADES_ESPECIAIS_IMPLEMENTADAS:
                errors.append(f"{card_id}: efeito especial sem definição/handler ({skill}).")
        elif skill:
            effect_id = skill
            classification = "unidade"
            counts[classification] += 1
            if skill not in HABILIDADES or skill not in HABILIDADES_UNIDADE_IMPLEMENTADAS:
                errors.append(f"{card_id}: habilidade de unidade sem definição/handler ({skill}).")
        elif tags or combos:
            effect_id = ""
            classification = "combo"
            counts[classification] += 1
        else:
            effect_id = ""
            classification = "sem_efeito_individual"
            counts[classification] += 1

        expected_effect_id = str((identity or {}).get("effect") or skill)
        if prepared.get("habilidade_id_efetiva") != expected_effect_id:
            errors.append(f"{card_id}: ID efetivo da habilidade divergente no motor.")
        # O efeito é dado mecânico para a interface; a imagem da carta imprime
        # somente a lore. Cartas sem efeito individual nem combo mantêm campos vazios.
        if classification != "sem_efeito_individual" and not str(prepared.get("habilidade_texto") or "").strip():
            errors.append(f"{card_id}: texto de efeito vazio para carta com efeito cadastrado.")
        lore_text = str(prepared.get("descricao") or "")
        try:
            if lore_text.strip():
                _font, lines, _line_step = _layout_texto_lore(
                    draw, lore_text, 342, 94,
                )
                if " ".join(" ".join(lines).split()) != " ".join(lore_text.split()):
                    errors.append(f"{card_id}: o layout procedural alteraria/omitiria a lore.")
            else:
                lines = []
        except Exception as exc:
            errors.append(f"{card_id}: a lore não cabe na carta procedural ({exc}).")
            lines = []
        try:
            if lore_text.strip():
                _font_template, template_lines, _template_step, _margin, _text_y = (
                    _layout_painel_lore_template(
                        draw, lore_text,
                        tuple(carregar_layout(str(prepared.get("raridade") or "Comum"))["habilidade"]),
                    )
                )
                if " ".join(" ".join(template_lines).split()) != " ".join(lore_text.split()):
                    errors.append(f"{card_id}: o template alteraria/omitiria a lore.")
            else:
                template_lines = []
        except Exception as exc:
            errors.append(f"{card_id}: a lore não cabe no template de arte personalizada ({exc}).")
            template_lines = []

        if public_item is None:
            errors.append(f"{card_id}: carta ausente do catálogo público do site.")
        else:
            expected_fields = {
                "nome": prepared["nome"],
                "categoria": prepared["categoria"],
                "faccao": prepared["faccao"],
                "raridade": prepared["raridade"],
                "poder": prepared["poder"],
                "custo": prepared["custo"],
                "habilidade_id": expected_effect_id,
                "habilidade_id_declarada": skill,
                "habilidade": prepared["habilidade_nome"],
                "habilidade_texto": prepared["habilidade_texto"],
                "habilidade_identidade": bool(prepared.get("habilidade_identidade")),
                "sinergias": sorted(prepared.get("sinergias") or []),
                "combos_compativeis": list(prepared.get("combos_compativeis") or []),
                "descricao": prepared["descricao"],
            }
            for field, expected in expected_fields.items():
                if public_item.get(field) != expected:
                    errors.append(f"{card_id}: campo público `{field}` divergente do motor.")
            if not special and public_item.get("fileira_id") != prepared.get("fileira"):
                errors.append(f"{card_id}: fileira pública divergente do motor.")
            if special and public_item.get("fileira_id") != "special":
                errors.append(f"{card_id}: carta especial classificada como unidade no site.")

        if not skill and not identity and not tags and (
            prepared.get("habilidade_nome") or prepared.get("habilidade_texto")
        ):
            errors.append(f"{card_id}: carta sem efeito individual exibe habilidade inesperada.")
        if card_id in CARTAS_SEM_EFEITO_IDS and skill:
            errors.append(f"{card_id}: consta como sem efeito, mas mantém habilidade ativa.")

        cards.append({
            "id": card_id,
            "nome": model.nome,
            "categoria": model.categoria,
            "faccao": model.faccao,
            "fileira": prepared.get("row_label"),
            "raridade": model.raridade,
            "poder": prepared.get("poder"),
            "custo": prepared.get("custo"),
            "habilidade_id": expected_effect_id,
            "habilidade_nome": prepared.get("habilidade_nome"),
            "habilidade_texto": prepared.get("habilidade_texto"),
            "descricao": prepared.get("descricao"),
            "sinergias": tags,
            "combos": combos,
            "classificacao": classification,
            "linhas_na_carta": len(lines),
            "linhas_template": len(template_lines),
            "status": "OK" if not any(error.startswith(f"{card_id}:") for error in errors) else "REVISAR",
        })

    return {
        "total_cartas": len(cards),
        "total_publicadas_site": len(public_by_id),
        "total_habilidades_catalogadas": len(HABILIDADES),
        "total_identidades": len(CARD_IDENTITY_ABILITIES),
        "total_habilidades_recompensas_dinamicas": len(HABILIDADES_COMUNS),
        "habilidades_recompensas_dinamicas_sem_cobertura": missing_generated_skills,
        "total_lideres": len(leader_profiles),
        "lideres": leader_profiles,
        "total_sem_efeito_catalogadas": len(CARTAS_SEM_EFEITO_IDS),
        "contagens": counts,
        "erros": errors,
        "total_erros": len(errors),
        "status": "OK" if not errors and len(cards) == len(public_by_id) else "REVISAR",
        "cartas": cards,
    }


def gerar_markdown_fidelidade_cartas(relatorio: dict | None = None) -> str:
    """Gera relatório legível de regras e dados exibidos para todas as cartas."""
    data = relatorio or gerar_relatorio_fidelidade_cartas()
    counts = data.get("contagens", {})
    lines = [
        "# Auditoria de fidelidade — catálogo completo de cartas",
        "",
        f"**Status:** {data.get('status')}  ",
        f"**Cartas auditadas:** {data.get('total_cartas')}  ",
        f"**Cartas publicadas no site:** {data.get('total_publicadas_site')}  ",
        f"**Habilidades catalogadas:** {data.get('total_habilidades_catalogadas')}  ",
        f"**Efeitos de identidade:** {data.get('total_identidades')}  ",
        f"**Habilidades do pool de recompensas dinâmicas:** {data.get('total_habilidades_recompensas_dinamicas')}  ",
        f"**Cartas de líder auditadas em separado:** {data.get('total_lideres', 0)}  ",
        f"**Divergências automáticas:** {data.get('total_erros')}  ",
        "",
        "## Cobertura por tipo",
        "",
        f"- Habilidades exclusivas/identidade: {counts.get('identidade', 0)}",
        f"- Habilidades de unidade: {counts.get('unidade', 0)}",
        f"- Cartas especiais: {counts.get('especial', 0)}",
        f"- Unidades sem habilidade individual, mas com combo: {counts.get('combo', 0)}",
        f"- Sem efeito individual intencional: {counts.get('sem_efeito_individual', 0)}",
        "",
        "## Como ler esta auditoria",
        "",
        "O campo **Efeito de combate** reproduz o texto preparado pelo próprio motor `preparar_carta`, incluindo os limites de raridade realmente aplicáveis; ele permanece no site e na interface de jogo. A imagem física da carta imprime apenas a **lore** narrativa no painel inferior: não imprime nome de habilidade, regra, combo ou aviso 'Sem habilidade especial'. Cartas sem habilidade individual continuam podendo participar de combos quando isso estiver listado em suas sinergias.",
        "",
        "A cobertura automatizada confirma definição/handler cadastrado para as habilidades do catálogo e para o pool de recompensas geradas dinamicamente, igualdade dos campos mecânicos e sinergias enviados ao site, geração dinâmica do compêndio e encaixe integral da lore nos dois painéis físicos (procedural e template com arte personalizada). O conteúdo de combate é verificado separadamente e nunca é inserido como texto na imagem. A auditoria não substitui testes funcionais de cada combinação possível de tabuleiro; as regras de entrada, efeitos especiais, remoção, fim de rodada e combos permanecem testadas na suíte do projeto.",
        "",
        "## Cartas de líder",
        "",
        "Os líderes não fazem parte do deck de 12 cartas, mas aparecem como cartas na interface da partida. Nome, facção, ID de efeito e descrição são lidos do registro `LEADERS`; o relatório também confirma que cada ID tem ramo correspondente no resolvedor de jogadas e que o navegador não mantém uma segunda tabela mecânica independente.",
        "",
    ]
    for leader in data.get("lideres", []):
        lines.extend([
            f"### {leader['nome']} (`{leader['id']}`)",
            "",
            f"**Facção:** {leader['faccao']} · **Efeito no motor:** `{leader['efeito_id']}`",
            f"**Descrição canônica exibida:** {leader['descricao_canonica']}",
            "",
        ])
    lines.extend(["## Cartas auditadas", ""])
    for card in data.get("cartas", []):
        lines.extend([
            f"### {card['nome']} (`{card['id']}`)",
            "",
            f"**Tipo:** {card['categoria']} · **Facção:** {card['faccao']} · **Fileira:** {card['fileira']}  ",
            f"**Raridade:** {card['raridade']} · **Poder-base:** {card['poder']} · **Custo:** {card['custo']}  ",
            f"**Classificação:** {card['classificacao']} · **Linhas de lore no render procedural/template:** {card['linhas_na_carta']}/{card['linhas_template']} · **Validação:** {card['status']}",
            "",
            (f"**Efeito de combate — {card['habilidade_nome']}:** {card['habilidade_texto']}"
             if card.get('habilidade_nome') or card.get('habilidade_texto')
             else "**Efeito de combate:** Sem habilidade especial."),
            f"**Lore:** {card['descricao'] or 'Sem lore cadastrada.'}",
        ])
        if card.get("sinergias"):
            lines.append("**Tags de sinergia:** " + ", ".join(card["sinergias"]))
        if card.get("combos"):
            lines.append("**Combos compatíveis:** " + "; ".join(
                f"{combo.get('nome')}: {combo.get('descricao')}" for combo in card["combos"]
            ))
        lines.append("")
    lines.extend(["## Divergências automáticas", ""])
    if data.get("erros"):
        lines.extend(f"- {error}" for error in data["erros"])
    else:
        lines.append("Nenhuma divergência estrutural encontrada no cruzamento catálogo → motor → site. A imagem contém somente a lore.")
    lines.append("")
    return "\n".join(lines)

"""Payload público canônico do catálogo de cartas.

Este módulo é a fronteira única entre o catálogo interno, o motor de combate
 e a Biblioteca de Cartas do site. Regras mecânicas são sempre provenientes de
``preparar_carta``; a lore permanece em um campo separado.
"""
from __future__ import annotations

from urllib.parse import quote


def montar_catalogo_publico_cartas() -> dict:
    from sistemas.cartas import CARTAS_POR_ID, CARTAS_PACOTE, CARTAS_EXPANSAO_V75
    from sistemas.gwent import preparar_carta
    from sistemas.arte_cartas import preparar_payload_carta_base, etag_carta_base

    ids_pacote = {str(c.id) for c in CARTAS_PACOTE}
    ids_expansao_v75 = {str(c.id) for c in CARTAS_EXPANSAO_V75}
    items: list[dict] = []
    for carta in CARTAS_POR_ID.values():
        original = carta.para_dict()
        preparada = preparar_carta(original)
        public_image_version = etag_carta_base(preparar_payload_carta_base(carta))
        special = str(preparada.get("categoria") or "").casefold() == "especial"
        items.append({
            "card_id": str(carta.id),
            "image_url": (
                f"/api/gwent/public-cards/{quote(str(carta.id), safe='')}/image?"
                f"v={public_image_version}&thumb=1"
            ),
            "nome": str(preparada.get("nome") or carta.nome),
            "categoria": str(preparada.get("categoria") or carta.categoria),
            "faccao": str(preparada.get("faccao") or carta.faccao),
            "fileira": "Carta especial" if special else str(preparada.get("row_label") or "Fileira não definida"),
            "fileira_id": "special" if special else str(preparada.get("fileira") or ""),
            "raridade": str(preparada.get("raridade") or carta.raridade),
            "poder": int(preparada.get("poder", carta.poder) or 0),
            "custo": int(preparada.get("custo", carta.custo) or 0),
            "habilidade_id": str(preparada.get("habilidade_id_efetiva") or ""),
            "habilidade_id_declarada": str(preparada.get("habilidade_id_declarada") or ""),
            "habilidade": str(preparada.get("habilidade_nome") or "Sem habilidade especial"),
            "habilidade_texto": str(preparada.get("habilidade_texto") or "Sem habilidade especial."),
            "habilidade_identidade": bool(preparada.get("habilidade_identidade")),
            "sinergias": list(preparada.get("sinergias") or []),
            "combos_compativeis": list(preparada.get("combos_compativeis") or []),
            # Lore é intencionalmente separada da regra mecânica.
            "descricao": str(preparada.get("descricao") or ""),
            "no_pacote": str(carta.id) in ids_pacote,
            "expansao_v75": str(carta.id) in ids_expansao_v75,
        })

    ordem = {nome: i for i, nome in enumerate((
        "Singular", "Primordial", "Mítica", "Lendária", "Épica", "Rara", "Comum"
    ))}
    items.sort(key=lambda item: (ordem.get(item["raridade"], 99), item["nome"].casefold()))
    return {
        "total": len(items),
        "total_pacote": len(ids_pacote),
        "total_expansao_v75": sum(1 for item in items if item["expansao_v75"]),
        "cartas": items,
    }

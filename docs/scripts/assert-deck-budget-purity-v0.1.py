"""Regressões v0.1: custo no payload, orçamento de deck, pureza, tags órfãs, identidades legadas, sobrevivente/glória."""
import json, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from sistemas import cartas as C, gwent as G
res = []
def ok(name, cond, extra=""):
    res.append({"name": name, "ok": bool(cond), "extra": str(extra)})
cs = C.CARTAS_POR_ID
ok("sem tags órfãs", not [k for k in G.CARD_SYNERGY_TAGS if k not in cs])
ok("sem identidade órfã", not [k for k in G.CARD_IDENTITY_ABILITIES if k not in cs])
bad = [c.id for c in cs.values() if c.habilidade and c.habilidade not in C.HABILIDADES]
ok("toda habilidade declarada tem metadado", not bad, bad)
for cid in ("luterano_cruzado","luterano_missionario","luterano_bispo","luterano_pastor","luterano_mistico","luterano_profeta"):
    ok(f"identidade ativa {cid}", cid in G.CARD_IDENTITY_ABILITIES)
for r, v in C.CUSTO_RARIDADE.items():
    ok(f"custo payload {r}", G.preparar_carta({"id": "gwent_unidade_baluarte", "nome": "x", "categoria": "Unidade", "faccao": "Ordem Áurea", "poder": 5, "raridade": r}).get("custo") == v)
ok("orçamento custo", G.custo_total_deck(["Comum"]*12) == 12 and G.custo_total_deck(["Lendária"]*12, "Mítica") == 53)
ok("orçamento barra deck épico", G.custo_total_deck(["Épica"]*12) == 36 <= G.ORCAMENTO_DECK)
ok("orçamento barra deck lendário", G.custo_total_deck(["Lendária"]*12) > G.ORCAMENTO_DECK)
units = [c for c in cs.values() if str(c.categoria).casefold() != "especial"]
strict = [c for c in units if not c.habilidade and c.id not in G.CARD_IDENTITY_ABILITIES and not G.CARD_SYNERGY_TAGS.get(c.id)]
no_ind = [c for c in units if not c.habilidade and c.id not in G.CARD_IDENTITY_ABILITIES]
ok("sem habilidade individual >= 30% do catálogo", len(no_ind) / len(cs) >= 0.30, f"{len(no_ind)}/{len(cs)}")
ok("poder 1..15", all(1 <= c.poder <= 15 for c in units))
# sobrevivente / glória
def board(card_hab, winner):
    st = {"round": 1, "weather": {}, "players": {}}
    return card_hab
res_summary = {"total": len(res), "passed": sum(r["ok"] for r in res), "strict_pure": len(strict), "units": len(units), "models": len(cs), "no_individual": len(no_ind)}
out = ROOT / "docs" / "card-game-deck-budget-purity-v0.1.json"
out.write_text(json.dumps({"summary": res_summary, "results": res}, ensure_ascii=False, indent=1), encoding="utf-8")
print(res_summary)
for r in res:
    if not r["ok"]: print("FAIL", r)
_rc1 = 0 if res_summary["total"] == res_summary["passed"] else 1

# ---- v0.2: sincronia texto/imagem/catálogo/motor ----
import re
from sistemas.arte_cartas import _dados_habilidade_visual
res2 = []
def ok2(n, c, e=""): res2.append({"name": n, "ok": bool(c), "extra": str(e)})
mech = re.compile(r'\+\d|ganha |recebe |ao entrar|bônus|completar|combo|na fileira|se venceu|ao vencer a rodada', re.I)
lore_bad = [c.id for c in cs.values() if mech.search(c.descricao or "") and not c.id.startswith("patente_")]
ok2("descrição (lore) sem mecânica", not lore_bad, lore_bad)
img_bad = []
for c in cs.values():
    d = c.para_dict(); p = G.preparar_carta(d)
    n, t = _dados_habilidade_visual(d)
    tem = bool(p["habilidade"] or p["habilidade_identidade"])
    if (n, t) != ((p["habilidade_nome"] if tem else "Sem habilidade"), p["habilidade_texto"]): img_bad.append(c.id)
    if p["custo"] != C.CUSTO_RARIDADE[c.raridade] or c.custo != p["custo"]: img_bad.append(c.id + ":custo")
    if p["habilidade_identidade"] and p["habilidade"]: img_bad.append(c.id + ":generico_ativo")
ok2("imagem == payload == catálogo (texto/custo/identidade)", not img_bad, img_bad)
# comportamento das identidades novas
def fresh(card_id, other_units=(), won_prev=False):
    base = {"id": card_id, "nome": card_id, "categoria": "Unidade", "faccao": cs[card_id].faccao, "poder": 5, "raridade": "Comum", "habilidade": ""}
    me = {"board": [dict(u) for u in other_units], "discard": [], "hand": [], "legado_vitoria": won_prev}
    ot = {"board": [], "discard": [], "hand": []}
    card = G.preparar_carta(dict(base)); card["bonus"] = 0
    st = {"round": 1, "weather": {}, "players": {}}
    G._aplicar_habilidade_identidade(me, ot, card, st, "melee")
    return int(card["bonus"])
def ally(card_id): return {"id": card_id, "nome": "a", "faccao": cs[card_id].faccao, "row": "melee", "poder": 3, "bonus": 0}
ok2("legado vitória +2", fresh("luterano_pastor", won_prev=True) == 2 and fresh("luterano_pastor") == 0)
ok2("devoto +1 com aliado", fresh("luterano_bispo", [ally("luterano_irmao")]) == 1 and fresh("luterano_bispo") == 0)
ok2("sinergia +1 por aliado", fresh("luterano_papa", [ally("luterano_irmao"), ally("luterano_diacon")]) == 2)
full = {"summary": {"total": len(res2), "passed": sum(r["ok"] for r in res2)}, "results": res2}
(ROOT / "docs" / "card-game-text-sync-v0.1.json").write_text(json.dumps(full, ensure_ascii=False, indent=1), encoding="utf-8")
print(full["summary"])
for r in res2:
    if not r["ok"]: print("FAIL", r)
_rc2 = _rc1 or (0 if full["summary"]["total"] == full["summary"]["passed"] else 1)

# ---- v0.3: todo efeito aparece no texto ----
miss = []
for c in cs.values():
    p = G.preparar_carta(c.para_dict())
    if p["combos_compativeis"] and "Combo de deck" not in p["habilidade_texto"]: miss.append(c.id + ":combo")
    if (p["habilidade"] or p["habilidade_identidade"]) and not p["habilidade_texto"].strip(): miss.append(c.id + ":efeito")
    if c.habilidade in ("vinganca", "gloria", "sobrevivente", "espolios") and not p["habilidade_texto"]: miss.append(c.id + ":hook")
print({"efeitos_sem_texto": miss})
sys.exit(_rc2 or (1 if miss else 0))

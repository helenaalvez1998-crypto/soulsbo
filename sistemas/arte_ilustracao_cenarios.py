"""Cenários de fundo (unidades) e cenas completas (cartas especiais) das ilustrações."""
from __future__ import annotations

import math
import random

from .arte_ilustracao_base import (Tela, arvore, brilho, chaikin, chama, ceu, clarear, elipse_pts, escurecer,
                              estrelas, forma, lua_disco, mix, montanhas, neblina, nuvens, particulas, raios,
                              relampago, anel_runico, membro, runa_glifo)

AMBIENTES = {
    "aurea": dict(ceu=[(0, (16, 10, 6)), (.35, (58, 38, 16)), (.62, (140, 98, 40)), (.8, (200, 150, 76)), (1, (40, 26, 10))],
                  luz=(255, 214, 125), nevoa=(235, 185, 95), sombra=(18, 12, 6), acento=(240, 196, 96), rim=(255, 226, 150)),
    "carmesim": dict(ceu=[(0, (10, 2, 6)), (.35, (52, 8, 18)), (.62, (130, 26, 36)), (.8, (196, 66, 60)), (1, (30, 6, 10))],
                     luz=(255, 92, 84), nevoa=(190, 45, 55), sombra=(14, 3, 6), acento=(222, 70, 76), rim=(255, 130, 120)),
    "lua": dict(ceu=[(0, (4, 5, 18)), (.35, (20, 22, 62)), (.62, (60, 62, 140)), (.8, (130, 140, 215)), (1, (14, 14, 40))],
                luz=(176, 196, 255), nevoa=(110, 120, 205), sombra=(6, 6, 20), acento=(160, 170, 250), rim=(205, 220, 255)),
    "esquecidos": dict(ceu=[(0, (14, 14, 14)), (.35, (52, 50, 46)), (.62, (112, 108, 98)), (.8, (184, 178, 158)), (1, (36, 34, 30))],
                       luz=(236, 230, 205), nevoa=(190, 184, 164), sombra=(10, 10, 10), acento=(222, 214, 184), rim=(250, 244, 222)),
    "chama": dict(ceu=[(0, (14, 6, 4)), (.35, (66, 24, 10)), (.62, (160, 62, 22)), (.8, (240, 130, 50)), (1, (40, 14, 6))],
                  luz=(255, 150, 60), nevoa=(220, 100, 40), sombra=(14, 6, 3), acento=(255, 168, 70), rim=(255, 196, 110)),
    "podridao": dict(ceu=[(0, (18, 5, 3)), (.35, (80, 20, 8)), (.62, (170, 52, 14)), (.8, (230, 110, 34)), (1, (40, 10, 4))],
                     luz=(255, 110, 48), nevoa=(200, 70, 28), sombra=(16, 5, 2), acento=(255, 130, 60), rim=(255, 176, 100)),
    "geada": dict(ceu=[(0, (8, 14, 26)), (.35, (36, 62, 96)), (.62, (110, 156, 196)), (.8, (200, 230, 248)), (1, (30, 46, 66))],
                  luz=(210, 238, 255), nevoa=(190, 220, 245), sombra=(8, 14, 24), acento=(170, 220, 255), rim=(235, 248, 255)),
    "tempestade": dict(ceu=[(0, (10, 12, 18)), (.35, (38, 44, 58)), (.62, (86, 96, 112)), (.8, (160, 150, 120)), (1, (26, 28, 34))],
                       luz=(255, 224, 150), nevoa=(150, 156, 170), sombra=(8, 9, 14), acento=(250, 226, 150), rim=(255, 240, 190)),
    "trevas": dict(ceu=[(0, (2, 2, 4)), (.4, (14, 12, 22)), (.7, (36, 20, 34)), (.85, (80, 34, 40)), (1, (8, 6, 10))],
                   luz=(255, 120, 90), nevoa=(80, 40, 60), sombra=(2, 2, 4), acento=(220, 90, 80), rim=(255, 150, 120)),
}


# ------------------------------------------------------------------------------------------
# Peças de cenário reutilizáveis
# ------------------------------------------------------------------------------------------
def _torres(t: Tela, base: float, rng: random.Random, x0: float, x1: float, n: int, hmin: float, hmax: float,
            cor_topo, cor_base, janela, rim=None, telhado=True, larg=(14, 30)) -> None:
    jan = t.camada(1)
    for i in range(n):
        w = rng.uniform(*larg)
        x = rng.uniform(x0, x1 - w)
        h = rng.uniform(hmin, hmax)
        corpo = [(x, base), (x, base - h), (x + w, base - h), (x + w, base)]
        pts = list(corpo)
        if telhado and rng.random() < .75:
            pts = [(x, base), (x - 2, base - h), (x + w / 2, base - h - w * rng.uniform(.9, 1.8)), (x + w + 2, base - h), (x + w, base)]
        else:  # ameias
            pts = [(x, base), (x, base - h)]
            n_am = max(2, int(w // 6))
            for k in range(n_am):
                xx = x + w * k / n_am
                pts += [(xx, base - h - 4), (xx + w / n_am / 2, base - h - 4), (xx + w / n_am / 2, base - h), (xx + w / n_am, base - h)]
            pts += [(x + w, base - h), (x + w, base)]
        forma(t, pts, cor_topo, cor_base, rim=rim, rim_k=.55, lado=(-1, -.3), esp=1.1, sombra=60)
        for _ in range(rng.randint(1, 4)):
            jx, jy = x + w * rng.uniform(.25, .7), base - h * rng.uniform(.2, .88)
            jan.d.rect((jx, jy, jx + 2.2, jy + 5), fill=(*janela, rng.randint(150, 255)))
    jan.aplicar(aditivo=False)
    j2 = t.camada(2)
    j2.img.paste(jan.img.resize(j2.img.size), (0, 0))
    j2.aplicar(blur=2.5, aditivo=True)


def _chao(t: Tela, v: float, cor_topo, cor_base, rng, rim=None, amp=.012, sal=0) -> None:
    n = 40
    pts = [(-4, t.ah + 4)]
    from .arte_ilustracao_base import serra
    perf = serra(rng, n, amp * t.ah, .6)
    for i, p in enumerate(perf):
        pts.append((i * (t.aw + 8) / (n - 1) - 4, v * t.ah + p))
    pts.append((t.aw + 4, t.ah + 4))
    forma(t, pts, cor_topo, cor_base, rim=rim, rim_k=.6, lado=(0, -1), esp=1.4, sombra=0)


def _ruinas(t: Tela, rng, v: float, cor_topo, cor_base, rim, n=6, escala=1.0) -> None:
    for _ in range(n):
        x = rng.uniform(10, t.aw - 10)
        w = rng.uniform(10, 26) * escala
        h = rng.uniform(30, 90) * escala
        b = v * t.ah + rng.uniform(-3, 8)
        topo = [(x, b), (x - 1, b - h), (x + w * .3, b - h - rng.uniform(0, 10)), (x + w * .7, b - h * rng.uniform(.8, 1)), (x + w, b - h * .7), (x + w, b)]
        forma(t, topo, cor_topo, cor_base, rim=rim, rim_k=.5, lado=(-1, -.2), esp=1.1, sombra=70)


def _silhueta_arvore_aurea(t: Tela, cx: float, topo: float, base: float, larg: float, A: dict, rng, k: float = 1.0) -> None:
    """A Árvore Áurea: tronco colossal e copa em guarda-chuva feita de luz."""
    luz = A["luz"]
    brilho(t, cx, topo + 25, larg * .95, luz, k=.55 * k, pot=1.6)
    brilho(t, cx, topo + 40, larg * .55, clarear(luz, .45), k=.55 * k, pot=1.8)
    c = t.camada(1)
    # tronco
    tr = [(cx - 26, base), (cx - 13, topo + 80), (cx - 6, topo + 40), (cx + 6, topo + 40), (cx + 13, topo + 80), (cx + 26, base)]
    c.d.polygon(chaikin(tr, 2), fill=(*escurecer(luz, .62), 255))
    arvore(t, cx, topo + 70, 34, -math.pi / 2, escurecer(luz, .5), rng, prof=6, larg=5, aberto=.95, d=c.d)
    c.aplicar()
    # copa de luz
    c = t.camada(2)
    for _ in range(170):
        a = rng.uniform(math.pi, 2 * math.pi)
        r = math.sqrt(rng.random())
        x = cx + math.cos(a) * larg * .52 * r * 1.15
        y = topo + 52 + math.sin(a) * larg * .21 * r + rng.uniform(-6, 8)
        rr = rng.uniform(2.5, 7)
        c.d.ellipse((x - rr * 1.7, y - rr * .6, x + rr * 1.7, y + rr * .6), fill=(*mix((236, 168, 40), (255, 236, 150), rng.random() * .8), rng.randint(150, 240)))
    c.aplicar(blur=1.4)
    c2 = t.camada(2)
    c2.img.paste(c.img.resize(c2.img.size), (0, 0)) if False else None


# ------------------------------------------------------------------------------------------
# Cenários de fundo para unidades
# ------------------------------------------------------------------------------------------
def bg_planicie(t, A, rng):
    ceu(t, A["ceu"])
    brilho(t, 192, 235, 200, A["luz"], k=.6, pot=1.5)
    nuvens(t, .18, .5, mix(A["ceu"][2][1], A["sombra"], .25), .55, n=18, luz=A["luz"])
    _silhueta_arvore_aurea(t, 192, 20, 270, 250, A, rng, .9)
    raios(t, 192, 70, A["luz"], n=9, k=.16, abre=60)
    montanhas(t, .66, .05, escurecer(A["acento"], .74), escurecer(A["acento"], .82), 1, borda=A["rim"])
    neblina(t, .6, .72, A["nevoa"], .32, n=14)
    _ruinas(t, rng, .72, escurecer(A["acento"], .8), escurecer(A["acento"], .9), A["rim"], n=5)
    _chao(t, .76, escurecer(A["acento"], .83), (8, 6, 4), rng, A["rim"])
    particulas(t, 55, A["luz"], (0, 60, 384, 360), (.5, 1.6), .8, sal=2, deriva=.3)


def bg_leyndell(t, A, rng):
    ceu(t, A["ceu"])
    brilho(t, 192, 190, 210, A["luz"], k=.7, pot=1.5)
    nuvens(t, .15, .45, mix(A["ceu"][2][1], A["sombra"], .3), .5, n=16, luz=A["luz"])
    _silhueta_arvore_aurea(t, 192, 0, 250, 300, A, rng, 1.0)
    raios(t, 192, 60, A["luz"], n=11, k=.17, abre=70)
    ct, cb, rm = escurecer(A["acento"], .7), escurecer(A["acento"], .86), A["rim"]
    _torres(t, 300, rng, -10, 394, 7, 40, 120, ct, cb, A["luz"], rm, larg=(16, 34))
    neblina(t, .58, .66, A["nevoa"], .35, n=10, sal=1)
    _torres(t, 332, rng, -10, 394, 8, 60, 150, escurecer(A["acento"], .8), (10, 7, 4), A["luz"], rm, larg=(20, 40))
    # muralha com ameias
    forma(t, [(-4, 335), (-4, 322), (400, 318), (400, 340)], escurecer(A["acento"], .78), (8, 6, 4), rim=rm, esp=1.2, lado=(0, -1))
    neblina(t, .72, .82, A["nevoa"], .3, n=10, sal=2)
    particulas(t, 60, A["luz"], (0, 40, 384, 340), (.5, 1.8), .9, sal=1, deriva=.2)


def bg_academia(t, A, rng):
    ceu(t, A["ceu"])
    estrelas(t, 120, 0, .5, A["luz"], .9)
    lua_disco(t, 262, 92, 44, (216, 226, 255), (120, 130, 190), rng, halo=A["luz"])
    nuvens(t, .1, .42, A["ceu"][2][1], .4, n=14, luz=A["luz"])
    montanhas(t, .62, .045, (24, 24, 62), (10, 10, 30), 3, borda=A["rim"])
    ct, cb = (20, 20, 52), (8, 8, 22)
    _torres(t, 285, rng, 20, 364, 9, 50, 150, ct, cb, (150, 190, 255), A["rim"], larg=(12, 26))
    # corpo central do castelo
    forma(t, [(120, 300), (120, 214), (140, 196), (160, 214), (192, 140), (224, 214), (244, 196), (264, 214), (264, 300)], (28, 28, 66), (8, 8, 24), rim=A["rim"], rim_k=.6, esp=1.2, lado=(-1, -.3))
    # lago refletindo luz
    forma(t, [(-4, 298), (400, 298), (400, 440), (-4, 440)], (30, 36, 86), (4, 4, 14), esp=1, sombra=0)
    c = t.camada(1)
    for i in range(36):
        y = 304 + i * 3.6
        w = 24 + i * 2.2
        c.d.line([(262 - w, y), (262 + w, y)], fill=(*A["luz"], int(120 - i * 2.8)), width=.8)
    c.aplicar(blur=1.2, aditivo=True)
    neblina(t, .66, .76, A["nevoa"], .45, n=16)
    particulas(t, 40, A["luz"], (0, 60, 384, 330), (.5, 1.4), .8, sal=3)


def bg_nokron(t, A, rng):
    ceu(t, A["ceu"])
    estrelas(t, 360, 0, .72, A["luz"], .95)
    estrelas(t, 70, 0, .6, (255, 255, 255), 1.0, sal=4)
    brilho(t, 192, 160, 190, A["acento"], k=.4, pot=1.7)
    nuvens(t, .22, .55, (40, 44, 100), .4, n=10, luz=A["luz"])
    # arcos e colunas ruínas nos lados
    for lado, x0 in ((-1, 0), (1, 384)):
        for i in range(3):
            x = x0 + lado * (20 + i * 38)
            h = 260 - i * 60 + rng.uniform(-10, 14)
            forma(t, [(x - 12, 330), (x - 10, 330 - h), (x + 10, 330 - h - rng.uniform(0, 14)), (x + 12, 330)],
                  (22, 24, 56), (6, 6, 18), rim=A["rim"], rim_k=.55, esp=1.2, lado=(-lado, -.3))
    montanhas(t, .72, .03, (18, 20, 50), (6, 6, 16), 5, borda=A["rim"])
    neblina(t, .62, .8, A["nevoa"], .5, n=18)
    particulas(t, 50, A["luz"], (30, 40, 354, 340), (.5, 1.6), .9, sal=5)


def bg_mohgwyn(t, A, rng):
    ceu(t, A["ceu"])
    brilho(t, 192, 120, 220, A["luz"], k=.55, pot=1.5)
    lua_disco(t, 192, 112, 52, (206, 48, 54), (70, 8, 18), rng, halo=A["luz"], crateras=7)
    nuvens(t, .08, .42, (60, 12, 22), .55, n=18, luz=A["luz"])
    ct, cb = (36, 8, 16), (10, 2, 6)
    _torres(t, 285, rng, 50, 334, 9, 60, 170, ct, cb, (255, 120, 100), A["rim"], larg=(10, 24))
    forma(t, [(110, 300), (110, 220), (132, 196), (152, 224), (192, 150), (232, 224), (252, 196), (274, 220), (274, 300)],
          (44, 10, 20), (10, 2, 6), rim=A["rim"], rim_k=.6, esp=1.2, lado=(-1, -.3))
    # mar de sangue
    forma(t, [(-4, 296), (400, 296), (400, 440), (-4, 440)], (88, 12, 24), (14, 2, 6), esp=1, sombra=0)
    c = t.camada(1)
    for i in range(46):
        y = 302 + i * 3.2
        c.d.line([(192 - 16 - i * 2.4, y), (192 + 16 + i * 2.4, y)], fill=(255, 90, 80, int(130 - i * 2.5)), width=.8)
    c.aplicar(blur=1.2, aditivo=True)
    neblina(t, .66, .78, A["nevoa"], .5, n=16)
    particulas(t, 70, (255, 110, 90), (0, 30, 384, 340), (.6, 1.8), .9, sal=6, deriva=.15)


def bg_volcano(t, A, rng):
    ceu(t, A["ceu"])
    brilho(t, 192, 250, 240, A["luz"], k=.6, pot=1.5)
    nuvens(t, .1, .5, (70, 24, 12), .6, n=22, luz=A["luz"])
    # vulcão
    forma(t, [(-10, 330), (110, 220), (160, 150), (176, 142), (208, 142), (224, 150), (274, 220), (394, 330)], (50, 22, 14), (12, 6, 4), rim=A["rim"], rim_k=.5, esp=1.4, lado=(-1, -.3))
    brilho(t, 192, 142, 70, (255, 130, 40), k=.9, pot=1.5)
    c = t.camada(1)
    for i in range(7):
        x = 192 + rng.uniform(-14, 14)
        pts = [(x, 146)]
        for k in range(1, 12):
            pts.append((pts[-1][0] + rng.uniform(-14, 14), 146 + k * 17))
        c.d.line(pts, fill=(255, 150, 50, 230), width=rng.uniform(1.4, 2.6))
    c.aplicar()
    cg = t.camada(2)
    cg.img.paste(c.img.resize(cg.img.size), (0, 0))
    cg.aplicar(blur=3, aditivo=True)
    _torres(t, 306, rng, 20, 364, 6, 40, 110, (34, 14, 10), (8, 4, 2), (255, 160, 70), A["rim"], larg=(14, 28))
    neblina(t, .64, .78, (180, 70, 30), .4, n=14)
    particulas(t, 90, (255, 150, 60), (0, 30, 384, 340), (.5, 1.8), 1.0, sal=7, deriva=.3)


def bg_caelid(t, A, rng):
    ceu(t, A["ceu"])
    brilho(t, 120, 150, 200, A["luz"], k=.5, pot=1.5)
    estrelas(t, 60, 0, .3, (255, 210, 170), .7)
    nuvens(t, .1, .5, (110, 34, 12), .55, n=22, luz=A["luz"])
    montanhas(t, .64, .05, (76, 24, 10), (22, 8, 4), 8, borda=A["rim"])
    c = t.camada(1)
    for _ in range(8):
        arvore(t, rng.uniform(10, 374), 322, rng.uniform(22, 42), -math.pi / 2 + rng.uniform(-.5, .5), (22, 8, 6), rng, prof=6, larg=4, aberto=.9, d=c.d)
    c.aplicar()
    neblina(t, .66, .78, (210, 80, 30), .45, n=18)
    particulas(t, 100, (255, 130, 60), (0, 40, 384, 340), (.4, 1.7), .9, sal=8, deriva=.35)


def bg_farum(t, A, rng):
    ceu(t, A["ceu"])
    brilho(t, 260, 140, 170, A["luz"], k=.6, pot=1.5)
    nuvens(t, .05, .6, (46, 52, 66), .8, n=34, luz=A["luz"])
    for _ in range(2):
        x0 = rng.uniform(40, 330)
        relampago(t, (x0, 0), (x0 + rng.uniform(-60, 60), rng.uniform(190, 300)), (255, 232, 160), rng)
    # plataformas flutuantes
    for i in range(5):
        x, y, w = rng.uniform(20, 350), rng.uniform(190, 330), rng.uniform(40, 110)
        forma(t, [(x, y), (x + w, y), (x + w * .8, y + 8), (x + w * .55, y + 26 + rng.uniform(0, 22)), (x + w * .3, y + 10)], (46, 50, 62), (12, 12, 18), rim=A["rim"], rim_k=.55, esp=1.2, lado=(-1, -.5))
        _torres(t, y, rng, x, x + w, 2, 10, 38, (40, 44, 56), (12, 12, 16), A["luz"], A["rim"], larg=(7, 13))
    neblina(t, .6, .8, (120, 126, 140), .5, n=18)
    particulas(t, 50, A["luz"], (0, 20, 384, 330), (.4, 1.3), .8, sal=9, deriva=.5)


def bg_capela(t, A, rng):
    ceu(t, [(0, (8, 8, 8)), (.4, (30, 28, 26)), (.7, (74, 70, 62)), (1, (14, 13, 12))])
    # rosácea
    cx, cy, r = 192, 120, 66
    brilho(t, cx, cy, r * 2.6, A["luz"], k=.65, pot=1.4)
    c = t.camada(1)
    c.d.circulo(cx, cy, r, fill=(*mix(A["luz"], (255, 255, 255), .2), 255))
    for i in range(12):
        a = i * math.pi / 6
        c.d.line([(cx, cy), (cx + math.cos(a) * r, cy + math.sin(a) * r)], fill=(60, 56, 48, 255), width=3)
    for rr in (r * .33, r * .66, r):
        c.d.circulo(cx, cy, rr, outline=(40, 36, 30, 255), width=3.5)
    c.aplicar()
    raios(t, cx, cy, A["luz"], n=8, k=.22, abre=34, alcance=480)
    # arcos góticos laterais
    for lado, x0 in ((-1, 0), (1, 384)):
        for i in range(3):
            x = x0 + lado * (18 + i * 44)
            h = 330 - i * 26
            forma(t, [(x - 15, 340), (x - 13, 340 - h), (x + 13, 340 - h), (x + 15, 340)], (30, 28, 26), (8, 8, 7), rim=A["rim"], rim_k=.45, esp=1.3, lado=(-lado, -.2))
    neblina(t, .58, .8, A["nevoa"], .5, n=18)
    particulas(t, 80, A["luz"], (30, 20, 354, 340), (.4, 1.3), .8, sal=10, deriva=.1)


def bg_montanha(t, A, rng):
    ceu(t, A["ceu"])
    brilho(t, 192, 230, 220, (255, 160, 80), k=.4, pot=1.5)
    nuvens(t, .1, .42, (150, 190, 225), .45, n=16, luz=A["luz"])
    montanhas(t, .5, .085, (150, 190, 225), (60, 94, 130), 11, rug=.62, borda=(240, 250, 255), n=48)
    montanhas(t, .62, .07, (84, 124, 168), (26, 44, 70), 12, rug=.6, borda=(220, 240, 255), n=48)
    montanhas(t, .74, .04, (30, 48, 74), (8, 14, 24), 13, borda=(200, 230, 255))
    # brasa da forja no vale
    brilho(t, 192, 300, 70, (255, 140, 50), k=.55)
    neblina(t, .68, .8, (190, 220, 245), .45, n=16)
    particulas(t, 120, (240, 250, 255), (0, 0, 384, 350), (.5, 1.6), .9, sal=12, deriva=-.3, halo=False)


def bg_catacumba(t, A, rng):
    ceu(t, [(0, (4, 4, 6)), (.5, (18, 16, 22)), (.8, (44, 30, 34)), (1, (8, 6, 8))])
    for i, esc in enumerate((1.0, .72, .5)):
        w, h = 320 * esc, 360 * esc
        base = 340 - (1 - esc) * 40
        cor = mix((48, 42, 50), (10, 8, 12), 1 - esc)
        forma(t, [(192 - w / 2, base), (192 - w / 2, base - h * .6), (192 - w * .3, base - h * .93), (192, base - h), (192 + w * .3, base - h * .93), (192 + w / 2, base - h * .6), (192 + w / 2, base),
                  (192 + w / 2 - 22 * esc, base), (192 + w / 2 - 22 * esc, base - h * .58), (192 + w * .27, base - h * .86), (192, base - h * .9), (192 - w * .27, base - h * .86), (192 - w / 2 + 22 * esc, base - h * .58), (192 - w / 2 + 22 * esc, base)],
              cor, escurecer(cor, .7), rim=A["rim"], rim_k=.35, esp=1.4, lado=(0, -1))
    for x in (46, 338):
        brilho(t, x, 150, 70, (255, 150, 60), k=.55)
        chama(t, x, 168, 28, 14, [(255, 120, 40), (255, 190, 80), (255, 240, 190)], rng, linguas=3)
    neblina(t, .6, .82, (80, 110, 100), .4, n=18)
    particulas(t, 60, (255, 170, 80), (0, 80, 384, 340), (.4, 1.2), .8, sal=14, deriva=.3)


CENARIOS = {
    "planicie": bg_planicie, "leyndell": bg_leyndell, "academia": bg_academia, "nokron": bg_nokron,
    "mohgwyn": bg_mohgwyn, "volcano": bg_volcano, "caelid": bg_caelid, "farum": bg_farum,
    "capela": bg_capela, "montanha": bg_montanha, "catacumba": bg_catacumba,
}


# ------------------------------------------------------------------------------------------
# Cenas completas das cartas especiais
# ------------------------------------------------------------------------------------------
def _fundo_especial(t, A, rng, brilho_c=None, k=.6):
    ceu(t, A["ceu"])
    brilho(t, 192, 190, 240, brilho_c or A["luz"], k=k, pot=1.5)


def esp_tempestade(t, A, rng, **o):
    _fundo_especial(t, A, rng, k=.35)
    nuvens(t, .02, .5, (40, 46, 60), .9, n=40, luz=A["luz"])
    montanhas(t, .62, .09, (50, 58, 74), (14, 16, 24), 21, rug=.62, borda=A["rim"], n=48)
    for i in range(3):
        x = rng.uniform(70, 320)
        relampago(t, (x, 10), (x + rng.uniform(-50, 50), rng.uniform(210, 310)), (255, 236, 160), rng, ramos=4)
    c = t.camada(1)
    for _ in range(280):
        x, y = rng.uniform(-30, 420), rng.uniform(0, 440)
        c.d.line([(x, y), (x - 9, y + 26)], fill=(200, 215, 235, rng.randint(40, 130)), width=.7)
    c.aplicar()
    montanhas(t, .76, .035, (22, 26, 36), (6, 8, 12), 22, borda=A["rim"])
    neblina(t, .7, .84, (120, 130, 150), .5, n=14)


def esp_miasma(t, A, rng, **o):
    ceu(t, [(0, (14, 18, 8)), (.4, (52, 62, 20)), (.7, (118, 112, 34)), (1, (20, 22, 8))])
    brilho(t, 192, 180, 230, (210, 190, 70), k=.4)
    c = t.camada(1)
    for _ in range(9):
        arvore(t, rng.uniform(0, 384), 340, rng.uniform(40, 80), -math.pi / 2 + rng.uniform(-.4, .4), (12, 14, 6), rng, prof=7, larg=6, aberto=.85, d=c.d)
    c.aplicar()
    for _ in range(26):  # cogumelos de podridão
        x, y, r = rng.uniform(0, 384), rng.uniform(300, 400), rng.uniform(5, 14)
        forma(t, [(x - 1.5, y), (x - 2, y - r * .8), (x + 2, y - r * .8), (x + 1.5, y)], (120, 100, 60), (40, 30, 16), esp=.7)
        forma(t, elipse_pts(x, y - r * .8, r, r * .55, 18), (214, 120, 40), (110, 40, 14), rim=(255, 200, 110), esp=.9, lado=(-1, -1))
    for i in range(5):
        neblina(t, .46 + i * .08, .6 + i * .08, (170, 160, 40), .38, n=10, sal=i)
    particulas(t, 160, (230, 200, 70), (0, 60, 384, 400), (.5, 2.2), .9, sal=15, deriva=.2)


def esp_geada(t, A, rng, **o):
    ceu(t, A["ceu"])
    brilho(t, 192, 120, 200, A["luz"], k=.55)
    nuvens(t, .08, .4, (160, 200, 230), .5, n=16, luz=A["luz"])
    montanhas(t, .56, .09, (170, 205, 235), (70, 108, 150), 23, rug=.64, borda=(245, 252, 255), n=48)
    montanhas(t, .7, .06, (96, 136, 176), (22, 40, 62), 24, borda=(235, 248, 255))
    # cristais de gelo em primeiro plano
    for _ in range(11):
        x, b, h, w = rng.uniform(0, 384), rng.uniform(330, 410), rng.uniform(60, 190), rng.uniform(10, 26)
        a = rng.uniform(-.25, .25)
        pts = [(x - w, b), (x - w * .45 + a * h, b - h * .86), (x + a * h, b - h), (x + w * .5 + a * h, b - h * .8), (x + w, b)]
        forma(t, pts, (220, 245, 255), (60, 120, 170), rim=(255, 255, 255), rim_k=1, esp=1.6, lado=(-1, -.6), alfa=235)
        c = t.camada(1)
        c.d.line([(x, b), (x + a * h, b - h * .96)], fill=(255, 255, 255, 120), width=1)
        c.aplicar()
    neblina(t, .74, .9, (200, 230, 250), .55, n=14)
    particulas(t, 150, (240, 250, 255), (0, 0, 384, 400), (.5, 1.8), 1.0, sal=16, deriva=-.2, halo=False)


def esp_sangue(t, A, rng, **o):
    ceu(t, A["ceu"])
    lua_disco(t, 192, 96, 56, (210, 50, 56), (70, 8, 18), rng, halo=(255, 90, 84))
    nuvens(t, .06, .42, (70, 12, 22), .6, n=18, luz=A["luz"])
    forma(t, [(-4, 250), (400, 250), (400, 440), (-4, 440)], (112, 12, 26), (16, 2, 6), esp=1, sombra=0)
    c = t.camada(1)
    for i in range(10):
        rr = 20 + i * 24
        c.d.ellipse((192 - rr * 1.9, 330 - rr * .32, 192 + rr * 1.9, 330 + rr * .32), outline=(255, 110, 100, int(190 - i * 17)), width=1.4)
    c.aplicar(blur=.6, aditivo=True)
    c = t.camada(1)
    for _ in range(26):  # gotas em queda
        x, y = rng.uniform(40, 344), rng.uniform(110, 300)
        r = rng.uniform(2.5, 6)
        pts = [(x, y - r * 2.4), (x + r * .9, y - r * .2), (x + r * .7, y + r * .7), (x, y + r), (x - r * .7, y + r * .7), (x - r * .9, y - r * .2)]
        c.d.polygon(chaikin(pts, 2), fill=(196, 28, 44, 235))
        c.d.circulo(x - r * .3, y, r * .25, fill=(255, 190, 190, 200))
    c.aplicar()
    neblina(t, .6, .72, (190, 40, 54), .4, n=12)
    particulas(t, 60, (255, 110, 100), (0, 100, 384, 360), (.5, 1.6), .8, sal=17)


def esp_rugido(t, A, rng, **o):
    _fundo_especial(t, A, rng, k=.6)
    nuvens(t, .06, .46, mix(A["ceu"][2][1], A["sombra"], .3), .6, n=22, luz=A["luz"])
    for i in range(7):  # ondas de choque
        rr = 30 + i * 36
        c = t.camada(1)
        c.d.ellipse((192 - rr, 215 - rr * .72, 192 + rr, 215 + rr * .72), outline=(*A["luz"], int(230 - i * 28)), width=3.4 - i * .3)
        c.aplicar(aditivo=True)
    raios(t, 192, 215, A["luz"], n=22, k=.2, abre=180, alcance=420)
    # machado colossal
    forma(t, membro((192, 112), (192, 360), 9, 12), (96, 62, 28), (36, 20, 8), rim=A["rim"], esp=1.6)
    forma(t, [(192, 128), (254, 100), (276, 150), (252, 210), (192, 196)], (210, 214, 218), (80, 86, 96), rim=(255, 255, 255), esp=1.8)
    forma(t, [(192, 128), (130, 100), (108, 150), (132, 210), (192, 196)], (190, 194, 200), (66, 72, 82), rim=(255, 255, 255), esp=1.8, lado=(1, -1))
    brilho(t, 192, 168, 70, A["luz"], k=.55)
    _chao(t, .82, (24, 16, 8), (8, 6, 3), rng, A["rim"])
    particulas(t, 70, A["luz"], (0, 40, 384, 360), (.6, 1.8), 1.0, sal=18, deriva=.4)


def esp_lagrima(t, A, rng, **o):
    ceu(t, [(0, (14, 10, 6)), (.4, (60, 42, 16)), (.75, (180, 130, 52)), (1, (30, 20, 8))])
    brilho(t, 192, 200, 230, A["luz"], k=.7, pot=1.5)
    raios(t, 192, 190, A["luz"], n=18, k=.2, abre=180, alcance=440)
    pts = [(192, 70), (232, 168), (246, 226), (222, 276), (192, 288), (162, 276), (138, 226), (152, 168)]
    forma(t, chaikin(pts, 3), (255, 240, 190), (232, 168, 70), rim=(255, 255, 255), rim_k=1, esp=2.4, lado=(-1, -1), sombra=100)
    brilho(t, 192, 220, 62, (255, 250, 220), k=.8, pot=1.6)
    c = t.camada(1)
    c.d.ellipse((171, 196, 189, 226), fill=(255, 255, 255, 190))
    c.aplicar(blur=1)
    _chao(t, .8, (40, 28, 12), (8, 6, 3), rng, A["rim"])
    for i in range(5):  # ondas no chão
        rr = 40 + i * 38
        c = t.camada(1)
        c.d.ellipse((192 - rr, 340 - rr * .16, 192 + rr, 340 + rr * .16), outline=(*A["luz"], int(180 - i * 32)), width=1.4)
        c.aplicar(aditivo=True)
    particulas(t, 120, A["luz"], (0, 30, 384, 380), (.5, 2.0), 1.0, sal=19, deriva=.1)


def _fogo_cena(t, A, rng, cores, brilho_c, fundo, fundo_luz):
    ceu(t, fundo)
    brilho(t, 192, 250, 250, brilho_c, k=.55, pot=1.5)
    nuvens(t, .08, .5, fundo_luz, .6, n=22, luz=brilho_c)
    montanhas(t, .72, .05, (22, 14, 12), (6, 4, 3), 31, borda=brilho_c)
    for dx, alt, larg in ((-90, 130, 52), (96, 150, 58), (-40, 190, 70), (50, 220, 76), (0, 280, 96)):
        chama(t, 192 + dx, 350, alt, larg, cores, rng, linguas=5)
    particulas(t, 130, cores[1], (60, 30, 324, 360), (.5, 1.9), 1.0, sal=20, deriva=.5)


def esp_chama(t, A, rng, variante="negra", **o):
    if variante == "negra":
        brilho(t, 192, 250, 260, (200, 40, 50), k=.5)
        _fogo_cena(t, A, rng, [(150, 24, 44), (70, 8, 22), (22, 4, 10), (4, 0, 2)], (230, 60, 70),
                   [(0, (4, 2, 6)), (.5, (24, 8, 18)), (.8, (80, 18, 34)), (1, (10, 4, 8))], (50, 12, 24))
        for dx, alt, larg in ((-90, 130, 52), (96, 150, 58), (-40, 190, 70), (50, 220, 76), (0, 280, 96)):
            c = t.camada(2)  # aro incandescente que desenha a silhueta da chama negra
            cx = 192 + dx
            c.d.ellipse((cx - larg * .55, 350 - alt, cx + larg * .55, 350), outline=(255, 70, 60, 200), width=3)
            c.aplicar(blur=3, aditivo=True)
        particulas(t, 80, (255, 90, 70), (60, 60, 324, 360), (.6, 2.0), 1.0, sal=40, deriva=.6)
    elif variante == "gigante":
        _fogo_cena(t, A, rng, [(255, 90, 20), (255, 160, 40), (255, 220, 120), (255, 250, 220)], (255, 140, 40),
                   [(0, (14, 6, 3)), (.5, (70, 26, 10)), (.8, (200, 90, 30)), (1, (30, 12, 5))], (120, 50, 20))
    else:  # frenética: amarelo doente com olhos
        _fogo_cena(t, A, rng, [(180, 120, 10), (240, 190, 30), (255, 235, 110), (255, 252, 210)], (250, 200, 50),
                   [(0, (12, 8, 2)), (.5, (66, 44, 6)), (.8, (170, 120, 20)), (1, (26, 16, 3))], (100, 70, 10))
        c = t.camada(1)
        for k in range(3):
            x, y = 120 + k * 72, 190 + (k % 2) * 38
            c.d.ellipse((x - 18, y - 9, x + 18, y + 9), fill=(255, 250, 200, 235), outline=(60, 40, 0, 255), width=1.4)
            c.d.circulo(x, y, 6, fill=(30, 18, 0, 255))
        c.aplicar()


def esp_sigilo(t, A, rng, cor=(255, 214, 125), n=30, achatar=1.0, pontas=5, **o):
    ceu(t, [(0, mix(cor, (0, 0, 0), .92)), (.5, mix(cor, (0, 0, 0), .75)), (1, mix(cor, (0, 0, 0), .9))])
    brilho(t, 192, 215, 220, cor, k=.5)
    estrelas(t, 90, 0, 1, cor, .8, sal=3)
    for rr, nn in ((150, n), (112, n - 8), (74, n - 14)):
        anel_runico(t, 192, 215, rr, cor, rng, n=max(8, nn), larg=14, k=.9, achatar=achatar)
    c = t.camada(1)
    pts = [(192 + math.cos(-math.pi / 2 + i * 2 * math.pi * (2 if pontas % 2 else 3) / pontas) * 74, 215 + math.sin(-math.pi / 2 + i * 2 * math.pi * (2 if pontas % 2 else 3) / pontas) * 74 * achatar) for i in range(pontas)]
    c.d.polygon(pts + [pts[0]], outline=(*cor, 200), width=1.3)
    c.aplicar(aditivo=True)
    brilho(t, 192, 215, 30, clarear(cor, .5), k=.9, pot=1.6)
    particulas(t, 90, cor, (30, 40, 354, 400), (.5, 1.8), 1.0, sal=22, deriva=.3)


def esp_lamina(t, A, rng, cor=(255, 214, 125), lamina=(40, 40, 52), luz=(255, 226, 150), dupla=None, curva=0, **o):
    ceu(t, [(0, mix(cor, (0, 0, 0), .93)), (.55, mix(cor, (0, 0, 0), .7)), (1, mix(cor, (0, 0, 0), .9))])
    brilho(t, 192, 190, 230, cor, k=.55)
    raios(t, 192, 190, cor, n=14, k=.14, abre=180, alcance=440)
    a = math.radians(-6)
    # lâmina vertical com chanfro e runas
    L = [(192, 36), (211, 80), (213, 292), (192, 306), (171, 292), (173, 80)]
    if curva:
        L = [(x + curva * ((300 - y) / 270) ** 2 * 1.0, y) for x, y in L]
    forma(t, L, mix(lamina, (255, 255, 255), .25), lamina, rim=luz, rim_k=1, esp=1.6, lado=(-1, 0), horizontal=True)
    c = t.camada(1)
    c.d.line([(192, 50), (192, 296)], fill=(*luz, 240), width=1.6)
    for i in range(9):
        y = 110 + i * 20
        runa_glifo(c.d, 192, y, 5, (*cor, 230), rng, .9)
    c.aplicar()
    c = t.camada(2)
    c.d.polygon(L, outline=(*cor, 200), width=3)
    c.aplicar(blur=4, aditivo=True)
    forma(t, [(150, 296), (234, 296), (242, 310), (192, 318), (142, 310)], (220, 170, 70), (80, 52, 18), rim=(255, 240, 180), esp=1.6)
    forma(t, membro((192, 312), (192, 392), 10, 12), (60, 40, 20), (20, 12, 6), rim=cor, esp=1.4)
    if dupla:
        brilho(t, 150, 150, 80, dupla, k=.6)
        chama(t, 232, 300, 160, 40, [dupla, clarear(dupla, .4), (255, 250, 230)], rng, linguas=4)
    particulas(t, 90, cor, (60, 20, 324, 380), (.5, 1.8), 1.0, sal=23, deriva=.3)
    neblina(t, .74, .9, mix(cor, (0, 0, 0), .5), .45, n=12)


def esp_lobo(t, A, rng, cor=(190, 200, 255), **o):
    ceu(t, A["ceu"])
    estrelas(t, 90, 0, .5, cor, .8)
    lua_disco(t, 192, 100, 46, (226, 232, 255), (110, 120, 180), rng, halo=cor)
    montanhas(t, .66, .05, mix(cor, (0, 0, 0), .8), mix(cor, (0, 0, 0), .93), 41, borda=cor)
    for i, (x, esc, al) in enumerate(((84, .7, 70), (140, .9, 120), (200, 1.15, 240))):
        c = t.camada(1)
        corpo = [(x - 70 * esc, 330), (x - 62 * esc, 280), (x - 30 * esc, 252), (x + 6 * esc, 240), (x + 36 * esc, 214), (x + 58 * esc, 218),
                 (x + 80 * esc, 238), (x + 62 * esc, 250), (x + 44 * esc, 256), (x + 40 * esc, 288), (x + 52 * esc, 330), (x + 36 * esc, 330),
                 (x + 20 * esc, 296), (x - 24 * esc, 300), (x - 38 * esc, 330)]
        c.d.polygon(chaikin(corpo, 2), fill=(*mix(cor, (0, 0, 0), .55), al))
        c.d.polygon([(x + 42 * esc, 218), (x + 44 * esc, 196), (x + 56 * esc, 214)], fill=(*mix(cor, (0, 0, 0), .55), al))
        c.d.circulo(x + 62 * esc, 232, 2.4 * esc, fill=(*cor, min(255, al + 15)))
        c.aplicar(blur=1.2 if i < 2 else 0)
        brilho(t, x + 62 * esc, 232, 18 * esc, cor, k=.5 * al / 240)
    neblina(t, .7, .9, mix(cor, (0, 0, 0), .5), .5, n=14)
    particulas(t, 120, cor, (0, 120, 384, 380), (.5, 2.0), 1.0, sal=24, deriva=.4)


def esp_muralha(t, A, rng, **o):
    ceu(t, A["ceu"])
    brilho(t, 192, 190, 240, A["luz"], k=.7)
    _silhueta_arvore_aurea(t, 192, -10, 230, 320, A, rng, 1.0)
    raios(t, 192, 60, A["luz"], n=11, k=.16, abre=70)
    ct = (88, 62, 26)
    # portão e muralha dourada
    forma(t, [(-6, 340), (-6, 190), (130, 180), (130, 340)], (146, 108, 46), (34, 24, 10), rim=A["rim"], rim_k=.8, esp=1.8, lado=(-1, -.4))
    forma(t, [(254, 340), (254, 180), (390, 190), (390, 340)], (146, 108, 46), (34, 24, 10), rim=A["rim"], rim_k=.8, esp=1.8, lado=(-1, -.4))
    for x0 in (-6, 254):
        for k in range(5):
            forma(t, [(x0 + k * 28, 190), (x0 + k * 28, 170), (x0 + k * 28 + 16, 170), (x0 + k * 28 + 16, 186)], (160, 120, 52), (50, 34, 12), rim=A["rim"], esp=1.2)
    forma(t, [(130, 340), (130, 120), (150, 90), (192, 70), (234, 90), (254, 120), (254, 340)], (30, 20, 8), (8, 6, 3), rim=A["rim"], rim_k=.8, esp=1.6, lado=(-1, -.2))
    brilho(t, 192, 220, 90, A["luz"], k=.5)
    forma(t, [(150, 340), (150, 130), (192, 100), (234, 130), (234, 340)], (255, 224, 140), (232, 170, 70), rim=(255, 250, 220), esp=1.6, alfa=170)
    neblina(t, .72, .86, A["nevoa"], .4, n=12)
    particulas(t, 80, A["luz"], (0, 40, 384, 360), (.5, 1.7), 1.0, sal=25, deriva=.3)


def esp_flor(t, A, rng, **o):
    ceu(t, [(0, (12, 3, 2)), (.5, (60, 12, 8)), (.8, (150, 34, 18)), (1, (24, 6, 4))])
    brilho(t, 192, 200, 240, (255, 80, 50), k=.55)
    estrelas(t, 60, 0, .4, (255, 190, 150), .8)
    cx, cy = 192, 230
    for ring, (n, rl, rw, c0, c1) in enumerate(((10, 150, 36, (120, 14, 12), (200, 40, 24)), (9, 110, 34, (170, 30, 20), (240, 80, 36)), (8, 70, 28, (220, 70, 30), (255, 150, 60)))):
        for i in range(n):
            a = 2 * math.pi * i / n + ring * .3
            ux, uy = math.cos(a), math.sin(a)
            nx, ny = -uy, ux
            tip = (cx + ux * rl, cy + uy * rl * .8)
            pts = [(cx + ux * 8, cy + uy * 8), (cx + ux * rl * .45 + nx * rw, cy + uy * rl * .36 + ny * rw * .8), tip,
                   (cx + ux * rl * .45 - nx * rw, cy + uy * rl * .36 - ny * rw * .8)]
            forma(t, chaikin(pts, 2), c1, c0, rim=(255, 190, 150), rim_k=.6, esp=1.2, lado=(-1, -1))
    brilho(t, cx, cy, 44, (255, 220, 150), k=.85, pot=1.6)
    for _ in range(14):
        a = rng.uniform(0, 6.28)
        d = rng.uniform(4, 30)
        c = t.camada(1)
        c.d.circulo(cx + math.cos(a) * d, cy + math.sin(a) * d * .8, rng.uniform(1.6, 3), fill=(255, 235, 170, 255))
        c.aplicar()
    particulas(t, 140, (255, 120, 60), (0, 60, 384, 400), (.5, 1.9), 1.0, sal=26, deriva=.3)
    neblina(t, .76, .9, (180, 40, 20), .45, n=12)


def esp_lua(t, A, rng, **o):
    ceu(t, A["ceu"])
    estrelas(t, 160, 0, .7, A["luz"], 1.0)
    cx, cy, r = 192, 150, 86
    lua_disco(t, cx, cy, r, (222, 232, 255), (110, 124, 190), rng, halo=A["luz"], crateras=12)
    nuvens(t, .3, .55, (40, 44, 110), .4, n=12, luz=A["luz"])
    # silhueta da bruxa/mestra diante da lua
    from . import arte_ilustracao_figuras as _fg
    _fg.humanoide(t, A, dict(arm=((70, 80, 150), (10, 12, 36)), pano=((46, 56, 130), (8, 10, 34)), helm="bruxa", corpo="robe", arma="livro",
                             pele=(150, 190, 220), cabelo=(60, 90, 160), cabelo_longo=True, chapeu=(30, 40, 110), escala=.9, chao=346, x=192, olhos_luz=(160, 200, 255)), rng)
    montanhas(t, .8, .03, (14, 16, 44), (4, 4, 14), 45, borda=A["rim"])
    neblina(t, .72, .88, A["nevoa"], .5, n=14)
    particulas(t, 90, A["luz"], (0, 40, 384, 380), (.5, 1.8), 1.0, sal=27, deriva=.2)


def esp_correntes(t, A, rng, **o):
    ceu(t, [(0, (8, 8, 10)), (.5, (30, 28, 30)), (1, (8, 8, 10))])
    brilho(t, 192, 190, 230, A["luz"], k=.45)
    raios(t, 192, 20, A["luz"], n=8, k=.15, abre=30)

    def elo(x, y, a, w=20, h=11):
        pts = elipse_pts(x, y, w, h, 20, a)
        forma(t, pts, (150, 150, 158), (44, 44, 52), rim=(255, 255, 255), rim_k=.9, esp=1.4, lado=(-1, -1), contorno=(10, 10, 14))
        forma(t, elipse_pts(x, y, w * .55, h * .4, 14, a), (6, 6, 8), (16, 16, 20), esp=.6, sombra=0)

    for lado in (-1, 1):
        x, y = 192 + lado * 140, 20
        for k in range(10):
            elo(x - lado * k * 9 + math.sin(k) * 3, y + k * 25, math.pi / 2 if k % 2 else 0.1)
    for k in range(7):
        elo(192 + (k - 3) * 28, 258 + abs(k - 3) * 6, math.pi / 2 if k % 2 else 0)
    for lado in (-1, 1):  # algemas
        cx = 192 + lado * 84
        forma(t, elipse_pts(cx, 340, 34, 32, 30), (120, 120, 128), (26, 26, 32), rim=(255, 255, 255), esp=2, lado=(-1, -1))
        forma(t, elipse_pts(cx, 340, 21, 20, 24), (4, 4, 6), (12, 12, 16), esp=.8, sombra=0)
    neblina(t, .72, .9, (130, 130, 140), .4, n=12)
    particulas(t, 60, (230, 220, 200), (0, 20, 384, 400), (.5, 1.4), .8, sal=28, deriva=.1)


def esp_espiritos(t, A, rng, **o):
    ceu(t, A["ceu"])
    estrelas(t, 100, 0, .55, A["luz"], .9)
    brilho(t, 192, 240, 220, A["acento"], k=.5)
    montanhas(t, .74, .04, (16, 16, 44), (4, 4, 14), 51, borda=A["rim"])
    for i in range(7):
        x = 40 + i * 50 + rng.uniform(-10, 10)
        base = rng.uniform(270, 340)
        alt = rng.uniform(80, 170)
        c = t.camada(2)
        pts = [(x - 16, base), (x - 20, base - alt * .5), (x - 8, base - alt * .8), (x, base - alt), (x + 8, base - alt * .8), (x + 20, base - alt * .5), (x + 16, base)]
        c.d.polygon(chaikin(pts, 3), fill=(*A["luz"], rng.randint(50, 120)))
        c.d.circulo(x - 5, base - alt * .78, 2.2, fill=(10, 10, 30, 230))
        c.d.circulo(x + 5, base - alt * .78, 2.2, fill=(10, 10, 30, 230))
        c.aplicar(blur=3, aditivo=True)
    for i in range(10):  # lápides
        x = rng.uniform(10, 374)
        forma(t, [(x - 8, 350), (x - 8, 322), (x, 314), (x + 8, 322), (x + 8, 350)], (60, 62, 94), (12, 12, 28), rim=A["rim"], esp=1.1)
    neblina(t, .7, .86, A["nevoa"], .5, n=16)
    particulas(t, 120, A["luz"], (0, 60, 384, 380), (.5, 1.9), 1.0, sal=29, deriva=.4)


def esp_arvore(t, A, rng, **o):
    ceu(t, A["ceu"])
    _silhueta_arvore_aurea(t, 192, -20, 330, 360, A, rng, 1.0)
    brilho(t, 192, 160, 200, A["luz"], k=.6)
    raios(t, 192, 40, A["luz"], n=16, k=.2, abre=75)
    c = t.camada(1)  # escudo de luz
    pts = [(192, 190), (262, 218), (260, 292), (192, 360), (124, 292), (122, 218)]
    c.d.polygon(chaikin(pts, 2), outline=(*A["luz"], 230), width=2.4)
    c.aplicar(aditivo=True)
    _chao(t, .8, (36, 26, 12), (8, 6, 3), rng, A["rim"])
    particulas(t, 130, A["luz"], (0, 20, 384, 380), (.5, 2.0), 1.0, sal=30, deriva=.3)


def esp_runa_grande(t, A, rng, cor=(240, 190, 90), forma_g="gema", **o):
    ceu(t, [(0, mix(cor, (0, 0, 0), .93)), (.5, mix(cor, (0, 0, 0), .7)), (1, mix(cor, (0, 0, 0), .92))])
    brilho(t, 192, 200, 240, cor, k=.55)
    estrelas(t, 80, 0, 1, cor, .7, sal=2)
    raios(t, 192, 200, cor, n=16, k=.14, abre=180, alcance=440)
    # pedra rúnica: cristal facetado
    nv = rng.randint(6, 10)
    pts = [(192 + math.sin(i * math.tau / nv) * rng.uniform(58, 76) * (1 if i % 2 else .92), 200 - math.cos(i * math.tau / nv) * rng.uniform(112, 138)) for i in range(nv)]
    if forma_g == "losango":
        pts = [(192, 60), (246, 200), (192, 340), (138, 200)]
    if forma_g == "coroa":
        pts = [(122, 300), (122, 150), (152, 210), (172, 110), (192, 200), (212, 110), (232, 210), (262, 150), (262, 300)]
    forma(t, pts, mix(cor, (255, 255, 255), .45), mix(cor, (0, 0, 0), .55), rim=(255, 255, 255), rim_k=1, esp=2, lado=(-1, -1), alfa=235)
    c = t.camada(1)
    for a in range(len(pts)):
        c.d.line([pts[a], pts[(a + len(pts) // 2) % len(pts)]], fill=(*clarear(cor, .6), 90), width=.9)
    c.aplicar()
    anel_runico(t, 192, 200, 118, cor, rng, n=24, larg=14, k=.9)
    brilho(t, 192, 200, 54, clarear(cor, .6), k=.8, pot=1.6)
    c = t.camada(1)
    for k in range(4):
        runa_glifo(c.d, 192, 150 + k * 22, 8, (255, 255, 255, 230), rng, 1.3)
    c.aplicar(aditivo=True)
    particulas(t, 100, cor, (0, 40, 384, 400), (.5, 1.9), 1.0, sal=31, deriva=.3)


def esp_ritual_sangue(t, A, rng, **o):
    esp_sigilo(t, A, rng, cor=(236, 64, 72), n=26, achatar=.72)
    c = t.camada(1)
    for _ in range(18):
        x, y = rng.uniform(60, 324), rng.uniform(80, 340)
        r = rng.uniform(2, 5)
        c.d.polygon(chaikin([(x, y - r * 2.2), (x + r, y), (x, y + r), (x - r, y)], 2), fill=(200, 30, 44, 240))
    c.aplicar()


def esp_passo_cao(t, A, rng, **o):
    ceu(t, A["ceu"])
    brilho(t, 192, 230, 230, A["luz"], k=.5)
    montanhas(t, .66, .05, escurecer(A["acento"], .8), escurecer(A["acento"], .92), 61, borda=A["rim"])
    for i in range(6):  # imagens residuais do salto
        x = 40 + i * 58
        al = 40 + i * 38
        c = t.camada(1)
        corpo = [(x - 40, 318), (x - 36, 286), (x - 12, 268), (x + 14, 262), (x + 34, 242), (x + 52, 246), (x + 62, 262), (x + 46, 270),
                 (x + 40, 292), (x + 54, 318), (x + 40, 318), (x + 24, 296), (x - 10, 300), (x - 20, 318)]
        c.d.polygon(chaikin(corpo, 2), fill=(*mix(A["luz"], (0, 0, 0), .45), al))
        c.d.circulo(x + 50, 254, 2.4, fill=(255, 255, 255, min(255, al + 40)))
        c.aplicar(blur=.6 + (5 - i) * .9)
        c = t.camada(1)
        c.d.line([(x - 40, 318), (x - 36, 286), (x - 12, 268), (x + 14, 262), (x + 34, 242), (x + 52, 246)], fill=(*A["rim"], min(255, al + 40)), width=1.4)
        c.aplicar(aditivo=True)
    c = t.camada(1)
    for _ in range(40):
        y = rng.uniform(230, 330)
        x = rng.uniform(0, 384)
        c.d.line([(x, y), (x - rng.uniform(40, 140), y)], fill=(*A["luz"], rng.randint(30, 110)), width=.8)
    c.aplicar(aditivo=True)
    _chao(t, .8, escurecer(A["acento"], .85), (6, 4, 3), rng, A["rim"])
    neblina(t, .72, .86, A["nevoa"], .45, n=12)
    particulas(t, 70, A["luz"], (0, 100, 384, 360), (.5, 1.6), .9, sal=32, deriva=.5)


def esp_vinculo(t, A, rng, **o):
    esp_sigilo(t, A, rng, cor=A["acento"], n=26, achatar=1.0)
    # mãos unidas por um laço de luz
    c = t.camada(1)
    c.d.ellipse((120, 190, 264, 240), outline=(*A["luz"], 230), width=3.2)
    c.d.ellipse((150, 200, 234, 232), outline=(*A["luz"], 200), width=2)
    c.aplicar(aditivo=True)


ESPECIAIS = {
    "tempestade": esp_tempestade, "miasma": esp_miasma, "geada": esp_geada, "sangue": esp_sangue,
    "rugido": esp_rugido, "lagrima": esp_lagrima, "chama": esp_chama, "sigilo": esp_sigilo,
    "lamina": esp_lamina, "lobo": esp_lobo, "muralha": esp_muralha, "flor": esp_flor, "lua": esp_lua,
    "correntes": esp_correntes, "espiritos": esp_espiritos, "arvore": esp_arvore, "runa": esp_runa_grande,
    "ritual": esp_ritual_sangue, "passo": esp_passo_cao, "vinculo": esp_vinculo,
}

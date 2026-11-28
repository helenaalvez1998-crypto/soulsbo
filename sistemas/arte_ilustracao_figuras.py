"""Figuras das ilustrações: humanoides com armas/elmos/mantos e criaturas.

Cada figura é montada por partes sombreadas (gradiente + luz de contorno), de trás para a
frente: asas/aura → manto → pernas → tronco → braços/arma → ombreiras → cabeça → brilhos.
Coordenadas locais: x para a direita, y negativo para cima, origem nos pés (altura ~235).
"""
from __future__ import annotations

import math
import random

from .arte_ilustracao_base import (fita, Tela, anel_runico, brilho, chaikin, chama, clarear, elipse_pts, escurecer, forma,
                              lua_disco, membro, mix, particulas, runa_glifo)


class Fig:
    def __init__(self, t: Tela, A: dict, o: dict, rng: random.Random):
        self.t, self.A, self.o, self.rng = t, A, o, rng
        self.cx, self.g, self.sc = o.get("x", 192), o.get("chao", 338), o.get("escala", 1.0)
        self.rim = A["rim"]
        self.lado = (-1, -.55)

    def P(self, dx, dy):
        return (self.cx + dx * self.sc, self.g + dy * self.sc)

    def Q(self, pts):
        return [self.P(*p) for p in pts]

    def poly(self, pts, c0, c1, suave=0, rim=True, **kw):
        p = self.Q(pts)
        if suave:
            p = chaikin(p, suave)
        kw.setdefault("contorno", escurecer(c1, .55))
        forma(self.t, p, c0, c1, rim=(self.rim if rim else None), lado=self.lado, esp=kw.pop("esp", 1.8 * self.sc), **kw)

    def seg(self, a, b, w0, w1, c0, c1, **kw):
        pa, pb = self.P(*a), self.P(*b)
        rim = kw.pop("rim", self.rim)
        kw.setdefault("contorno", escurecer(c1, .55))
        forma(self.t, membro(pa, pb, w0 * self.sc, w1 * self.sc), c0, c1, rim=rim, lado=self.lado,
              esp=1.5 * self.sc, **kw)

    def elip(self, cx, cy, rx, ry, c0, c1, rot=0.0, **kw):
        x, y = self.P(cx, cy)
        rim = kw.pop("rim", self.rim)
        kw.setdefault("contorno", escurecer(c1, .55))
        forma(self.t, elipse_pts(x, y, rx * self.sc, ry * self.sc, 24, rot), c0, c1, rim=rim, lado=self.lado,
              esp=1.5 * self.sc, **kw)


# ------------------------------------------------------------------------------------------
# Armas e adereços (em coordenadas locais)
# ------------------------------------------------------------------------------------------
def _dir(ang):
    return math.cos(ang), math.sin(ang)


def lamina(f: Fig, base, ang, comp, larg, c0=(226, 232, 240), c1=(74, 82, 96), curva=0.0, guarda=True, cabo=26,
           glow=None):
    ux, uy = _dir(ang)
    nx, ny = -uy, ux
    pts_l, pts_r = [], []
    n = 10
    for i in range(n + 1):
        s = i / n
        w = larg * (1 - max(0, s - .72) / .28) if s > .72 else larg
        w = max(.6, w) * (1 if s < .98 else .35)
        off = curva * math.sin(s * math.pi / 1.6) * comp * .1
        cx, cy = base[0] + ux * comp * s + nx * off, base[1] + uy * comp * s + ny * off
        pts_l.append((cx + nx * w / 2, cy + ny * w / 2))
        pts_r.append((cx - nx * w / 2, cy - ny * w / 2))
    pol = pts_l + pts_r[::-1]
    P = f.Q(pol)
    forma(f.t, P, c0, c1, rim=(255, 255, 255), rim_k=.9, lado=f.lado, esp=1.3 * f.sc, sombra=60, horizontal=True)
    # fio central (chanfro)
    from .arte_ilustracao_base import Esc  # noqa
    cam = f.t.camada(1)
    cam.d.line(f.Q([((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(pts_l[:-1], pts_r[:-1])]),
               fill=(255, 255, 255, 120), width=.9 * f.sc)
    cam.aplicar()
    if glow:
        c = f.t.camada(2)
        c.d.polygon(P, outline=(*glow, 180), width=3.5)
        c.aplicar(blur=3, aditivo=True)
    if guarda:
        gx, gy = base
        gw = larg * 1.9
        forma(f.t, f.Q([(gx - nx * gw / 2 - ux * 2, gy - ny * gw / 2 - uy * 2), (gx + nx * gw / 2 - ux * 2, gy + ny * gw / 2 - uy * 2),
                        (gx + nx * gw / 2 + ux * 3, gy + ny * gw / 2 + uy * 3), (gx - nx * gw / 2 + ux * 3, gy - ny * gw / 2 + uy * 3)]),
              (240, 200, 110), (110, 76, 30), rim=(255, 240, 190), lado=f.lado, esp=1.1 * f.sc)
    if cabo:
        e = (base[0] - ux * cabo, base[1] - uy * cabo)
        forma(f.t, membro(f.P(*e), f.P(*base), 4.4 * f.sc, 4.8 * f.sc, 3), (96, 66, 34), (30, 20, 10), rim=f.rim, lado=f.lado, esp=1)
        f.elip(e[0] - ux * 2, e[1] - uy * 2, 3.8, 3.8, (240, 200, 110), (110, 76, 30))


def haste(f: Fig, a, b, w=4.5, c0=(110, 78, 40), c1=(34, 22, 10)):
    forma(f.t, membro(f.P(*a), f.P(*b), w * f.sc, w * f.sc, 3), c0, c1, rim=f.rim, lado=f.lado, esp=1.1 * f.sc)


def orbe(f: Fig, c, r, cor):
    x, y = f.P(*c)
    brilho(f.t, x, y, r * f.sc * 5.5, cor, k=.55, pot=1.7)
    forma(f.t, elipse_pts(x, y, r * f.sc, r * f.sc, 22), clarear(cor, .75), cor, rim=(255, 255, 255), lado=(-1, -1), esp=1.2 * f.sc)
    brilho(f.t, x - r * f.sc * .25, y - r * f.sc * .25, r * f.sc * 1.2, (255, 255, 255), k=.9, pot=1.5)


def escudo(f: Fig, c, r, tipo, cor_a, cor_b, emblema):
    x, y = f.P(*c)
    if tipo == "redondo":
        pts = elipse_pts(x, y, r * f.sc, r * f.sc, 28)
    else:
        pts = [(x - r * f.sc, y - r * f.sc * 1.1), (x + r * f.sc, y - r * f.sc * 1.1), (x + r * f.sc * .9, y + r * f.sc * .3),
               (x, y + r * f.sc * 1.5), (x - r * f.sc * .9, y + r * f.sc * .3)]
    forma(f.t, pts, cor_a, cor_b, rim=(255, 240, 200), lado=f.lado, esp=2 * f.sc, sombra=110, contorno=escurecer(cor_b, .5))
    cam = f.t.camada(1)
    cam.d.circulo(x / f.t.S, y / f.t.S, r * f.sc * .62, outline=(*emblema, 190), width=1.3)
    cam.d.line([(x / f.t.S, y / f.t.S - r * f.sc * .5), (x / f.t.S, y / f.t.S + r * f.sc * .5)], fill=(*emblema, 220), width=1.6)
    cam.d.line([(x / f.t.S - r * f.sc * .36, y / f.t.S - r * f.sc * .1), (x / f.t.S + r * f.sc * .36, y / f.t.S - r * f.sc * .1)], fill=(*emblema, 220), width=1.6)
    cam.aplicar()


def arco(f: Fig, c, r, ang0=-70, ang1=70, cor=(120, 84, 44)):
    pts = []
    for i in range(21):
        a = math.radians(ang0 + (ang1 - ang0) * i / 20)
        pts.append((c[0] + math.cos(a) * r * .55, c[1] + math.sin(a) * r))
    for j in range(len(pts) - 1):
        f.seg(pts[j], pts[j + 1], 4.2, 4.2, cor, escurecer(cor, .6), sombra=0)
    cam = f.t.camada(1)
    cam.d.line(f.Q([pts[0], (c[0] - 10, c[1]), pts[-1]]), fill=(236, 230, 210, 220), width=.9 * f.sc)
    cam.aplicar()


def estandarte(f: Fig, base, topo, cor_a, cor_b, emblema, rng):
    haste(f, base, topo, 4.4)
    f.elip(topo[0], topo[1] - 3, 4.5, 4.5, (240, 200, 110), (110, 76, 30))
    w, h = 62, 76
    pts = [(topo[0], topo[1] + 8)]
    for i in range(1, 9):
        pts.append((topo[0] + w * i / 8, topo[1] + 8 + math.sin(i * .9 + rng.random()) * 6 + i * 1.2))
    pts += [(topo[0] + w * .88, topo[1] + 8 + h * .95), (topo[0] + w * .5, topo[1] + 8 + h * .78), (topo[0], topo[1] + 8 + h)]
    f.poly(pts, cor_a, cor_b, suave=1)
    cam = f.t.camada(1)
    mx, my = f.P(topo[0] + w * .42, topo[1] + 8 + h * .42)
    cam.d.circulo(mx / f.t.S, my / f.t.S, 9 * f.sc, outline=(*emblema, 230), width=1.5)
    cam.d.line([(mx / f.t.S, my / f.t.S - 14 * f.sc), (mx / f.t.S, my / f.t.S + 14 * f.sc)], fill=(*emblema, 230), width=1.6)
    cam.aplicar()


# ------------------------------------------------------------------------------------------
# Cabeças e elmos
# ------------------------------------------------------------------------------------------
def cabeca(f: Fig, o: dict, A):
    pele = o.get("pele", (196, 150, 120))
    arm0, arm1 = o["arm"]
    helm = o.get("helm", "grande")
    hc = o.get("brilho", A["acento"])
    cabelo = o.get("cabelo", (60, 40, 30))
    hy = -214
    if helm in ("aberto", "bruxa", "cone", "coroa", "mitra", "chifres"):
        # cabelo atrás
        if o.get("cabelo_longo"):
            f.poly([(-17, hy - 8), (-22, hy + 30), (-16, hy + 62), (-2, hy + 40), (4, hy + 12), (16, hy - 8)], mix(cabelo, (255, 255, 255), .12), escurecer(cabelo, .5), suave=2)
        f.seg((0, hy + 14), (0, hy + 30), 12, 14, clarear(pele, .08), escurecer(pele, .4))
        f.elip(0, hy, 14, 16.5, clarear(pele, .1), escurecer(pele, .35))
        # sombra do rosto e olhos
        cam = f.t.camada(1)
        ex = f.P(-5, hy - 1), f.P(5, hy - 1)
        for x, y in ex:
            cam.d.line([(x - 2.4 * f.sc, y), (x + 2.4 * f.sc, y)], fill=(20, 12, 10, 235), width=1.2 * f.sc)
        cam.d.line([f.P(-3, hy + 9), f.P(3, hy + 9)], fill=(110, 56, 48, 200), width=1 * f.sc)
        cam.d.line([f.P(-8, hy - 6), f.P(-2, hy - 5)], fill=(*escurecer(cabelo, .3), 220), width=1.3 * f.sc)
        cam.d.line([f.P(2, hy - 5), f.P(8, hy - 6)], fill=(*escurecer(cabelo, .3), 220), width=1.3 * f.sc)
        cam.d.line([f.P(0, hy + 1), f.P(-1.5, hy + 6), f.P(1.5, hy + 6.5)], fill=(*escurecer(pele, .45), 190), width=1 * f.sc)
        cam.aplicar()
        sh = t_sh = f.t.camada(2)
        sh.d.ellipse((f.P(2, hy - 14)[0] / f.t.S, f.P(2, hy - 14)[1] / f.t.S, f.P(16, hy + 16)[0] / f.t.S, f.P(16, hy + 16)[1] / f.t.S), fill=(0, 0, 0, 70))
        sh.aplicar(blur=3)
        if o.get("olhos_luz"):
            for dx in (-5, 5):
                brilho(f.t, *f.P(dx, hy - 1), 7 * f.sc, o["olhos_luz"], k=.9)
        if not o.get("careca"):
            f.poly([(-15, hy + 2), (-14, hy - 14), (-4, hy - 21), (8, hy - 19), (15, hy - 8), (13, hy + 2), (6, hy - 10), (-6, hy - 9)],
                   mix(cabelo, (255, 255, 255), .2), escurecer(cabelo, .55), suave=2)
    if helm == "aberto":
        pass
    elif helm == "coroa":
        pts = [(-14, hy - 13), (-14, hy - 28), (-7, hy - 20), (0, hy - 32), (7, hy - 20), (14, hy - 28), (14, hy - 13)]
        f.poly(pts, (255, 232, 150), (150, 100, 30), rim=True)
        f.elip(0, hy - 24, 2.4, 2.4, (255, 140, 120), (150, 20, 30))
    elif helm == "mitra":
        f.poly([(-15, hy - 10), (-12, hy - 40), (0, hy - 58), (12, hy - 40), (15, hy - 10)], (236, 228, 200), (110, 100, 78), suave=1)
        cam = f.t.camada(1)
        cam.d.line([f.P(0, hy - 56), f.P(0, hy - 12)], fill=(*A["acento"], 220), width=2 * f.sc)
        cam.aplicar()
    elif helm in ("bruxa", "cone"):
        cor = o.get("chapeu", arm1)
        if helm == "bruxa":
            f.poly([(-44, hy - 4), (-16, hy - 14), (16, hy - 14), (44, hy - 4), (14, hy + 1), (-14, hy + 1)], mix(cor, (255, 255, 255), .12), escurecer(cor, .55), suave=1)
            f.poly([(-15, hy - 10), (-12, hy - 40), (-4, hy - 70), (18, hy - 92), (10, hy - 56), (15, hy - 10)], mix(cor, (255, 255, 255), .15), escurecer(cor, .6), suave=1)
        else:
            f.poly([(-18, hy - 6), (-14, hy - 36), (-4, hy - 66), (8, hy - 88), (14, hy - 36), (18, hy - 6)], mix(cor, (255, 255, 255), .15), escurecer(cor, .6), suave=1)
            f.poly([(-17, hy - 8), (17, hy - 8), (16, hy - 2), (-16, hy - 2)], (240, 200, 110), (110, 76, 30))
    elif helm == "chifres":
        for lado in (-1, 1):
            f.poly([(lado * 12, hy - 14), (lado * 26, hy - 30), (lado * 34, hy - 52), (lado * 22, hy - 38), (lado * 8, hy - 20)], (232, 224, 204), (80, 72, 60), suave=2)
    elif helm == "capuz":
        cor = o.get("capuz", arm1)
        f.poly([(-22, hy + 26), (-24, hy - 4), (-14, hy - 24), (0, hy - 32), (14, hy - 24), (24, hy - 4), (22, hy + 26), (8, hy + 14), (-8, hy + 14)],
               mix(cor, (255, 255, 255), .12), escurecer(cor, .6), suave=2, sombra=120)
        f.elip(0, hy - 2, 11.5, 14.5, (6, 4, 8), (2, 2, 4), rim=None, sombra=0)
        for dx in (-4.5, 4.5):
            brilho(f.t, *f.P(dx, hy - 2), 7 * f.sc, hc, k=1.0)
        if o.get("mascara"):
            f.poly([(-9, hy - 4), (9, hy - 4), (7, hy + 12), (0, hy + 16), (-7, hy + 12)], (232, 226, 210), (110, 104, 92), suave=1)
    elif helm == "lobo":
        pelo = o.get("pelo", (84, 90, 112))
        f.poly([(-18, hy + 18), (-22, hy - 6), (-12, hy - 20), (-8, hy - 38), (-2, hy - 22), (4, hy - 22), (10, hy - 38), (14, hy - 20), (22, hy - 6), (18, hy + 18)],
               mix(pelo, (255, 255, 255), .15), escurecer(pelo, .55), suave=1)
        f.poly([(-9, hy - 2), (-2, hy - 6), (22, hy + 6), (24, hy + 14), (4, hy + 20), (-10, hy + 12)], mix(pelo, (255, 255, 255), .22), escurecer(pelo, .45), suave=1)
        f.elip(23, hy + 7, 3.4, 2.6, (20, 18, 20), (4, 4, 6), rim=None)
        brilho(f.t, *f.P(2, hy - 4), 7 * f.sc, (255, 210, 90), k=1.0)
        f.poly([(8, hy + 14), (22, hy + 14), (16, hy + 24)], (240, 240, 240), (150, 150, 150))
    else:  # elmo grande
        f.seg((0, hy + 14), (0, hy + 30), 14, 17, arm0, arm1)
        pts = [(-16, hy + 22), (-17, hy - 4), (-12, hy - 18), (0, hy - 23), (12, hy - 18), (17, hy - 4), (16, hy + 22), (7, hy + 24), (-7, hy + 24)]
        f.poly(pts, mix(arm0, (255, 255, 255), .18), arm1, suave=2, sombra=110)
        cam = f.t.camada(1)
        cam.d.line([f.P(-15, hy - 2), f.P(15, hy - 2)], fill=(8, 6, 8, 255), width=3.2 * f.sc)
        cam.d.line([f.P(0, hy - 22), f.P(0, hy + 22)], fill=(*escurecer(arm1, .4), 200), width=1.4 * f.sc)
        cam.aplicar()
        for dx in (-6, 6):
            brilho(f.t, *f.P(dx, hy - 2), 7 * f.sc, hc, k=.9)
        crista = o.get("crista")
        if crista == "pluma":
            cor = o.get("pluma", A["acento"])
            f.poly([(-4, hy - 20), (4, hy - 48), (24, hy - 56), (36, hy - 36), (26, hy - 18), (10, hy - 12)], mix(cor, (255, 255, 255), .2), escurecer(cor, .55), suave=2)
        elif crista == "chifres":
            for lado in (-1, 1):
                f.poly([(lado * 14, hy - 14), (lado * 28, hy - 30), (lado * 36, hy - 60), (lado * 22, hy - 40), (lado * 10, hy - 22)], (236, 228, 208), (72, 66, 56), suave=2)
        elif crista == "asas_elmo":
            for lado in (-1, 1):
                f.poly([(lado * 14, hy - 8), (lado * 38, hy - 30), (lado * 62, hy - 34), (lado * 44, hy - 18), (lado * 56, hy - 12), (lado * 34, hy - 2), (lado * 16, hy + 2)], (255, 232, 150), (150, 100, 30), suave=1)
        elif crista == "cobra":
            f.poly([(-4, hy - 20), (-8, hy - 44), (2, hy - 62), (14, hy - 52), (8, hy - 40), (10, hy - 20)], (170, 190, 150), (40, 54, 34), suave=2)
        elif crista == "aureola":
            pass
        elif crista == "coroa":
            f.poly([(-14, hy - 18), (-14, hy - 36), (-7, hy - 28), (0, hy - 42), (7, hy - 28), (14, hy - 36), (14, hy - 18)], (255, 232, 150), (150, 100, 30))


# ------------------------------------------------------------------------------------------
# Humanoide completo
# ------------------------------------------------------------------------------------------
def asas(f: Fig, cor0, cor1, n=9, abre=1.0, glow=None):
    rng = f.rng
    for lado in (-1, 1):
        raiz = (lado * 30, -186)
        if glow:
            x, y = f.P(lado * 100 * abre, -220)
            brilho(f.t, x, y, 100 * f.sc, glow, k=.45)
        for i in range(n):
            s = i / (n - 1)
            a = math.radians(-100 + 150 * s)  # de cima a baixo
            comp = (150 - 40 * abs(s - .35)) * abre
            ux, uy = lado * math.cos(a + math.radians(90) * 0) , math.sin(a)
            ux = lado * abs(math.cos(a)) if abs(math.cos(a)) > .25 else lado * .25
            end = (raiz[0] + ux * comp * .75, raiz[1] + uy * comp * .95 - 40 + 50 * s)
            mid = ((raiz[0] + end[0]) / 2, (raiz[1] + end[1]) / 2 - 10)
            nx, ny = -(end[1] - raiz[1]), (end[0] - raiz[0])
            ln = math.hypot(nx, ny) or 1
            wv = 15 + 5 * (1 - s)
            pts = [raiz, (mid[0] + nx / ln * wv, mid[1] + ny / ln * wv), end, (mid[0] - nx / ln * wv, mid[1] - ny / ln * wv)]
            f.poly(pts, cor0, cor1, suave=2, sombra=60, alfa=238)


def humanoide(t: Tela, A: dict, o: dict, rng: random.Random):
    f = Fig(t, A, o, rng)
    corpo = o.get("corpo", "placas")
    arma = o.get("arma", "espada_grande")
    arm0, arm1 = o["arm"]
    pano0, pano1 = o["pano"]
    pele = o.get("pele", (196, 150, 120))
    acc = o.get("brilho", A["acento"])
    ouro = ((240, 202, 112), (120, 84, 30))
    side = o.get("lado", 1)
    if not o.get("montado"):
        brilho(t, f.cx, f.g - 140 * f.sc, 105 * f.sc, (0, 0, 0), k=.55, pot=1.4, aditivo=False, ry=160 * f.sc)
        brilho(t, f.cx, f.g - 160 * f.sc, 120 * f.sc, A["luz"], k=.3, pot=1.7, ry=140 * f.sc)
        brilho(t, f.cx, f.g + 2, 70 * f.sc, (0, 0, 0), k=.7, aditivo=False, ry=10 * f.sc)  # lado da arma principal
    cx = f.cx
    ex = o.get("extras", ())
    if "runas" in ex:
        anel_runico(t, cx, f.g - 150 * f.sc, 118 * f.sc, acc, rng, n=26, larg=14, k=.7, achatar=1.0)
    if "lua" in ex:
        x, y = f.P(0, -214)
        brilho(t, x, y, 96 * f.sc, A["luz"], k=.5)
        c = t.camada(1)
        c.d.circulo(x / t.S, y / t.S, 58 * f.sc, outline=(235, 240, 255, 235), width=3)
        c.aplicar(aditivo=True)
    if "aureola" in ex:
        x, y = f.P(0, -246)
        brilho(t, x, y, 70 * f.sc, A["luz"], k=.6)
        c = t.camada(1)
        c.d.ellipse((x - 32 * f.sc, y - 8 * f.sc, x + 32 * f.sc, y + 8 * f.sc), outline=(255, 244, 200, 245), width=2.6)
        c.aplicar(aditivo=True)
    if "asas" in ex or "asas_negras" in ex:
        if "asas_negras" in ex:
            asas(f, (60, 52, 70), (10, 8, 14), glow=None)
        else:
            asas(f, (250, 246, 232), mix(acc, (80, 70, 50), .5), n=9, glow=A["luz"])
    if "chamas" in ex:
        x, y = f.P(0, -10)
        chama(t, x, y, 230 * f.sc, 120 * f.sc, [mix(acc, (0, 0, 0), .2), acc, clarear(acc, .55)], rng, linguas=6, k=.55)

    # --- manto -------------------------------------------------------------------------
    if o.get("manto", True):
        vento = rng.uniform(-1, 1) * 24 + o.get("vento", 0)
        cape = [(-30, -192), (30, -192), (46 + vento * .4, -150), (66 + vento, -80), (76 + vento * 1.4, -16), (30 + vento, -4), (-10, -12), (-52 + vento, -6),
                (-70 + vento, -22), (-58 + vento * .6, -90), (-44, -150)]
        f.poly(cape, mix(pano0, (255, 255, 255), .1), escurecer(pano1, .35), suave=2, sombra=130, horizontal=True)
        forro = [(-30, -190), (-8, -188), (-2, -120), (6, -60), (-4, -14), (-52 + vento, -6), (-70 + vento, -22), (-58 + vento * .6, -90), (-44, -150)]
        f.poly(forro, escurecer(pano1, .25), escurecer(pano1, .7), suave=2, rim=False, alfa=170)
        cam = t.camada(1)
        for i in range(5):
            xx = -42 + i * 22 + vento * .4
            cam.d.line([f.P(xx * .45, -170), f.P(xx + vento * (i / 5) * 1.1, -14)], fill=(*escurecer(pano1, .55), 90), width=1.8 * f.sc)
        cam.d.line(f.Q([(-70 + vento, -22), (-52 + vento, -6), (-10, -12), (30 + vento, -4), (76 + vento * 1.4, -16)]), fill=(*acc, 150), width=1.4 * f.sc)
        cam.aplicar()

    # --- pernas / saia ---------------------------------------------------------------------
    robe = corpo in ("robe",)
    if not robe and not o.get("montado"):
        passo = o.get("passo", 12)
        for lado in (-1, 1):
            hip = (lado * 14, -118)
            joelho = (lado * (17 + passo * .5), -62)
            tor = (lado * (20 + passo), -10)
            leg0, leg1 = (pele, escurecer(pele, .5)) if corpo == "nu" else (arm0, arm1)
            f.seg(hip, joelho, 29, 22, mix(leg0, (255, 255, 255), .08), leg1)
            f.seg(joelho, tor, 22, 17, mix(leg0, (255, 255, 255), .05), leg1)
            if corpo != "nu":
                f.elip(joelho[0], joelho[1], 12, 11, mix(arm0, (255, 255, 255), .18), arm1)
            f.poly([(tor[0] - 9, tor[1] - 6), (tor[0] + 9, tor[1] - 6), (tor[0] + 24 * (1 if lado > 0 else 1), tor[1] + 9), (tor[0] - 10, tor[1] + 9)], (60, 50, 44), (14, 12, 12))
    # --- tronco ------------------------------------------------------------------------
    if robe:
        sk = [(-14, -200), (14, -200), (38, -190), (42, -160), (50, -90), (78, -10), (30, 0), (-30, 0), (-78, -10), (-50, -90), (-42, -160), (-38, -190)]
        f.poly(sk, mix(pano0, (255, 255, 255), .16), escurecer(pano1, .3), suave=2, sombra=120, horizontal=True)
        cam = t.camada(1)
        for i in range(6):
            xx = -52 + i * 21
            cam.d.line([f.P(xx * .35, -120), f.P(xx * 1.3, -4)], fill=(*escurecer(pano1, .55), 90), width=1.8 * f.sc)
        cam.d.line(f.Q([(0, -190), (0, -2)]), fill=(*acc, 120), width=1.4 * f.sc)
        cam.d.line(f.Q([(-74, -10), (-30, 0), (30, 0), (74, -10)]), fill=(*acc, 170), width=1.6 * f.sc)
        cam.aplicar()
        f.poly([(-36, -186), (-26, -190), (30, -118), (22, -112)], mix(acc, pano0, .5), escurecer(pano1, .2), rim=False, alfa=210)
        f.poly([(-16, -204), (16, -204), (30, -188), (0, -176), (-30, -188)], mix(pano0, (255, 255, 255), .22), escurecer(pano1, .2), suave=1)
        if o.get("cinto", True):
            f.poly([(-26, -128), (26, -128), (27, -118), (-27, -118)], ouro[0], ouro[1])
    elif corpo == "nu":
        f.poly([(-38, -194), (38, -194), (34, -160), (26, -124), (-26, -124), (-34, -160)], mix(pele, (255, 255, 255), .12), escurecer(pele, .55), suave=2, sombra=110, horizontal=True)
        cam = t.camada(1)
        for dy in (-170, -150, -134):
            cam.d.line(f.Q([(-14, dy), (14, dy)]), fill=(*escurecer(pele, .6), 120), width=1.4 * f.sc)
        cam.d.line(f.Q([(0, -176), (0, -124)]), fill=(*escurecer(pele, .6), 120), width=1.4 * f.sc)
        cam.aplicar()
        f.poly([(-24, -128), (24, -128), (24, -84), (0, -70), (-24, -84)], mix(pano0, (255, 255, 255), .1), pano1, suave=1)
    else:
        couro = corpo == "couro"
        f.poly([(-38, -194), (38, -194), (35, -164), (26, -126), (24, -112), (-24, -112), (-26, -126), (-35, -164)], mix(arm0, (255, 255, 255), .22), arm1, suave=2, sombra=120, horizontal=True)
        cam = t.camada(1)
        if not couro:
            cam.d.line(f.Q([(0, -194), (0, -118)]), fill=(*escurecer(arm1, .4), 190), width=1.8 * f.sc)
            cam.d.line(f.Q([(-26, -158), (-4, -150), (-4, -128)]), fill=(*escurecer(arm1, .4), 130), width=1.3 * f.sc)
            cam.d.line(f.Q([(26, -158), (4, -150), (4, -128)]), fill=(*escurecer(arm1, .4), 130), width=1.3 * f.sc)
            cam.d.line(f.Q([(-35, -164), (35, -164)]), fill=(*acc, 120), width=1.2 * f.sc)
        cam.aplicar()
        f.poly([(-26, -128), (26, -128), (27, -118), (-27, -118)], ouro[0], ouro[1])
        if not couro:
            cam2 = t.camada(2)  # reflexo no peitoral e placas do abdômen
            cam2.d.polygon(f.Q([(-24, -186), (-12, -186), (-10, -140), (-20, -150)]), fill=(255, 255, 255, 120))
            cam2.aplicar(blur=2.4, aditivo=True)
            for dy in (-146, -136, -126):
                cam3 = t.camada(1)
                cam3.d.line(f.Q([(-22, dy), (22, dy)]), fill=(*escurecer(arm1, .5), 150), width=1.1 * f.sc)
                cam3.d.line(f.Q([(-22, dy + 1.4), (22, dy + 1.4)]), fill=(*clarear(arm0, .3), 90), width=.7 * f.sc)
                cam3.aplicar()
        # tassetes / tabardo
        f.poly([(-24, -118), (24, -118), (34, -52), (14, -36), (0, -48), (-14, -36), (-34, -52)], mix(pano0, (255, 255, 255), .12), escurecer(pano1, .2), suave=1, sombra=100)
        cam = t.camada(1)
        cam.d.polygon([f.P(0, -104), f.P(8, -86), f.P(0, -68), f.P(-8, -86)], fill=(*acc, 215))
        cam.aplicar()
    # --- braços e arma ------------------------------------------------------------------
    cor_braco = (pele, escurecer(pele, .5)) if corpo == "nu" else ((arm0, arm1) if corpo != "robe" else (pano0, pano1))
    larg_b = 1.28 if corpo == "robe" else 1.0
    ombro_d, ombro_e = (36 * side, -186), (-36 * side, -186)

    def braco(ombro, mao, lado):
        cotovelo = ((ombro[0] + mao[0]) / 2 + lado * 16, (ombro[1] + mao[1]) / 2 + 12)
        f.seg(ombro, cotovelo, 25 * larg_b, 20 * larg_b, mix(cor_braco[0], (255, 255, 255), .14), cor_braco[1])
        f.seg(cotovelo, mao, 20 * larg_b, 17 * larg_b * (1.25 if corpo == "robe" else 1), mix(cor_braco[0], (255, 255, 255), .08), cor_braco[1])
        if corpo in ("placas", "couro"):
            f.elip(*mao, 7.2, 8.4, mix(arm0, (255, 255, 255), .15), arm1)
            f.elip(mao[0], mao[1] - 3, 4, 3, clarear(arm0, .4), arm0, rim=None, sombra=0, contorno=None)
        else:
            f.elip(*mao, 6.5, 6.5, clarear(pele, .06), escurecer(pele, .4))

    mao_d = (60 * side, -150)
    mao_e = (-40 * side, -132)
    if arma == "espada_grande":
        ang = math.radians(-90 + side * 11)
        base = (mao_d[0], mao_d[1] - 6)
        lamina(f, (base[0], base[1] - 4), ang, 205, 15, glow=o.get("brilho_lamina"))
        braco(ombro_d, mao_d, side)
        braco(ombro_e, (mao_d[0] - 4 * side, mao_d[1] + 12), -side)
    elif arma == "espada_escudo":
        mao_d = (58 * side, -196)
        lamina(f, (mao_d[0], mao_d[1] - 2), math.radians(-90 + side * 20), 128, 11, glow=o.get("brilho_lamina"))
        escudo(f, (-42 * side, -134), 29, o.get("escudo", "redondo"), mix(arm0, (255, 255, 255), .1), arm1, acc)
        braco(ombro_d, mao_d, side)
        braco(ombro_e, (-34 * side, -140), -side)
    elif arma == "lanca":
        topo = (62 * side + 10 * side, -320)
        haste(f, (50 * side, 6), topo, 5)
        f.poly([(topo[0] - 5, topo[1] + 2), (topo[0], topo[1] - 40), (topo[0] + 5, topo[1] + 2), (topo[0], topo[1] + 8)], (226, 232, 240), (74, 82, 96), esp=1.2)
        braco(ombro_d, (54 * side, -170), side)
        braco(ombro_e, (56 * side, -128), -side)
    elif arma == "alabarda":
        haste(f, (46 * side, 6), (62 * side, -322), 5)
        f.poly([(62 * side, -318), (62 * side + 44 * side, -306), (62 * side + 38 * side, -262), (62 * side, -270)], (226, 232, 240), (74, 82, 96))
        f.poly([(62 * side, -322), (60 * side, -352), (66 * side, -322)], (226, 232, 240), (74, 82, 96), esp=1)
        braco(ombro_d, (52 * side, -190), side)
        braco(ombro_e, (50 * side, -142), -side)
    elif arma in ("machado", "martelo"):
        haste(f, (30 * side, -80), (74 * side, -300), 6.5)
        if arma == "machado":
            f.poly([(72 * side, -300), (112 * side, -318), (126 * side, -278), (106 * side, -244), (74 * side, -262)], (226, 232, 240), (66, 74, 88))
            f.poly([(74 * side, -296), (50 * side, -312), (40 * side, -282), (56 * side, -258), (76 * side, -268)], (206, 212, 220), (60, 68, 82))
        else:
            f.poly([(40 * side, -318), (112 * side, -336), (118 * side, -278), (46 * side, -262)], (210, 214, 222), (56, 64, 78))
        braco(ombro_d, (52 * side, -200), side)
        braco(ombro_e, (34 * side, -138), -side)
    elif arma == "cajado":
        topo = (54 * side, -300)
        haste(f, (50 * side, 6), topo, 5)
        orbe(f, (topo[0], topo[1] - 12), 13, o.get("orbe", acc))
        braco(ombro_d, (52 * side, -170), side)
        braco(ombro_e, (-52 * side, -150), -side)
    elif arma == "arco":
        arco(f, (60 * side, -172), 92)
        braco(ombro_d, (58 * side, -172), side)
        braco(ombro_e, (-16 * side, -166), -side)
    elif arma == "adagas":
        lamina(f, (62 * side, -150), math.radians(-60 * side - 90 + 60), 70, 9, cabo=14)
        lamina(f, (-62 * side, -150), math.radians(-120 + 60 * side), 70, 9, cabo=14)
        braco(ombro_d, (62 * side, -150), side)
        braco(ombro_e, (-62 * side, -150), -side)
    elif arma == "katana":
        lamina(f, (58 * side, -148), math.radians(-90 + side * 28), 175, 9, curva=.7 * side, cabo=30, glow=o.get("brilho_lamina"))
        braco(ombro_d, (58 * side, -148), side)
        braco(ombro_e, (50 * side, -132), -side)
    elif arma == "duas_espadas":
        lamina(f, (64 * side, -176), math.radians(-90 + side * 28), 150, 11, glow=o.get("brilho_lamina"))
        lamina(f, (-64 * side, -176), math.radians(-90 - side * 28), 150, 11, glow=o.get("brilho_lamina"))
        braco(ombro_d, (64 * side, -176), side)
        braco(ombro_e, (-64 * side, -176), -side)
    elif arma == "livro":
        x, y = f.P(-14 * side, -146)
        brilho(t, x, y, 62 * f.sc, acc, k=.75)
        f.poly([(-44 * side, -128), (-14 * side, -142), (-14 * side, -108), (-44 * side, -96)], (230, 220, 190), (110, 96, 70))
        f.poly([(-14 * side, -142), (16 * side, -128), (16 * side, -96), (-14 * side, -108)], (244, 236, 206), (130, 116, 84))
        braco(ombro_d, (42 * side, -214), side)
        braco(ombro_e, (-30 * side, -122), -side)
        brilho(t, *f.P(44 * side, -218), 40 * f.sc, acc, k=.8)
    elif arma == "estandarte":
        estandarte(f, (46 * side, 6), (46 * side, -326), pano0, pano1, acc, rng)
        braco(ombro_d, (48 * side, -176), side)
        braco(ombro_e, (46 * side, -132), -side)
    elif arma == "foice":
        haste(f, (40 * side, 4), (60 * side, -300), 5)
        f.poly([(60 * side, -300), (110 * side, -312), (130 * side, -270), (108 * side, -284), (66 * side, -284)], (210, 216, 224), (60, 68, 82), suave=1)
        braco(ombro_d, (54 * side, -190), side)
        braco(ombro_e, (50 * side, -140), -side)
    else:
        braco(ombro_d, (46 * side, -122), side)
        braco(ombro_e, (-46 * side, -122), -side)
    # --- ombreiras e gorjal -------------------------------------------------------------
    if corpo in ("placas", "couro"):
        for lado in (-1, 1):
            f.elip(lado * 38, -186, 18, 17, escurecer(arm1, .1), escurecer(arm1, .5), rot=lado * .3)
            f.elip(lado * 36, -192, 17, 13, mix(arm0, (255, 255, 255), .25), arm1, rot=lado * .3)
            f.elip(lado * 35, -196, 11, 7, mix(arm0, (255, 255, 255), .4), mix(arm0, arm1, .5), rot=lado * .3, rim=None)
            cam = t.camada(1)
            cam.d.line(f.Q([(lado * 22, -192), (lado * 48, -186)]), fill=(*acc, 140), width=1.2 * f.sc)
            cam.aplicar()
    # --- cabeça ---------------------------------------------------------------------------
    cabeca(f, o, A)
    # --- brilho de runas no peito -------------------------------------------------------------
    if "peito_luz" in ex:
        brilho(t, *f.P(0, -160), 22 * f.sc, acc, k=.8)
    return f


# ------------------------------------------------------------------------------------------
# Criaturas e figuras especiais
# ------------------------------------------------------------------------------------------
def cavalo(t: Tela, A: dict, o: dict, rng: random.Random):
    """Cavalo de guerra visto de lado (frente à direita); devolve a Fig do chão para o cavaleiro."""
    f = Fig(t, A, o, rng)
    pelo0, pelo1 = o.get("pelo", ((70, 70, 78), (14, 14, 18)))
    corpo = [(-95, -120), (-60, -135), (-10, -138), (30, -132), (55, -160), (75, -200), (92, -208), (116, -186), (122, -172), (112, -166), (92, -176),
             (70, -150), (62, -118), (66, -100), (62, -60), (64, -18), (70, 0), (50, 0), (48, -18), (46, -62), (40, -96), (10, -94), (-30, -94),
             (-50, -80), (-66, -40), (-62, -10), (-58, 0), (-78, 0), (-82, -12), (-88, -48), (-98, -84), (-104, -110)]
    # pernas do lado oposto, mais escuras
    for dx in (-14, 12):
        f.poly([(40 + dx, -96), (44 + dx, -50), (46 + dx, -4), (58 + dx, 0), (34 + dx, 0), (30 + dx, -50), (28 + dx, -96)], escurecer(pelo0, .4), escurecer(pelo1, .2), rim=False, suave=1)
    f.poly(corpo, mix(pelo0, (255, 255, 255), .1), pelo1, suave=2, sombra=130)
    # crina e cauda
    f.poly([(55, -160), (75, -204), (70, -212), (46, -176), (30, -140)], (20, 18, 22), (6, 6, 8), suave=2, rim=False)
    f.poly([(-98, -120), (-130, -100), (-150, -50), (-140, -20), (-124, -60), (-110, -96)], (24, 22, 26), (6, 6, 8), suave=2)
    # arreios e manta
    f.poly([(-40, -134), (40, -130), (46, -70), (20, -60), (-30, -64), (-48, -84)], o.get("manta0", (120, 24, 28)), o.get("manta1", (40, 6, 10)), suave=1)
    cam = t.camada(1)
    cam.d.line(f.Q([(78, -192), (96, -172), (112, -170)]), fill=(*A["acento"], 220), width=1.4 * f.sc)
    cam.aplicar()
    brilho(t, *f.P(96, -193), 6 * f.sc, o.get("brilho", A["acento"]), k=.8)
    return f


def gurranq(t: Tela, A: dict, o: dict, rng: random.Random):
    f = Fig(t, A, o, rng)
    pelo0, pelo1 = (92, 70, 108), (14, 8, 20)
    x, y = f.P(0, -170)
    brilho(t, x, y, 170 * f.sc, (255, 190, 80), k=.35)
    # trapos e capa sobre os ombros
    f.poly([(-58, 0), (-86, -70), (-114, -160), (-62, -206), (0, -192), (62, -206), (114, -160), (86, -70), (58, 0)], mix(pelo0, (255, 255, 255), .08), pelo1, suave=2, sombra=150, horizontal=True)
    for k in range(9):  # pelagem em tufos
        px = -96 + k * 24
        f.poly([(px - 10, -150 + (k % 3) * 8), (px, -196 + (k % 2) * 10), (px + 10, -150 + (k % 3) * 8)], mix(pelo0, (255, 255, 255), .15), pelo1, esp=1, sombra=60)
    f.poly([(-92, -176), (-30, -196), (30, -196), (92, -176), (70, -122), (0, -112), (-70, -122)], (118, 30, 38), (34, 6, 10), suave=2, sombra=120, horizontal=True)
    # braço estendido oferecendo a palma
    forma_b, centro, normais, ws = fita([f.P(70, -176), f.P(118, -140), f.P(150, -88), f.P(164, -52)], [40 * f.sc, 34 * f.sc, 28 * f.sc, 24 * f.sc])
    forma(t, forma_b, mix(pelo0, (255, 255, 255), .12), pelo1, rim=A["rim"], lado=f.lado, esp=2, contorno=escurecer(pelo1, .5))
    f.poly([(142, -60), (190, -52), (200, -28), (166, -14), (140, -34)], mix(pelo0, (255, 255, 255), .22), pelo1, suave=1)
    for k in range(4):
        f.poly([(160 + k * 9, -34 + k * 3), (196 + k * 10, -22 + k * 5), (164 + k * 9, -26 + k * 3)], (236, 230, 214), (90, 84, 70), esp=.9)
    # cabeça felina com focinho longo e chifres curvos
    f.poly([(-50, -226), (-56, -262), (-34, -290), (0, -302), (34, -290), (56, -262), (50, -226), (28, -196), (-28, -196)], mix(pelo0, (255, 255, 255), .14), pelo1, suave=2, sombra=130)
    f.poly([(-24, -262), (24, -262), (30, -226), (16, -206), (0, -200), (-16, -206), (-30, -226)], mix(pelo0, (255, 255, 255), .26), escurecer(pelo1, .1), suave=2)
    f.poly([(-12, -224), (12, -224), (9, -207), (-9, -207)], (8, 4, 12), (4, 2, 6), rim=False)
    for k in range(4):  # presas
        f.poly([(-13 + k * 8.6, -207), (-10 + k * 8.6, -192), (-7 + k * 8.6, -207)], (244, 240, 226), (150, 144, 128), esp=.7)
    for lado in (-1, 1):
        horn, _, _, _ = fita([(lado * 36, -284), (lado * 62, -316), (lado * 96, -330), (lado * 122, -304), (lado * 118, -268)], [20 * f.sc, 18 * f.sc, 14 * f.sc, 9 * f.sc, 3 * f.sc])
        forma(t, [(f.P(0, 0)[0] + (px - f.P(0, 0)[0]), py) for px, py in [(f.P(0, 0)[0] + 0, 0)]] and horn, (226, 218, 198), (62, 56, 46), rim=A["rim"], lado=f.lado, esp=1.6)
        f.poly([(lado * 30, -278), (lado * 20, -258), (lado * 10, -250)], (20, 14, 26), (6, 4, 10), rim=False, esp=1)
        brilho(t, *f.P(lado * 22, -270), 12 * f.sc, (255, 210, 70), k=1.0)
        f.elip(lado * 22, -270, 6, 3.4, (255, 240, 150), (210, 140, 20), rim=None, sombra=0)
    return f


def dragao(t: Tela, A: dict, o: dict, rng: random.Random):
    f = Fig(t, A, o, rng)
    esc0, esc1 = o.get("escamas", ((150, 154, 176), (22, 24, 36)))
    glow = o.get("brilho", (255, 230, 150))
    x, y = f.P(0, -200)
    brilho(t, x, y, 190 * f.sc, glow, k=.4)
    # asas de membrana com falanges
    for lado in (-1, 1):
        raiz = (lado * 14, -150)
        pulso = (lado * 120, -262)
        pontas = [(lado * 196, -318), (lado * 206, -236), (lado * 170, -158), (lado * 112, -108)]
        pol = [raiz, pulso]
        prev = pulso
        for k, pt in enumerate(pontas):
            mid = ((prev[0] + pt[0]) / 2 - lado * 10, (prev[1] + pt[1]) / 2 + 18)
            pol += [mid, pt]
            prev = pt
        pol += [(lado * 60, -88)]
        f.poly(pol, mix(esc0, (255, 255, 255), .04), escurecer(esc1, .25), alfa=238, sombra=150, horizontal=True)
        cam = t.camada(1)
        for pt in pontas:
            cam.d.line([f.P(*pulso), f.P(*pt)], fill=(*clarear(esc0, .25), 190), width=1.8 * f.sc)
        cam.d.line([f.P(*raiz), f.P(*pulso)], fill=(*clarear(esc0, .25), 200), width=3.2 * f.sc)
        cam.aplicar()
    # corpo em S (uma única fita contínua) + espinhos dorsais
    eixo = [(-130, -6), (-70, -2), (-6, -34), (30, -96), (14, -156), (-26, -198), (-22, -246), (22, -284), (62, -298)]
    contorno, centro, normais, ws = fita([f.P(*p) for p in eixo], [10 * f.sc, 26 * f.sc, 46 * f.sc, 56 * f.sc, 48 * f.sc, 38 * f.sc, 30 * f.sc, 24 * f.sc, 20 * f.sc])
    forma(t, contorno, mix(esc0, (255, 255, 255), .1), esc1, rim=A["rim"], lado=f.lado, esp=2.4, sombra=130, contorno=escurecer(esc1, .6), horizontal=True)
    cam = t.camada(1)
    for i in range(3, len(centro) - 4, 3):  # escamas e espinhos
        cx, cy = centro[i]
        nx, ny = normais[i]
        w = ws[i]
        cam.d.line([(cx / t.S - nx * w / t.S * .15, cy / t.S - ny * w / t.S * .15), (cx / t.S + nx * w / t.S * .42, cy / t.S + ny * w / t.S * .42)], fill=(*escurecer(esc1, .4), 120), width=1.2)
    cam.aplicar()
    for i in range(6, len(centro) - 6, 4):
        cx, cy = centro[i]
        nx, ny = normais[i]
        w = ws[i]
        base = (cx / t.S, cy / t.S)
        sx, sy = -nx, -ny
        forma(t, [(base[0] + nx * w / t.S * .5 * 0 + sx * w / t.S * .5 - 4, base[1] + sy * w / t.S * .5), (base[0] + sx * (w / t.S * .5 + 15), base[1] + sy * (w / t.S * .5 + 15)),
                  (base[0] + sx * w / t.S * .5 + 4, base[1] + sy * w / t.S * .5)], clarear(esc0, .2), esc1, esp=1)
    # cabeça de dragão com mandíbula aberta
    f.poly([(46, -310), (84, -322), (126, -306), (150, -286), (122, -282), (88, -280), (60, -270), (40, -276)], mix(esc0, (255, 255, 255), .12), esc1, suave=1, sombra=130)
    f.poly([(62, -272), (96, -276), (146, -274), (124, -250), (90, -246), (66, -254)], mix(esc0, (255, 255, 255), .04), escurecer(esc1, .2), suave=1)
    for k in range(7):
        f.poly([(88 + k * 8, -279), (91 + k * 8, -264), (94 + k * 8, -279)], (244, 240, 224), (140, 134, 118), esp=.7)
    for lado in (0, 1):
        f.poly([(50 + lado * 22, -314), (28 + lado * 20, -350), (56 + lado * 22, -330)], (230, 224, 204), (80, 74, 60), suave=1)
    brilho(t, *f.P(88, -300), 14 * f.sc, glow, k=1.0)
    from .arte_ilustracao_base import relampago
    for _ in range(3):
        p0 = f.P(142, -272)
        relampago(t, p0, (p0[0] + rng.uniform(30, 110), p0[1] + rng.uniform(40, 120)), glow, rng, ramos=2)
    return f


def besta_pristina(t: Tela, A: dict, o: dict, rng: random.Random):
    f = Fig(t, A, o, rng)
    luz = A["luz"]
    x, y = f.P(0, -160)
    brilho(t, x, y, 200 * f.sc, luz, k=.5)
    anel_runico(t, x, y, 124 * f.sc, luz, rng, n=30, larg=12, k=.8)
    c = t.camada(2)
    for i in range(40):  # juba de estrelas
        a = 2 * math.pi * i / 40
        r0, r1 = 48 * f.sc, (88 + (i % 3) * 18) * f.sc
        c.d.polygon([(x + math.cos(a - .05) * r0, y + math.sin(a - .05) * r0), (x + math.cos(a) * r1, y + math.sin(a) * r1),
                     (x + math.cos(a + .05) * r0, y + math.sin(a + .05) * r0)], fill=(*luz, 150))
    c.aplicar(blur=1.4, aditivo=True)
    # leão de luz (silhueta de frente)
    f.poly([(-44, -160), (-52, -200), (-32, -228), (0, -238), (32, -228), (52, -200), (44, -160), (30, -128), (0, -118), (-30, -128)], (255, 252, 236), (214, 190, 120), suave=2, sombra=60)
    f.poly([(-30, -176), (-20, -198), (-6, -186), (0, -176), (6, -186), (20, -198), (30, -176), (18, -150), (0, -142), (-18, -150)], (255, 255, 250), (230, 214, 160), suave=1, sombra=40)
    for dx in (-17, 17):
        brilho(t, *f.P(dx, -178), 10 * f.sc, (255, 255, 255), k=1.0)
    f.poly([(-18, -216), (-14, -246), (-4, -224)], (255, 252, 236), (214, 190, 120), esp=1)
    f.poly([(18, -216), (14, -246), (4, -224)], (255, 252, 236), (214, 190, 120), esp=1)
    # patas dianteiras
    for lado in (-1, 1):
        f.seg((lado * 20, -128), (lado * 24, -40), 24, 20, (255, 250, 230), (200, 176, 110))
        f.poly([(lado * 24 - 14, -40), (lado * 24 + 16, -40), (lado * 24 + 20, -4), (lado * 24 - 18, -4)], (255, 250, 230), (200, 176, 110), suave=1)
    return f


def mae_sem_forma(t: Tela, A: dict, o: dict, rng: random.Random):
    f = Fig(t, A, o, rng)
    x, y = f.P(0, -140)
    brilho(t, x, y, 210 * f.sc, (255, 70, 80), k=.5)
    for i in range(22):  # massa de sangue
        px = rng.uniform(-90, 90)
        py = -rng.uniform(10, 240) * (1 - abs(px) / 190)
        r = rng.uniform(26, 62)
        f.elip(px, py, r, r * rng.uniform(.8, 1.2), (176, 20, 38), (36, 3, 10), sombra=140)
    for i in range(9):  # tentáculos
        a = rng.uniform(-math.pi * .95, -math.pi * .05)
        pts = [(rng.uniform(-40, 40), -120)]
        for k in range(1, 7):
            pts.append((pts[-1][0] + math.cos(a + math.sin(k + i) * .6) * 30, pts[-1][1] + math.sin(a + math.sin(k + i) * .6) * 30))
        for k in range(len(pts) - 1):
            f.seg(pts[k], pts[k + 1], 20 - k * 2.6, 20 - (k + 1) * 2.6, (160, 20, 36), (40, 4, 12), sombra=90)
    for i in range(12):  # olhos
        ex, ey = rng.uniform(-80, 80), -rng.uniform(40, 220)
        r = rng.uniform(5, 11)
        f.elip(ex, ey, r * 1.3, r, (255, 244, 220), (200, 150, 120), rim=None, sombra=0)
        f.elip(ex, ey, r * .5, r * .8, (160, 8, 20), (30, 0, 4), rim=None, sombra=0)
        brilho(t, *f.P(ex, ey), r * 2.6 * f.sc, (255, 80, 80), k=.45)
    return f


def lobisomem_ou_blaidd(t, A, o, rng):
    return humanoide(t, A, {**o, "helm": "lobo"}, rng)


def gemeas(t, A, o, rng):
    o1 = {**o, "x": 128, "escala": .86, "lado": 1}
    o2 = {**o, "x": 258, "escala": .86, "lado": -1, "pano": o.get("pano2", o["pano"])}
    humanoide(t, A, o1, rng)
    humanoide(t, A, o2, rng)


def gigante(t, A, o, rng):
    f = humanoide(t, A, {**o, "escala": o.get("escala", 1.32), "chao": o.get("chao", 372)}, rng)
    cam = t.camada(1)
    for _ in range(14):  # rachaduras de magma
        x, y = f.P(rng.uniform(-30, 30), rng.uniform(-190, -130))
        pts = [(x, y)]
        for _k in range(4):
            pts.append((pts[-1][0] + rng.uniform(-9, 9), pts[-1][1] + rng.uniform(4, 13)))
        cam.d.line(pts, fill=(255, 150, 50, 235), width=1.4)
    cam.aplicar(aditivo=True)
    return f

"""Motor de pintura procedural das ilustrações de cartas.

Tudo é desenhado em *unidades de design* (janela de arte de 384 x 430) e renderizado em
super-amostragem (S x) para depois ser reduzido com LANCZOS. As formas recebem gradiente,
luz de contorno e sombra interna; a atmosfera (névoa, brilho aditivo, partículas, raios de
luz, grão e vinheta) dá profundidade. Somente Pillow; determinístico por semente.
"""
from __future__ import annotations

import math
import random
from typing import Callable, Sequence

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

Cor = tuple[int, int, int]
Pt = tuple[float, float]


def mix(a: Cor, b: Cor, t: float) -> Cor:
    t = max(0.0, min(1.0, t))
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), int(a[2] + (b[2] - a[2]) * t))


def clarear(c: Cor, t: float) -> Cor:
    return mix(c, (255, 255, 255), t)


def escurecer(c: Cor, t: float) -> Cor:
    return mix(c, (0, 0, 0), t)


class Esc:
    """Desenho com coordenadas de design, escaladas para o raster da camada."""

    def __init__(self, img: Image.Image, k: float):
        self.img, self.k, self.d = img, k, ImageDraw.Draw(img, "RGBA")

    def _p(self, pts):
        return [(x * self.k, y * self.k) for x, y in pts]

    def polygon(self, pts, fill=None, outline=None, width=1):
        self.d.polygon(self._p(pts), fill=fill, outline=outline, width=max(1, int(width * self.k)) if outline else 1)

    def ellipse(self, box, fill=None, outline=None, width=1):
        x0, y0, x1, y1 = box
        self.d.ellipse((x0 * self.k, y0 * self.k, x1 * self.k, y1 * self.k), fill=fill, outline=outline,
                       width=max(1, int(width * self.k)))

    def circulo(self, cx, cy, r, fill=None, outline=None, width=1):
        self.ellipse((cx - r, cy - r, cx + r, cy + r), fill, outline, width)

    def line(self, pts, fill=None, width=1, joint="curve"):
        self.d.line(self._p(pts), fill=fill, width=max(1, int(round(width * self.k))), joint=joint)

    def arc(self, box, a0, a1, fill=None, width=1):
        x0, y0, x1, y1 = box
        self.d.arc((x0 * self.k, y0 * self.k, x1 * self.k, y1 * self.k), a0, a1, fill=fill,
                   width=max(1, int(round(width * self.k))))

    def rect(self, box, fill=None, outline=None, width=1):
        x0, y0, x1, y1 = box
        self.d.rectangle((x0 * self.k, y0 * self.k, x1 * self.k, y1 * self.k), fill=fill, outline=outline,
                         width=max(1, int(width * self.k)))


class Tela:
    def __init__(self, aw: int, ah: int, S: int = 2, seed: int = 1):
        self.aw, self.ah, self.S = aw, ah, S
        self.W, self.H = aw * S, ah * S
        self.img = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 255))
        self.rng = random.Random(seed)
        self.seed = seed

    # -- camadas ---------------------------------------------------------------------------
    def camada(self, res: int = 1) -> "Camada":
        return Camada(self, res)

    def tela_aditiva(self, lay: Image.Image) -> None:
        base = self.img.convert("RGB")
        pre = Image.new("RGB", base.size, (0, 0, 0))
        pre.paste(lay.convert("RGB"), (0, 0), lay.getchannel("A"))
        self.img = ImageChops.screen(base, pre).convert("RGBA")


class Camada:
    def __init__(self, t: Tela, res: int = 1):
        self.t, self.res = t, res
        self.img = Image.new("RGBA", (max(1, t.W // res), max(1, t.H // res)), (0, 0, 0, 0))
        self.d = Esc(self.img, t.S / res)

    def aplicar(self, blur: float = 0.0, k: float = 1.0, aditivo: bool = False) -> None:
        im = self.img
        if blur:
            im = im.filter(ImageFilter.GaussianBlur(blur * self.t.S / self.res))
        if self.res != 1:
            im = im.resize((self.t.W, self.t.H), Image.Resampling.BILINEAR)
        if k < 1.0:
            im.putalpha(im.getchannel("A").point(lambda v: int(v * k)))
        if aditivo:
            self.t.tela_aditiva(im)
        else:
            self.t.img.alpha_composite(im)


# ------------------------------------------------------------------------------------------
# Céu, luz e atmosfera
# ------------------------------------------------------------------------------------------
def ceu(t: Tela, paradas: Sequence[tuple[float, Cor]]) -> None:
    """Gradiente vertical por paradas (v de 0 a 1, cor)."""
    d = ImageDraw.Draw(t.img)
    for y in range(t.H):
        v = y / max(1, t.H - 1)
        for i in range(len(paradas) - 1):
            v0, c0 = paradas[i]
            v1, c1 = paradas[i + 1]
            if v0 <= v <= v1:
                col = mix(c0, c1, (v - v0) / max(1e-6, v1 - v0))
                break
        else:
            col = paradas[0][1] if v < paradas[0][0] else paradas[-1][1]
        d.line((0, y, t.W, y), fill=col)


def _radial(diam: int, pot: float, k: float) -> Image.Image:
    base = ImageOps.invert(Image.radial_gradient("L")).resize((diam, diam), Image.Resampling.BILINEAR)
    lut = [min(255, int(255 * ((i / 255) ** pot) * k)) for i in range(256)]
    return base.point(lut)


def brilho(t: Tela, cx: float, cy: float, r: float, cor: Cor, k: float = 0.8, pot: float = 2.0,
           aditivo: bool = True, ry: float | None = None) -> None:
    """Brilho radial suave (``ry`` cria elipse)."""
    S = t.S
    dw = max(2, int(2 * r * S))
    dh = max(2, int(2 * (ry if ry else r) * S))
    m = _radial(max(dw, dh), pot, k).resize((dw, dh), Image.Resampling.BILINEAR)
    x, y = int(cx * S - dw / 2), int(cy * S - dh / 2)
    x0, y0, x1, y1 = max(0, x), max(0, y), min(t.W, x + dw), min(t.H, y + dh)
    if x1 <= x0 or y1 <= y0:
        return
    m = m.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    if aditivo:
        reg = t.img.crop((x0, y0, x1, y1)).convert("RGB")
        pre = Image.new("RGB", reg.size, (0, 0, 0))
        pre.paste(Image.new("RGB", reg.size, cor), (0, 0), m)
        t.img.paste(ImageChops.screen(reg, pre).convert("RGBA"), (x0, y0))
    else:
        lay = Image.new("RGBA", m.size, (*cor, 255))
        lay.putalpha(m)
        t.img.alpha_composite(lay, (x0, y0))


def neblina(t: Tela, v0: float, v1: float, cor: Cor, k: float = 0.5, n: int = 14, sal: int = 0) -> None:
    rng = random.Random(t.seed * 31 + sal + int(v0 * 977))
    c = t.camada(2)
    for _ in range(n):
        cx = rng.uniform(-40, t.aw + 40)
        cy = rng.uniform(v0, v1) * t.ah
        w = rng.uniform(90, 230)
        h = rng.uniform(12, 34) * (1 + (v1 - v0) * 2)
        c.d.ellipse((cx - w, cy - h, cx + w, cy + h), fill=(*cor, int(255 * k * rng.uniform(.5, 1))))
    c.aplicar(blur=16)


def nuvens(t: Tela, v0: float, v1: float, cor: Cor, k: float = 0.5, n: int = 24, sal: int = 0,
           luz: Cor | None = None) -> None:
    rng = random.Random(t.seed * 17 + sal)
    c = t.camada(2)
    for _ in range(n):
        cx = rng.uniform(-30, t.aw + 30)
        cy = rng.uniform(v0, v1) * t.ah
        w = rng.uniform(50, 150)
        h = w * rng.uniform(.14, .32)
        for j in range(4):
            ox = rng.uniform(-w * .5, w * .5)
            oy = rng.uniform(-h * .6, h * .6)
            c.d.ellipse((cx + ox - w * .5, cy + oy - h, cx + ox + w * .5, cy + oy + h),
                        fill=(*cor, int(255 * k * rng.uniform(.4, 1))))
    c.aplicar(blur=9)
    if luz:
        c2 = t.camada(2)
        for _ in range(n // 2):
            cx = rng.uniform(0, t.aw)
            cy = rng.uniform(v0, v1) * t.ah
            w = rng.uniform(40, 110)
            c2.d.ellipse((cx - w, cy - w * .12, cx + w, cy + w * .06), fill=(*luz, int(255 * k * .55)))
        c2.aplicar(blur=6, aditivo=True)


def raios(t: Tela, ox: float, oy: float, cor: Cor, n: int = 9, k: float = 0.2, abre: float = 70,
          alcance: float = 520, base_ang: float = 90) -> None:
    rng = random.Random(t.seed * 7 + n)
    c = t.camada(2)
    for _ in range(n):
        ang = math.radians(base_ang + rng.uniform(-abre, abre))
        larg = math.radians(rng.uniform(1.2, 4.2))
        p1 = (ox + math.cos(ang - larg) * alcance, oy + math.sin(ang - larg) * alcance)
        p2 = (ox + math.cos(ang + larg) * alcance, oy + math.sin(ang + larg) * alcance)
        c.d.polygon([(ox, oy), p1, p2], fill=(*cor, int(255 * k * rng.uniform(.4, 1))))
    c.aplicar(blur=7, aditivo=True)


def estrelas(t: Tela, n: int, v0: float = 0, v1: float = .6, cor: Cor = (235, 240, 255), k: float = 1.0,
             sal: int = 0) -> None:
    rng = random.Random(t.seed * 13 + sal)
    c = t.camada(1)
    for _ in range(n):
        x, y = rng.uniform(0, t.aw), rng.uniform(v0, v1) * t.ah
        r = rng.choice((.4, .5, .6, .8, 1.1)) * (1.4 if rng.random() < .08 else 1)
        a = int(255 * k * rng.uniform(.35, 1))
        c.d.circulo(x, y, r, fill=(*cor, a))
        if r > 1:
            c.d.line([(x - r * 3, y), (x + r * 3, y)], fill=(*cor, a // 3), width=.5)
            c.d.line([(x, y - r * 3), (x, y + r * 3)], fill=(*cor, a // 3), width=.5)
    c.aplicar()


def particulas(t: Tela, n: int, cor: Cor, caixa: tuple[float, float, float, float], tam=(.5, 1.8), k: float = 1.0,
               sal: int = 0, halo: bool = True, deriva: float = 0.0) -> None:
    rng = random.Random(t.seed * 5 + sal + n)
    x0, y0, x1, y1 = caixa
    pontos = [(rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(*tam), rng.uniform(.3, 1)) for _ in range(n)]
    if halo:
        c = t.camada(2)
        for x, y, r, a in pontos:
            c.d.circulo(x, y, r * 3.2, fill=(*cor, int(70 * a * k)))
        c.aplicar(blur=2.2, aditivo=True)
    c = t.camada(1)
    for x, y, r, a in pontos:
        if deriva:
            c.d.line([(x, y), (x + deriva * r * 4, y - abs(deriva) * r * 6)], fill=(*cor, int(150 * a * k)), width=r * .6)
        c.d.circulo(x, y, r, fill=(*clarear(cor, .5), int(255 * a * k)))
    c.aplicar()


def serra(rng: random.Random, n: int, amp: float, rugosidade: float = .55) -> list[float]:
    """Perfil de montanha por deslocamento de ponto médio (valores de 0 a 1 em torno de 0)."""
    pts = [rng.uniform(-amp, amp), rng.uniform(-amp, amp)]
    desl = amp
    while len(pts) < n:
        novo = []
        for a, b in zip(pts, pts[1:]):
            novo += [a, (a + b) / 2 + rng.uniform(-desl, desl)]
        novo.append(pts[-1])
        pts, desl = novo, desl * rugosidade
    # reamostra para exatamente n pontos
    return [pts[int(i * (len(pts) - 1) / (n - 1))] for i in range(n)]


def montanhas(t: Tela, base_v: float, amp: float, cor_topo: Cor, cor_base: Cor, sal: int = 0, rug: float = .55,
              borda: Cor | None = None, n: int = 64) -> None:
    rng = random.Random(t.seed * 11 + sal)
    perfil = serra(rng, n, amp * t.ah, rug)
    pts = [(-4, t.ah + 4)]
    for i, v in enumerate(perfil):
        pts.append((i * (t.aw + 8) / (n - 1) - 4, base_v * t.ah + v))
    pts.append((t.aw + 4, t.ah + 4))
    forma(t, pts, cor_topo, cor_base, rim=borda, rim_k=.5, lado=(0, -1), esp=1.2, sombra=0)


def chaikin(pts: Sequence[Pt], n: int = 2, fechado: bool = True) -> list[Pt]:
    p = list(pts)
    for _ in range(n):
        novo: list[Pt] = []
        rng_i = range(len(p)) if fechado else range(len(p) - 1)
        if not fechado:
            novo.append(p[0])
        for i in rng_i:
            a, b = p[i], p[(i + 1) % len(p)]
            novo += [(a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25), (a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75)]
        if not fechado:
            novo.append(p[-1])
        p = novo
    return p


# ------------------------------------------------------------------------------------------
# Formas sombreadas
# ------------------------------------------------------------------------------------------
def forma(t: Tela, pts: Sequence[Pt], cima: Cor, baixo: Cor, rim: Cor | None = None, rim_k: float = .85,
          lado: tuple[float, float] = (-1, -1), esp: float = 2.2, sombra: int = 80, alfa: int = 255,
          contorno: Cor | None = None, horizontal: bool = False) -> None:
    """Polígono com gradiente, luz de contorno (lado da luz) e sombra interna oposta."""
    S = t.S
    P = [(x * S, y * S) for x, y in pts]
    if len(P) < 3:
        return
    pad = int(esp * S * 4) + 6
    x0 = max(0, int(min(p[0] for p in P)) - pad)
    y0 = max(0, int(min(p[1] for p in P)) - pad)
    x1 = min(t.W, int(max(p[0] for p in P)) + pad)
    y1 = min(t.H, int(max(p[1] for p in P)) + pad)
    if x1 <= x0 + 1 or y1 <= y0 + 1:
        return
    w, h = x1 - x0, y1 - y0
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon([(x - x0, y - y0) for x, y in P], fill=255)
    g = Image.linear_gradient("L")
    g = g.rotate(90, expand=True) if horizontal else g
    g = g.resize((w, h), Image.Resampling.BILINEAR)
    fill = ImageOps.colorize(g, black=cima, white=baixo).convert("RGBA")
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    lay.paste(fill, (0, 0), m if alfa >= 255 else m.point(lambda v: v * alfa // 255))
    e = max(1, int(esp * S))
    if sombra:
        sm = ImageChops.subtract(m, ImageChops.offset(m, int(lado[0] * e * 2.2), int(lado[1] * e * 2.2)))
        sm = sm.filter(ImageFilter.GaussianBlur(e * .9)).point(lambda v: v * sombra // 255)
        lay.paste(Image.new("RGBA", (w, h), (0, 0, 0, 255)), (0, 0), ImageChops.multiply(sm, m))
    if rim:
        rm = ImageChops.subtract(m, ImageChops.offset(m, int(-lado[0] * e), int(-lado[1] * e)))
        rm = rm.filter(ImageFilter.GaussianBlur(.7 * S * .6)).point(lambda v: min(255, int(v * rim_k)))
        lay.paste(Image.new("RGBA", (w, h), (*rim, 255)), (0, 0), ImageChops.multiply(rm, m))
    if contorno:
        ImageDraw.Draw(lay).line([(x - x0, y - y0) for x, y in P] + [(P[0][0] - x0, P[0][1] - y0)],
                                 fill=(*contorno, 170), width=max(1, int(.7 * S)), joint="curve")
    t.img.alpha_composite(lay, (x0, y0))


def membro(p0: Pt, p1: Pt, w0: float, w1: float, passos: int = 5) -> list[Pt]:
    """Segmento afunilado com pontas arredondadas (coordenadas de design)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ang = math.atan2(dy, dx)
    pts: list[Pt] = []
    for i in range(passos + 1):
        a = ang - math.pi / 2 - math.pi * i / passos
        pts.append((p1[0] + math.cos(a) * w1 / 2, p1[1] + math.sin(a) * w1 / 2))
    for i in range(passos + 1):
        a = ang + math.pi / 2 - math.pi * i / passos
        pts.append((p0[0] + math.cos(a) * w0 / 2, p0[1] + math.sin(a) * w0 / 2))
    return pts


def elipse_pts(cx: float, cy: float, rx: float, ry: float, n: int = 28, rot: float = 0.0) -> list[Pt]:
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = math.cos(a) * rx, math.sin(a) * ry
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


def raio_jagged(rng: random.Random, p0: Pt, p1: Pt, desv: float = 18, niveis: int = 5) -> list[Pt]:
    pts = [p0, p1]
    for _ in range(niveis):
        novo = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            nx, ny = -(b[1] - a[1]), (b[0] - a[0])
            ln = math.hypot(nx, ny) or 1
            d = rng.uniform(-desv, desv)
            novo += [(mx + nx / ln * d, my + ny / ln * d), b]
        pts, desv = novo, desv * .55
    return pts


def relampago(t: Tela, p0: Pt, p1: Pt, cor: Cor, rng: random.Random, ramos: int = 3, esp: float = 2.4) -> None:
    pts = raio_jagged(rng, p0, p1, desv=22)
    c = t.camada(2)
    c.d.line(pts, fill=(*cor, 120), width=esp * 3.5)
    c.aplicar(blur=4, aditivo=True)
    c = t.camada(1)
    c.d.line(pts, fill=(*clarear(cor, .75), 255), width=esp)
    for _ in range(ramos):
        i = rng.randint(len(pts) // 5, len(pts) * 4 // 5)
        a = pts[i]
        fim = (a[0] + rng.uniform(-70, 70), a[1] + rng.uniform(25, 90))
        c.d.line(raio_jagged(rng, a, fim, 10, 4), fill=(*clarear(cor, .6), 220), width=esp * .55)
    c.aplicar()


def arvore(t: Tela, x: float, y: float, comp: float, ang: float, cor: Cor, rng: random.Random, prof: int = 7,
           larg: float = 8, aberto: float = .5, folhas: Cor | None = None, d=None) -> None:
    """Árvore ramificada recursiva (galhos mortos ou copa da Árvore Áurea)."""
    own = d is None
    if own:
        cam = t.camada(1)
        d = cam.d

    def rec(px, py, a, ln, w, n):
        if n == 0 or ln < 2:
            if folhas:
                d.circulo(px, py, rng.uniform(3, 7), fill=(*folhas, rng.randint(70, 150)))
            return
        qx, qy = px + math.cos(a) * ln, py + math.sin(a) * ln
        d.line([(px, py), (qx, qy)], fill=(*cor, 255), width=max(.7, w))
        k = rng.choice((2, 2, 3))
        for i in range(k):
            da = (i - (k - 1) / 2) * aberto + rng.uniform(-.18, .18)
            rec(qx, qy, a + da, ln * rng.uniform(.68, .82), w * .68, n - 1)

    rec(x, y, ang, comp, larg, prof)
    if own:
        cam.aplicar()


def runa_glifo(d: Esc, cx: float, cy: float, r: float, cor, rng: random.Random, w: float = 1.1) -> None:
    n = rng.randint(3, 5)
    pts = [(cx + rng.uniform(-r, r) * .8, cy + rng.uniform(-r, r)) for _ in range(n)]
    d.line(pts, fill=cor, width=w)
    d.line([(cx, cy - r), (cx, cy + r)], fill=cor, width=w * .8)


def anel_runico(t: Tela, cx: float, cy: float, r: float, cor: Cor, rng: random.Random, n: int = 28,
                larg: float = 10, k: float = .9, achatar: float = 1.0) -> None:
    c = t.camada(1)
    for rr in (r, r - larg, r + 3):
        c.d.ellipse((cx - rr, cy - rr * achatar, cx + rr, cy + rr * achatar), outline=(*cor, int(210 * k)), width=1.1)
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r - larg / 2
        runa_glifo(c.d, cx + math.cos(a) * rr, cy + math.sin(a) * rr * achatar, larg * .32, (*cor, int(230 * k)), rng, .9)
    c.aplicar()
    c = t.camada(2)
    c.d.ellipse((cx - r, cy - r * achatar, cx + r, cy + r * achatar), outline=(*cor, 120), width=5)
    c.aplicar(blur=4, aditivo=True)


def chama(t: Tela, cx: float, cy: float, alt: float, larg: float, cores: Sequence[Cor], rng: random.Random,
          linguas: int = 5, k: float = 1.0) -> None:
    """Chama pintada em camadas (da borda ao núcleo) com brilho aditivo."""
    for i, cor in enumerate(cores):
        esc = 1 - i / (len(cores) + .6)
        c = t.camada(2 if i < len(cores) - 1 else 1)
        for j in range(linguas):
            ox = (j - (linguas - 1) / 2) * larg * .55 / max(1, linguas / 2) * esc
            h = alt * esc * rng.uniform(.55, 1.0) * (1 - abs(j - (linguas - 1) / 2) / (linguas) * .7)
            w = larg * esc * rng.uniform(.28, .5)
            tip = (cx + ox + rng.uniform(-w, w) * .8, cy - h)
            pts = [(cx + ox - w, cy), (cx + ox - w * .9, cy - h * .38), (cx + ox - w * .25, cy - h * .72), tip,
                   (cx + ox + w * .3, cy - h * .62), (cx + ox + w * .95, cy - h * .32), (cx + ox + w, cy)]
            c.d.polygon(chaikin(pts, 2, True), fill=(*cor, int(235 * k)))
        c.aplicar(blur=2.2 + (len(cores) - i) * .6, aditivo=(i > 0))
    brilho(t, cx, cy - alt * .35, larg * 1.5, cores[len(cores) // 2], k=.45 * k)


def lua_disco(t: Tela, cx: float, cy: float, r: float, cor: Cor, sombra: Cor, rng: random.Random,
              halo: Cor | None = None, crateras: int = 9) -> None:
    if halo:
        brilho(t, cx, cy, r * 3.1, halo, k=.5)
        brilho(t, cx, cy, r * 1.6, halo, k=.5)
    c = t.camada(1)
    c.d.circulo(cx, cy, r, fill=(*cor, 255))
    c.aplicar()
    c = t.camada(1)
    for _ in range(crateras):
        a, d = rng.uniform(0, 6.28), rng.uniform(0, r * .78)
        rr = rng.uniform(r * .06, r * .2)
        c.d.circulo(cx + math.cos(a) * d, cy + math.sin(a) * d, rr, fill=(*sombra, rng.randint(40, 90)))
    c.aplicar()
    # sombra de fase
    c = t.camada(1)
    c.d.circulo(cx + r * .35, cy + r * .2, r * .95, fill=(*sombra, 120))
    c.aplicar(blur=r * .12)
    # recorte circular do disco: reaplica o céu fora do disco não é necessário (sombra é translúcida)


def vinheta(t: Tela, k: float = .55, v_base: float = 0.0) -> None:
    m = Image.radial_gradient("L").resize((t.W, t.H), Image.Resampling.BILINEAR)
    m = m.point(lambda v: int(max(0, (v - 95)) * k * 1.7))
    t.img.paste(Image.new("RGBA", (t.W, t.H), (0, 0, 0, 255)), (0, 0), m)


def grao(t: Tela, k: float = .10) -> None:
    n = Image.effect_noise((t.W, t.H), 42).convert("RGB")
    base = t.img.convert("RGB")
    t.img = Image.blend(base, ImageChops.overlay(base, n), k).convert("RGBA")


def bloom(t: Tela, k: float = .28, raio: float = 10) -> None:
    base = t.img.convert("RGB")
    br = base.point(lambda v: max(0, v - 120) * 2).filter(ImageFilter.GaussianBlur(raio * t.S))
    t.img = Image.blend(base, ImageChops.screen(base, br), k).convert("RGBA")


def finalizar(t: Tela, vinhetak: float = .55, granulo: float = .09, bloom_k: float = .3) -> Image.Image:
    bloom(t, bloom_k)
    vinheta(t, vinhetak)
    grao(t, granulo)
    return t.img.resize((t.aw, t.ah), Image.Resampling.LANCZOS)


def catmull(pts: Sequence[Pt], n: int = 8) -> list[Pt]:
    P = [pts[0]] + list(pts) + [pts[-1]]
    out: list[Pt] = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            u = k / n
            u2, u3 = u * u, u * u * u
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * u + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u2
                                     + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u3) for j in (0, 1)))  # type: ignore
    out.append(tuple(pts[-1]))  # type: ignore
    return out


def fita(pts: Sequence[Pt], larguras: Sequence[float], n: int = 8):
    """Curva suave com largura variável → (contorno, centro, normais)."""
    c = catmull(pts, n)
    m = len(c)
    ws = []
    for i in range(m):
        u = i / max(1, m - 1) * (len(larguras) - 1)
        a = int(u)
        b = min(len(larguras) - 1, a + 1)
        ws.append(larguras[a] + (larguras[b] - larguras[a]) * (u - a))
    esq, dire, normais = [], [], []
    for i, (x, y) in enumerate(c):
        a, b = c[max(0, i - 1)], c[min(m - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        normais.append((nx, ny))
        esq.append((x + nx * ws[i] / 2, y + ny * ws[i] / 2))
        dire.append((x - nx * ws[i] / 2, y - ny * ws[i] / 2))
    return esq + dire[::-1], c, normais, ws

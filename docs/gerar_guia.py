#!/usr/bin/env python3
"""Gera docs/Guia_Montagem_Talos.pdf (guia de ligação e operação do Projeto Talos).

Uso:  pipx run --spec reportlab python docs/gerar_guia.py   (ou: pip install reportlab; python3 docs/gerar_guia.py)
Fontes: Noto Sans e DejaVu Sans (pacotes fonts-noto-core e fonts-dejavu-core no Ubuntu).
"""
import os

from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Circle, Drawing, Line, Path, Polygon, PolyLine, Rect, String
from reportlab.lib.colors import HexColor as H, white
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, KeepTogether, NextPageTemplate, PageBreak,
                                PageTemplate, Paragraph, Preformatted, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "Guia_Montagem_Talos.pdf")

# ------------------------------------------------------------------ fontes
NOTO, DJ = "/usr/share/fonts/truetype/noto/", "/usr/share/fonts/truetype/dejavu/"
for nome, arq in [("Sans", NOTO + "NotoSans-Regular.ttf"), ("Sans-B", NOTO + "NotoSans-Bold.ttf"),
                  ("Sans-I", NOTO + "NotoSans-Italic.ttf"), ("Sans-BI", NOTO + "NotoSans-BoldItalic.ttf"),
                  ("Mono", NOTO + "NotoSansMono-Regular.ttf"), ("Mono-B", NOTO + "NotoSansMono-Bold.ttf"),
                  ("Sym", DJ + "DejaVuSans.ttf"), ("Sym-B", DJ + "DejaVuSans-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(nome, arq))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-B", italic="Sans-I", boldItalic="Sans-BI")

ARW = '<font name="Sym">→</font>'
WARN = '<font name="Sym">⚠</font>'

# ------------------------------------------------------------------ cores
NAVY, ACC, INK, MUTED = H("#16233A"), H("#E07A1F"), H("#1F2933"), H("#5F6B7A")
LIGHT, LINE, PAPER = H("#F2F4F7"), H("#D5DAE1"), H("#FFFFFF")
C = {k: H(v) for k, v in dict(v12="#D62828", v5="#F77F00", v33="#E5389B", gnd="#1E1E1E", lock="#7B2CBF",
                              buz="#B58900", led="#0096C7", bat="#8D5524", door="#6C757D", dio="#0F766E",
                              clk="#65A30D").items()}
KP = [H(c) for c in ["#0B3D91", "#1F6FEB", "#4A90E2", "#76A9EA",   # linhas L1..L4 (azuis)
                     "#0B6E4F", "#2E9E44", "#4CB85C", "#7CCB86"]]  # colunas C1..C4 (verdes)
KPN = ["L1", "L2", "L3", "L4", "C1", "C2", "C3", "C4"]

# ------------------------------------------------------------------ estilos de texto
def st(nome, **kw):
    base = dict(fontName="Sans", fontSize=9.5, leading=13.6, textColor=INK, spaceAfter=5)
    base.update(kw)
    return ParagraphStyle(nome, **base)

S = dict(
    body=st("body"),
    small=st("small", fontSize=8.2, leading=11),
    cell=st("cell", fontSize=8.2, leading=10.6, spaceAfter=0),
    cellb=st("cellb", fontName="Sans-B", fontSize=8.2, leading=10.6, spaceAfter=0),
    head=st("head", fontName="Sans-B", fontSize=8.2, leading=10.6, textColor=white, spaceAfter=0),
    h1=st("h1", fontName="Sans-B", fontSize=19, leading=23, textColor=NAVY, spaceBefore=16, spaceAfter=10),
    h2=st("h2", fontName="Sans-B", fontSize=12.5, leading=16, textColor=NAVY, spaceBefore=10, spaceAfter=5),
    cap=st("cap", fontName="Sans-I", fontSize=8.2, leading=10.5, textColor=MUTED, alignment=TA_CENTER,
           spaceBefore=3, spaceAfter=10),
    code=st("code", fontName="Mono", fontSize=8.3, leading=11.2, textColor=H("#E6EDF3"), spaceAfter=0),
    li=st("li", leftIndent=14, bulletIndent=3, spaceAfter=3),
    toc1=st("toc1", fontName="Sans-B", fontSize=10.5, leading=17, textColor=NAVY),
    toc2=st("toc2", fontSize=9.2, leading=13.5, leftIndent=16, textColor=INK),
)


SIMBOLOS = "→←✓☐⚠≥≤"


def fx(t):
    """Noto Sans não tem setas e afins: troca esses caracteres para a DejaVu."""
    for ch in SIMBOLOS:
        t = t.replace(ch, '<font name="Sym">%s</font>' % ch)
    return t


def P(t, s="body"):
    return Paragraph(fx(t), S[s])


def bullets(itens, s="li"):
    return [Paragraph(fx(t), S[s], bulletText="•") for t in itens]


def numerados(itens):
    return [Paragraph(fx(t), S["li"], bulletText=f"{i}.") for i, t in enumerate(itens, 1)]


def code(txt):
    t = Table([[Preformatted(txt.strip("\n"), S["code"])]], colWidths=["100%"])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), H("#1B2433")),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return KeepTogether([t, Spacer(1, 7)])


CALLOUT = {"warn": (H("#E07A1F"), H("#FFF4E8"), "ATENÇÃO"), "danger": (H("#C62828"), H("#FDECEC"), "CUIDADO"),
           "tip": (H("#2E7D32"), H("#EDF7EE"), "DICA"), "info": (H("#1F6FEB"), H("#EAF2FE"), "NOTA")}


def callout(tipo, texto, titulo=None):
    cor, fundo, padrao = CALLOUT[tipo]
    conteudo = [Paragraph(f'<font color="{cor.hexval()}"><b>{titulo or padrao}</b></font>', S["cell"]),
                Paragraph(fx(texto), st("co", fontSize=8.8, leading=12.4, spaceAfter=0))]
    t = Table([["", conteudo]], colWidths=[4, None])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), cor), ("BACKGROUND", (1, 0), (1, 0), fundo),
                           ("LEFTPADDING", (1, 0), (1, 0), 9), ("RIGHTPADDING", (1, 0), (1, 0), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                           ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 0)]))
    return KeepTogether([t, Spacer(1, 8)])


def tabela(linhas, larguras, destaque_col0=False, zebra=True):
    dados = [[Paragraph(str(c), S["head"]) for c in linhas[0]]]
    for ln in linhas[1:]:
        dados.append([c if not isinstance(c, str) else Paragraph(fx(c), S["cellb" if destaque_col0 and j == 0 else "cell"])
                      for j, c in enumerate(ln)])
    t = Table(dados, colWidths=larguras, repeatRows=1)
    estilo = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
              ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("TOPPADDING", (0, 0), (-1, -1), 4),
              ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LEFTPADDING", (0, 0), (-1, -1), 5),
              ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    if zebra:
        estilo += [("BACKGROUND", (0, i), (-1, i), LIGHT) for i in range(2, len(dados), 2)]
    t.setStyle(TableStyle(estilo))
    return t


def swatch(cor, w=22, h=8):
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, rx=2, ry=2, fillColor=cor, strokeColor=None))
    return d

# ------------------------------------------------------------------ primitivas de desenho
def txt(d, x, y, s, size=7, font="Sans", color=INK, anchor="start"):
    if font.startswith("Sans") and any(ch in s for ch in SIMBOLOS):
        font = "Sym-B" if "-B" in font else "Sym"
    d.add(String(x, y, s, fontName=font, fontSize=size, fillColor=color, textAnchor=anchor))


def fio(d, pts, cor, w=1.9, dash=None):
    d.add(PolyLine(pts, strokeColor=cor, strokeWidth=w, strokeLineJoin=1, strokeLineCap=1, strokeDashArray=dash))


def ponto(d, x, y, cor=INK, r=2.1):
    d.add(Circle(x, y, r, fillColor=cor, strokeColor=None))


def linha(d, x1, y1, x2, y2, cor=INK, w=1.1, dash=None):
    d.add(Line(x1, y1, x2, y2, strokeColor=cor, strokeWidth=w, strokeLineCap=1, strokeDashArray=dash))


def res_h(d, x1, x2, y, valor, nome="", cor=INK):
    """Resistor (IEC) horizontal entre x1 e x2."""
    m = (x1 + x2) / 2
    linha(d, x1, y, m - 11, y, cor)
    linha(d, m + 11, y, x2, y, cor)
    d.add(Rect(m - 11, y - 4, 22, 8, fillColor=H("#FFFDF5"), strokeColor=INK, strokeWidth=1.1))
    txt(d, m, y + 7, valor, 6.6, "Sans-B", anchor="middle")
    if nome:
        txt(d, m, y - 12, nome, 6, "Sans", MUTED, "middle")


def res_v(d, x, y1, y2, valor, nome="", lado="right", cor=INK):
    """Resistor (IEC) vertical entre y1 (baixo) e y2 (cima)."""
    m = (y1 + y2) / 2
    linha(d, x, y1, x, m - 11, cor)
    linha(d, x, m + 11, x, y2, cor)
    d.add(Rect(x - 4, m - 11, 8, 22, fillColor=H("#FFFDF5"), strokeColor=INK, strokeWidth=1.1))
    dx, anc = (7, "start") if lado == "right" else (-7, "end")
    txt(d, x + dx, m + 1, valor, 6.6, "Sans-B", anchor=anc)
    if nome:
        txt(d, x + dx, m - 7, nome, 6, "Sans", MUTED, anc)


def terra(d, x, y, cor=INK):
    linha(d, x, y, x, y - 6, cor)
    for i, w in enumerate([14, 9, 4]):
        linha(d, x - w / 2, y - 6 - 2.6 * i, x + w / 2, y - 6 - 2.6 * i, cor, 1.2)


def bandeira(d, x, y, texto, cor):
    """Símbolo de alimentação: haste para cima com barra e rótulo."""
    linha(d, x, y, x, y + 7, cor, 1.3)
    linha(d, x - 7, y + 7, x + 7, y + 7, cor, 2)
    txt(d, x, y + 11, texto, 7, "Sans-B", cor, "middle")


def diodo_v(d, x, y1, y2, nome="", lado="right"):
    """Diodo vertical, catodo para cima (y2)."""
    m = (y1 + y2) / 2
    linha(d, x, y1, x, m - 6)
    linha(d, x, m + 6, x, y2)
    d.add(Polygon([x - 6, m - 6, x + 6, m - 6, x, m + 5], fillColor=INK, strokeColor=INK, strokeWidth=0.8))
    linha(d, x - 7, m + 6, x + 7, m + 6, INK, 1.6)
    if nome:
        dx, anc = (10, "start") if lado == "right" else (-10, "end")
        txt(d, x + dx, m - 2, nome, 6.6, "Sans-B", anchor=anc)


def bobina_v(d, x, y1, y2, n=4):
    p = Path(strokeColor=INK, strokeWidth=1.2, fillColor=None)
    passo = (y2 - y1) / n
    p.moveTo(x, y1)
    for i in range(n):
        a = y1 + i * passo
        p.curveTo(x + 9, a, x + 9, a + passo, x, a + passo)
    d.add(p)


def nmos(d, cx, cy):
    """MOSFET canal N. Retorna (gate, dreno, fonte)."""
    d.add(Circle(cx + 1, cy, 15, fillColor=H("#FFFFFF"), strokeColor=INK, strokeWidth=1))
    linha(d, cx - 18, cy, cx - 6, cy)
    linha(d, cx - 6, cy - 9, cx - 6, cy + 9, INK, 1.4)
    for a, b in [(6, 11), (-2.5, 2.5), (-11, -6)]:
        linha(d, cx - 2, cy + a, cx - 2, cy + b, INK, 1.6)
    linha(d, cx - 2, cy + 8.5, cx + 6, cy + 8.5)
    linha(d, cx + 6, cy + 8.5, cx + 6, cy + 20)
    linha(d, cx - 2, cy - 8.5, cx + 6, cy - 8.5)
    linha(d, cx + 6, cy - 8.5, cx + 6, cy - 20)
    linha(d, cx - 2, cy, cx + 6, cy)
    linha(d, cx + 6, cy, cx + 6, cy - 8.5)
    d.add(Polygon([cx - 1.5, cy, cx + 3, cy + 2.6, cx + 3, cy - 2.6], fillColor=INK, strokeColor=None))
    txt(d, cx - 16, cy + 3, "G", 5.8, "Sans-B", MUTED)
    txt(d, cx + 9, cy + 15, "D", 5.8, "Sans-B", MUTED)
    txt(d, cx + 9, cy - 19, "S", 5.8, "Sans-B", MUTED)
    return (cx - 18, cy), (cx + 6, cy + 20), (cx + 6, cy - 20)


def npn(d, cx, cy):
    """Transistor NPN. Retorna (base, coletor, emissor)."""
    d.add(Circle(cx, cy, 13, fillColor=H("#FFFFFF"), strokeColor=INK, strokeWidth=1))
    linha(d, cx - 16, cy, cx - 4, cy)
    linha(d, cx - 4, cy - 7, cx - 4, cy + 7, INK, 1.6)
    linha(d, cx - 4, cy + 3, cx + 6, cy + 9)
    linha(d, cx + 6, cy + 9, cx + 6, cy + 18)
    linha(d, cx - 4, cy - 3, cx + 6, cy - 9)
    linha(d, cx + 6, cy - 9, cx + 6, cy - 18)
    d.add(Polygon([cx + 6, cy - 9, cx + 0.6, cy - 8.6, cx + 3.4, cy - 4.4], fillColor=INK, strokeColor=None))
    txt(d, cx - 14, cy + 3, "B", 5.8, "Sans-B", MUTED)
    txt(d, cx + 9, cy + 12, "C", 5.8, "Sans-B", MUTED)
    txt(d, cx + 9, cy - 16, "E", 5.8, "Sans-B", MUTED)
    return (cx - 16, cy), (cx + 6, cy + 18), (cx + 6, cy - 18)


def buzzer(d, cx, cy, r=12):
    """Buzzer ativo (vista de cima). Terminal + em cima, - embaixo."""
    d.add(Circle(cx, cy, r, fillColor=H("#202020"), strokeColor=H("#000000"), strokeWidth=1))
    d.add(Circle(cx, cy, r * 0.28, fillColor=H("#555555"), strokeColor=None))
    txt(d, cx - r - 6, cy + r - 6, "+", 9, "Sans-B", C["v12"], "middle")
    linha(d, cx, cy + r, cx, cy + r + 4)
    linha(d, cx, cy - r, cx, cy - r - 4)


def led_v(d, x, y1, y2, cor=C["led"]):
    """LED vertical, anodo em cima (y2), catodo embaixo."""
    m = (y1 + y2) / 2
    linha(d, x, y2, x, m + 6)
    linha(d, x, m - 6, x, y1)
    d.add(Polygon([x - 6, m + 6, x + 6, m + 6, x, m - 5], fillColor=cor, strokeColor=INK, strokeWidth=0.8))
    linha(d, x - 7, m - 6, x + 7, m - 6, INK, 1.6)
    for k in (0, 5):
        linha(d, x + 8, m + 2 - k, x + 14, m + 7 - k, cor, 0.9)
        d.add(Polygon([x + 14, m + 7 - k, x + 11, m + 7 - k, x + 14, m + 4 - k], fillColor=cor, strokeColor=None))


def cap_v(d, x, y1, y2, valor, lado="right"):
    m = (y1 + y2) / 2
    linha(d, x, y1, x, m - 2.5)
    linha(d, x, m + 2.5, x, y2)
    linha(d, x - 7, m + 2.5, x + 7, m + 2.5, INK, 1.6)
    linha(d, x - 7, m - 2.5, x + 7, m - 2.5, INK, 1.6)
    dx, anc = (10, "start") if lado == "right" else (-10, "end")
    txt(d, x + dx, m - 2, valor, 6.6, "Sans-B", anchor=anc)


def reed_h(d, x1, x2, y):
    m = (x1 + x2) / 2
    linha(d, x1, y, m - 9, y)
    linha(d, m + 9, y, x2, y)
    linha(d, m - 9, y, m + 7, y + 6, INK, 1.3)
    d.add(Rect(m - 14, y - 6, 28, 15, rx=7, ry=7, fillColor=None, strokeColor=MUTED, strokeWidth=0.8,
               strokeDashArray=[2, 1.5]))


def pnp(d, cx, cy):
    """Transistor PNP (emissor em cima). Retorna (base, emissor, coletor)."""
    d.add(Circle(cx, cy, 13, fillColor=H("#FFFFFF"), strokeColor=INK, strokeWidth=1))
    linha(d, cx - 16, cy, cx - 4, cy)
    linha(d, cx - 4, cy - 7, cx - 4, cy + 7, INK, 1.6)
    linha(d, cx - 4, cy + 3, cx + 6, cy + 9)
    linha(d, cx + 6, cy + 9, cx + 6, cy + 18)
    linha(d, cx - 4, cy - 3, cx + 6, cy - 9)
    linha(d, cx + 6, cy - 9, cx + 6, cy - 18)
    d.add(Polygon([cx - 2.7, cy + 3.8, cx + 0.3, cy + 8.6, cx + 2.9, cy + 4.2], fillColor=INK, strokeColor=None))
    txt(d, cx - 14, cy + 3, "B", 5.8, "Sans-B", MUTED)
    txt(d, cx + 9, cy + 12, "E", 5.8, "Sans-B", MUTED)
    txt(d, cx + 9, cy - 16, "C", 5.8, "Sans-B", MUTED)
    return (cx - 16, cy), (cx + 6, cy + 18), (cx + 6, cy - 18)


def diodo_h(d, x1, x2, y, nome=""):
    """Diodo horizontal, catodo à direita (x2)."""
    m = (x1 + x2) / 2
    linha(d, x1, y, m - 6, y)
    linha(d, m + 6, y, x2, y)
    d.add(Polygon([m - 6, y - 6, m - 6, y + 6, m + 5, y], fillColor=INK, strokeColor=INK, strokeWidth=0.8))
    linha(d, m + 6, y - 7, m + 6, y + 7, INK, 1.6)
    if nome:
        txt(d, m, y - 15, nome, 6.6, "Sans-B", anchor="middle")


def bobina_h(d, x1, x2, y, n=4):
    p = Path(strokeColor=INK, strokeWidth=1.2, fillColor=None)
    passo = (x2 - x1) / n
    p.moveTo(x1, y)
    for i in range(n):
        a = x1 + i * passo
        p.curveTo(a, y + 9, a + passo, y + 9, a + passo, y)
    d.add(p)


SEG7 = {"0": 0x3F, "1": 0x06, "2": 0x5B, "3": 0x4F, "4": 0x66, "5": 0x6D, "6": 0x7D, "7": 0x07, "8": 0x7F,
        "9": 0x6F, "-": 0x40, "_": 0x08, "A": 0x77, "b": 0x7C, "C": 0x39, "E": 0x79, "L": 0x38, "n": 0x54,
        "O": 0x3F, "P": 0x73, "t": 0x78, " ": 0}


def digito7(d, x, y, h, mask, on=H("#FF3B30"), off=H("#3A2020")):
    """Um dígito de 7 segmentos (bits: dp g f e d c b a, como no firmware)."""
    w, t = h * 0.56, h * 0.12

    def seg(bit, rx, ry, rw, rh):
        d.add(Rect(rx, ry, rw, rh, rx=t * 0.45, ry=t * 0.45, fillColor=on if mask >> bit & 1 else off,
                   strokeColor=None))
    seg(0, x + t, y + h - t, w - 2 * t, t)
    seg(1, x + w - t, y + h / 2 + 0.3 * t, t, h / 2 - 1.3 * t)
    seg(2, x + w - t, y + t, t, h / 2 - 1.3 * t)
    seg(3, x + t, y, w - 2 * t, t)
    seg(4, x, y + t, t, h / 2 - 1.3 * t)
    seg(5, x, y + h / 2 + 0.3 * t, t, h / 2 - 1.3 * t)
    seg(6, x + t, y + h / 2 - t / 2, w - 2 * t, t)
    d.add(Circle(x + w + 0.9 * t, y + t / 2, 0.55 * t, fillColor=on if mask & 0x80 else off, strokeColor=None))


def painel(d, x, y, h, texto):
    """Os 6 displays lado a lado. '.' depois de um caractere acende o ponto dele."""
    cel = []
    for ch in texto:
        if ch == "." and cel:
            cel[-1] |= 0x80
        else:
            cel.append(SEG7[ch])
    passo = h * 0.86
    d.add(Rect(x - h * 0.22, y - h * 0.2, passo * 6 + h * 0.2, h * 1.4, rx=3, ry=3, fillColor=H("#140C0C"),
               strokeColor=H("#000000"), strokeWidth=0.8))
    for i, m in enumerate(cel[:6]):
        digito7(d, x + i * passo, y, h, m)
    return passo * 6


def etiqueta(d, x, y, texto, cor, anchor="start", size=6.6):
    """Rótulo em caixa arredondada (net label)."""
    w = pdfmetrics.stringWidth(texto, "Sym-B", size) + 8
    x0 = x if anchor == "start" else x - w
    d.add(Rect(x0, y - 5, w, 11, rx=3, ry=3, fillColor=H("#FFFFFF"), strokeColor=cor, strokeWidth=1.1))
    txt(d, x0 + 4, y - 1.6, texto, size, "Sym-B", cor)
    return x0, x0 + w

# ------------------------------------------------------------------ ESP32 DevKit V1 (30 pinos)
ESQ = ["EN", "VP", "VN", "D34", "D35", "D32", "D33", "D25", "D26", "D27", "D14", "D12", "D13", "GND", "VIN"]
DIR = ["D23", "D22", "TX0", "RX0", "D21", "D19", "D18", "D5", "TX2", "RX2", "D4", "D2", "D15", "GND", "3V3"]
GPIO_ESQ = ["reset", "GPIO36", "GPIO39", "GPIO34", "GPIO35", "GPIO32", "GPIO33", "GPIO25", "GPIO26", "GPIO27",
            "GPIO14", "GPIO12", "GPIO13", "terra", "5 V entrada"]
GPIO_DIR = ["GPIO23", "GPIO22", "GPIO1", "GPIO3", "GPIO21", "GPIO19", "GPIO18", "GPIO5", "GPIO17", "GPIO16",
            "GPIO4", "GPIO2", "GPIO15", "terra", "3,3 V saída"]

USO = {  # (lado, índice) -> cor do fio
    ("L", 1): C["bat"], ("L", 2): C["door"], ("L", 5): KP[0], ("L", 6): KP[1], ("L", 7): KP[2], ("L", 8): KP[3],
    ("L", 9): KP[4], ("L", 10): KP[5], ("L", 11): KP[6], ("L", 12): KP[7], ("L", 13): C["gnd"], ("L", 14): C["v5"],
    ("R", 8): C["buz"], ("R", 9): C["lock"], ("R", 11): C["led"], ("R", 14): C["v33"],
    ("R", 5): C["clk"], ("R", 6): C["dio"],
}


def placa(d, x0, y0pino, passo=22, w=140, uso=USO, titulo=True):
    """Desenha a placa. y0pino = y do pino 1 (EN / D23). Retorna função pad(lado, i) -> (x, y)."""
    x1 = x0 + w
    py = lambda i: y0pino - i * passo
    topo, base = y0pino + 2.9 * passo, py(14) - 1.35 * passo
    # PCB
    d.add(Rect(x0 + 2, base - 3, w, topo - base, rx=7, ry=7, fillColor=H("#0A1B30"), strokeColor=None))
    d.add(Rect(x0, base, w, topo - base, rx=7, ry=7, fillColor=H("#1D4F8F"), strokeColor=H("#123564"), strokeWidth=1.2))
    for hx, hy in [(x0 + 9, topo - 9), (x1 - 9, topo - 9), (x0 + 9, base + 9), (x1 - 9, base + 9)]:
        d.add(Circle(hx, hy, 4.2, fillColor=H("#D9DDE2"), strokeColor=H("#B8A15A"), strokeWidth=1.2))
        d.add(Circle(hx, hy, 2.2, fillColor=H("#0F1B2A"), strokeColor=None))
    # módulo WROOM-32: antena + blindagem
    mx0, mx1 = x0 + 34, x1 - 34
    d.add(Rect(mx0 - 2, topo - 2.85 * passo - 2, mx1 - mx0 + 4, 2.85 * passo, fillColor=H("#111418"),
               strokeColor=None))
    ay = topo - 8
    ant = [mx0 + 4, ay]
    for k in range(7):
        xa = mx0 + 4 + k * (mx1 - mx0 - 8) / 7
        ant += [xa, ay - 9, xa + (mx1 - mx0 - 8) / 14, ay - 9, xa + (mx1 - mx0 - 8) / 14, ay]
    d.add(PolyLine(ant, strokeColor=H("#C9A548"), strokeWidth=1.3))
    sy1, sy0 = topo - 22, topo - 2.85 * passo + 2
    d.add(Rect(mx0, sy0, mx1 - mx0, sy1 - sy0, rx=1.5, ry=1.5, fillColor=H("#C7CDD4"), strokeColor=H("#8E98A4"),
               strokeWidth=1))
    d.add(Rect(mx0 + 3, sy0 + 3, mx1 - mx0 - 6, sy1 - sy0 - 6, fillColor=None, strokeColor=H("#AEB6C0"),
               strokeWidth=0.6))
    txt(d, (mx0 + mx1) / 2, (sy0 + sy1) / 2 + 6, "ESP-WROOM-32", 6.2, "Sans-B", H("#3A4350"), "middle")
    txt(d, (mx0 + mx1) / 2, (sy0 + sy1) / 2 - 3, "Wi-Fi + BT", 5, "Sans", H("#5A6370"), "middle")
    txt(d, (mx0 + mx1) / 2, (sy0 + sy1) / 2 - 11, "ESPRESSIF", 5, "Sans-B", H("#5A6370"), "middle")
    # chips e componentes da placa
    cx = (x0 + x1) / 2
    d.add(Rect(cx - 11, py(7.6), 22, 22, fillColor=H("#1A1A1A"), strokeColor=H("#000000"), strokeWidth=0.6))
    txt(d, cx, py(7.6) + 8, "CP2102", 4.8, "Sans-B", H("#9AA0A6"), "middle")
    d.add(Rect(cx - 13, py(10.6), 26, 13, fillColor=H("#1A1A1A"), strokeColor=None))
    d.add(Rect(cx - 9, py(10.6) + 13, 18, 4, fillColor=H("#BFC5CC"), strokeColor=None))
    txt(d, cx, py(10.6) + 4, "AMS1117", 4.5, "Sans-B", H("#9AA0A6"), "middle")
    txt(d, cx, py(5.2), "ESP32", 8, "Sans-B", white, "middle")
    txt(d, cx, py(5.2) - 9, "DEVKIT V1", 6, "Sans-B", white, "middle")
    txt(d, cx, py(5.2) - 17, "DOIT", 5.5, "Sans", H("#BFD3EE"), "middle")
    # botões EN e BOOT
    for bx, rot in [(x0 + 36, "EN"), (x1 - 36 - 14, "BOOT")]:
        d.add(Rect(bx, py(13.1), 14, 14, rx=1.5, ry=1.5, fillColor=H("#C0C6CC"), strokeColor=H("#7D8790"),
                   strokeWidth=0.6))
        d.add(Circle(bx + 7, py(13.1) + 7, 4, fillColor=H("#2B2B2B"), strokeColor=None))
        txt(d, bx + 7, py(13.1) - 7, rot, 5.3, "Sans-B", white, "middle")
    # LEDs
    d.add(Rect(cx - 16, py(12.2), 6, 4, fillColor=H("#FF3B30"), strokeColor=None))
    txt(d, cx - 13, py(12.2) - 6, "PWR", 4.3, "Sans", H("#BFD3EE"), "middle")
    d.add(Rect(cx + 10, py(12.2), 6, 4, fillColor=H("#33A1FF"), strokeColor=None))
    txt(d, cx + 13, py(12.2) - 6, "D2", 4.3, "Sans", H("#BFD3EE"), "middle")
    # USB micro
    d.add(Rect(cx - 15, base - 7, 30, 16, rx=2, ry=2, fillColor=H("#C9CED4"), strokeColor=H("#868F99"),
               strokeWidth=0.9))
    d.add(Rect(cx - 10, base - 3, 20, 5, rx=1.5, ry=1.5, fillColor=H("#4B525A"), strokeColor=None))
    txt(d, cx, base + 12, "USB", 5, "Sans-B", white, "middle")
    # pinos
    for i in range(15):
        y = py(i)
        for lado, nomes, px in (("L", ESQ, x0 + 9), ("R", DIR, x1 - 9)):
            cor = uso.get((lado, i))
            if cor is not None:
                d.add(Circle(px, y, 6, fillColor=cor, strokeColor=None))
            d.add(Circle(px, y, 4.1, fillColor=H("#D9B44A"), strokeColor=H("#8C6D1F"), strokeWidth=0.7))
            d.add(Circle(px, y, 1.7, fillColor=H("#3A2E10"), strokeColor=None))
            nome = nomes[i]
            if lado == "L":
                txt(d, x0 + 17, y - 2.4, nome, 6.8, "Mono-B", white)
            else:
                txt(d, x1 - 17, y - 2.4, nome, 6.8, "Mono-B", white, "end")
    if ("L", 11) not in uso:  # D12 proibido
        y = py(11)
        linha(d, x0 + 5, y - 4, x0 + 13, y + 4, H("#FF4D4D"), 1.6)
        linha(d, x0 + 5, y + 4, x0 + 13, y - 4, H("#FF4D4D"), 1.6)
    if titulo:
        txt(d, cx, base - 18, "ESP32 DevKit V1 · 30 pinos (vista de cima)", 7, "Sans-B", NAVY, "middle")
    return lambda lado, i: ((x0 + 9) if lado == "L" else (x1 - 9), py(i))

# ------------------------------------------------------------------ teclado 4x4
TECLAS = [["1", "2", "3", "A"], ["4", "5", "6", "B"], ["7", "8", "9", "C"], ["*", "0", "#", "D"]]


def teclado(d, x, y, w, h, legenda=False):
    """Teclado de membrana (vista de frente). (x, y) = canto inferior esquerdo."""
    d.add(Rect(x + 2, y - 2, w, h, rx=6, ry=6, fillColor=H("#0B0B0B"), strokeColor=None))
    d.add(Rect(x, y, w, h, rx=6, ry=6, fillColor=H("#24262E"), strokeColor=H("#111111"), strokeWidth=1))
    m = w * 0.08
    kw = (w - 2 * m) / 4 * 0.78
    kh = (h - 2 * m) / 4 * 0.74
    for li in range(4):
        for co in range(4):
            kx = x + m + co * (w - 2 * m) / 4 + ((w - 2 * m) / 4 - kw) / 2
            ky = y + h - m - (li + 1) * (h - 2 * m) / 4 + ((h - 2 * m) / 4 - kh) / 2
            cor = H("#D23B3B") if co == 3 else H("#2D6FD6")
            d.add(Rect(kx, ky, kw, kh, rx=3, ry=3, fillColor=cor, strokeColor=H("#0E0E0E"), strokeWidth=0.6))
            d.add(Rect(kx + 1.5, ky + kh * 0.55, kw - 3, kh * 0.38, rx=2, ry=2, fillColor=white,
                       fillOpacity=0.13, strokeColor=None))
            tecla = TECLAS[li][co]
            txt(d, kx + kw / 2, ky + kh / 2 - kh * 0.17, tecla, kh * 0.5, "Sans-B", white, "middle")
            if legenda and tecla in "*#A":
                sub = {"*": "LIMPAR", "#": "CONFIRMAR", "A": "TROCAR SENHA"}[tecla]
                txt(d, kx + kw / 2, ky - 7, sub, 5.2, "Sans-B", H("#FFD27A"), "middle")


def ribbon_reto(d, cx, ytopo, ybase, n=8, passo=3.2):
    """Cabo flat descendo do teclado (vista de frente): condutor 1 à esquerda."""
    w = n * passo
    d.add(Rect(cx - w / 2, ybase, w, ytopo - ybase, fillColor=H("#BCC2CA"), strokeColor=H("#8C939C"),
               strokeWidth=0.6))
    for k in range(n):
        linha(d, cx - w / 2 + passo * (k + 0.5), ybase, cx - w / 2 + passo * (k + 0.5), ytopo, H("#6E7680"), 0.8)

# ------------------------------------------------------------------ figura: diagrama completo (paisagem)
def modulo_tm1637(d, x, y, w=200, h=118, texto="123___", tracejado=True, passo=16, y0=12):
    """Módulo de 6 dígitos TM1637. Pinos no lado esquerdo; retorna dict nome -> (x, y) do pino."""
    d.add(Rect(x, y, w, h, rx=5, ry=5, fillColor=H("#1D4F8F"), strokeColor=H("#123564"), strokeWidth=1))
    if tracejado:
        d.add(Rect(x - 5, y - 5, w + 10, h + 10, rx=7, ry=7, fillColor=None, strokeColor=ACC, strokeWidth=1.2,
                   strokeDashArray=[4, 3]))
    painel(d, x + 22, y + h - 52, 30, texto)
    d.add(Rect(x + w - 58, y + 10, 30, 22, rx=1.5, ry=1.5, fillColor=H("#1C1C1C"), strokeColor=None))
    txt(d, x + w - 43, y + 18.5, "TM1637", 4.8, "Sans-B", H("#C9CED4"), "middle")
    pinos = {}
    for k, nome in enumerate(["DIO", "CLK", "VCC", "GND"]):
        py = y + y0 + passo * k
        d.add(Rect(x - 6, py - 3, 10, 6, fillColor=H("#D9B44A"), strokeColor=None))
        txt(d, x + 8, py - 2.3, nome, 6, "Sans-B", white)
        pinos[nome] = (x - 6, py)
    return pinos


def diagrama_completo():
    W, Hh = 770, 470
    d = Drawing(W, Hh)
    pad = placa(d, 320, 392)

    # ---- teclado + cabo flat (dobrado: a dobra de 45° põe o pino 1 em cima)
    teclado(d, 20, 150, 150, 165)
    txt(d, 95, 320, "Teclado de membrana 4x4", 7.5, "Sans-B", NAVY, "middle")
    bx0, bw, passo = 83, 24, 3
    yb1 = 130
    p = Path(fillColor=H("#BCC2CA"), strokeColor=H("#8C939C"), strokeWidth=0.6)
    p.moveTo(bx0, 150); p.lineTo(bx0 + bw, 150); p.lineTo(bx0 + bw, yb1 - bw); p.lineTo(bx0, yb1); p.closePath()
    d.add(p)
    p = Path(fillColor=H("#949BA4"), strokeColor=H("#7A818A"), strokeWidth=0.6)
    p.moveTo(bx0, yb1); p.lineTo(bx0 + bw, yb1 - bw); p.lineTo(170, yb1 - bw); p.lineTo(170, yb1); p.closePath()
    d.add(p)
    pinos_y = [282 - 22 * k for k in range(8)]
    for k in range(8):
        a = passo * (k + 0.5)
        linha(d, bx0 + a, 150, bx0 + a, yb1 - a, H("#6E7680"), 0.7)
        linha(d, bx0 + a, yb1 - a, 170, yb1 - a, H("#5E656E"), 0.7)
        f = Path(strokeColor=H("#6E7680"), strokeWidth=0.8, fillColor=None)
        f.moveTo(170, yb1 - a); f.curveTo(200, yb1 - a, 196, pinos_y[k], 222, pinos_y[k])
        d.add(f)
    txt(d, 128, yb1 - bw - 9, "cabo flat (dobrado)", 5.8, "Sans-I", MUTED, "middle")
    d.add(Rect(222, 118, 14, 176, rx=2, ry=2, fillColor=H("#151515"), strokeColor=H("#000000"), strokeWidth=0.6))
    for k, y in enumerate(pinos_y):
        d.add(Rect(233, y - 3, 6, 6, fillColor=H("#D9B44A"), strokeColor=None))
        txt(d, 228, y - 2.3, str(k + 1), 6, "Sans-B", white, "middle")
    txt(d, 229, 300, "conector", 6, "Sans-B", NAVY, "middle")
    for k in range(8):
        x, y = pad("L", 5 + k)
        fio(d, [239, pinos_y[k], x, y], KP[k])
        txt(d, 247, pinos_y[k] + 3.5, KPN[k], 6.4, "Sans-B", KP[k])

    # ---- divisor de bateria (VP)
    x, y = pad("L", 1)
    fio(d, [x, y, 262, y], C["bat"])
    ponto(d, 262, y)
    res_v(d, 262, y, 432, "330 kΩ", "R1", "right")
    bandeira(d, 262, 432, "+12 V", C["v12"])
    res_h(d, 196, 262, y, "100 kΩ", "R2")
    terra(d, 196, y)
    txt(d, 300, y + 6, "bateria (ADC)", 5.8, "Sans-I", C["bat"], "middle")

    # ---- sensor de porta (opcional)
    x, y = pad("L", 2)
    fio(d, [x, y, 300, y], C["door"], dash=[3, 2])
    etiqueta(d, 300, y, "sensor da porta (opc., §5.6)", C["door"], "end")

    # ---- alimentação (VIN/GND -> buck, embaixo à esquerda)
    xg, yg = pad("L", 13)
    xv, yv = pad("L", 14)
    fio(d, [xg, yg, 300, yg, 300, 48, 185, 48], C["gnd"], 2.2)
    fio(d, [xv, yv, 312, yv, 312, 24, 185, 24], C["v5"], 2.2)
    txt(d, 240, 52, "GND", 6.4, "Sans-B", C["gnd"], "middle")
    txt(d, 240, 28, "+5 V (VIN)", 6.4, "Sans-B", C["v5"], "middle")
    d.add(Rect(50, 6, 135, 64, rx=3, ry=3, fillColor=H("#1F4E8C"), strokeColor=H("#123564"), strokeWidth=1))
    d.add(Rect(100, 14, 26, 26, rx=4, ry=4, fillColor=H("#3A3F45"), strokeColor=H("#222"), strokeWidth=0.6))
    for cx_ in (82, 144):
        d.add(Circle(cx_, 27, 8, fillColor=H("#2A2A2A"), strokeColor=H("#777"), strokeWidth=0.8))
        d.add(Circle(cx_, 27, 2.6, fillColor=H("#888"), strokeColor=None))
    d.add(Rect(106, 44, 13, 10, fillColor=H("#2B6CD4"), strokeColor=H("#0F3E85"), strokeWidth=0.6))
    d.add(Circle(112.5, 49, 2.6, fillColor=H("#E3C26A"), strokeColor=None))
    txt(d, 117, 60, "LM2596 · ajuste p/ 5,0 V", 6, "Sans-B", white, "middle")
    for yy, rot in [(48, "OUT–"), (24, "OUT+")]:
        d.add(Rect(179, yy - 4, 6, 8, fillColor=H("#D9B44A"), strokeColor=None))
        txt(d, 176, yy - 2.2, rot, 5.4, "Sans-B", white, "end")
    for yy, rot in [(48, "IN+"), (24, "IN–")]:
        d.add(Rect(50, yy - 4, 6, 8, fillColor=H("#D9B44A"), strokeColor=None))
        txt(d, 59, yy - 2.2, rot, 5.4, "Sans-B", white)
    fio(d, [50, 48, 36, 48, 36, 62], C["v12"], 2.2)
    bandeira(d, 36, 62, "+12 V", C["v12"])
    fio(d, [50, 24, 22, 24], C["gnd"], 2.2)
    terra(d, 22, 24)

    # ---- módulo display TM1637 (ainda não chegou: tracejado)
    mx, my = 566, 256
    pinos = modulo_tm1637(d, mx, my, 200, 148, passo=22, y0=4)
    txt(d, mx + 100, my + 172, "MÓDULO DISPLAY 6 DÍGITOS TM1637", 6.8, "Sans-B", NAVY, "middle")
    txt(d, mx + 100, my + 163, "a comprar · TEM_DISPLAY = false até ligar (§5.5)", 5.8, "Sans-I", ACC, "middle")
    for nome, i, chave, gp in [("DIO", 6, "dio", "GPIO18"), ("CLK", 5, "clk", "GPIO19")]:
        x, y = pad("R", i)
        px, py = pinos[nome]
        fio(d, [x, y, 530, y, 530, py, px, py] if abs(y - py) > 0.5 else [x, y, px, py], C[chave], dash=[4, 2])
        txt(d, 500, y + 3.5, gp, 5.6, "Sans-I", C[chave], "middle")
    for nome, rot, cor in [("VCC", "3V3", C["v33"]), ("GND", "GND", C["gnd"])]:
        px, py = pinos[nome]
        linha(d, px - 12, py, px, py, cor, 1.6, [4, 2])
        etiqueta(d, px - 12, py, rot, cor, "end")

    # ---- fechadura solenoide (RX2 = GPIO16)
    x, y = pad("R", 9)
    fio(d, [x, y, 486, y], C["lock"])
    txt(d, 474, y - 9, "GPIO16", 5.6, "Sans-I", C["lock"], "middle")
    res_h(d, 486, 526, y, "100 Ω")
    linha(d, 526, y, 550, y)
    ponto(d, 538, y)
    res_v(d, 538, 158, y, "10 kΩ", "", "left")
    terra(d, 538, 158)
    g, dr, so = nmos(d, 568, y)
    txt(d, 590, y - 4, "IRLZ44N", 6.4, "Sans-B")
    linha(d, so[0], so[1], so[0], 158)
    terra(d, so[0], 158)
    linha(d, dr[0], dr[1], dr[0], 226)
    linha(d, dr[0], 226, 596, 226)
    bobina_h(d, 596, 644, 226)
    linha(d, 644, 226, 700, 226)
    bandeira(d, 700, 226, "+12 V", C["v12"])
    for xx in (590, 650):
        linha(d, xx, 226, xx, 240)
        ponto(d, xx, 226)
    diodo_h(d, 590, 650, 240)
    txt(d, 656, 236, "1N4007", 6.2, "Sans-B")
    txt(d, 620, 213, "bobina", 5.6, "Sans-I", MUTED, "middle")
    # fechadura física
    lx, ly = 655, 160
    linha(d, 620, 208, lx + 18, ly + 32, MUTED, 0.7, [2, 2])
    d.add(Rect(lx, ly, 58, 32, rx=2, ry=2, fillColor=H("#C9CED4"), strokeColor=H("#7D8790"), strokeWidth=1))
    d.add(Rect(lx + 3, ly + 3, 32, 26, fillColor=H("#AEB5BD"), strokeColor=H("#8C949D"), strokeWidth=0.6))
    p = Path(fillColor=H("#E8EBEE"), strokeColor=H("#7D8790"), strokeWidth=0.8)
    p.moveTo(lx + 58, ly + 8); p.lineTo(lx + 70, ly + 8); p.lineTo(lx + 77, ly + 19); p.lineTo(lx + 58, ly + 24)
    p.closePath()
    d.add(p)
    txt(d, lx + 19, ly + 13, "FEC-91", 5.6, "Sans-B", H("#3A4350"), "middle")
    txt(d, lx + 82, ly + 26, "Fechadura", 6.2, "Sans-B")
    txt(d, lx + 82, ly + 18, "solenoide 12 V", 6.2, "Sans-B")
    txt(d, lx + 82, ly + 10, "(a bobina", 5.6, "Sans-I", MUTED)
    txt(d, lx + 82, ly + 3, "acima)", 5.6, "Sans-I", MUTED)

    # ---- buzzer (TX2 = GPIO17), desenhado embaixo e ligado por etiqueta
    x, y = pad("R", 8)
    fio(d, [x, y, 470, y], C["buz"])
    etiqueta(d, 470, y, "TX2 → buzzer", C["buz"])
    yb = 110
    etiqueta(d, 470, yb, "TX2 (GPIO17)", C["buz"])
    linha(d, 529, yb, 534, yb)
    res_h(d, 534, 574, yb, "1 kΩ")
    linha(d, 574, yb, 596, yb)
    ponto(d, 584, yb)
    res_v(d, 584, 74, yb, "10 kΩ", "", "left")
    terra(d, 584, 74)
    b, c_, e = npn(d, 612, yb)
    txt(d, 630, yb - 10, "BC547", 6.4, "Sans-B")
    linha(d, e[0], e[1], e[0], 78)
    terra(d, e[0], 78)
    linha(d, c_[0], c_[1], c_[0], c_[1] + 2)
    buzzer(d, c_[0], c_[1] + 16, 10)
    linha(d, c_[0], c_[1] + 30, c_[0], c_[1] + 34)
    bandeira(d, c_[0], c_[1] + 34, "+5 V", C["v5"])
    txt(d, c_[0] + 16, c_[1] + 18, "Buzzer ativo 5 V", 6.4, "Sans-B")
    txt(d, c_[0] + 16, c_[1] + 10, "(+) para cima", 5.6, "Sans-I", MUTED)

    # ---- outros pinos do lado direito
    x, y = pad("R", 11)
    fio(d, [x, y, 470, y], C["led"])
    etiqueta(d, 470, y, "LED", C["led"])
    x, y = pad("R", 14)
    fio(d, [x, y, 470, y], C["v33"], dash=[3, 2])
    etiqueta(d, 470, y, "3V3 (opc.)", C["v33"])

    # ---- legenda (alto à esquerda)
    lx, ly = 22, 452
    d.add(Rect(14, 333, 164, 131, rx=4, ry=4, fillColor=H("#F7F8FA"), strokeColor=LINE, strokeWidth=0.8))
    txt(d, lx, ly, "LEGENDA DOS FIOS", 7, "Sans-B", NAVY)
    itens = [(C["v12"], "+12 V (bateria)"), (C["v5"], "+5 V (saída do buck)"), (C["gnd"], "GND (terra comum)"),
             (KP[1], "teclado: linhas L1–L4"), (KP[5], "teclado: colunas C1–C4"),
             (C["dio"], "display: DIO/CLK (a ligar)"), (C["lock"], "comando da fechadura"),
             (C["buz"], "comando do buzzer"), (C["bat"], "leitura da bateria"), (C["door"], "opcional (tracejado)")]
    for k, (cor, rot) in enumerate(itens):
        yy = ly - 13 - 11.2 * k
        linha(d, lx, yy + 2, lx + 16, yy + 2, cor, 2.4, [3, 2] if "opcional" in rot else None)
        txt(d, lx + 22, yy, rot, 6.2)
    # ---- avisos (embaixo à direita)
    d.add(Rect(662, 2, 106, 92, rx=4, ry=4, fillColor=H("#FFF4E8"), strokeColor=H("#F2C08F"), strokeWidth=0.8))
    txt(d, 669, 82, "⚠ ANTES DE LIGAR", 6.8, "Sym-B", H("#B85C00"))
    for k, s_ in enumerate(["GND é um só ponto.", "Buck em 5,0 V antes", "de ligar o ESP32.",
                            "No D12 só o fio 7.", "10 kΩ no gate e na", "base: obrigatórios.", "Display no 3V3."]):
        txt(d, 669, 70 - 9.4 * k, s_, 6.1)
    return d

# ------------------------------------------------------------------ figura: pinagem da placa
def figura_pinagem():
    d = Drawing(500, 440)
    pad = placa(d, 180, 380, 22, 140)
    funcs_esq = {1: ("bateria (ADC, divisor)", C["bat"]), 2: ("sensor de porta (opcional)", C["door"]),
                 5: ("teclado fio 1 · L1", KP[0]), 6: ("teclado fio 2 · L2", KP[1]), 7: ("teclado fio 3 · L3", KP[2]),
                 8: ("teclado fio 4 · L4", KP[3]), 9: ("teclado fio 5 · C1", KP[4]), 10: ("teclado fio 6 · C2", KP[5]),
                 11: ("teclado fio 7 · C3 (só ele!)", KP[6]), 12: ("teclado fio 8 · C4", KP[7]),
                 13: ("GND comum", C["gnd"]), 14: ("+5 V do buck", C["v5"])}
    funcs_dir = {5: ("display: CLK (TM1637)", C["clk"]), 6: ("display: DIO (TM1637)", C["dio"]),
                 8: ("buzzer (base do BC547)", C["buz"]), 9: ("tranca (gate do MOSFET)", C["lock"]),
                 11: ("LED de status", C["led"]), 13: ("GND (opcional)", C["gnd"]),
                 14: ("VCC do display + pull-up sensor", C["v33"])}
    for i in range(15):
        x, y = pad("L", i)
        f = funcs_esq.get(i)
        cor = f[1] if f else H("#AAB2BD")
        linha(d, x - 20, y, 176, y, cor, 1.4 if f else 0.6)
        txt(d, 170, y + 2.2, GPIO_ESQ[i], 6, "Mono", MUTED, "end")
        txt(d, 170, y - 6.2, f[0] if f else "livre", 6.4, "Sans-B" if f else "Sans-I", cor, "end")
        x, y = pad("R", i)
        f = funcs_dir.get(i)
        cor = f[1] if f else H("#AAB2BD")
        linha(d, 324, y, x + 20, y, cor, 1.4 if f else 0.6)
        txt(d, 330, y + 2.2, GPIO_DIR[i], 6, "Mono", MUTED)
        txt(d, 330, y - 6.2, f[0] if f else "livre", 6.4, "Sans-B" if f else "Sans-I", cor)
    # tampa os trechos de linha que passaram por cima da placa
    return d

# ------------------------------------------------------------------ figura: teclado detalhado
def figura_teclado():
    d = Drawing(500, 300)
    teclado(d, 30, 110, 170, 180, legenda=True)
    ribbon_reto(d, 115, 110, 58)
    d.add(Rect(115 - 26, 40, 52, 18, rx=2, ry=2, fillColor=H("#151515"), strokeColor=None))
    for k in range(8):
        x = 115 - 26 + 3.25 + 6.5 * k
        d.add(Rect(x - 1.6, 44, 3.2, 10, fillColor=H("#D9B44A"), strokeColor=None))
        linha(d, x, 40, x, 30 - (k % 2) * 0, KP[k], 1.6)
        txt(d, x, 21 - (k % 2) * 9, str(k + 1), 6.4, "Sans-B", KP[k], "middle")
    txt(d, 115, 2, "fios 1 a 8 da ESQUERDA para a DIREITA (teclado de frente)", 6.4, "Sans-I", MUTED, "middle")
    # matriz interna
    mx, my = 280, 70
    txt(d, mx + 95, 285, "Como o teclado é ligado por dentro", 7.6, "Sans-B", NAVY, "middle")
    for li in range(4):
        y = my + 180 - li * 50
        linha(d, mx, y, mx + 190, y, KP[li], 1.8)
        txt(d, mx - 6, y - 2.5, f"fio {li + 1} · L{li + 1}", 6.6, "Sans-B", KP[li], "end")
    for co in range(4):
        x = mx + 30 + co * 45
        linha(d, x, my - 8, x, my + 200, KP[4 + co], 1.8)
        txt(d, x, my - 18, f"C{co + 1}", 6.6, "Sans-B", KP[4 + co], "middle")
        txt(d, x, my - 27, f"fio {co + 5}", 6, "Sans", KP[4 + co], "middle")
    for li in range(4):
        for co in range(4):
            x, y = mx + 30 + co * 45, my + 180 - li * 50
            d.add(Rect(x + 4, y + 4, 15, 15, rx=3, ry=3, fillColor=H("#EEF1F5"), strokeColor=H("#9AA4B1"),
                       strokeWidth=0.7))
            txt(d, x + 11.5, y + 8, TECLAS[li][co], 7.5, "Sans-B", INK, "middle")
            linha(d, x, y, x + 4, y + 4, MUTED, 0.6)
            ponto(d, x, y, MUTED, 1.4)
    return d

# ------------------------------------------------------------------ esquemáticos por bloco
def esq_alimentacao():
    d = Drawing(500, 190)
    # bateria
    bx, by = 40, 70
    linha(d, bx, by + 70, bx, by + 34)
    for k in range(3):
        y = by + 30 - k * 11
        linha(d, bx - 12, y, bx + 12, y, INK, 1.6)
        linha(d, bx - 6, y - 4, bx + 6, y - 4, INK, 3)
    linha(d, bx, by + 4 - 22 + 22 - 12, bx, by - 30)
    txt(d, bx - 16, by + 24, "+", 9, "Sans-B", C["v12"], "end")
    txt(d, bx + 18, by + 22, "Bateria 12 V", 7, "Sans-B")
    txt(d, bx + 18, by + 13, "pack 3S 18650 + BMS", 6, "Sans-I", MUTED)
    txt(d, bx + 18, by + 5, "(ou fonte 12 V 2 A)", 6, "Sans-I", MUTED)
    # fusível
    fio(d, [bx, by + 70, bx, 160, 70, 160], C["v12"], 2)
    d.add(Rect(70, 155, 26, 10, rx=5, ry=5, fillColor=H("#FFFDF5"), strokeColor=INK, strokeWidth=1))
    linha(d, 70, 160, 96, 160, INK, 0.8)
    txt(d, 83, 170, "fusível 2 A", 6.2, "Sans-B", INK, "middle")
    fio(d, [96, 160, 480, 160], C["v12"], 2)
    txt(d, 480, 165, "+12 V", 7.5, "Sans-B", C["v12"], "end")
    fio(d, [bx, by - 30, bx, 20, 480, 20], C["gnd"], 2)
    txt(d, 480, 25, "GND comum", 7.5, "Sans-B", C["gnd"], "end")
    # capacitor de reserva
    ponto(d, 140, 160)
    ponto(d, 140, 20)
    linha(d, 140, 160, 140, 98)
    linha(d, 140, 82, 140, 20)
    linha(d, 133, 98, 147, 98, INK, 1.6)
    p = Path(strokeColor=INK, strokeWidth=1.6, fillColor=None)
    p.moveTo(133, 80); p.curveTo(137, 84, 143, 84, 147, 80)
    d.add(p)
    txt(d, 131, 100, "+", 7, "Sans-B", C["v12"], "end")
    txt(d, 152, 92, "470 µF", 6.6, "Sans-B")
    txt(d, 152, 84, "25 V", 6, "Sans", MUTED)
    # ramos
    for x, rot in [(215, "solenoide (§5.3)"), (285, "R1 do divisor (§5.6)")]:
        ponto(d, x, 160)
        linha(d, x, 160, x, 130, C["v12"], 1.4)
        txt(d, x, 120, "→ " + rot, 6.6, "Sym", INK, "middle")
    # buck
    ponto(d, 330, 160)
    ponto(d, 330, 20)
    fio(d, [330, 160, 330, 120, 342, 120], C["v12"], 1.6)
    fio(d, [330, 20, 330, 68, 342, 68], C["gnd"], 1.6)
    d.add(Rect(342, 58, 70, 72, rx=3, ry=3, fillColor=H("#1F4E8C"), strokeColor=H("#123564"), strokeWidth=1))
    txt(d, 377, 100, "LM2596", 7, "Sans-B", white, "middle")
    txt(d, 377, 90, "12 → 5,0 V", 6.4, "Sans", white, "middle")
    for y, r in [(120, "IN+"), (68, "IN–")]:
        txt(d, 346, y - 2.3, r, 5.4, "Sans-B", H("#FFD27A"))
    for y, r in [(120, "OUT+"), (68, "OUT–")]:
        txt(d, 408, y - 2.3, r, 5.4, "Sans-B", H("#FFD27A"), "end")
    fio(d, [412, 120, 432, 120], C["v5"], 2)
    txt(d, 436, 117.5, "VIN do ESP32", 6.8, "Sans-B", C["v5"])
    txt(d, 436, 108, "e +5 V do buzzer", 6, "Sans", MUTED)
    fio(d, [412, 68, 420, 68, 420, 20], C["gnd"], 1.6)
    ponto(d, 420, 20)
    return d


def esq_tranca():
    d = Drawing(500, 200)
    txt(d, 30, 100, "D16 / RX2", 7.5, "Mono-B", C["lock"])
    txt(d, 30, 90, "(GPIO16)", 6.2, "Sans", MUTED)
    fio(d, [80, 102, 150, 102], C["lock"], 1.8)
    res_h(d, 150, 210, 102, "100 Ω", "R gate")
    linha(d, 210, 102, 262, 102)
    ponto(d, 236, 102)
    res_v(d, 236, 40, 102, "10 kΩ", "pull-down", "left")
    terra(d, 236, 40)
    g, dr, so = nmos(d, 280, 102)
    txt(d, 300, 99, "IRLZ44N", 7, "Sans-B")
    txt(d, 300, 90, "(ou IRLB8721)", 6, "Sans-I", MUTED)
    linha(d, so[0], so[1], so[0], 40)
    terra(d, so[0], 40)
    linha(d, dr[0], dr[1], dr[0], 135)
    bobina_v(d, dr[0], 135, 175)
    linha(d, dr[0], 175, dr[0], 182)
    bandeira(d, dr[0], 182, "+12 V", C["v12"])
    for yy in (135, 175):
        linha(d, dr[0], yy, 330, yy)
        ponto(d, dr[0], yy)
    diodo_v(d, 330, 135, 175, "1N4007", "right")
    txt(d, dr[0] - 10, 157, "solenoide", 6.6, "Sans-B", INK, "end")
    txt(d, dr[0] - 10, 149, "FEC-91", 6.2, "Sans", MUTED, "end")
    d.add(Rect(380, 40, 115, 140, rx=4, ry=4, fillColor=H("#F7F8FA"), strokeColor=LINE, strokeWidth=0.8))
    for k, s in enumerate(["Por que cada peça?", "", "100 Ω: limita o pico de", "corrente no gate.",
                           "10 kΩ: mantém o MOSFET", "desligado no boot e no", "deep sleep (GPIO solto).",
                           "1N4007: absorve o pico de", "tensão quando a bobina", "desliga. Faixa = +12 V.",
                           "GPIO HIGH = destrava."]):
        txt(d, 388, 168 - 11 * k, s, 6.4, "Sans-B" if k == 0 else "Sans", NAVY if k == 0 else INK)
    return d


def esq_buzzer():
    d = Drawing(500, 170)
    txt(d, 30, 80, "TX2", 7.5, "Mono-B", C["buz"])
    txt(d, 30, 70, "(GPIO17)", 6.2, "Sans", MUTED)
    fio(d, [60, 82, 140, 82], C["buz"], 1.8)
    res_h(d, 140, 200, 82, "1 kΩ", "R base")
    linha(d, 200, 82, 252, 82)
    ponto(d, 224, 82)
    res_v(d, 224, 25, 82, "10 kΩ", "pull-down", "left")
    terra(d, 224, 25)
    b, c_, e = npn(d, 268, 82)
    txt(d, 290, 79, "BC547", 7, "Sans-B")
    txt(d, 290, 70, "(ou BC337, 2N2222)", 6, "Sans-I", MUTED)
    linha(d, e[0], e[1], e[0], 25)
    terra(d, e[0], 25)
    buzzer(d, c_[0], c_[1] + 20, 13)
    linha(d, c_[0], c_[1], c_[0], c_[1] + 3)
    linha(d, c_[0], c_[1] + 37, c_[0], 150)
    bandeira(d, c_[0], 150, "+5 V", C["v5"])
    txt(d, c_[0] + 20, c_[1] + 22, "Buzzer ativo 5 V", 6.8, "Sans-B")
    txt(d, c_[0] + 20, c_[1] + 13, "perna longa / '+' para cima", 6, "Sans-I", MUTED)
    d.add(Rect(380, 25, 115, 120, rx=4, ry=4, fillColor=H("#F7F8FA"), strokeColor=LINE, strokeWidth=0.8))
    for k, s in enumerate(["Por que transistor?", "", "O buzzer de 5 V consome", "~30 mA: muito para um",
                           "GPIO de 3,3 V. O BC547", "chaveia o buzzer.", "O 10 kΩ evita apito", "durante o deep sleep."]):
        txt(d, 388, 133 - 11 * k, s, 6.4, "Sans-B" if k == 0 else "Sans", NAVY if k == 0 else INK)
    return d


def esq_sensores():
    d = Drawing(500, 175)
    # divisor
    txt(d, 70, 160, "Leitura da bateria", 7.5, "Sans-B", NAVY, "middle")
    bandeira(d, 70, 135, "+12 V", C["v12"])
    res_v(d, 70, 85, 135, "330 kΩ", "R1", "right")
    ponto(d, 70, 85)
    res_v(d, 70, 30, 85, "100 kΩ", "R2", "left")
    terra(d, 70, 30)
    linha(d, 70, 85, 112, 85)
    ponto(d, 112, 85)
    cap_v(d, 112, 30, 85, "100 nF", "right")
    terra(d, 112, 30)
    fio(d, [112, 85, 150, 85], C["bat"], 1.8)
    txt(d, 153, 83, "VP", 7.5, "Mono-B", C["bat"])
    txt(d, 153, 74, "(GPIO36)", 6, "Sans", MUTED)
    txt(d, 70, 4, "12,6 V → 2,93 V no pino", 6.2, "Sym", MUTED, "middle")
    # LED
    txt(d, 255, 160, "LED externo (opcional)", 7.5, "Sans-B", NAVY, "middle")
    txt(d, 220, 128, "D2", 7.5, "Mono-B", C["led"])
    fio(d, [234, 130, 255, 130], C["led"], 1.8)
    res_v(d, 255, 95, 130, "220 Ω", "", "right")
    led_v(d, 255, 45, 95)
    terra(d, 255, 45)
    txt(d, 270, 66, "perna longa", 6, "Sans-I", MUTED)
    txt(d, 270, 58, "= anodo (+)", 6, "Sans-I", MUTED)
    txt(d, 255, 4, "em paralelo com o LED azul da placa", 6.2, "Sans-I", MUTED, "middle")
    # reed
    txt(d, 415, 160, "Sensor da porta (opcional)", 7.5, "Sans-B", NAVY, "middle")
    bandeira(d, 400, 135, "3V3", C["v33"])
    res_v(d, 400, 92, 135, "10 kΩ", "pull-up", "left")
    ponto(d, 400, 92)
    fio(d, [400, 92, 460, 92], C["door"], 1.8)
    txt(d, 463, 90, "VN", 7.5, "Mono-B", C["door"])
    txt(d, 463, 81, "(GPIO39)", 6, "Sans", MUTED)
    linha(d, 400, 92, 400, 80)
    linha(d, 400, 80, 400, 70)
    linha(d, 400, 70, 407, 52, INK, 1.3)
    linha(d, 400, 50, 400, 40)
    d.add(Rect(392, 44, 16, 32, rx=8, ry=8, fillColor=None, strokeColor=MUTED, strokeWidth=0.8,
               strokeDashArray=[2, 1.5]))
    terra(d, 400, 40)
    txt(d, 414, 60, "reed switch", 6.4, "Sans-B")
    txt(d, 414, 52, "fecha com o ímã", 6, "Sans-I", MUTED)
    txt(d, 415, 4, "porta fechada = VN em LOW", 6.2, "Sans-I", MUTED, "middle")
    return d

# ------------------------------------------------------------------ figura: identificação de terminais
def figura_componentes():
    d = Drawing(500, 340)
    # IRLZ44N (TO-220)
    x, y = 40, 215
    txt(d, x + 25, 328, "IRLZ44N (TO-220)", 7.5, "Sans-B", NAVY, "middle")
    d.add(Rect(x, y + 50, 50, 28, fillColor=H("#C9CED4"), strokeColor=H("#7D8790"), strokeWidth=0.8))
    d.add(Circle(x + 25, y + 66, 5.5, fillColor=white, strokeColor=H("#7D8790"), strokeWidth=0.8))
    d.add(Rect(x, y + 10, 50, 42, fillColor=H("#1C1C1C"), strokeColor=None))
    txt(d, x + 25, y + 34, "IRLZ44N", 6, "Sans-B", H("#BBBBBB"), "middle")
    for k, (rot, cor) in enumerate([("G", C["lock"]), ("D", INK), ("S", C["gnd"])]):
        lx = x + 10 + 15 * k
        d.add(Rect(lx - 2, y - 30, 4, 40, fillColor=H("#C9CED4"), strokeColor=H("#7D8790"), strokeWidth=0.5))
        txt(d, lx, y - 42, rot, 8, "Sans-B", cor, "middle")
    for k, s in enumerate(["G = gate ← resistor 100 Ω", "D = dreno ← solenoide (–)", "S = fonte → GND",
                           "letras para você, pernas para baixo"]):
        txt(d, x - 10, y - 58 - 9 * k, s, 6, "Sym" if k < 3 else "Sans-I", INK if k < 3 else MUTED)
    # BC547 (TO-92)
    x, y = 205, 240
    txt(d, x + 15, 328, "BC547 (TO-92)", 7.5, "Sans-B", NAVY, "middle")
    p = Path(fillColor=H("#1C1C1C"), strokeColor=None)
    p.moveTo(x, y + 20); p.lineTo(x + 30, y + 20); p.lineTo(x + 30, y + 44)
    p.curveTo(x + 30, y + 64, x, y + 64, x, y + 44); p.closePath()
    d.add(p)
    txt(d, x + 15, y + 36, "BC", 5.5, "Sans-B", H("#BBBBBB"), "middle")
    txt(d, x + 15, y + 28, "547", 5.5, "Sans-B", H("#BBBBBB"), "middle")
    for k, (rot, cor) in enumerate([("C", INK), ("B", C["buz"]), ("E", C["gnd"])]):
        lx = x + 5 + 10 * k
        linha(d, lx, y + 20, lx, y - 20, H("#9AA3AE"), 1.6)
        txt(d, lx, y - 32, rot, 8, "Sans-B", cor, "middle")
    for k, s in enumerate(["C = coletor ← buzzer (–)", "B = base ← resistor 1 kΩ", "E = emissor → GND",
                           "face reta para você"]):
        txt(d, x - 20, y - 48 - 9 * k, s, 6, "Sym" if k < 3 else "Sans-I", INK if k < 3 else MUTED)
    # 1N4007
    x, y = 345, 280
    txt(d, x + 40, 328, "Diodo 1N4007", 7.5, "Sans-B", NAVY, "middle")
    linha(d, x, y, x + 80, y, H("#9AA3AE"), 1.6)
    d.add(Rect(x + 22, y - 8, 36, 16, rx=3, ry=3, fillColor=H("#1C1C1C"), strokeColor=None))
    d.add(Rect(x + 50, y - 8, 5, 16, fillColor=H("#D0D4D9"), strokeColor=None))
    txt(d, x + 52, y - 20, "faixa = catodo (K)", 6.2, "Sans-B", INK, "middle")
    txt(d, x + 52, y - 29, "vai no +12 V", 6, "Sans-I", MUTED, "middle")
    txt(d, x + 10, y + 12, "A", 7, "Sans-B", MUTED, "middle")
    txt(d, x + 72, y + 12, "K", 7, "Sans-B", MUTED, "middle")
    # LED
    x, y = 455, 270
    txt(d, x, 328, "LED 5 mm", 7.5, "Sans-B", NAVY, "middle")
    p = Path(fillColor=H("#5BC0EB"), strokeColor=H("#2F8FBF"), strokeWidth=0.8)
    p.moveTo(x - 9, y + 10); p.lineTo(x - 9, y + 30); p.curveTo(x - 9, y + 44, x + 9, y + 44, x + 9, y + 30)
    p.lineTo(x + 9, y + 10); p.closePath()
    d.add(p)
    d.add(Rect(x - 11, y + 8, 22, 3, fillColor=H("#2F8FBF"), strokeColor=None))
    linha(d, x - 4, y + 8, x - 4, y - 30, H("#9AA3AE"), 1.4)
    linha(d, x + 4, y + 8, x + 4, y - 18, H("#9AA3AE"), 1.4)
    txt(d, x - 4, y - 40, "+", 8, "Sans-B", C["v12"], "middle")
    txt(d, x + 6, y - 28, "–", 8, "Sans-B", INK, "middle")
    txt(d, x, y - 52, "longa = anodo", 6, "Sans-I", MUTED, "middle")
    # buzzer
    x, y = 70, 60
    txt(d, x, 108, "Buzzer ativo 5 V", 7.5, "Sans-B", NAVY, "middle")
    d.add(Circle(x, y + 30, 18, fillColor=H("#1C1C1C"), strokeColor=None))
    d.add(Circle(x, y + 30, 4, fillColor=H("#555"), strokeColor=None))
    txt(d, x - 10, y + 36, "+", 8, "Sans-B", C["v12"], "middle")
    txt(d, x, y - 4, "'+' marcado no topo e", 6, "Sans-I", MUTED, "middle")
    txt(d, x, y - 12, "perna mais longa = +", 6, "Sans-I", MUTED, "middle")
    txt(d, x, y - 20, "(tire o adesivo só no final)", 6, "Sans-I", MUTED, "middle")
    # buck
    x, y = 170, 30
    txt(d, x + 75, 108, "Módulo buck LM2596", 7.5, "Sans-B", NAVY, "middle")
    d.add(Rect(x, y, 150, 64, rx=3, ry=3, fillColor=H("#1F4E8C"), strokeColor=H("#123564"), strokeWidth=1))
    d.add(Rect(x + 52, y + 16, 34, 34, rx=4, ry=4, fillColor=H("#3A3F45"), strokeColor=None))
    for cx_ in (x + 28, x + 112):
        d.add(Circle(cx_, y + 33, 11, fillColor=H("#2A2A2A"), strokeColor=H("#777"), strokeWidth=0.8))
    d.add(Rect(x + 95, y + 46, 16, 13, fillColor=H("#2B6CD4"), strokeColor=H("#0F3E85"), strokeWidth=0.6))
    d.add(Circle(x + 103, y + 52.5, 3.5, fillColor=H("#E3C26A"), strokeColor=None))
    txt(d, x + 122, y + 70, "trimpot", 6, "Sans-B", INK)
    linha(d, x + 112, y + 56, x + 120, y + 68, MUTED, 0.6)
    for yy, r in [(y + 52, "IN+"), (y + 12, "IN–")]:
        d.add(Rect(x + 2, yy - 4, 7, 8, fillColor=H("#D9B44A"), strokeColor=None))
        txt(d, x - 3, yy - 2.3, r, 6.4, "Sans-B", C["v12"] if "+" in r else INK, "end")
    for yy, r in [(y + 52, "OUT+"), (y + 12, "OUT–")]:
        d.add(Rect(x + 141, yy - 4, 7, 8, fillColor=H("#D9B44A"), strokeColor=None))
        txt(d, x + 153, yy - 2.3, r, 6.4, "Sans-B", C["v5"] if "+" in r else INK)
    # reed
    x, y = 390, 70
    txt(d, x + 40, 108, "Reed switch + ímã", 7.5, "Sans-B", NAVY, "middle")
    linha(d, x, y + 20, x + 80, y + 20, H("#9AA3AE"), 1.4)
    d.add(Rect(x + 15, y + 12, 50, 16, rx=8, ry=8, fillColor=H("#E8F4F8"), fillOpacity=0.7, strokeColor=H("#8CB8C8"),
               strokeWidth=0.8))
    linha(d, x + 22, y + 20, x + 42, y + 22, INK, 1.2)
    linha(d, x + 38, y + 18, x + 58, y + 20, INK, 1.2)
    d.add(Rect(x + 20, y - 12, 40, 12, fillColor=H("#D62828"), strokeColor=None))
    d.add(Rect(x + 40, y - 12, 20, 12, fillColor=H("#1F6FEB"), strokeColor=None))
    txt(d, x + 40, y - 26, "sem polaridade; ímã a < 1 cm", 6, "Sans-I", MUTED, "middle")
    return d

# ------------------------------------------------------------------ figura: blocos
def figura_blocos():
    d = Drawing(500, 200)

    def bloco(x, y, w, h, t1, t2, cor):
        d.add(Rect(x, y, w, h, rx=5, ry=5, fillColor=H("#FFFFFF"), strokeColor=cor, strokeWidth=1.4))
        d.add(Rect(x, y + h - 5, w, 5, fillColor=cor, strokeColor=None))
        txt(d, x + w / 2, y + h / 2 + 1, t1, 7.6, "Sans-B", INK, "middle")
        txt(d, x + w / 2, y + h / 2 - 9, t2, 6.2, "Sans", MUTED, "middle")

    def seta(x1, y1, x2, y2, cor=INK, rot=""):
        linha(d, x1, y1, x2, y2, cor, 1.3)
        import math
        a = math.atan2(y2 - y1, x2 - x1)
        d.add(Polygon([x2, y2, x2 - 7 * math.cos(a - 0.4), y2 - 7 * math.sin(a - 0.4),
                       x2 - 7 * math.cos(a + 0.4), y2 - 7 * math.sin(a + 0.4)], fillColor=cor, strokeColor=None))
        if rot:
            txt(d, (x1 + x2) / 2, (y1 + y2) / 2 + 4, rot, 5.8, "Sans-I", MUTED, "middle")

    bloco(195, 75, 110, 60, "ESP32 DevKit V1", "controle (FSM)", NAVY)
    bloco(20, 130, 110, 46, "Teclado 4x4", "8 fios", KP[1])
    bloco(20, 60, 110, 46, "Divisor 330k/100k", "tensão da bateria", C["bat"])
    bloco(370, 140, 110, 44, "MOSFET IRLZ44N", "→ fechadura 12 V", C["lock"])
    bloco(370, 82, 110, 44, "BC547", "→ buzzer 5 V", C["buz"])
    bloco(370, 24, 110, 44, "LED de status", "desafio / avisos", C["led"])
    bloco(20, 0, 110, 40, "Bateria 12 V", "3S Li-ion", C["v12"])
    bloco(195, 0, 110, 40, "Buck LM2596", "12 V → 5 V", C["v5"])
    bloco(195, 152, 110, 40, "Display 6 dígitos", "TM1637 (a comprar)", C["dio"])
    seta(250, 135, 250, 152, C["dio"])
    txt(d, 256, 140, "2 fios", 5.8, "Sans-I", MUTED)
    seta(130, 153, 195, 120, KP[1], "")
    seta(130, 83, 195, 95, C["bat"])
    seta(305, 120, 370, 162, C["lock"], "GPIO16")
    seta(305, 105, 370, 104, C["buz"], "GPIO17")
    seta(305, 90, 370, 46, C["led"], "GPIO2")
    seta(130, 20, 195, 20, C["v12"], "12 V")
    seta(250, 40, 250, 75, C["v5"], "")
    txt(d, 256, 55, "5 V (VIN)", 5.8, "Sans-I", MUTED)
    seta(75, 40, 75, 60, C["v12"])
    linha(d, 130, 14, 160, 14, C["v12"], 1.1, [3, 2])
    linha(d, 160, 14, 160, 6, C["v12"], 1.1, [3, 2])
    linha(d, 160, 6, 330, 6, C["v12"], 1.1, [3, 2])
    linha(d, 330, 6, 330, 190, C["v12"], 1.1, [3, 2])
    seta(330, 190, 370, 175, C["v12"])
    txt(d, 334, 196, "12 V p/ fechadura", 5.8, "Sans-I", MUTED)
    return d

# ------------------------------------------------------------------ figura: fluxo de uso
def figura_fluxo():
    d = Drawing(500, 150)
    caixas = [("Aperte qualquer", "tecla (acorda)"), ("Digite os 2 dígitos", "do desafio"),
              ("Digite a senha", "(6 dígitos) + #"), ("Destrava", "por 5 s"), ("Trava e", "dorme")]
    xs = [8 + 99 * k for k in range(5)]
    for k, (a, b) in enumerate(caixas):
        cor = [MUTED, KP[1], NAVY, H("#2E7D32"), C["lock"]][k]
        d.add(Rect(xs[k], 82, 84, 44, rx=6, ry=6, fillColor=H("#FFFFFF"), strokeColor=cor, strokeWidth=1.4))
        d.add(Circle(xs[k] + 10, 126, 8, fillColor=cor, strokeColor=None))
        txt(d, xs[k] + 10, 123, str(k + 1), 8, "Sans-B", white, "middle")
        txt(d, xs[k] + 42, 106, a, 6.8, "Sans-B", INK, "middle")
        txt(d, xs[k] + 42, 96, b, 6.4, "Sans", MUTED, "middle")
        if k < 4:
            linha(d, xs[k] + 84, 104, xs[k + 1] - 4, 104, INK, 1.2)
            d.add(Polygon([xs[k + 1], 104, xs[k + 1] - 6, 107, xs[k + 1] - 6, 101], fillColor=INK, strokeColor=None))
    # retornos
    for k, rot in [(1, "dígito errado: novo desafio"), (2, "senha errada: digite de novo")]:
        x = xs[k] + 42
        linha(d, x, 82, x, 50, H("#C62828"), 1, [3, 2])
        txt(d, x, 40, rot, 6, "Sans-I", H("#C62828"), "middle")
    txt(d, xs[2] + 42, 28, "5ª senha errada seguida: bloqueio", 6, "Sans-B", H("#C62828"), "middle")
    txt(d, xs[2] + 42, 19, "60 s, dobrando até 30 min", 6, "Sans-I", H("#C62828"), "middle")
    linha(d, xs[4] + 42, 82, xs[4] + 42, 50, MUTED, 1, [3, 2])
    txt(d, xs[4] + 42, 40, "15 s sem tecla em", 6, "Sans-I", MUTED, "middle")
    txt(d, xs[4] + 42, 31, "qualquer etapa: dorme", 6, "Sans-I", MUTED, "middle")
    txt(d, xs[3] + 42, 74, "tecla A (nesses 5 s):", 6, "Sans-I", MUTED, "middle")
    txt(d, xs[3] + 42, 66, "trocar senha", 6, "Sans-I", MUTED, "middle")
    return d

# ------------------------------------------------------------------ figura: telas dos displays
def figura_telas():
    d = Drawing(500, 236)
    telas = [("  47  ", "Desafio: digite 4 e depois 7"), ("  4.7  ", "4 aceito (o ponto acende)"),
             ("123___", "Senha: dígitos digitados, _ = falta"), (" OPEn ", "Destravado (5 s)"),
             (" bLOC ", "Bloqueado (depois apaga)"), (" bAt  ", "Bateria fraca (ao acordar)"),
             ("------", "Troca de senha (após a tecla A)"), ("      ", "Apagado: dormindo")]
    for k, (t_, legenda) in enumerate(telas):
        col, lin = k % 2, k // 2
        x, y = 16 + col * 250, 200 - lin * 58
        w = painel(d, x, y, 20, t_)
        txt(d, x + w + 6, y + 13, legenda.split(":")[0] + (":" if ":" in legenda else ""), 6.8, "Sans-B")
        if ":" in legenda:
            txt(d, x + w + 6, y + 3, legenda.split(":", 1)[1].strip(), 6.4, "Sans", MUTED)
    return d

# ------------------------------------------------------------------ figura: ligação do TM1637
def figura_tm1637():
    d = Drawing(500, 150)
    pinos = modulo_tm1637(d, 240, 14, 230, 118, "  47  ", tracejado=False)
    alvos = {"DIO": ("D18", "GPIO18", C["dio"]), "CLK": ("D19", "GPIO19", C["clk"]),
             "VCC": ("3V3", "3,3 V (não 5 V!)", C["v33"]), "GND": ("GND", "terra comum", C["gnd"])}
    for nome, (px, py) in pinos.items():
        rot, sub, cor = alvos[nome]
        fio(d, [px, py, 120, py], cor, 2)
        d.add(Rect(60, py - 6, 58, 12, rx=2, ry=2, fillColor=H("#1D4F8F"), strokeColor=None))
        txt(d, 89, py - 2.5, rot, 6.8, "Mono-B", white, "middle")
        txt(d, 54, py - 2.5, sub, 6, "Sans-I", MUTED, "end")
    txt(d, 89, 92, "ESP32", 7.2, "Sans-B", NAVY, "middle")
    txt(d, 180, 92, "4 fios fêmea-fêmea", 6.2, "Sans-I", MUTED, "middle")
    return d


# ------------------------------------------------------------------ figura: piscadas do desafio (sem display)
def figura_piscadas():
    d = Drawing(500, 110)
    seq = [(200, 1), (250, 0), (200, 1), (250, 0), (200, 1), (1000, 0), (800, 1), (2500, 0)]
    x0, esc, yb, alt = 30, 0.078, 45, 30
    pts = [x0, yb]
    x = x0
    marcas = []
    for dur, on in seq:
        y = yb + alt * on
        pts += [x, y]
        x2 = x + dur * esc
        pts += [x2, y]
        marcas.append((x, x2, on, dur))
        x = x2
    pts += [x, yb]
    d.add(PolyLine(pts, strokeColor=C["led"], strokeWidth=1.8, strokeLineJoin=1))
    linha(d, x0 - 5, yb, x + 20, yb, LINE, 0.6)
    txt(d, x0 - 8, yb + alt - 3, "aceso", 6, "Sans", MUTED, "end")
    txt(d, x0 - 8, yb - 2, "apagado", 6, "Sans", MUTED, "end")
    a1, a2 = marcas[0][0], marcas[4][1]
    linha(d, a1, yb + alt + 12, a2, yb + alt + 12, NAVY, 0.8)
    txt(d, (a1 + a2) / 2, yb + alt + 16, "3 piscadas = dígito 3", 6.6, "Sans-B", NAVY, "middle")
    b1, b2 = marcas[6][0], marcas[6][1]
    linha(d, b1, yb + alt + 12, b2, yb + alt + 12, NAVY, 0.8)
    txt(d, (b1 + b2) / 2, yb + alt + 16, "1 longa = dígito 0", 6.6, "Sans-B", NAVY, "middle")
    for (xa, xb, on, dur) in marcas:
        if not on and dur >= 1000:
            txt(d, (xa + xb) / 2, yb + 8, "pausa %.1f s" % (dur / 1000), 6, "Sans-I", MUTED, "middle")
    txt(d, marcas[0][0] + 7.8, yb - 12, "0,2 s", 5.6, "Sans", MUTED, "middle")
    txt(d, marcas[6][0] + 31, yb - 12, "0,8 s", 5.6, "Sans", MUTED, "middle")
    txt(d, x + 8, yb + 12, "repete…", 6.4, "Sans-I", MUTED)
    txt(d, 250, 8, "Exemplo: desafio “3 0”. Digite 3 e depois 0. O buzzer bipa junto (exceto no modo stealth).",
        6.6, "Sans-I", INK, "middle")
    return d


# ------------------------------------------------------------------ documento
class Guia(BaseDocTemplate):
    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name in ("h1", "h1l", "h2"):
            nivel = 1 if f.style.name == "h2" else 0
            texto = f.getPlainText()
            chave = "sec%d" % id(f)
            self.canv.bookmarkPage(chave)
            self.canv.addOutlineEntry(texto, chave, nivel, closed=nivel > 0)
            self.notify("TOCEntry", (nivel, texto, self.page, chave))


def cabecalho(c, doc):
    w, h = c._pagesize
    c.saveState()
    c.setStrokeColor(NAVY)
    c.setLineWidth(0.8)
    c.line(18 * mm, h - 13 * mm, w - 18 * mm, h - 13 * mm)
    c.setFont("Sans-B", 7.5)
    c.setFillColor(NAVY)
    c.drawString(18 * mm, h - 11.2 * mm, "PROJETO TALOS")
    c.setFont("Sans", 7.5)
    c.setFillColor(MUTED)
    c.drawString(18 * mm + 62, h - 11.2 * mm, "Guia de montagem e operação")
    c.drawRightString(w - 18 * mm, h - 11.2 * mm, "PCS3848 · Sistemas Embarcados · Grupo 7")
    c.setFillColor(ACC)
    c.rect(w / 2 - 10, 9 * mm, 20, 1.2, fill=1, stroke=0)
    c.setFillColor(MUTED)
    c.setFont("Sans", 7.5)
    c.drawCentredString(w / 2, 11 * mm, str(doc.page))
    c.restoreState()


def capa(c, doc):
    w, h = A4
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, h * 0.40, w, h * 0.60, fill=1, stroke=0)
    c.setFillColor(ACC)
    c.rect(0, h * 0.40 - 4, w, 4, fill=1, stroke=0)
    c.setFillColor(H("#9FB3CF"))
    c.setFont("Sans-B", 9)
    c.drawString(22 * mm, h - 28 * mm, "ESCOLA POLITÉCNICA DA USP · PCS3848 SISTEMAS EMBARCADOS")
    c.setFillColor(white)
    c.setFont("Sans-B", 40)
    c.drawString(22 * mm, h - 62 * mm, "Projeto Talos")
    c.setFont("Sans", 17)
    c.drawString(22 * mm, h - 73 * mm, "Cofre eletrônico com ESP32")
    c.setFillColor(ACC)
    c.setFont("Sans-B", 13)
    c.drawString(22 * mm, h - 92 * mm, "Guia de ligação, gravação e operação")
    c.setFillColor(H("#C8D3E3"))
    c.setFont("Sans", 9.5)
    for k, s in enumerate(["Diagrama completo com a placa · pinagem · esquemáticos",
                           "montagem passo a passo · software · testes · solução de problemas"]):
        c.drawString(22 * mm, h - 101 * mm - 13 * k, s)
    # placa ilustrada na capa
    d = Drawing(200, 430)
    placa(d, 30, 360, 22, 140, uso={}, titulo=False)
    c.translate(w - 22 * mm - 150, h * 0.40 + 18)
    c.scale(0.62, 0.62)
    renderPDF.draw(d, c, 0, 0)
    c.restoreState()
    c.saveState()
    c.setFillColor(INK)
    c.setFont("Sans-B", 10)
    y = h * 0.40 - 22 * mm
    c.drawString(22 * mm, y, "Grupo 7")
    c.setFont("Sans", 10)
    for k, s in enumerate(["André Moreno · 13682785", "Felipe Soria · 13864287", "Giovani Sebastianutti · 13680171",
                           "Matheus Guidoni · 12683120"]):
        c.drawString(22 * mm, y - 15 - 14 * k, s)
    c.setFillColor(MUTED)
    c.setFont("Sans", 8.5)
    c.drawString(22 * mm, 30 * mm, "Placa-alvo: ESP32 DevKit V1 (DOIT, 30 pinos) · firmware em src/main.cpp")
    c.drawString(22 * mm, 25 * mm, "São Paulo, outubro de 2026")
    c.restoreState()


def construir():
    doc = Guia(SAIDA, pagesize=A4, title="Projeto Talos — Guia de montagem e operação",
               author="Grupo 7 — PCS3848", subject="Cofre eletrônico com ESP32")
    mr = 18 * mm
    fr = Frame(mr, 16 * mm, A4[0] - 2 * mr, A4[1] - 32 * mm, id="r", leftPadding=0, rightPadding=0)
    L = landscape(A4)
    fl = Frame(12 * mm, 13 * mm, L[0] - 24 * mm, L[1] - 28 * mm, id="l", leftPadding=0, rightPadding=0,
               topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate("capa", [Frame(0, 0, A4[0], A4[1])], onPage=capa),
                          PageTemplate("retrato", [fr], onPage=cabecalho),
                          PageTemplate("paisagem", [fl], onPage=cabecalho, pagesize=L)])
    E = []
    E += [NextPageTemplate("retrato"), PageBreak()]

    # ---------------- sumário
    E.append(Paragraph("Sumário", st("tt", fontName="Sans-B", fontSize=19, leading=23, textColor=NAVY,
                                      spaceAfter=12)))
    toc = TableOfContents()
    toc.levelStyles = [S["toc1"], S["toc2"]]
    toc.dotsMinLevel = 0
    E += [toc, PageBreak()]

    # ---------------- 1 visão geral
    E.append(P("1. Visão geral", "h1"))
    E.append(P("Este guia mostra como montar o hardware do <b>Projeto Talos</b> e gravar o firmware no "
               "<b>ESP32 DevKit V1</b>. O cofre abre uma fechadura solenoide de 12 V quando alguém digita a senha "
               "de 6 dígitos no teclado 4x4. Um módulo de display de 6 dígitos (a caminho) mostra o que está "
               "sendo digitado. Antes da senha, o cofre mostra 2 dígitos aleatórios que precisam ser digitados "
               "primeiro (desafio anti-marcas). Enquanto o display não chega, eles aparecem como piscadas e bipes. Depois de 5 erros seguidos, o teclado fica bloqueado. Sem uso, o ESP32 entra em "
               "<i>deep sleep</i> e os displays apagam."))
    E.append(P("O guia segue a ordem da montagem. Primeiro vem a lista de materiais e a pinagem da placa, "
               "depois o diagrama completo de ligação. Em seguida há um esquemático para cada bloco, "
               "a montagem passo a passo com um teste em cada etapa, e por fim o software, a operação e os "
               "testes de aceitação."))
    E.append(figura_blocos())
    E.append(P("Figura 1 – Blocos do sistema e sinais entre eles.", "cap"))
    E.append(callout("info", "O firmware usa exatamente os pinos deste guia. Se mudar algum pino, altere também "
                             "as constantes no topo de <font name='Mono'>src/main.cpp</font> (§7.6)."))

    # ---------------- 2 materiais
    E.append(P("2. Lista de materiais", "h1"))
    E.append(P("Os quatro primeiros itens já foram comprados (pedido da imagem). Os demais são componentes "
               "baratos e comuns, necessários para ligar a fechadura, o buzzer e a alimentação com segurança."))
    ok, falta, opc = ('<font color="#2E7D32"><b>comprado</b></font>', '<font color="#C62828"><b>comprar</b></font>',
                      '<font color="#5F6B7A"><b>opcional</b></font>')
    E.append(tabela([
        ["Item", "Qtd.", "Para que serve", "Situação"],
        ["Case em MDF Cofre Valorem (cód. 08908)", "1", "Caixa do cofre", ok],
        ["Fechadura solenoide FEC-91 12 V (cód. 09552)", "1", "Trava/destrava a porta", ok],
        ["Teclado matricial de membrana 4x4 (cód. 05621)", "1", "Entrada da senha", ok],
        ["Buzzer ativo 5 V BAT5V 12 mm (cód. 06265)", "1", "Feedback sonoro", ok],
        ["ESP32 DevKit V1 (DOIT, 30 pinos) + cabo micro-USB <b>de dados</b>", "1", "Controlador", falta],
        ["MOSFET IRLZ44N (ou IRLB8721)", "1", "Chaveia os 12 V do solenoide", falta],
        ["Diodo 1N4007", "1", "Proteção contra o pico da bobina", falta],
        ["Transistor BC547 (ou BC337 / 2N2222)", "1", "Chaveia o buzzer", falta],
        ["Resistores: 100 Ω, 1 kΩ, 2× 10 kΩ, 100 kΩ, 330 kΩ", "6", "Gate, base, pull-downs, divisor", falta],
        ["Capacitor 100 nF cerâmico", "1", "Estabiliza a leitura da bateria", falta],
        ["Capacitor eletrolítico 470 µF / 25 V", "1", "Reserva de corrente no acionamento", falta],
        ["Módulo buck LM2596 (ou MP1584)", "1", "12 V → 5 V para o ESP32 e o buzzer", falta],
        ["Bateria 12 V: pack 3S 18650 com BMS (ou fonte 12 V / 2 A)", "1", "Alimentação", falta],
        ["Fusível 2 A + porta-fusível", "1", "Proteção da bateria", opc],
        ["<b>Módulo display 7 segmentos 6 dígitos TM1637</b> (0,56\", com pontos decimais)", "1",
         "Mostrar desafio e senha", '<font color="#E07A1F"><b>comprar</b></font>'],
        ["Protoboard ou placa perfurada, jumpers, bornes KF301", "–", "Interligação", falta],
        ["LED 5 mm + resistor 220 Ω", "1", "Indicador visível de fora do case", opc],
        ["Reed switch + ímã + resistor 10 kΩ", "1", "Detecção de porta fechada", opc],
    ], [205, 30, 170, None]))
    E.append(Spacer(1, 6))
    E.append(callout("tip", "<b>Display recomendado:</b> módulo de <b>6 dígitos com TM1637</b>, de 0,56\" e com "
                            "pontos decimais (procure por “módulo display 6 dígitos TM1637”, padrão RobotDyn). Ele "
                            "usa só <b>2 fios</b> de sinal, multiplexa sozinho e funciona em 3,3 V, então liga direto "
                            "no ESP32 sem nenhum outro componente. Evite os de 4 dígitos com dois-pontos (relógio) e "
                            "o MAX7219 de 8 dígitos, que pede 5 V e nível lógico acima do que o ESP32 garante.",
                     "O QUE COMPRAR"))
    E.append(callout("warn", "O solenoide é de <b>12 V</b> e puxa por volta de 0,5 a 1 A (confira na etiqueta). "
                             "Uma bateria de 3,7 V, como na monografia, não aciona essa fechadura. Por isso o "
                             "sistema roda em 12 V, e o ESP32 recebe 5 V por um conversor buck."))

    # ---------------- 3 pinagem
    E.append(PageBreak())
    E.append(P("3. Pinagem do ESP32 DevKit V1", "h1"))
    E.append(P("A placa tem 15 pinos de cada lado. Os nomes da figura são os mesmos impressos na placa "
               "(<i>silkscreen</i>). Atenção a dois nomes que confundem: <b>RX2 é o GPIO16</b> e "
               "<b>TX2 é o GPIO17</b>. Os pinos coloridos são usados pelo projeto e os cinzas ficam livres."))
    E.append(figura_pinagem())
    E.append(P("Figura 2 – Pinos usados (vista de cima, antena para cima, USB para baixo).", "cap"))
    E.append(callout("danger", "O <b>D12</b> define a tensão da flash no boot: se estiver em HIGH quando a placa "
                               "reinicia, ela não inicia, a menos que o eFuse de 3,3 V esteja gravado (§5.2). Aqui ele "
                               "recebe <b>só o fio do teclado</b>. Não ligue mais nada nele. Os pinos D2, D15, D0 (BOOT) e "
                               "D5 também são de boot; o D2 é usado só como saída para o LED, o que é seguro."))
    E.append(PageBreak())
    E.append(P("3.1 Tabela mestre de ligações", "h2"))
    sw = lambda c: swatch(c)
    E.append(tabela([
        ["Cor", "Pino na placa", "GPIO", "Liga em", "Detalhe"],
        [sw(KP[0]), "D32", "32", "Teclado, fio 1 (L1)", "§5.2"],
        [sw(KP[1]), "D33", "33", "Teclado, fio 2 (L2)", "§5.2"],
        [sw(KP[2]), "D25", "25", "Teclado, fio 3 (L3)", "§5.2"],
        [sw(KP[3]), "D26", "26", "Teclado, fio 4 (L4)", "§5.2"],
        [sw(KP[4]), "D27", "27", "Teclado, fio 5 (C1)", "§5.2"],
        [sw(KP[5]), "D14", "14", "Teclado, fio 6 (C2)", "§5.2"],
        [sw(KP[6]), "D12", "12", "Teclado, fio 7 (C3), e nada mais neste pino", "§5.2"],
        [sw(KP[7]), "D13", "13", "Teclado, fio 8 (C4)", "§5.2"],
        [sw(C["dio"]), "D18", "18", "DIO do módulo display TM1637 (quando chegar)", "§5.5"],
        [sw(C["clk"]), "D19", "19", "CLK do módulo display TM1637 (quando chegar)", "§5.5"],
        [sw(C["lock"]), "RX2", "16", "Resistor 100 Ω → gate do IRLZ44N", "§5.3"],
        [sw(C["buz"]), "TX2", "17", "Resistor 1 kΩ → base do BC547", "§5.4"],
        [sw(C["led"]), "D2", "2", "LED azul da placa (+ LED externo opcional)", "§5.6"],
        [sw(C["bat"]), "VP", "36", "Meio do divisor 330 kΩ / 100 kΩ", "§5.6"],
        [sw(C["door"]), "VN", "39", "Reed switch (opcional)", "§5.6"],
        [sw(C["v5"]), "VIN", "–", "OUT+ do buck (5,0 V)", "§5.1"],
        [sw(C["gnd"]), "GND", "–", "GND comum (bateria, buck, MOSFET, BC547)", "§5.1"],
        [sw(C["v33"]), "3V3", "–", "VCC do display TM1637 e pull-up do reed switch (opcional)", "§5.5/5.6"],
    ], [34, 68, 38, 230, None], destaque_col0=False))

    # ---------------- 4 diagrama completo (paisagem)
    E += [NextPageTemplate("paisagem"), PageBreak()]
    E.append(Paragraph("4. Diagrama completo de ligação", st("h1l", parent=S["h1"], fontSize=15, leading=18,
                                                              spaceAfter=4)))
    E.append(diagrama_completo())
    E += [NextPageTemplate("retrato"), PageBreak()]
    E.append(P("4.1 Como ler o diagrama", "h2"))
    E += bullets([
        "Cada cor de fio tem um significado (veja a legenda no diagrama). Os fios do teclado usam azuis para as "
        "linhas e verdes para as colunas.",
        "Os símbolos <b>+12 V</b>, <b>+5 V</b> e <b>3V3</b> indicam ligação à respectiva alimentação. Todo símbolo "
        "de terra (três traços) é o <b>mesmo GND</b>. Na prática, tudo vai para uma única barra de GND na "
        "protoboard.",
        "Os 8 fios do teclado vão em sequência nos pinos <b>D32 a D13</b>, sem resistores.",
        "O cabo flat aparece dobrado só para manter a ordem dos fios no desenho. Na montagem, basta seguir "
        "a numeração dos fios (1 a 8, da esquerda para a direita com o teclado de frente).",
        "O buzzer aparece ligado por etiquetas, e o esquema completo está no §5.4. O módulo de display, "
        "contornado em laranja tracejado, ainda não chegou: seus fios só serão ligados depois.",
        "Elementos tracejados são opcionais.",
    ])
    E.append(callout("danger", "Antes de energizar: (1) todos os GND interligados; (2) buck ajustado em 5,0 V; "
                               "(3) no D12, só o fio 7 do teclado; (4) resistores de 10 kΩ no gate do MOSFET e na base do BC547 "
                               "(mantêm a fechadura e o buzzer desligados no boot e no deep sleep); (5) VCC do display no <b>3V3</b>.",
                     "CHECKLIST ANTES DE LIGAR"))

    # ---------------- 5 blocos
    E.append(P("5. Ligações por bloco", "h1"))
    E.append(P("5.1 Alimentação", "h2"))
    E.append(P("A bateria de 12 V alimenta diretamente a fechadura. Um conversor buck baixa a tensão para "
               "5 V, que alimenta o pino <b>VIN</b> do ESP32 (o regulador da placa gera os 3,3 V) e o buzzer. O "
               "capacitor de 470 µF perto do MOSFET segura a tensão no instante em que o solenoide liga, o que "
               "evita o reset do ESP32 por queda de tensão (<i>brownout</i>)."))
    E.append(esq_alimentacao())
    E.append(P("Figura 3 – Distribuição de energia. O GND é um só para todo o circuito.", "cap"))
    E.append(callout("danger", "<b>Ajuste o buck antes de ligar o ESP32.</b> Ligue só a bateria no IN+/IN–, meça "
                               "o OUT+/OUT– com o multímetro e gire o trimpot até ler <b>5,0 V</b>. Esses módulos "
                               "costumam vir de fábrica com a saída perto da entrada (12 V), e 12 V no VIN queima "
                               "a placa."))
    E.append(callout("warn", "Não alimente pelo VIN e pelo USB ao mesmo tempo, a não ser que sua placa tenha o "
                             "diodo de proteção no VIN (nem todo clone tem). Para gravar o firmware, desligue "
                             "o 12 V ou use só o USB. Sem 12 V, o teclado e o buzzer funcionam, mas a fechadura "
                             "não aciona."))

    E.append(CondPageBreak(120 * mm))
    E.append(P("5.2 Teclado 4x4", "h2"))
    E.append(P("O teclado tem 8 fios: 4 linhas (L1 a L4) e 4 colunas (C1 a C4). Cada tecla, quando apertada, "
               "liga uma linha a uma coluna. O firmware energiza uma coluna por vez e lê as linhas para "
               "descobrir a tecla. Com o teclado de <b>frente</b> e o cabo para baixo, o fio 1 é o da esquerda."))
    E.append(figura_teclado())
    E.append(P("Figura 4 – Teclado de frente, numeração dos fios e matriz interna. As teclas * e # e a coluna "
               "A–D têm função especial.", "cap"))
    E.append(tabela([
        ["Fio", "Função", "Pino na placa", "GPIO", "Cor sugerida"],
        ["1", "Linha L1 (1 2 3 A)", "D32", "32", swatch(KP[0])],
        ["2", "Linha L2 (4 5 6 B)", "D33", "33", swatch(KP[1])],
        ["3", "Linha L3 (7 8 9 C)", "D25", "25", swatch(KP[2])],
        ["4", "Linha L4 (* 0 # D)", "D26", "26", swatch(KP[3])],
        ["5", "Coluna C1 (1 4 7 *)", "D27", "27", swatch(KP[4])],
        ["6", "Coluna C2 (2 5 8 0)", "D14", "14", swatch(KP[5])],
        ["7", "Coluna C3 (3 6 9 #)", "D12", "12", swatch(KP[6])],
        ["8", "Coluna C4 (A B C D)", "D13", "13", swatch(KP[7])],
    ], [30, 120, 120, 50, None], destaque_col0=True))
    E.append(Spacer(1, 6))
    E.append(callout("tip", "<b>Confirme a numeração com o multímetro</b> (modo continuidade). Aperte e segure "
                            "a tecla <b>1</b>: deve apitar entre os fios <b>1 e 5</b>. Tecla <b>D</b>: fios "
                            "<b>4 e 8</b>. Tecla <b>0</b>: fios <b>4 e 6</b>. Se der o contrário, sua contagem "
                            "começou do lado errado.", "TESTE DE 1 MINUTO"))
    E.append(P("Os 8 fios caem em <b>pinos vizinhos e em ordem</b> no lado esquerdo da placa, do D32 ao D13, então "
               "dá para usar um pente de 8 jumpers lado a lado. Não precisa de resistores: o firmware usa os "
               "pull-downs internos do ESP32."))
    E.append(callout("warn", "<b>Teclas espelhadas?</b> Se você aperta 2 e o cofre lê C (ou aperta 4 e lê #), a "
                             "ordem dos fios ficou invertida: o fio que está no D32 é o 8 do teclado. Isso depende do "
                             "teclado e de como o conector foi contado. Resolva no firmware com "
                             "<font name='Mono'>TECLADO_INVERTIDO</font>: <font name='Mono'>true</font> para os fios na "
                             "ordem 8…1 (como ficou o teclado do grupo, e é o padrão), <font name='Mono'>false</font> "
                             "para a ordem 1…8 do guia.", "TECLADO INVERTIDO"))
    E.append(callout("info", "<b>Para todas as teclas acordarem o cofre</b>, a placa precisa do eFuse que fixa a "
                             "flash em 3,3 V (já gravado na placa do grupo). Sem ele, o D12 é um pino de boot e precisa "
                             "ficar em LOW no deep sleep, então as teclas ligadas a ele não acordam (4, 5, 6 e B com "
                             "<font name='Mono'>TECLADO_INVERTIDO = true</font>). O firmware detecta o eFuse sozinho e "
                             "mostra no serial: <font name='Mono'>D12 livre</font> ou <font name='Mono'>D12 strapping</font>. "
                             "Para gravar numa placa nova com módulo <b>WROOM-32</b> (flash de 3,3 V): "
                             "<font name='Mono'>espefuse.py --port /dev/ttyUSB0 set_flash_voltage 3.3V</font>. "
                             "<b>É irreversível</b>: nunca use 1.8V nem faça isso em módulos com flash de 1,8 V.",
                     "SOBRE O D12 E O EFUSE"))

    E.append(CondPageBreak(110 * mm))
    E.append(P("5.3 Fechadura solenoide (MOSFET)", "h2"))
    E.append(P("O GPIO16 (RX2) liga o MOSFET, que fecha o caminho do solenoide para o GND. Com o GPIO em HIGH, "
               "o solenoide energiza e a lingueta recolhe (destravado). O firmware mantém o solenoide ligado "
               "por 5 s e depois o desliga."))
    E.append(esq_tranca())
    E.append(P("Figura 5 – Driver da fechadura (chaveamento no lado do GND).", "cap"))
    E += bullets([
        "Fio do solenoide <b>sem polaridade</b>: um vai no +12 V e o outro no <b>D</b>reno do MOSFET.",
        "O diodo fica em paralelo com o solenoide, com a <b>faixa (catodo) no +12 V</b>. Invertido, ele causa um "
        "curto quando o MOSFET liga.",
        "O resistor de 10 kΩ do gate ao GND é <b>obrigatório</b>. No deep sleep, o GPIO16 fica solto e, sem esse "
        "resistor, a fechadura pode abrir sozinha.",
        "O IRLZ44N conduz bem com 3,3 V no gate para correntes de até ~1 A. Se esquentar, use o IRLB8721, que "
        "é melhor em 3,3 V.",
    ])

    E.append(CondPageBreak(95 * mm))
    E.append(P("5.4 Buzzer", "h2"))
    E.append(esq_buzzer())
    E.append(P("Figura 6 – Driver do buzzer ativo de 5 V.", "cap"))
    E.append(P("O buzzer é <b>ativo</b>: basta energizar para ele apitar, sempre no mesmo tom. Por isso os "
               "avisos do cofre se diferenciam pelo número e pela duração dos bipes, não pela melodia (§8.4)."))

    E.append(PageBreak())
    E.append(P("5.5 Display de 6 dígitos (TM1637)", "h2"))
    E.append(P("O módulo de display ainda não chegou. O firmware já tem o driver, mas ele fica desligado com "
               "<font name='Mono'>TEM_DISPLAY = false</font>. Até lá, o desafio aparece em piscadas do LED e bipes "
               "(§8.2) e também no monitor serial. Quando o módulo chegar, são só 4 fios:"))
    E.append(figura_tm1637())
    E.append(P("Figura 7 – Ligação do módulo TM1637. A ordem dos pinos no módulo pode variar: siga os nomes "
               "impressos nele.", "cap"))
    E.append(tabela([
        ["Pino do módulo", "Liga em", "Observação"],
        ["VCC", "3V3 do ESP32", "<b>Não use 5 V.</b> Os pull-ups do módulo vão ao VCC e jogariam 5 V nos GPIOs"],
        ["GND", "GND comum", ""],
        ["DIO", "D18 (GPIO18)", "dados"],
        ["CLK", "D19 (GPIO19)", "clock"],
    ], [90, 110, None], destaque_col0=True))
    E.append(Spacer(1, 6))
    E.append(P("<b>Para ativar:</b>", "body"))
    E += numerados([
        "Ligue os 4 fios com a placa desconectada.",
        "Em <font name='Mono'>src/main.cpp</font>, troque <font name='Mono'>TEM_DISPLAY = false</font> por "
        "<font name='Mono'>true</font> e grave (<font name='Mono'>pio run -t upload</font>).",
        "Ao ligar, o desafio aparece no meio do display, por exemplo <font name='Mono'>  47  </font>.",
        "Se os dígitos saírem embaralhados (por exemplo, a ordem 3 2 1 6 5 4), ajuste o vetor "
        "<font name='Mono'>POS_TM</font> logo abaixo dos pinos. Para o brilho, use "
        "<font name='Mono'>BRILHO_DISPLAY</font> (0 a 7).",
    ])
    E.append(callout("danger", "Alimente o módulo pelo <b>3V3</b> da placa, nunca pelo 5 V. Os GPIOs do ESP32 não "
                               "aguentam 5 V, e as linhas DIO e CLK do módulo são puxadas para a tensão do VCC."))

    E.append(CondPageBreak(95 * mm))
    E.append(P("5.6 Bateria, LED e sensor de porta", "h2"))
    E.append(esq_sensores())
    E.append(P("Figura 8 – Divisor de tensão, LED externo e sensor de porta.", "cap"))
    E += bullets([
        "<b>Divisor:</b> com 330 kΩ / 100 kΩ, 12,6 V (bateria cheia) viram 2,93 V no pino, dentro da faixa do "
        "ADC. O firmware avisa abaixo de <b>10,5 V</b>. Os resistores reais variam, então meça a bateria com o "
        "multímetro e ajuste <font name='Mono'>BAT_DIV</font> se a leitura no serial não bater (§7.6).",
        "<b>LED:</b> o LED azul da placa (D2) pisca junto com os bipes, o que ajuda no modo stealth. Para ver de "
        "fora, ligue um LED com 220 Ω no D2 e fure o case.",
        "<b>Reed switch:</b> não foi comprado. Sem ele, a fechadura trava sozinha após 5 s. Se instalar, mude "
        "<font name='Mono'>TEM_SENSOR_PORTA</font> para <font name='Mono'>true</font> e o cofre trava assim que "
        "a porta abrir e fechar de novo. Ele vai no VN (GPIO39), que não tem pull-up interno, por isso o resistor externo de 10 kΩ.",
    ])

    E.append(CondPageBreak(120 * mm))
    E.append(P("5.7 Identificando os terminais", "h2"))
    E.append(figura_componentes())
    E.append(P("Figura 9 – Terminais dos componentes (vista de frente, pernas para baixo). "
               "", "cap"))

    # ---------------- 6 montagem
    E.append(PageBreak())
    E.append(P("6. Montagem passo a passo", "h1"))
    E.append(P("Monte e teste um bloco por vez. Assim, se algo falhar, você sabe exatamente onde procurar. "
               "Faça tudo com a bateria <b>desconectada</b> e só ligue na hora do teste."))
    passos = [
        ("Buck", "Ligue a bateria no IN+/IN– do buck (com o fusível, se tiver). Ajuste o trimpot até "
                 "<b>5,0 V</b> no OUT+/OUT–. Desligue."),
        ("Barramentos", "Na protoboard, crie uma barra de <b>+12 V</b>, uma de <b>+5 V</b> (OUT+ do buck) e uma "
                        "de <b>GND</b>. O OUT– do buck, o negativo da bateria e o IN– ficam todos nessa barra de GND."),
        ("ESP32", "Encaixe a placa no meio da protoboard. Ligue o VIN na barra de +5 V e o GND na barra de GND. "
                  "Teste: ligue a bateria, e o LED vermelho (PWR) deve acender."),
        ("Firmware", "Desligue a bateria, conecte o USB e grave o firmware (§7). No monitor serial deve aparecer "
                     "<font name='Mono'>Talos: boot</font> e um desafio."),
        ("Display (quando chegar)", "Ligue VCC no 3V3, GND, DIO no D18 e CLK no D19 (§5.5). Mude "
                                    "<font name='Mono'>TEM_DISPLAY</font> para true e grave. Teste: o desafio aparece "
                                    "no display."),
        ("Teclado", "Faça o teste de continuidade (§5.2) e ligue os 8 fios em sequência (D32 a D13). Teste: aperte uma tecla, a placa "
                    "acorda e o serial mostra um novo desafio. Digite os 2 dígitos e veja a mensagem "
                    "<font name='Mono'>S3: digite a senha</font>."),
        ("Buzzer", "Monte o BC547, os resistores de 1 kΩ e 10 kΩ e o buzzer (§5.4). Teste: cada tecla dá um "
                   "bipe curto."),
        ("Fechadura", "Monte o MOSFET, os resistores de 100 Ω e 10 kΩ, o diodo e o capacitor de 470 µF (§5.3). "
                      "Ligue os fios do solenoide. Teste com bateria e <b>sem</b> USB: senha "
                      "<font name='Mono'>000000</font> + <b>#</b> deve recolher a lingueta por 5 s."),
        ("Bateria e opcionais", "Monte o divisor com o capacitor de 100 nF. Se for o caso, monte também o LED "
                                "externo e o reed switch (§5.6)."),
        ("Case", "Fixe o teclado na tampa e a fechadura alinhada com o batente. Deixe a bateria acessível pelo "
                 "lado de fora (RF-10), sem expor a eletrônica (RNF-07). Rode os testes do §9."),
    ]
    linhas = [["#", "Etapa", "O que fazer e como testar", "OK"]]
    for k, (a, b) in enumerate(passos, 1):
        linhas.append([str(k), a, b, "☐"])
    t = tabela(linhas, [20, 72, None, 26], destaque_col0=True)
    t.setStyle(TableStyle([("FONTNAME", (3, 1), (3, -1), "Sym"), ("FONTSIZE", (3, 1), (3, -1), 12),
                           ("ALIGN", (3, 0), (3, -1), "CENTER")]))
    E.append(t)
    E.append(Spacer(1, 8))
    E.append(callout("tip", "Corte os fios no tamanho certo e mantenha os de 12 V (fechadura) longe dos fios do "
                            "teclado. Prenda os jumpers no case com fita ou abraçadeira, porque a vibração da "
                            "fechadura solta contatos de protoboard com o tempo."))

    # ---------------- 7 software
    E.append(PageBreak())
    E.append(P("7. Software: compilar e gravar", "h1"))
    E.append(P("O projeto usa o <b>PlatformIO</b>, que baixa sozinho o compilador e as bibliotecas do ESP32 na "
               "primeira compilação (alguns minutos, ~1 GB). Depois disso, gravar leva um comando só."))
    E.append(P("7.1 Opção A: terminal (Linux ou WSL)", "h2"))
    E.append(code("""
sudo apt update && sudo apt install -y pipx git
pipx ensurepath                 # depois feche e abra o terminal
pipx install platformio
git clone https://github.com/AndreMorenoGoveia/talos-project-embedded.git
cd talos-project-embedded
pio run -t upload -t monitor    # compila, grava e abre o serial
"""))
    E.append(P("Para sair do monitor serial, use <b>Ctrl+C</b>. No Linux, se aparecer <i>Permission denied</i> "
               "na porta, rode o comando abaixo uma vez e faça logout/login:"))
    E.append(code("sudo usermod -aG dialout $USER"))
    E.append(P("7.2 Opção B: VS Code (Windows, Linux ou macOS)", "h2"))
    E += numerados([
        "Instale o VS Code e, na aba de extensões, a extensão <b>PlatformIO IDE</b>.",
        "No Windows, instale o driver da ponte USB da placa: <b>CP210x</b> (Silicon Labs) ou <b>CH340</b>, "
        "conforme o chip da sua placa (o nome aparece no Gerenciador de Dispositivos).",
        "Abra a pasta do projeto (<i>File " + ARW + " Open Folder</i>).",
        "Na barra azul inferior, clique em <b>" + '<font name="Sym">✓</font>' + "</b> (Build), depois em <b>"
        + ARW + "</b> (Upload) e por fim no ícone de tomada (Serial Monitor).",
    ])
    E.append(P("7.3 Usando o WSL? Passe o USB para o Linux", "h2"))
    E.append(P("O WSL não enxerga portas USB sozinho. Instale o <b>usbipd-win</b> uma vez e repita o "
               "<i>attach</i> sempre que reconectar a placa. No PowerShell <b>como administrador</b>:"))
    E.append(code("""
winget install --interactive --exact dorssel.usbipd-win
usbipd list                          # ache a linha "CP210x" ou "CH340", ex.: BUSID 1-4
usbipd bind   --busid 1-4            # só na primeira vez
usbipd attach --wsl --busid 1-4      # toda vez que plugar a placa
"""))
    E.append(P("No WSL, confira com <font name='Mono'>ls /dev/ttyUSB*</font>. Alternativa: use a opção B direto "
               "no Windows, sem WSL."))
    E.append(P("7.4 Comandos úteis", "h2"))
    E.append(tabela([
        ["Comando", "O que faz"],
        ["<font name='Mono'>pio run</font>", "Só compila e mostra o uso de memória (Flash ~24%, RAM ~7%)"],
        ["<font name='Mono'>pio run -t upload</font>", "Compila e grava"],
        ["<font name='Mono'>pio device monitor</font>", "Abre o monitor serial (115200 baud)"],
        ["<font name='Mono'>pio device list</font>", "Lista as portas seriais encontradas"],
        ["<font name='Mono'>pio run -t upload --upload-port /dev/ttyUSB0</font>",
         "Grava numa porta específica (no Windows: COM5 etc.)"],
        ["<font name='Mono'>pio run -t erase</font>",
         "Apaga a flash inteira, inclusive senha e bloqueio. Grave de novo em seguida"],
    ], [210, None]))
    E.append(Spacer(1, 6))
    E.append(callout("tip", "Se a gravação parar em <font name='Mono'>Connecting....____</font>, segure o "
                            "botão <b>BOOT</b> da placa até aparecer <i>Writing at 0x…</i>. Se a porta nem "
                            "aparece, troque o cabo: muitos cabos micro-USB só carregam e não transmitem dados."))
    E.append(P("7.5 O que aparece no monitor serial", "h2"))
    E.append(P("No primeiro boot, a memória está vazia e o firmware grava a senha de fábrica <b>000000</b>. "
               "Uma sessão típica:"))
    E.append(code("""
[NVS] sem configuracao valida, usando padrao

Talos: boot (wake=0, stealth=0)
S1/S2: desafio anti-marcas = 4 7          <- digite 4 e 7
S3: digite a senha (6 digitos) e #        <- digite 000000 e #
S5: acesso concedido
S7: trancado
S0: deep sleep                            <- dorme logo após trancar
Talos: boot (wake=3, stealth=0)           <- acordou pelo teclado
"""))
    E.append(P("<font name='Mono'>wake=0</font> indica ligar ou reset, <font name='Mono'>wake=3</font> uma "
               "tecla e <font name='Mono'>wake=4</font> o timer (fim do bloqueio). O serial nunca mostra a "
               "senha."))
    E.append(P("7.6 Ajustando parâmetros", "h2"))
    E.append(P("Todos os parâmetros ficam no topo de <font name='Mono'>src/main.cpp</font>. Depois de mudar, "
               "grave de novo com <font name='Mono'>pio run -t upload</font>."))
    E.append(tabela([
        ["Constante", "Padrão", "Significado"],
        ["T_INAT", "15000 ms", "Sem tecla em qualquer etapa: descarta a entrada e entra em deep sleep"],
        ["T_ACIO", "5000 ms", "Tempo com a fechadura destravada"],
        ["N_TENT", "5", "Senhas erradas seguidas até o bloqueio"],
        ["T_LOCK / T_MAX", "60 s / 30 min", "Bloqueio inicial e teto (dobra a cada bloqueio)"],
        ["W_REC", "15 min", "Janela em que um novo bloqueio conta como consecutivo"],
        ["DESAFIO_CONTA_FALHA", "false", "Errar o desafio conta como tentativa?"],
        ["TEM_SENSOR_PORTA", "false", "Ative se instalar o reed switch"],
        ["TEM_DISPLAY", "false", "Ative quando ligar o módulo TM1637"],
        ["TECLADO_INVERTIDO", "true", "Fios do teclado na ordem 8…1 (true) ou 1…8 (false); veja o §5.2"],
        ["DEBUG_TECLADO", "false", "Mostra cada tecla no serial (revela a senha: só para diagnóstico)"],
        ["BRILHO_DISPLAY / POS_TM", "4 / {2,1,0,5,4,3}", "Brilho (0–7) / ordem dos dígitos no módulo"],
        ["V_LOW / BAT_DIV", "10,5 V / 4,3", "Limiar de bateria fraca / razão do divisor (calibre)"],
    ], [120, 80, None]))

    # ---------------- 8 operação
    E.append(PageBreak())
    E.append(P("8. Operação", "h1"))
    E.append(figura_fluxo())
    E.append(P("Figura 10 – Uso normal do cofre.", "cap"))
    E.append(P("8.1 Teclas", "h2"))
    E.append(tabela([
        ["Tecla", "Função"],
        ["0 – 9", "Dígitos do desafio e da senha. Qualquer tecla acorda o cofre (com o eFuse, §5.2)"],
        ["*", "Limpar: apaga o que foi digitado (age ao <b>soltar</b> a tecla)"],
        ["#", "Confirmar: só aceita com exatamente 6 dígitos (age ao <b>soltar</b>)"],
        ["A", "Trocar a senha: aperte durante os 5 s em que a tranca está aberta"],
        ["* e # juntos por 3 s", "Liga/desliga o modo stealth (sem som). O LED pisca 2 vezes para confirmar"],
        ["B, C, D", "Sem função (bipe de entrada inválida)"],
    ], [110, None], destaque_col0=True))
    E.append(P("8.2 Lendo o desafio anti-marcas", "h2"))
    E.append(P("Ao acordar, o cofre sorteia 2 dígitos. Digite esses 2 dígitos e então a senha. Como os dígitos "
               "mudam a cada vez, todas as teclas se desgastam por igual e as marcas de uso não entregam a senha."))
    E.append(P("<b>Agora, sem display:</b> cada dígito é um grupo de piscadas do LED com bipes, e o 0 é uma piscada "
               "longa. O padrão se repete até você começar a digitar. Os dígitos também saem no monitor serial."))
    E.append(figura_piscadas())
    E.append(P("Figura 11 – Desafio em piscadas (sem display).", "cap"))
    E.append(P("<b>Com o display (TEM_DISPLAY = true):</b> o desafio aparece no meio do display e as piscadas "
               "deixam de ser usadas."))
    E.append(figura_telas())
    E.append(P("Figura 12 – Telas do display.", "cap"))
    E.append(callout("warn", "O display mostra os dígitos reais da senha enquanto ela é digitada. Isso facilita "
                             "o uso, mas qualquer pessoa ao lado consegue ler. Cubra o display com a mão ao digitar."))
    E.append(P("8.3 Trocar a senha", "h2"))
    E += numerados([
        "Abra o cofre normalmente (desafio + senha atual + #).",
        "Enquanto a tranca está aberta (5 s), aperte <b>A</b>. A tranca fecha na hora e começa a troca. O display mostra <font name='Mono'>------</font> (sem display: bipe "
        "duplo curto).",
        "Digite a senha <b>atual</b> + <b>#</b>. Se estiver errada, conta como tentativa.",
        "Digite a senha <b>nova</b> + <b>#</b> e depois repita a nova + <b>#</b>.",
        "Três bipes crescentes indicam que a senha foi salva. Dois bipes indicam que as duas digitações não "
        "conferem, e a senha antiga continua valendo.",
    ])
    E.append(P("8.4 Sons e sinais", "h2"))
    E.append(tabela([
        ["Situação", "Som (e LED)"],
        ["Tecla aceita", "1 bipe curto"],
        ["Pronto para a senha / entrada inválida / # com menos de 6 dígitos", "2 bipes curtíssimos"],
        ["Desafio ou senha errados", "2 bipes curtos"],
        ["Acesso concedido", "3 bipes, cada um mais longo"],
        ["Bloqueio", "1 bipe longo (1,5 s)"],
        ["Bateria fraca (ao acordar)", "5 bipes rápidos"],
        ["Modo stealth ligado/desligado", "LED pisca 2 vezes, sem som"],
        ["Bateria fraca / bloqueio / destravado", "Com display: bAt / bLOC / OPEn"],
    ], [260, None]))
    E.append(Spacer(1, 6))
    E.append(P("8.5 Bloqueio", "h2"))
    E.append(P("Na 5ª senha errada seguida, o cofre bloqueia por 60 s. Se outro bloqueio acontecer até 15 min "
               "depois do fim do anterior, o tempo dobra (120 s, 240 s…) até 30 min. Durante o bloqueio, o "
               "ESP32 dorme e <b>o teclado não o acorda</b>. Quando o tempo acaba, aperte qualquer tecla. "
               "Tirar a bateria ou dar reset não zera o bloqueio, porque ele fica salvo na memória flash."))
    E.append(callout("info", "Esqueceu a senha? Conecte o USB e rode <font name='Mono'>pio run -t erase</font> "
                             "seguido de <font name='Mono'>pio run -t upload</font>. A senha volta a ser "
                             "<b>000000</b>. Como isso exige abrir o cofre, é seguro."))

    # ---------------- 9 testes
    E.append(CondPageBreak(120 * mm))
    E.append(P("9. Testes de aceitação", "h1"))
    E.append(P("Estes testes seguem a Tabela 9 da monografia. Marque cada um depois da montagem final."))
    testes = [
        ["T-01", "RF-01", "Aperte cada tecla uma vez e depois segure uma tecla.", "Um bipe por toque. Segurar não repete."],
        ["T-02", "RF-02", "Após o desafio, digite 3 dígitos e espere 15 s.", "Entrada descartada e o cofre dorme."],
        ["T-03", "RF-15", "Digite 4 dígitos e aperte #.", "2 bipes curtíssimos. Não valida nem destrava."],
        ["T-04", "RF-03", "Erre a senha 5 vezes seguidas.", "Bipe longo. Teclado ignorado por 60 s."],
        ["T-05", "RF-04", "Provoque 2 bloqueios seguidos (até 15 min).", "Serial: o 2º dura 120 s."],
        ["T-06", "RF-07", "Tente digitar a senha sem acertar o desafio.", "Dígito errado reinicia o desafio."],
        ["T-07", "RF-14", "Segure * e # por 3 s e use o cofre.", "Nenhum som. Só o LED funciona."],
        ["T-08", "RF-11", "Alimente com fonte ajustável em 10 V.", "5 bipes rápidos ao acordar."],
        ["T-09", "RF-16", "Troque a senha, tire a bateria e religue.", "A senha nova continua valendo."],
        ["T-11", "RF-17", "Com reed instalado: abra e feche a porta.", "Trava ao fechar, antes dos 5 s."],
        ["T-12", "RF-05", "Fluxo completo: acordar, desafio, senha, #.", "Destrava 5 s com 3 bipes crescentes."],
        ["Extra", "RF-07", "Com display: digite 888888 após o desafio.", "Todos os segmentos acendem por igual."],
    ]
    linhas = [["ID", "Req.", "Procedimento", "Resultado esperado", "OK"]] + [t_ + ["☐"] for t_ in testes]
    t = tabela(linhas, [34, 38, 190, None, 26], destaque_col0=True)
    t.setStyle(TableStyle([("FONTNAME", (4, 1), (4, -1), "Sym"), ("FONTSIZE", (4, 1), (4, -1), 12),
                           ("ALIGN", (4, 0), (4, -1), "CENTER")]))
    E.append(t)
    E.append(Spacer(1, 8))
    E.append(callout("tip", "Para os testes de bloqueio, deixe o monitor serial aberto: ele mostra a duração de "
                            "cada bloqueio e o contador de falhas."))

    # ---------------- 10 problemas
    E.append(P("10. Solução de problemas", "h1"))
    E.append(tabela([
        ["Sintoma", "Causa provável", "O que fazer"],
        ["Gravação para em “Connecting…”", "Placa não entrou em modo de gravação", "Segure BOOT durante a gravação"],
        ["Porta serial não aparece", "Cabo só de carga, driver ou WSL", "Troque o cabo, instale CP210x/CH340, use "
                                                                         "usbipd attach (§7.3)"],
        ["Permission denied em /dev/ttyUSB0", "Usuário fora do grupo dialout", "§7.1, depois logout/login"],
        ["Placa não inicia / reinicia em loop", "Algo além do fio 7 no D12, ou 12 V no VIN", "Deixe só o teclado no D12. Meça o buck"],
        ["Teclas trocadas (aperto 1, sai outra)", "Ordem dos fios invertida", "Teste de continuidade (§5.2)"],
        ["Uma linha ou coluna inteira não responde", "Fio solto ou no pino errado", "Confira a tabela do §5.2"],
        ["Tecla não acorda a placa", "Placa sem o eFuse de 3,3 V: normal para as 4 teclas do D12", "Use outra tecla ou grave o eFuse (§5.2)"],
        ["Teclas espelhadas (aperta 2, lê C)", "Ordem dos 8 fios invertida", "Troque TECLADO_INVERTIDO (§5.2)"],
        ["Fechadura não aciona", "Sem 12 V, GND separado, MOSFET invertido",
         "GND comum. MOSFET com as letras para você: G D S"],
        ["Fechadura abre sozinha / no boot", "Falta o 10 kΩ do gate ao GND", "Coloque o resistor (§5.3)"],
        ["ESP32 reinicia ao destravar", "Queda de tensão (brownout)", "Diodo no lugar, capacitor de 470 µF, bateria "
                                                                    "carregada"],
        ["Buzzer apita durante o sono", "Falta o 10 kΩ da base ao GND", "Coloque o resistor (§5.4)"],
        ["Alerta de bateria fraca falso", "Divisor fora do valor", "Calibre BAT_DIV com o multímetro"],
        ["Sem som nenhum", "Modo stealth ligado", "Segure * e # por 3 s"],
        ["Display apagado", "TEM_DISPLAY = false, sem 3V3, DIO e CLK trocados", "§5.5"],
        ["Dígitos fora de ordem", "Módulo com outra ordem interna", "Ajuste POS_TM (§5.5)"],
        ["Display com lixo ou travado", "Fios longos ou mal encaixados", "Fios curtos (< 20 cm), conectores firmes"],
        ["Teclado ignorado após erros", "Bloqueio ativo", "Espere (o serial mostra o tempo) e aperte uma tecla"],
    ], [130, 140, None]))

    # ---------------- 11 consumo
    E.append(P("11. Consumo e limitações conhecidas", "h1"))
    E += bullets([
        "<b>Autonomia:</b> a meta de 2 anos da monografia pressupõe ~10 µA em repouso. A DevKit V1 sozinha gasta "
        "alguns mA mesmo em deep sleep, por causa do LED PWR, do regulador AMS1117 e do chip USB, e o LM2596 "
        "soma mais alguns mA. Com um pack de 2500 mAh, isso dá algumas semanas. Para chegar perto da meta, "
        "use um módulo ESP32 sem a placa de desenvolvimento (ou remova o LED PWR) e um regulador de baixo "
        "consumo (por exemplo, MP1584 ou HT7333 alimentado por um conversor de baixa corrente quiescente).",
        "<b>Display:</b> o driver do TM1637 já está no firmware e foi compilado, mas só será testado no hardware "
        "quando o módulo chegar. Até lá, o desafio sai em piscadas, bipes e no serial.",
        "<b>Melodia:</b> o buzzer ativo tem um único tom. A “melodia ascendente” do RF-08 virou bipes de "
        "duração crescente.",
        "<b>Troca de senha por jumper:</b> não implementada. A troca é feita pela tecla A logo depois de "
        "autenticar (RF-06).",
        "<b>Aleatoriedade:</b> com Wi-Fi e Bluetooth desligados, o gerador do ESP32 é pseudoaleatório. Isso "
        "basta para espalhar o desgaste das teclas, mas não serve para criptografia.",
    ])
    doc.multiBuild(E)


if __name__ == "__main__":
    construir()
    print("gerado:", SAIDA)

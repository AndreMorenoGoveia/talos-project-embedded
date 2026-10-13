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
            "GPIO14", "GPIO12", "GPIO13", "terra", "entrada (bateria)"]
GPIO_DIR = ["GPIO23", "GPIO22", "GPIO1", "GPIO3", "GPIO21", "GPIO19", "GPIO18", "GPIO5", "GPIO17", "GPIO16",
            "GPIO4", "GPIO2", "GPIO15", "terra", "3,3 V saída"]

USO = {  # (lado, índice) -> cor do fio
    ("L", 1): C["bat"], ("L", 2): C["door"], ("L", 5): KP[0], ("L", 6): KP[1], ("L", 7): KP[2], ("L", 8): KP[3],
    ("L", 9): KP[4], ("L", 10): KP[5], ("L", 11): KP[6], ("L", 12): KP[7], ("L", 13): C["gnd"], ("L", 14): C["v12"],
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
    bandeira(d, 262, 432, "+9 V", C["v12"])
    res_h(d, 196, 262, y, "100 kΩ", "R2")
    terra(d, 196, y)
    txt(d, 300, y + 6, "bateria (ADC)", 5.8, "Sans-I", C["bat"], "middle")

    # ---- sensor de porta (opcional)
    x, y = pad("L", 2)
    fio(d, [x, y, 300, y], C["door"], dash=[3, 2])
    etiqueta(d, 300, y, "sensor da porta (opc., §5.6)", C["door"], "end")

    # ---- alimentação: bateria 9 V direto no VIN
    xg, yg = pad("L", 13)
    xv, yv = pad("L", 14)
    b = bateria9v(d, 40, 12, 100, 46, mais_em_cima=False)
    txt(d, 90, 66, "Bateria 9 V", 7.2, "Sans-B", NAVY, "middle")
    fio(d, [b["+"][0], b["+"][1], 312, b["+"][1], 312, yv, xv, yv], C["v12"], 2.2)
    fio(d, [b["-"][0], b["-"][1], 300, b["-"][1], 300, yg, xg, yg], C["gnd"], 2.2)
    txt(d, 230, b["+"][1] + 4, "+9 V → VIN", 6.4, "Sans-B", C["v12"], "middle")
    txt(d, 230, b["-"][1] + 4, "– → GND", 6.4, "Sans-B", C["gnd"], "middle")

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

    # ---- fechadura: bloco (montagem detalhada na §4.3)
    x, y = pad("R", 9)
    fio(d, [x, y, 566, y], C["lock"])
    txt(d, 500, y + 4, "GPIO16", 5.6, "Sans-I", C["lock"], "middle")
    bx, by = 566, 100
    d.add(Rect(bx, by, 200, 112, rx=6, ry=6, fillColor=H("#F7F8FA"), strokeColor=C["lock"], strokeWidth=1.2))
    txt(d, bx + 100, by + 100, "FECHADURA (detalhe: §4.3)", 6.8, "Sans-B", C["lock"], "middle")
    to220(d, bx + 40, by + 48, "IRLZ44N")
    resistor_fis(d, bx + 70, by + 20, bx + 70, by + 70, "10 kΩ")
    diodo_fis(d, bx + 92, by + 20, bx + 92, by + 70)
    fechadura_fis(d, bx + 104, by + 22)
    d.add(Rect(bx - 3, y - 4, 7, 8, fillColor=H("#D9B44A"), strokeColor=None))
    txt(d, bx + 7, y - 13, "sinal", 5.6, "Sans-I", MUTED)
    for yy, rot, cor in [(150, "+9 V", C["v12"]), (124, "GND", C["gnd"])]:
        linha(d, bx - 10, yy, bx, yy, cor, 1.8)
        etiqueta(d, bx - 10, yy, rot, cor, "end")

    # ---- buzzer direto no TX2
    x, y = pad("R", 8)
    bz = buzzer_fis(d, 524, 240, 10)
    fio(d, [x, y, bz["+"][0], y, bz["+"][0], bz["+"][1]], C["buz"])
    fio(d, [bz["-"][0], bz["-"][1], bz["-"][0] + 14, bz["-"][1]], C["gnd"], 1.6)
    etiqueta(d, bz["-"][0] + 14, bz["-"][1], "GND", C["gnd"])
    txt(d, 511, 237, "Buzzer", 6.4, "Sans-B", INK, "end")

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
    itens = [(C["v12"], "+9 V (bateria)"), (C["gnd"], "GND (terra comum)"),
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
    for k, s_ in enumerate(["GND é um só ponto.", "Bateria 9 V no VIN", "(nunca no 3V3).",
                            "10 kΩ no gate:", "obrigatório.", "Diodo: faixa no +.", "Display no 3V3."]):
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
                 13: ("GND comum (– da bateria)", C["gnd"]), 14: ("+9 V da bateria", C["v12"])}
    funcs_dir = {5: ("display: CLK (TM1637)", C["clk"]), 6: ("display: DIO (TM1637)", C["dio"]),
                 8: ("buzzer (+)", C["buz"]), 9: ("tranca (gate do MOSFET)", C["lock"]),
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
def esq_sensores():
    d = Drawing(500, 175)
    # divisor
    txt(d, 70, 160, "Leitura da bateria", 7.5, "Sans-B", NAVY, "middle")
    bandeira(d, 70, 135, "+9 V", C["v12"])
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
    txt(d, 70, 4, "9,6 V → 2,23 V no pino", 6.2, "Sym", MUTED, "middle")
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
# ------------------------------------------------------------------ componentes desenhados (vista real)
FAIXAS = {"10 kΩ": ["#8B4513", "#111111", "#F28C28"], "100 kΩ": ["#8B4513", "#111111", "#E8C21A"],
          "330 kΩ": ["#F28C28", "#F28C28", "#E8C21A"], "220 Ω": ["#D62828", "#D62828", "#8B4513"]}


def resistor_fis(d, x1, y1, x2, y2, valor):
    """Resistor de verdade (corpo bege com faixas de cor) entre dois pontos."""
    linha(d, x1, y1, x2, y2, H("#9AA3AE"), 1.4)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    vert = abs(x2 - x1) < abs(y2 - y1)
    w, h = (9, 26) if vert else (26, 9)
    d.add(Rect(mx - w / 2, my - h / 2, w, h, rx=4, ry=4, fillColor=H("#E9D3A8"), strokeColor=H("#B89B6A"),
               strokeWidth=0.6))
    for pos, cor in zip([-7, -3, 1, 7], FAIXAS[valor] + ["#C9A227"]):
        if vert:
            d.add(Rect(mx - w / 2, my - pos - 1.2, w, 2.4, fillColor=H(cor), strokeColor=None))
        else:
            d.add(Rect(mx + pos - 1.2, my - h / 2, 2.4, h, fillColor=H(cor), strokeColor=None))


def diodo_fis(d, x1, y1, x2, y2):
    """Diodo 1N4007 de verdade: corpo preto, faixa prateada (catodo) do lado de (x2, y2)."""
    linha(d, x1, y1, x2, y2, H("#9AA3AE"), 1.4)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    vert = abs(x2 - x1) < abs(y2 - y1)
    w, h = (9, 22) if vert else (22, 9)
    d.add(Rect(mx - w / 2, my - h / 2, w, h, rx=2, ry=2, fillColor=H("#1C1C1C"), strokeColor=None))
    sx = 1 if (x2 > x1 if not vert else y2 > y1) else -1
    if vert:
        d.add(Rect(mx - w / 2, my + sx * 6 - 1.6, w, 3.2, fillColor=H("#D0D4D9"), strokeColor=None))
    else:
        d.add(Rect(mx + sx * 6 - 1.6, my - h / 2, 3.2, h, fillColor=H("#D0D4D9"), strokeColor=None))


def to220(d, cx, yb, nome="IRLZ44N"):
    """MOSFET em TO-220 de frente, pernas para baixo. Retorna as pontas das pernas G, D, S."""
    d.add(Rect(cx - 18, yb + 30, 36, 16, fillColor=H("#C9CED4"), strokeColor=H("#7D8790"), strokeWidth=0.8))
    d.add(Circle(cx, yb + 38, 3.5, fillColor=white, strokeColor=H("#7D8790"), strokeWidth=0.8))
    d.add(Rect(cx - 18, yb, 36, 30, fillColor=H("#1C1C1C"), strokeColor=None))
    txt(d, cx, yb + 17, nome, 5.4, "Sans-B", H("#BBBBBB"), "middle")
    pernas = {}
    for k, rot in enumerate("GDS"):
        x = cx - 12 + 12 * k
        d.add(Rect(x - 1.5, yb - 20, 3, 20, fillColor=H("#C9CED4"), strokeColor=H("#7D8790"), strokeWidth=0.4))
        txt(d, x, yb + 4, rot, 6, "Sans-B", white, "middle")
        pernas[rot] = (x, yb - 20)
    return pernas


def bateria9v(d, x, y, w=96, h=46, mais_em_cima=True):
    """Bateria 9 V com clip. Terminais saem pela direita. Retorna {'+': (x, y), '-': (x, y)}."""
    d.add(Rect(x + 2, y - 2, w, h, rx=4, ry=4, fillColor=H("#0B0B0B"), strokeColor=None))
    d.add(Rect(x, y, w, h, rx=4, ry=4, fillColor=H("#1E1E1E"), strokeColor=H("#000000"), strokeWidth=0.8))
    d.add(Rect(x, y + h * 0.28, w * 0.72, h * 0.44, fillColor=H("#E8B923"), strokeColor=None))
    txt(d, x + w * 0.36, y + h / 2 - 5, "9V", 14, "Sans-B", H("#1E1E1E"), "middle")
    d.add(Rect(x + w, y + 4, 12, h - 8, rx=2, ry=2, fillColor=H("#2B2B2B"), strokeColor=None))
    ym, yn = (y + h * 0.7, y + h * 0.3) if mais_em_cima else (y + h * 0.3, y + h * 0.7)
    txt(d, x + w + 16, ym + 3, "+", 9, "Sans-B", C["v12"])
    txt(d, x + w + 16, yn + 3, "–", 9, "Sans-B", INK)
    return {"+": (x + w + 12, ym), "-": (x + w + 12, yn)}


def buzzer_fis(d, cx, cy, r=13):
    """Buzzer visto de cima, pernas para baixo: + (mais longa) à esquerda."""
    d.add(Circle(cx, cy, r, fillColor=H("#1C1C1C"), strokeColor=H("#000000"), strokeWidth=0.8))
    d.add(Circle(cx, cy, r * 0.28, fillColor=H("#555555"), strokeColor=None))
    txt(d, cx - r * 0.55, cy + r * 0.3, "+", 8, "Sans-B", white, "middle")
    linha(d, cx - 4, cy - r, cx - 4, cy - r - 14, H("#9AA3AE"), 1.6)
    linha(d, cx + 4, cy - r, cx + 4, cy - r - 10, H("#9AA3AE"), 1.6)
    return {"+": (cx - 4, cy - r - 14), "-": (cx + 4, cy - r - 10)}


def fechadura_fis(d, x, y):
    """Fechadura solenoide FEC-91 com os 2 fios saindo pela esquerda (sem polaridade)."""
    d.add(Rect(x, y, 66, 44, rx=2, ry=2, fillColor=H("#C9CED4"), strokeColor=H("#7D8790"), strokeWidth=1))
    d.add(Rect(x + 4, y + 4, 36, 36, fillColor=H("#AEB5BD"), strokeColor=H("#8C949D"), strokeWidth=0.6))
    p = Path(fillColor=H("#E8EBEE"), strokeColor=H("#7D8790"), strokeWidth=0.8)
    p.moveTo(x + 66, y + 12); p.lineTo(x + 80, y + 12); p.lineTo(x + 88, y + 26); p.lineTo(x + 66, y + 32)
    p.closePath()
    d.add(p)
    txt(d, x + 22, y + 19, "FEC-91", 6, "Sans-B", H("#3A4350"), "middle")
    return {"a": (x, y + 10), "b": (x, y + 34)}


def pino_esp(d, x, y, rot, sub=""):
    """Caixinha azul representando um pino da placa ESP32. Retorna a ponta direita."""
    d.add(Rect(x, y - 6, 58, 12, rx=2, ry=2, fillColor=H("#1D4F8F"), strokeColor=None))
    txt(d, x + 29, y - 2.5, rot, 6.8, "Mono-B", white, "middle")
    if sub:
        txt(d, x + 29, y - 15, sub, 5.6, "Sans-I", MUTED, "middle")
    return x + 58, y


def ponte(d, x, y, cor, cor_baixo, w=1.9):
    """Fio horizontal passando por cima de um fio vertical em (x, y) (salto)."""
    d.add(Rect(x - 5, y - 2, 10, 4, fillColor=white, strokeColor=None))
    linha(d, x, y - 3, x, y + 3, cor_baixo, w)
    p = Path(strokeColor=cor, strokeWidth=w, fillColor=None, strokeLineCap=1)
    p.moveTo(x - 5, y); p.curveTo(x - 5, y + 7, x + 5, y + 7, x + 5, y)
    d.add(p)


# ------------------------------------------------------------------ figuras de montagem por bloco
def figura_alimentacao():
    d = Drawing(493, 110)
    b = bateria9v(d, 30, 30, 104, 50, mais_em_cima=True)
    txt(d, 82, 92, "Bateria 9 V", 7.4, "Sans-B", NAVY, "middle")
    xv, yv = pino_esp(d, 380, b["+"][1], "VIN")
    xg, yg = pino_esp(d, 380, b["-"][1], "GND")
    fio(d, [b["+"][0], b["+"][1], 380, b["+"][1]], C["v12"], 2.2)
    fio(d, [b["-"][0], b["-"][1], 380, b["-"][1]], C["gnd"], 2.2)
    txt(d, 409, 92, "ESP32", 7.4, "Sans-B", NAVY, "middle")
    txt(d, 200, b["+"][1] + 4, "fio vermelho (+)", 6.2, "Sans-I", C["v12"])
    txt(d, 200, b["-"][1] + 4, "fio preto (–)", 6.2, "Sans-I", INK)
    ponto(d, 300, b["+"][1], C["v12"])
    ponto(d, 320, b["-"][1], C["gnd"])
    fio(d, [300, b["+"][1], 300, 100], C["v12"], 1.6)
    etiqueta(d, 304, 100, "+9 V → fechadura (§4.3)", C["v12"])
    fio(d, [320, b["-"][1], 320, 8], C["gnd"], 1.6)
    etiqueta(d, 324, 8, "GND → fechadura e buzzer", C["gnd"])
    return d


def figura_fechadura():
    d = Drawing(493, 200)
    xs, ys = pino_esp(d, 4, 108, "RX2", "GPIO16")
    xg, yg = pino_esp(d, 4, 30, "GND")
    m = to220(d, 200, 128)
    txt(d, 224, 150, "letras", 5.8, "Sans-I", MUTED)
    txt(d, 224, 143, "para você", 5.8, "Sans-I", MUTED)
    fio(d, [xs, ys, m["G"][0], ys, m["G"][0], m["G"][1]], C["lock"], 1.9)
    ponto(d, 150, ys, C["lock"])
    resistor_fis(d, 150, ys, 150, 30, "10 kΩ")
    txt(d, 158, 72, "10 kΩ", 6.6, "Sans-B")
    txt(d, 158, 64, "(marrom, preto,", 5.6, "Sans-I", MUTED)
    txt(d, 158, 57, "laranja)", 5.6, "Sans-I", MUTED)
    fio(d, [xg, 30, 472, 30], C["gnd"], 2.2)
    txt(d, 70, 34, "GND comum", 6, "Sans-B", C["gnd"])
    fio(d, [m["S"][0], m["S"][1], m["S"][0], 30], C["gnd"], 1.9)
    ponto(d, m["S"][0], 30, C["gnd"])
    cinza = H("#555555")
    fio(d, [m["D"][0], m["D"][1], m["D"][0], 62, 290, 62], cinza, 1.9)
    ponte(d, m["S"][0], 62, cinza, C["gnd"])
    f = fechadura_fis(d, 300, 52)
    linha(d, 290, 62, f["a"][0], f["a"][1], cinza, 1.9)
    fio(d, [262, 96, 290, 96, 290, f["b"][1], f["b"][0], f["b"][1]], C["v12"], 1.9)
    ponto(d, 262, 62, cinza)
    ponto(d, 262, 96, C["v12"])
    diodo_fis(d, 262, 62, 262, 96)
    txt(d, 252, 82, "1N4007", 6.4, "Sans-B", INK, "end")
    txt(d, 252, 74, "faixa para", 5.6, "Sans-I", MUTED, "end")
    txt(d, 252, 67, "o lado do +", 5.6, "Sans-I", MUTED, "end")
    txt(d, 333, 108, "Fechadura (sem polaridade)", 6.4, "Sans-B", INK, "middle")
    bt = bateria9v(d, 360, 120, 90, 44, mais_em_cima=True)
    fio(d, [262, 96, 262, 190, 480, 190, 480, bt["+"][1], bt["+"][0], bt["+"][1]], C["v12"], 1.9)
    fio(d, [bt["-"][0], bt["-"][1], 472, bt["-"][1], 472, 30], C["gnd"], 1.9)
    txt(d, 405, 170, "Bateria 9 V", 6.6, "Sans-B", NAVY, "middle")
    txt(d, 370, 194, "+9 V (o mesmo + que vai no VIN)", 6, "Sans-I", C["v12"], "middle")
    txt(d, 200, 196, "MOSFET IRLZ44N", 6.8, "Sans-B", NAVY, "middle")
    return d


def figura_buzzer():
    d = Drawing(493, 84)
    xs, ys = pino_esp(d, 4, 42, "TX2", "GPIO17")
    xg, yg = pino_esp(d, 4, 14, "GND")
    bz = buzzer_fis(d, 170, 70, 13)
    fio(d, [xs, ys, bz["+"][0], ys, bz["+"][0], bz["+"][1]], C["buz"], 1.9)
    fio(d, [bz["-"][0], bz["-"][1], bz["-"][0], yg, xg, yg], C["gnd"], 1.9)
    txt(d, 192, 74, "Buzzer ativo", 6.8, "Sans-B")
    txt(d, 192, 65, "perna longa (+) no TX2", 6, "Sans-I", MUTED)
    txt(d, 192, 57, "perna curta (–) no GND", 6, "Sans-I", MUTED)
    return d


def figura_componentes():
    """Como identificar os terminais de cada peça."""
    d = Drawing(493, 150)
    to220(d, 50, 70)
    txt(d, 50, 130, "MOSFET IRLZ44N", 7, "Sans-B", NAVY, "middle")
    for k, s_ in enumerate(["G = gate (RX2)", "D = dreno (fechadura)", "S = fonte (GND)"]):
        txt(d, 12, 36 - 9 * k, s_, 6, "Sans", INK)
    diodo_fis(d, 120, 90, 190, 90)
    txt(d, 155, 130, "Diodo 1N4007", 7, "Sans-B", NAVY, "middle")
    txt(d, 155, 72, "faixa prateada = catodo", 6, "Sans", INK, "middle")
    txt(d, 155, 63, "vai no lado do +9 V", 6, "Sans-I", MUTED, "middle")
    resistor_fis(d, 220, 90, 290, 90, "10 kΩ")
    txt(d, 255, 130, "Resistor 10 kΩ", 7, "Sans-B", NAVY, "middle")
    txt(d, 255, 72, "marrom, preto, laranja", 6, "Sans", INK, "middle")
    txt(d, 255, 63, "sem polaridade", 6, "Sans-I", MUTED, "middle")
    buzzer_fis(d, 345, 98, 14)
    txt(d, 345, 130, "Buzzer", 7, "Sans-B", NAVY, "middle")
    txt(d, 345, 58, "perna longa / '+' = TX2", 6, "Sans", INK, "middle")
    bateria9v(d, 395, 74, 72, 36)
    txt(d, 437, 130, "Bateria 9 V", 7, "Sans-B", NAVY, "middle")
    txt(d, 437, 58, "clip: vermelho = +", 6, "Sans", INK, "middle")
    txt(d, 437, 49, "preto = –", 6, "Sans", INK, "middle")
    return d


def figura_blocos():
    d = Drawing(493, 190)

    def bloco(x, y, w, h, t1, t2, cor):
        d.add(Rect(x, y, w, h, rx=5, ry=5, fillColor=H("#FFFFFF"), strokeColor=cor, strokeWidth=1.4))
        d.add(Rect(x, y + h - 5, w, 5, fillColor=cor, strokeColor=None))
        txt(d, x + w / 2, y + h / 2 + 1, t1, 7.6, "Sans-B", INK, "middle")
        txt(d, x + w / 2, y + h / 2 - 9, t2, 6.2, "Sans", MUTED, "middle")

    def seta(x1, y1, x2, y2, cor=INK, rot=""):
        import math
        linha(d, x1, y1, x2, y2, cor, 1.3)
        a = math.atan2(y2 - y1, x2 - x1)
        d.add(Polygon([x2, y2, x2 - 7 * math.cos(a - 0.4), y2 - 7 * math.sin(a - 0.4),
                       x2 - 7 * math.cos(a + 0.4), y2 - 7 * math.sin(a + 0.4)], fillColor=cor, strokeColor=None))
        if rot:
            txt(d, (x1 + x2) / 2, (y1 + y2) / 2 + 4, rot, 5.8, "Sans-I", MUTED, "middle")

    bloco(190, 70, 110, 60, "ESP32 DevKit V1", "controle", NAVY)
    bloco(15, 120, 110, 46, "Teclado 4x4", "8 fios", KP[1])
    bloco(190, 145, 110, 40, "Display 6 dígitos", "TM1637 (a caminho)", C["dio"])
    bloco(365, 120, 115, 46, "MOSFET + diodo", "→ fechadura", C["lock"])
    bloco(365, 60, 115, 40, "Buzzer", "direto no pino", C["buz"])
    bloco(15, 20, 110, 46, "Bateria 9 V", "única alimentação", C["v12"])
    seta(125, 140, 190, 112, KP[1])
    seta(245, 130, 245, 145, C["dio"])
    seta(300, 112, 365, 140, C["lock"], "GPIO16")
    seta(300, 90, 365, 80, C["buz"], "GPIO17")
    seta(125, 45, 190, 80, C["v12"], "VIN")
    linha(d, 125, 30, 488, 30, C["v12"], 1.1, [3, 2])
    linha(d, 488, 30, 488, 143, C["v12"], 1.1, [3, 2])
    seta(488, 143, 480, 143, C["v12"])
    txt(d, 300, 22, "+9 V direto para a fechadura", 5.8, "Sans-I", MUTED, "middle")
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
    for k, s in enumerate(["Diagrama completo com a placa · pinagem · desenhos de montagem",
                           "passo a passo · software · operação · solução de problemas"]):
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
    E = [NextPageTemplate("retrato"), PageBreak()]
    E.append(Paragraph("Sumário", st("tt", fontName="Sans-B", fontSize=19, leading=23, textColor=NAVY,
                                      spaceAfter=12)))
    toc = TableOfContents()
    toc.levelStyles = [S["toc1"], S["toc2"]]
    toc.dotsMinLevel = 0
    E += [toc, PageBreak()]

    # ---------------- 1 visão geral
    E.append(P("1. Visão geral", "h1"))
    E.append(P("Este guia mostra como montar o hardware do <b>Projeto Talos</b> e gravar o firmware no "
               "<b>ESP32 DevKit V1</b>. O cofre abre uma fechadura solenoide quando alguém digita a senha de 6 "
               "dígitos no teclado 4x4. Antes da senha, o cofre mostra 2 dígitos aleatórios que precisam ser "
               "digitados primeiro (desafio anti-marcas). Depois de 5 erros seguidos, o teclado fica bloqueado. "
               "Sem uso, o ESP32 entra em <i>deep sleep</i>."))
    E.append(P("Tudo é alimentado por <b>uma bateria de 9 V</b>: ela vai direto no pino VIN da placa e na "
               "fechadura. Não há conversor de tensão. O guia segue a ordem da montagem: pinagem, diagrama "
               "completo, um desenho para cada bloco, o passo a passo, o software e a operação. Os testes estão "
               "num documento separado, o <b>Guia de Testes</b>."))
    E.append(figura_blocos())
    E.append(P("Figura 1 – Blocos do sistema.", "cap"))
    E.append(callout("info", "O firmware usa exatamente os pinos deste guia. Se mudar algum pino, altere também "
                             "as constantes no topo de <font name='Mono'>src/main.cpp</font> (§6.6)."))

    # ---------------- 2 pinagem
    E.append(PageBreak())
    E.append(P("2. Pinagem do ESP32 DevKit V1", "h1"))
    E.append(P("A placa tem 15 pinos de cada lado. Os nomes da figura são os mesmos impressos na placa "
               "(<i>silkscreen</i>). Atenção a dois nomes que confundem: <b>RX2 é o GPIO16</b> e "
               "<b>TX2 é o GPIO17</b>. Os pinos coloridos são usados pelo projeto e os cinzas ficam livres."))
    E.append(figura_pinagem())
    E.append(P("Figura 2 – Pinos usados (vista de cima, antena para cima, USB para baixo).", "cap"))
    E.append(callout("danger", "O <b>D12</b> define a tensão da flash no boot. Na placa do grupo isso foi fixado "
                               "por eFuse (§4.2), e o D12 recebe <b>só o fio do teclado</b>. Não ligue mais nada nele. "
                               "Os pinos D2, D15, D0 (BOOT) e D5 também são de boot; o D2 é usado só como saída "
                               "para o LED, o que é seguro."))
    E.append(PageBreak())
    E.append(P("2.1 Tabela de ligações", "h2"))
    sw = lambda c: swatch(c)
    E.append(tabela([
        ["Cor", "Pino na placa", "GPIO", "Liga em", "Detalhe"],
        [sw(KP[0]), "D32", "32", "Teclado, fio 1", "§4.2"],
        [sw(KP[1]), "D33", "33", "Teclado, fio 2", "§4.2"],
        [sw(KP[2]), "D25", "25", "Teclado, fio 3", "§4.2"],
        [sw(KP[3]), "D26", "26", "Teclado, fio 4", "§4.2"],
        [sw(KP[4]), "D27", "27", "Teclado, fio 5", "§4.2"],
        [sw(KP[5]), "D14", "14", "Teclado, fio 6", "§4.2"],
        [sw(KP[6]), "D12", "12", "Teclado, fio 7, e nada mais neste pino", "§4.2"],
        [sw(KP[7]), "D13", "13", "Teclado, fio 8", "§4.2"],
        [sw(C["lock"]), "RX2", "16", "Perna G do MOSFET (fechadura)", "§4.3"],
        [sw(C["buz"]), "TX2", "17", "Perna + do buzzer", "§4.4"],
        [sw(C["dio"]), "D18", "18", "DIO do display TM1637 (quando chegar)", "§4.5"],
        [sw(C["clk"]), "D19", "19", "CLK do display TM1637 (quando chegar)", "§4.5"],
        [sw(C["led"]), "D2", "2", "LED azul da placa (já vem ligado)", "§4.6"],
        [sw(C["bat"]), "VP", "36", "Divisor de tensão da bateria (opcional)", "§4.6"],
        [sw(C["door"]), "VN", "39", "Sensor de porta (opcional)", "§4.6"],
        [sw(C["v12"]), "VIN", "–", "+ da bateria 9 V (fio vermelho)", "§4.1"],
        [sw(C["gnd"]), "GND", "–", "– da bateria, perna S do MOSFET, – do buzzer", "§4.1"],
        [sw(C["v33"]), "3V3", "–", "VCC do display TM1637 (quando chegar)", "§4.5"],
    ], [34, 68, 38, 230, None]))

    # ---------------- 3 diagrama completo (paisagem)
    E += [NextPageTemplate("paisagem"), PageBreak()]
    E.append(Paragraph("3. Diagrama completo de ligação", st("h1l", parent=S["h1"], fontSize=15, leading=18,
                                                              spaceAfter=4)))
    E.append(diagrama_completo())
    E += [NextPageTemplate("retrato"), PageBreak()]
    E.append(P("3.1 Como ler o diagrama", "h2"))
    E += bullets([
        "Cada cor de fio tem um significado (veja a legenda). Vermelho é +9 V e preto é GND. Os fios do teclado "
        "usam azuis para as linhas e verdes para as colunas.",
        "Todo símbolo de terra (três traços) e toda etiqueta “GND” são o <b>mesmo GND</b>. Na protoboard, use "
        "uma única barra de GND para tudo.",
        "Os 8 fios do teclado vão em sequência nos pinos <b>D32 a D13</b>, sem resistores.",
        "A fechadura aparece como um bloco; o desenho de montagem dela está no §4.3.",
        "O módulo de display, contornado em laranja tracejado, ainda não chegou: seus fios só serão ligados "
        "depois. Elementos tracejados são opcionais.",
    ])
    E.append(callout("danger", "Antes de ligar a bateria: (1) todos os GND interligados; (2) o + da bateria no "
                               "<b>VIN</b>, nunca no 3V3; (3) resistor de 10 kΩ no gate do MOSFET (sem ele a "
                               "fechadura pode abrir sozinha); (4) diodo com a faixa no lado do +9 V; (5) no D12, só "
                               "o fio do teclado.", "CHECKLIST ANTES DE LIGAR"))

    # ---------------- 4 montagem por bloco
    E.append(P("4. Montagem por bloco", "h1"))
    E.append(P("4.1 Alimentação (bateria 9 V)", "h2"))
    E.append(P("A bateria vai <b>direto</b> na placa: o fio vermelho (+) no <b>VIN</b> e o preto (–) no "
               "<b>GND</b>. O regulador da própria placa gera os 3,3 V do ESP32. O mesmo + da bateria também vai "
               "na fechadura (§4.3)."))
    E.append(figura_alimentacao())
    E.append(P("Figura 3 – Bateria 9 V na placa.", "cap"))
    E.append(callout("warn", "Quando a placa estiver no USB para gravar ou ver o serial, <b>desconecte a "
                             "bateria</b>. Alguns clones da DevKit não têm proteção entre o VIN e o USB. Sem a "
                             "bateria, o teclado e o buzzer funcionam pelo USB, mas a fechadura não aciona."))

    E.append(CondPageBreak(120 * mm))
    E.append(P("4.2 Teclado 4x4", "h2"))
    E.append(P("O teclado tem 8 fios. Cada tecla, quando apertada, encosta um fio de linha num fio de coluna, e o "
               "firmware descobre qual foi. Ligue os 8 fios <b>em sequência</b> nos pinos <b>D32, D33, D25, D26, "
               "D27, D14, D12 e D13</b>, que são vizinhos no lado esquerdo da placa. Não precisa de resistores."))
    E.append(figura_teclado())
    E.append(P("Figura 4 – Teclado de frente e como as teclas se ligam por dentro.", "cap"))
    E.append(callout("warn", "<b>Teclas espelhadas?</b> Se você aperta 2 e o cofre lê C (ou aperta 4 e lê #), a "
                             "ordem dos fios ficou invertida em relação ao teclado. Não precisa mexer nos fios: mude "
                             "<font name='Mono'>TECLADO_INVERTIDO</font> no firmware. O padrão é "
                             "<font name='Mono'>true</font>, que é como ficou o teclado do grupo.", "TECLADO INVERTIDO"))
    E.append(callout("info", "<b>Todas as teclas acordam o cofre</b> porque a placa do grupo tem o eFuse que fixa a "
                             "flash em 3,3 V. Sem ele, o D12 seria um pino de boot e precisaria ficar em LOW no "
                             "deep sleep, e as teclas ligadas a ele (4, 5, 6 e B) não acordariam. O firmware detecta "
                             "o eFuse sozinho e mostra no serial: <font name='Mono'>D12 livre</font> ou "
                             "<font name='Mono'>D12 strapping</font>. Para gravar numa placa nova com módulo "
                             "<b>WROOM-32</b> (flash de 3,3 V): <font name='Mono'>espefuse.py --port /dev/ttyUSB0 "
                             "set_flash_voltage 3.3V</font>. <b>É irreversível</b>: nunca use 1.8V.",
                     "SOBRE O D12 E O EFUSE"))

    E.append(CondPageBreak(110 * mm))
    E.append(P("4.3 Fechadura", "h2"))
    E.append(P("O pino do ESP32 não aguenta a corrente da fechadura, então quem a liga é um <b>MOSFET</b>, que "
               "funciona como uma chave. Quando o RX2 vai para HIGH, o MOSFET fecha o caminho entre a fechadura "
               "e o GND, e a lingueta recolhe por 5 s. São só 3 peças além da fechadura:"))
    E.append(figura_fechadura())
    E.append(P("Figura 5 – Montagem da fechadura. O fio cinza passa por cima do preto sem encostar.", "cap"))
    E.append(tabela([
        ["Peça", "Onde liga"],
        ["MOSFET, perna <b>G</b> (esquerda)", "RX2 da placa"],
        ["MOSFET, perna <b>D</b> (meio)", "um fio da fechadura"],
        ["MOSFET, perna <b>S</b> (direita)", "GND"],
        ["Resistor 10 kΩ", "entre a perna G e o GND (mantém a fechadura fechada no boot e no sono)"],
        ["Fechadura, outro fio", "+ da bateria 9 V"],
        ["Diodo 1N4007", "entre os 2 fios da fechadura, com a <b>faixa no lado do +</b> (protege o MOSFET)"],
    ], [150, None], destaque_col0=True))
    E.append(Spacer(1, 6))
    E.append(callout("tip", "As pernas do MOSFET são lidas com as <b>letras (a face com o nome) para você</b> e as "
                            "pernas para baixo: <b>G, D, S</b> da esquerda para a direita. A fechadura não tem "
                            "polaridade, mas o diodo tem."))

    E.append(CondPageBreak(60 * mm))
    E.append(P("4.4 Buzzer", "h2"))
    E.append(figura_buzzer())
    E.append(P("Figura 6 – Buzzer ligado direto na placa.", "cap"))
    E.append(P("São 2 fios: a perna longa (+) no <b>TX2</b> e a curta (–) no <b>GND</b>. O buzzer é de 5 V e aqui "
               "recebe 3,3 V, então apita mais baixo. Ele é <b>ativo</b>: sempre o mesmo tom, por isso os avisos se "
               "diferenciam pelo número e pela duração dos bipes (§7.4)."))

    E.append(CondPageBreak(110 * mm))
    E.append(P("4.5 Display de 6 dígitos (quando chegar)", "h2"))
    E.append(P("O firmware já tem o driver do módulo TM1637, mas ele fica desligado com "
               "<font name='Mono'>TEM_DISPLAY = false</font>. Até lá, o desafio aparece em piscadas do LED e bipes "
               "(§7.2) e no monitor serial. Quando o módulo chegar, são 4 fios:"))
    E.append(figura_tm1637())
    E.append(P("Figura 7 – Ligação do módulo TM1637. Siga os nomes impressos no módulo.", "cap"))
    E += numerados([
        "Ligue <b>VCC no 3V3</b> (nunca no VIN), GND no GND, DIO no D18 e CLK no D19.",
        "Em <font name='Mono'>src/main.cpp</font>, troque <font name='Mono'>TEM_DISPLAY = false</font> por "
        "<font name='Mono'>true</font> e grave.",
        "Se os dígitos saírem embaralhados, ajuste o vetor <font name='Mono'>POS_TM</font>. Brilho: "
        "<font name='Mono'>BRILHO_DISPLAY</font> (0 a 7).",
    ])

    E.append(CondPageBreak(95 * mm))
    E.append(P("4.6 Opcionais: leitura da bateria, LED externo e sensor de porta", "h2"))
    E.append(esq_sensores())
    E.append(P("Figura 8 – Opcionais.", "cap"))
    E += bullets([
        "<b>Leitura da bateria:</b> dois resistores (330 kΩ e 100 kΩ) fazem o cofre avisar quando a bateria fica "
        "abaixo de <b>7 V</b>. Sem eles, o aviso de bateria fraca fica desligado (ou acusa errado, porque o pino "
        "fica solto; nesse caso, ligue o VP no GND).",
        "<b>LED externo:</b> o LED azul da placa (D2) já pisca junto com os bipes. Para vê-lo de fora do case, "
        "ligue um LED com 220 Ω no D2.",
        "<b>Sensor de porta:</b> não foi comprado. Sem ele, a fechadura trava sozinha após 5 s.",
    ])

    E.append(CondPageBreak(70 * mm))
    E.append(P("4.7 Identificando as peças", "h2"))
    E.append(figura_componentes())
    E.append(P("Figura 9 – Como reconhecer os terminais de cada peça.", "cap"))

    # ---------------- 5 passo a passo
    E.append(PageBreak())
    E.append(P("5. Montagem passo a passo", "h1"))
    E.append(P("Monte e teste um bloco por vez. Faça tudo com a bateria <b>desconectada</b>."))
    passos = [
        ("Firmware", "Conecte só o USB e grave o firmware (§6). No monitor serial deve aparecer "
                     "<font name='Mono'>Talos: boot</font> e um desafio."),
        ("Teclado", "Ligue os 8 fios em sequência (D32 a D13). Aperte uma tecla: o serial mostra um desafio. "
                    "Digite os 2 dígitos e veja <font name='Mono'>S3: digite a senha</font>."),
        ("Buzzer", "Perna longa no TX2, curta no GND. Cada tecla deve dar um bipe."),
        ("Fechadura", "Monte o MOSFET, o resistor de 10 kΩ e o diodo (§4.3). Antes da fechadura, dá para testar "
                      "com um LED + resistor no lugar dela."),
        ("Bateria", "Desconecte o USB. Ligue a bateria: + no VIN e na fechadura, – no GND. O LED vermelho da "
                    "placa acende. Senha <font name='Mono'>000000</font> + <b>#</b> deve recolher a lingueta por 5 s."),
        ("Case", "Fixe o teclado na tampa e a fechadura alinhada com o batente. Deixe a bateria acessível por "
                 "fora (RF-10). Rode o Guia de Testes."),
    ]
    linhas = [["#", "Etapa", "O que fazer e como testar", "OK"]]
    for k, (a_, b_) in enumerate(passos, 1):
        linhas.append([str(k), a_, b_, "☐"])
    t = tabela(linhas, [20, 72, None, 26], destaque_col0=True)
    t.setStyle(TableStyle([("ALIGN", (3, 0), (3, -1), "CENTER")]))
    E.append(t)

    # ---------------- 6 software
    E.append(PageBreak())
    E.append(P("6. Software: compilar e gravar", "h1"))
    E.append(P("O projeto usa o <b>PlatformIO</b>, que baixa sozinho o compilador e as bibliotecas do ESP32 na "
               "primeira compilação (alguns minutos). Depois disso, gravar leva um comando."))
    E.append(P("6.1 Opção A: terminal (Linux ou WSL)", "h2"))
    E.append(code("""
sudo apt update && sudo apt install -y pipx git
pipx ensurepath                 # depois feche e abra o terminal
pipx install platformio
git clone https://github.com/AndreMorenoGoveia/talos-project-embedded.git
cd talos-project-embedded
pio run -t upload -t monitor    # compila, grava e abre o serial
"""))
    E.append(P("Para sair do monitor serial, use <b>Ctrl+C</b>."))
    E.append(P("6.2 Opção B: VS Code (Windows, Linux ou macOS)", "h2"))
    E += numerados([
        "Instale o VS Code e a extensão <b>PlatformIO IDE</b>.",
        "No Windows, instale o driver da ponte USB da placa: <b>CP210x</b> ou <b>CH340</b>.",
        "Abra a pasta do projeto e use os botões da barra azul inferior: Build, Upload e Serial Monitor.",
    ])
    E.append(P("6.3 Usando o WSL? Passe o USB para o Linux", "h2"))
    E.append(P("No PowerShell <b>como administrador</b> (o <i>attach</i> precisa ser repetido toda vez que a placa "
               "for reconectada):"))
    E.append(code("""
winget install --exact dorssel.usbipd-win     # uma vez só
usbipd list                                   # ache "CP210x" e anote o BUSID (ex.: 1-2)
usbipd bind   --busid 1-2                     # uma vez só
usbipd attach --wsl --busid 1-2               # toda vez que plugar a placa
"""))
    E.append(P("No WSL, libere a porta: <font name='Mono'>sudo chmod 666 /dev/ttyUSB0</font>. Se a porta não "
               "aparecer, carregue o driver uma vez: <font name='Mono'>sudo modprobe cp210x</font>."))
    E.append(P("6.4 Comandos úteis", "h2"))
    E.append(tabela([
        ["Comando", "O que faz"],
        ["<font name='Mono'>pio run -t upload</font>", "Compila e grava"],
        ["<font name='Mono'>pio device monitor</font>", "Abre o monitor serial (115200 baud)"],
        ["<font name='Mono'>pio run -t erase</font>", "Apaga a flash inteira (senha volta a 000000). Grave de novo depois"],
    ], [180, None]))
    E.append(Spacer(1, 6))
    E.append(callout("tip", "Se a gravação parar em <font name='Mono'>Connecting...</font>, segure o botão "
                            "<b>BOOT</b> da placa. Se a porta nem aparece, troque o cabo: muitos só carregam."))
    E.append(P("6.5 O que aparece no monitor serial", "h2"))
    E.append(code("""
Talos: boot (wake=0, stealth=0, D12 livre: todas as teclas acordam)
S1/S2: desafio anti-marcas = 4 7          <- digite 4 e 7
S3: digite a senha (6 digitos) e #        <- digite 000000 e #
S5: acesso concedido
S7: trancado
S0: deep sleep                            <- dorme logo após trancar
"""))
    E.append(P("<font name='Mono'>wake=0</font> indica ligar ou reset, <font name='Mono'>wake=3</font> uma "
               "tecla e <font name='Mono'>wake=4</font> o fim de um bloqueio. O serial nunca mostra a senha."))
    E.append(P("6.6 Ajustando parâmetros", "h2"))
    E.append(P("Todos ficam no topo de <font name='Mono'>src/main.cpp</font>. Depois de mudar, grave de novo."))
    E.append(tabela([
        ["Constante", "Padrão", "Significado"],
        ["T_INAT", "15000 ms", "Sem tecla em qualquer etapa: descarta a entrada e dorme"],
        ["T_ACIO", "5000 ms", "Tempo com a fechadura destravada"],
        ["N_TENT", "5", "Senhas erradas seguidas até o bloqueio"],
        ["T_LOCK / T_MAX", "60 s / 30 min", "Bloqueio inicial e teto (dobra a cada bloqueio)"],
        ["W_REC", "15 min", "Janela em que um novo bloqueio conta como consecutivo"],
        ["TECLADO_INVERTIDO", "true", "Fios do teclado na ordem 8…1 (true) ou 1…8 (false)"],
        ["TEM_DISPLAY", "false", "Ative quando ligar o módulo TM1637"],
        ["DEBUG_TECLADO", "false", "Mostra cada tecla no serial (revela a senha: só para teste)"],
        ["V_LOW / BAT_DIV", "7,0 V / 4,3", "Limiar de bateria fraca / razão do divisor"],
    ], [120, 80, None]))

    # ---------------- 7 operação
    E.append(PageBreak())
    E.append(P("7. Operação", "h1"))
    E.append(figura_fluxo())
    E.append(P("Figura 10 – Uso normal do cofre.", "cap"))
    E.append(P("7.1 Teclas", "h2"))
    E.append(tabela([
        ["Tecla", "Função"],
        ["qualquer", "Acorda o cofre"],
        ["0 – 9", "Dígitos do desafio e da senha"],
        ["*", "Limpar: apaga o que foi digitado (age ao <b>soltar</b>)"],
        ["#", "Confirmar: só aceita com exatamente 6 dígitos (age ao <b>soltar</b>)"],
        ["A", "Trocar a senha: aperte durante os 5 s em que a tranca está aberta"],
        ["* e # juntos por 3 s", "Liga/desliga o modo stealth (sem som). O LED pisca 2 vezes"],
        ["B, C, D", "Sem função"],
    ], [110, None], destaque_col0=True))
    E.append(P("7.2 Lendo o desafio anti-marcas", "h2"))
    E.append(P("Ao acordar, o cofre sorteia 2 dígitos: digite-os e então a senha. Sem display, cada dígito é um "
               "grupo de piscadas do LED com bipes (o 0 é uma piscada longa), e eles também saem no serial."))
    E.append(figura_piscadas())
    E.append(P("Figura 11 – Desafio em piscadas (sem display).", "cap"))
    E.append(P("Com o display ligado, o desafio aparece nele:"))
    E.append(figura_telas())
    E.append(P("Figura 12 – Telas do display.", "cap"))
    E.append(P("7.3 Trocar a senha", "h2"))
    E += numerados([
        "Abra o cofre normalmente (desafio + senha atual + #).",
        "Enquanto a tranca está aberta (5 s), aperte <b>A</b>. A tranca fecha e começa a troca.",
        "Digite a senha <b>atual</b> + <b>#</b>, depois a <b>nova</b> + <b>#</b> e repita a nova + <b>#</b>.",
        "Três bipes crescentes: senha salva. Dois bipes: as duas digitações não conferem e a antiga continua.",
    ])
    E.append(P("7.4 Sons", "h2"))
    E.append(tabela([
        ["Situação", "Som"],
        ["Tecla aceita", "1 bipe curto"],
        ["Pronto para a senha / entrada inválida", "2 bipes curtíssimos"],
        ["Desafio ou senha errados", "2 bipes curtos"],
        ["Acesso concedido", "3 bipes, cada um mais longo"],
        ["Bloqueio", "1 bipe longo (1,5 s)"],
        ["Bateria fraca (ao acordar)", "5 bipes rápidos"],
    ], [260, None]))
    E.append(P("7.5 Erros e bloqueio", "h2"))
    E.append(P("Senha errada: 2 bipes e você digita a senha de novo, sem novo desafio. Na 5ª senha errada "
               "seguida, o cofre bloqueia por 60 s; se outro bloqueio acontecer até 15 min depois, o tempo dobra "
               "(até 30 min). Durante o bloqueio, o teclado não acorda o cofre. Acertar a senha zera todas as "
               "punições. Esqueceu a senha? Pelo USB, <font name='Mono'>pio run -t erase</font> e grave de novo: "
               "a senha volta a <b>000000</b>."))

    # ---------------- 8 testes
    E.append(P("8. Testes", "h1"))
    E.append(P("Os casos de teste completos, com passo a passo e resultado esperado de cada um, estão no "
               "documento <b>Guia de Testes</b> (<font name='Mono'>docs/Guia_Testes_Talos.pdf</font>)."))

    # ---------------- 9 problemas
    E.append(P("9. Solução de problemas", "h1"))
    E.append(tabela([
        ["Sintoma", "Causa provável", "O que fazer"],
        ["Gravação para em “Connecting…”", "Placa não entrou em modo de gravação", "Segure BOOT durante a gravação"],
        ["Porta serial não aparece", "Cabo só de carga, driver ou WSL", "Troque o cabo; usbipd attach (§6.3)"],
        ["Teclas espelhadas (aperta 2, lê C)", "Ordem dos fios invertida", "Troque TECLADO_INVERTIDO (§4.2)"],
        ["Uma linha ou coluna não responde", "Fio solto ou no pino errado", "Confira a tabela do §2.1"],
        ["Fechadura não aciona", "Sem bateria, GND separado, MOSFET invertido", "GND comum; G D S com as letras para você"],
        ["Fechadura abre sozinha", "Falta o 10 kΩ do gate ao GND", "Coloque o resistor (§4.3)"],
        ["ESP32 reinicia ao destravar", "Bateria fraca ou diodo ausente", "Troque a bateria; confira o diodo"],
        ["Alerta de bateria fraca falso", "Divisor ausente (pino VP solto)", "Ligue o VP no GND ou monte o divisor"],
        ["Sem som nenhum", "Modo stealth ligado", "Segure * e # por 3 s"],
        ["[NVS] falha na verificação", "Gravação na flash falhou (energia fraca)", "Outra porta/cabo USB ou bateria nova"],
        ["Teclado ignorado após erros", "Bloqueio ativo", "Espere (o serial mostra o tempo)"],
    ], [130, 140, None]))

    # ---------------- 10 limitações
    E.append(P("10. Limitações conhecidas", "h1"))
    E += bullets([
        "<b>Autonomia:</b> mesmo dormindo, a DevKit V1 gasta alguns mA (LED de energia, regulador e chip USB). "
        "Com uma bateria de 9 V comum (~500 mAh), isso dá <b>poucos dias</b>. A meta de 2 anos da monografia "
        "exigiria um ESP32 sem a placa de desenvolvimento.",
        "<b>Buzzer:</b> recebe 3,3 V em vez de 5 V, então apita mais baixo. Tem um único tom, por isso a "
        "“melodia” de sucesso virou bipes de duração crescente.",
        "<b>Display:</b> o driver está pronto, mas só será testado quando o módulo chegar.",
        "<b>Aleatoriedade:</b> com Wi-Fi e Bluetooth desligados, o sorteio do desafio é pseudoaleatório. Basta "
        "para espalhar o desgaste das teclas.",
    ])
    doc.multiBuild(E)


if __name__ == "__main__":
    construir()
    print("gerado:", SAIDA)

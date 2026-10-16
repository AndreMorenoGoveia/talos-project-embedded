#!/usr/bin/env python3
"""Exporta as figuras do guia (docs/gerar_guia.py) como PDFs vetoriais para o relatório."""
import os
import sys

from reportlab.graphics import renderPDF

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "docs"))
import gerar_guia as g  # noqa: E402

FIGS = {"diagrama": g.diagrama_completo, "blocos": g.figura_blocos, "pinagem": g.figura_pinagem,
        "teclado": g.figura_teclado, "fechadura": g.figura_fechadura, "alimentacao": g.figura_alimentacao,
        "buzzer": g.figura_buzzer, "tm1637": g.figura_tm1637, "piscadas": g.figura_piscadas,
        "telas": g.figura_telas, "fluxo": g.figura_fluxo}

for nome, f in FIGS.items():
    renderPDF.drawToFile(f(), os.path.join(AQUI, "figuras", nome + ".pdf"))
print("figuras:", ", ".join(FIGS))

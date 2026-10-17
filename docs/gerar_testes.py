#!/usr/bin/env python3
"""Gera docs/Guia_Testes_Talos.pdf (casos de teste do Projeto Talos). Uso: python3 docs/gerar_testes.py"""
import os

from reportlab.lib.colors import HexColor as H, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (Frame, KeepTogether, NextPageTemplate, PageBreak, PageTemplate, Paragraph,
                                Preformatted, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

from gerar_guia import (ACC, INK, LIGHT, LINE, MUTED, NAVY, S, Guia, P, bullets, callout, fx, st,
                        tabela)

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Guia_Testes_Talos.pdf")

ROT = st("rot", fontName="Sans-B", fontSize=8, leading=10.5, textColor=NAVY, spaceAfter=0)
CEL = st("cel", fontSize=8.4, leading=11.2, spaceAfter=1)
TIT = st("tit", fontName="Sans-B", fontSize=9.5, leading=12, textColor=white, spaceAfter=0)
SER = st("ser", fontName="Mono", fontSize=7.4, leading=9.6, textColor=H("#E6EDF3"), spaceAfter=0)

RESUMO = []  # (id, título) para a folha de resultados


def caso(cid, titulo, req, objetivo, prep, passos, esperado, serial=None):
    RESUMO.append((cid, titulo))
    esp = [Paragraph(fx("• " + t), CEL) for t in esperado]
    if serial:
        t = Table([[Preformatted(serial.strip("\n"), SER)]], colWidths=["100%"])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), H("#1B2433")),
                               ("LEFTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 4),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        esp += [Spacer(1, 3), t]
    linhas = [
        [Paragraph(fx(f"{cid}  ·  {titulo}"), TIT), ""],
        [Paragraph("Objetivo", ROT), Paragraph(fx(objetivo), CEL)],
        [Paragraph("Requisito", ROT), Paragraph(fx(req), CEL)],
        [Paragraph("Preparação", ROT), Paragraph(fx(prep), CEL)],
        [Paragraph("Passos", ROT), [Paragraph(fx(f"{i}. {p}"), CEL) for i, p in enumerate(passos, 1)]],
        [Paragraph("Resultado esperado", ROT), esp],
        [Paragraph("Resultado", ROT),
         Paragraph('<font name="Sym">☐</font> Passou&nbsp;&nbsp;&nbsp;&nbsp;<font name="Sym">☐</font> Falhou'
                   '&nbsp;&nbsp;&nbsp;&nbsp;Obs.: ________________________________', CEL)],
    ]
    t = Table(linhas, colWidths=[78, None])
    t.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)), ("BACKGROUND", (0, 0), (1, 0), NAVY),
        ("BACKGROUND", (0, 1), (0, -1), LIGHT), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE), ("LINEBELOW", (0, 1), (-1, -2), 0.4, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return KeepTogether([t, Spacer(1, 10)])


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
    c.drawString(18 * mm + 62, h - 11.2 * mm, "Guia de testes")
    c.drawRightString(w - 18 * mm, h - 11.2 * mm, "PCS3848 · Sistemas Embarcados · Grupo 7")
    c.setFillColor(ACC)
    c.rect(w / 2 - 10, 9 * mm, 20, 1.2, fill=1, stroke=0)
    c.setFillColor(MUTED)
    c.drawCentredString(w / 2, 11 * mm, str(doc.page))
    c.restoreState()


def capa(c, doc):
    w, h = A4
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, h * 0.55, w, h * 0.45, fill=1, stroke=0)
    c.setFillColor(ACC)
    c.rect(0, h * 0.55 - 4, w, 4, fill=1, stroke=0)
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
    c.drawString(22 * mm, h - 92 * mm, "Guia de testes")
    c.setFillColor(H("#C8D3E3"))
    c.setFont("Sans", 9.5)
    c.drawString(22 * mm, h - 101 * mm, "Casos de teste para validar a placa, o firmware e a montagem")
    c.setFillColor(INK)
    c.setFont("Sans-B", 10)
    y = h * 0.55 - 22 * mm
    c.drawString(22 * mm, y, "Grupo 7")
    c.setFont("Sans", 10)
    for k, s_ in enumerate(["André Moreno · 13682785", "Felipe Soria · 13864287", "Giovani Sebastianutti · 13680171",
                            "Matheus Guidoni · 12683120"]):
        c.drawString(22 * mm, y - 15 - 14 * k, s_)
    c.setFillColor(MUTED)
    c.setFont("Sans", 8.5)
    c.drawString(22 * mm, 25 * mm, "São Paulo, outubro de 2026")
    c.restoreState()


def construir():
    doc = Guia(SAIDA, pagesize=A4, title="Projeto Talos — Guia de testes", author="Grupo 7 — PCS3848")
    fr = Frame(18 * mm, 16 * mm, A4[0] - 36 * mm, A4[1] - 32 * mm, leftPadding=0, rightPadding=0)
    doc.addPageTemplates([PageTemplate("capa", [Frame(0, 0, A4[0], A4[1])], onPage=capa),
                          PageTemplate("retrato", [fr], onPage=cabecalho)])
    E = [NextPageTemplate("retrato"), PageBreak()]
    E.append(Paragraph("Sumário", st("tt", fontName="Sans-B", fontSize=19, leading=23, textColor=NAVY,
                                      spaceAfter=12)))
    toc = TableOfContents()
    toc.levelStyles = [S["toc1"], S["toc2"]]
    E += [toc, PageBreak()]

    # ---------------- como usar
    E.append(P("1. Como usar este guia", "h1"))
    E.append(P("Cada caso de teste diz o que preparar, o que fazer e o que deve acontecer. O resultado esperado "
               "inclui as linhas exatas que aparecem no monitor serial. Faça os testes <b>na ordem</b>: os primeiros "
               "confirmam o básico (placa, teclado), e os seguintes dependem deles."))
    E.append(P("1.1 O que você precisa", "h2"))
    E += bullets([
        "Placa com o firmware gravado e o <b>monitor serial aberto</b>: <font name='Mono'>pio device monitor</font> "
        "(veja o Guia de Montagem, §6).",
        "Teclado ligado (D32 a D13).",
        "Algo no lugar da fechadura: a fechadura de verdade (com MOSFET e bateria) <b>ou</b> um LED + resistor no RX2.",
        "Um cronômetro (o do celular serve) para os testes de tempo.",
        "A senha de fábrica é <b>000000</b>. Se ela já foi trocada, use a senha atual onde estiver escrito 000000.",
    ])
    E.append(P("1.2 Lembretes", "h2"))
    E += bullets([
        "O cofre dorme depois de <b>15 s sem tecla</b>. Se a tela do serial parar, aperte uma tecla para acordar.",
        "O desafio muda a cada vez: leia os 2 dígitos no serial (<font name='Mono'>S1/S2: desafio anti-marcas = "
        "X Y</font>) ou nas piscadas do LED.",
        "As teclas <b>*</b> e <b>#</b> agem quando você <b>solta</b> a tecla.",
        "Com a placa no USB, deixe a bateria desconectada (a fechadura não aciona, mas o LED de teste sim).",
    ])
    E.append(callout("warn", "O TC-04 pede para ligar o <font name='Mono'>DEBUG_TECLADO</font>, que mostra cada "
                             "tecla no serial, inclusive a senha. <b>Desligue de novo</b> e grave o firmware antes de "
                             "seguir para os outros testes."))

    # ---------------- A. inicialização
    E.append(PageBreak())
    E.append(P("2. Inicialização e energia", "h1"))
    E.append(caso("TC-01", "Boot pelo USB", "RNF-01",
                  "Confirmar que o firmware inicia num estado seguro.",
                  "Placa só no USB. Monitor serial aberto.",
                  ["Aperte o botão <b>EN</b> da placa.", "Observe o serial e o LED (ou a fechadura) do RX2."],
                  ["Aparece a linha de boot com <font name='Mono'>D12 livre</font>.",
                   "Logo depois aparece um desafio.",
                   "O LED/fechadura do RX2 <b>não</b> acende em nenhum momento do boot.",
                   "Após 15 s sem tecla, o cofre dorme."],
                  """
Talos: boot (wake=0, stealth=0, D12 livre: todas as teclas acordam)
S1/S2: desafio anti-marcas = 4 7
S0: deep sleep
"""))
    E.append(caso("TC-02", "Primeiro boot (memória vazia)", "RF-06, RNF-03",
                  "Confirmar que, sem configuração salva, o cofre assume a senha de fábrica.",
                  "Placa no USB. <b>Isso apaga a senha e o bloqueio.</b>",
                  ["Rode <font name='Mono'>pio run -t erase</font> e depois <font name='Mono'>pio run -t upload -t monitor</font>.",
                   "Desafio + <font name='Mono'>000000</font> + <b>#</b>."],
                  ["No primeiro boot aparece a mensagem de configuração padrão (se o monitor abrir depois dela, "
                   "tudo bem: ela só aparece uma vez).",
                   "A senha <font name='Mono'>000000</font> abre o cofre."],
                  """
[NVS] sem configuracao valida, usando padrao
Talos: boot (wake=0, stealth=0, D12 livre: todas as teclas acordam)
"""))
    E.append(caso("TC-03", "Funcionamento só com a bateria de 9 V", "RF-10, RNF-05",
                  "Confirmar que a placa funciona sem o USB.",
                  "USB <b>desconectado</b>. Bateria 9 V: + no VIN e na fechadura, – no GND.",
                  ["Conecte a bateria.", "Aperte uma tecla, faça o desafio e digite a senha + #."],
                  ["O LED vermelho (PWR) da placa acende.",
                   "Cada tecla dá um bipe e a fechadura abre por 3 s com a senha certa.",
                   "A placa não reinicia quando a fechadura aciona (se reiniciar, a bateria está fraca)."]))

    # ---------------- B. teclado
    E.append(PageBreak())
    E.append(P("3. Teclado", "h1"))
    E.append(caso("TC-04", "Mapa das 16 teclas", "RF-01",
                  "Confirmar que cada tecla é lida como ela mesma.",
                  "Em <font name='Mono'>src/main.cpp</font>, mude <font name='Mono'>DEBUG_TECLADO</font> para "
                  "<font name='Mono'>true</font> e grave. Monitor serial aberto.",
                  ["Acorde o cofre.",
                   "Aperte, uma de cada vez: 1 2 3 A 4 5 6 B 7 8 9 C * 0 # D.",
                   "Para cada tecla, compare a tecla apertada com a que aparece entre aspas no serial.",
                   "No fim, volte <font name='Mono'>DEBUG_TECLADO</font> para <font name='Mono'>false</font> e grave."],
                  ["As 16 teclas aparecem como elas mesmas.",
                   "Se aparecerem espelhadas (aperta 2, lê C), troque <font name='Mono'>TECLADO_INVERTIDO</font>.",
                   "Se uma linha ou coluna inteira não aparece, há um fio solto."],
                  """
[tecla] mascara=0x4000 -> '2' (energizada 3 = GPIO13, lida 2 = GPIO25)
"""))
    E.append(caso("TC-05", "Um toque = uma tecla (debounce)", "RF-01",
                  "Confirmar que um toque gera exatamente uma tecla e que segurar não repete.",
                  "Cofre acordado, no desafio.",
                  ["Aperte uma tecla rapidamente: ouça 1 bipe.",
                   "Aperte e <b>segure</b> uma tecla por 3 s."],
                  ["Cada toque dá exatamente 1 bipe.", "Segurar dá só 1 bipe (não repete)."]))
    E.append(caso("TC-06", "Limpar com *", "RF-02",
                  "Confirmar que * apaga o que foi digitado.",
                  "Senha atual = 000000.",
                  ["Faça o desafio.", "Digite <font name='Mono'>999</font> e aperte <b>*</b>.",
                   "Digite <font name='Mono'>000000</font> e <b>#</b>."],
                  ["O acesso é concedido: o 999 foi apagado. (Se o * não funcionasse, a senha lida seria 999000 e "
                   "daria erro.)"],
                  "S5: acesso concedido"))
    E.append(caso("TC-07", "Confirmar com menos de 6 dígitos", "RF-15",
                  "Confirmar que # só valida com exatamente 6 dígitos.",
                  "Cofre no passo da senha (S3).",
                  ["Digite 4 dígitos e aperte <b>#</b>.", "Digite mais 2 dígitos (total 6) e aperte <b>#</b>."],
                  ["No passo 1: 2 bipes curtíssimos e <b>nenhuma</b> linha de Falha ou acesso no serial.",
                   "No passo 2 a senha é validada normalmente (os 4 primeiros dígitos foram mantidos)."]))
    E.append(caso("TC-08", "Teclas sem função (B, C, D)", "RNF-04",
                  "Confirmar que as letras não fazem nada indevido.",
                  "Cofre no passo da senha.",
                  ["Aperte B, C e D."],
                  ["Cada uma dá 2 bipes curtíssimos.", "Nada muda no serial."]))

    # ---------------- C. sono
    E.append(PageBreak())
    E.append(P("4. Sono e despertar", "h1"))
    E.append(caso("TC-09", "Dorme sozinho sem uso", "RF-12",
                  "Confirmar que o cofre entra em deep sleep após 15 s sem tecla.",
                  "Cronômetro.",
                  ["Acorde o cofre e não aperte mais nada.", "Cronometre até aparecer S0 no serial."],
                  ["Em ~15 s aparece <font name='Mono'>S0: deep sleep</font> e o LED para de piscar."],
                  "S0: deep sleep"))
    E.append(caso("TC-10", "Todas as 16 teclas acordam", "RF-13",
                  "Confirmar que qualquer tecla tira o cofre do sono (depende do eFuse do D12).",
                  "Boot mostra <font name='Mono'>D12 livre</font>.",
                  ["Espere o cofre dormir.", "Aperte uma tecla e confira a linha de boot.",
                   "Repita para as 16 teclas (marque abaixo)."],
                  ["Cada tecla gera um boot com <font name='Mono'>wake=3</font>.",
                   "Teclas: 1☐ 2☐ 3☐ A☐ 4☐ 5☐ 6☐ B☐ 7☐ 8☐ 9☐ C☐ *☐ 0☐ #☐ D☐"],
                  "Talos: boot (wake=3, stealth=0, D12 livre: todas as teclas acordam)"))
    E.append(caso("TC-11", "Tecla que acorda não conta como dígito", "RF-13",
                  "Confirmar que o toque usado para acordar é descartado.",
                  "Cofre dormindo.",
                  ["Acorde com uma tecla de número.", "Digite os 2 dígitos do desafio."],
                  ["O desafio é aceito normalmente: aparece <font name='Mono'>S3</font>, sem "
                   "<font name='Mono'>Desafio incorreto</font>."],
                  "S3: digite a senha (6 digitos) e #"))
    E.append(caso("TC-12", "Desistência no meio da senha", "RF-02",
                  "Confirmar que uma entrada parcial é descartada após 15 s.",
                  "Cronômetro.",
                  ["Faça o desafio.", "Digite 3 dígitos e espere."],
                  ["Em ~15 s: <font name='Mono'>Timeout de inatividade</font> e o cofre dorme.",
                   "Ao acordar de novo, começa do zero (novo desafio)."],
                  """
Timeout de inatividade
S0: deep sleep
"""))

    # ---------------- D. desafio e senha
    E.append(PageBreak())
    E.append(P("5. Desafio e senha", "h1"))
    E.append(caso("TC-13", "Desafio anti-marcas correto", "RF-07",
                  "Confirmar que o desafio precisa ser digitado antes da senha.",
                  "Cofre dormindo.",
                  ["Acorde e leia o desafio (serial ou piscadas do LED).", "Digite os 2 dígitos."],
                  ["Aparece <font name='Mono'>S3: digite a senha</font>.",
                   "As piscadas do LED batem com os dígitos do serial (0 = 1 piscada longa)."],
                  "S3: digite a senha (6 digitos) e #"))
    E.append(caso("TC-14", "Desafio errado", "RF-07",
                  "Confirmar que um dígito errado reinicia o desafio e não libera a senha.",
                  "Cofre no desafio.",
                  ["Digite um dígito diferente do primeiro do desafio."],
                  ["Aparece <font name='Mono'>Desafio incorreto</font> e um <b>novo</b> desafio.",
                   "Não conta como tentativa de senha."],
                  """
Desafio incorreto
S1/S2: desafio anti-marcas = 2 5
"""))
    E.append(caso("TC-15", "Senha correta abre a fechadura", "RF-05, RF-18",
                  "Fluxo completo de abertura.",
                  "Cronômetro. Fechadura ou LED no RX2.",
                  ["Desafio + <font name='Mono'>000000</font> + <b>#</b>.", "Cronometre o tempo aberto."],
                  ["Tiriri rápido (3 bipes curtos).", "Fechadura/LED liga por <b>3 s</b> e desliga com 1 bipe.",
                   "Logo depois de trancar, o cofre dorme (sem novo desafio)."],
                  """
S5: acesso concedido
S7: trancado
S0: deep sleep
"""))
    E.append(caso("TC-16", "Senha errada", "RF-03",
                  "Confirmar que a senha errada não abre e pede a senha de novo.",
                  "Cofre no passo da senha.",
                  ["Digite <font name='Mono'>111111</font> + <b>#</b>.", "Em seguida digite a senha certa + #."],
                  ["2 bipes curtos, <font name='Mono'>Falha 1/5</font> e volta direto para a senha (sem desafio).",
                   "A fechadura não aciona no erro.", "A senha certa em seguida abre normalmente."],
                  """
Falha 1/5
S3: digite a senha (6 digitos) e #
"""))

    # ---------------- E. bloqueio
    E.append(PageBreak())
    E.append(P("6. Bloqueio e punições", "h1"))
    E.append(caso("TC-17", "Bloqueio após 5 erros", "RF-03",
                  "Confirmar o bloqueio de 60 s e que o teclado é ignorado.",
                  "Cronômetro. Nenhum bloqueio nos últimos 15 min (ou acerte a senha antes, para zerar).",
                  ["Erre a senha 5 vezes seguidas.", "Durante o bloqueio, aperte várias teclas.",
                   "Cronometre até aparecer o fim do bloqueio."],
                  ["Na 5ª: bipe longo e <font name='Mono'>S6: bloqueado por 60 s</font>.",
                   "Durante o bloqueio, nenhuma tecla acorda o cofre.",
                   "Depois de ~60 s ele acorda sozinho, encerra o bloqueio e volta a dormir. Aí uma tecla acorda normalmente."],
                  """
Falha 5/5
S6: bloqueado por 60 s
S0: deep sleep (timer)
Talos: boot (wake=4, ...)
S6: fim do bloqueio
S0: deep sleep
"""))
    E.append(caso("TC-18", "Bloqueio progressivo", "RF-04",
                  "Confirmar que um 2º bloqueio em até 15 min dura o dobro.",
                  "Logo após o fim do bloqueio do TC-17, <b>sem acertar a senha</b>.",
                  ["Erre a senha mais 5 vezes."],
                  ["Aparece <font name='Mono'>S6: bloqueado por 120 s</font>."],
                  "S6: bloqueado por 120 s"))
    E.append(caso("TC-19", "Desligar não zera o bloqueio", "RF-16, RNF-02",
                  "Confirmar que tirar a energia durante o bloqueio não o cancela.",
                  "Cofre bloqueado.",
                  ["Desligue tudo (USB e bateria) por alguns segundos e religue."],
                  ["No boot o cofre volta direto para o bloqueio. Como o relógio zera sem energia, o bloqueio "
                   "recomeça do início (por exemplo, 60 s de novo)."],
                  """
Talos: boot (wake=0, ...)
S6: bloqueado por 60 s
"""))
    E.append(caso("TC-20", "Erros sobrevivem a desligar", "RF-16",
                  "Confirmar que o contador de erros não zera ao desligar.",
                  "Nenhum erro pendente (acerte a senha antes).",
                  ["Erre 3 vezes (<font name='Mono'>Falha 3/5</font>).", "Desligue e religue.",
                   "Erre mais 2 vezes."],
                  ["O 2º erro depois de religar mostra <font name='Mono'>Falha 5/5</font> e bloqueia."],
                  "Falha 5/5"))
    E.append(caso("TC-21", "Acertar zera todas as punições", "RF-04",
                  "Confirmar que a senha certa zera o contador e o nível do bloqueio.",
                  "Depois do TC-18 (2º bloqueio já aconteceu).",
                  ["Espere o bloqueio acabar e <b>acerte</b> a senha.", "Erre a senha 5 vezes de novo."],
                  ["O primeiro erro mostra <font name='Mono'>Falha 1/5</font>.",
                   "O bloqueio volta a ser de <b>60 s</b> (e não 240 s)."],
                  "S6: bloqueado por 60 s"))

    # ---------------- F. troca de senha
    E.append(PageBreak())
    E.append(P("7. Troca de senha", "h1"))
    E.append(caso("TC-22", "Troca de senha com sucesso", "RF-06",
                  "Trocar a senha e usar a nova.",
                  "Senha atual 000000.",
                  ["Acorde o cofre, faça o desafio e, no passo da senha, aperte <b>C</b>.",
                   "Digite <font name='Mono'>000000</font> + # (senha antiga) e depois "
                   "<font name='Mono'>123456</font> + # (senha nova).",
                   "Acorde e tente abrir com 000000 e depois com 123456."],
                  ["1 bipe ao aceitar a senha antiga.", "3 bipes crescentes ao confirmar a nova, que fica salva.",
                   "000000 dá Falha; 123456 abre."],
                  """
S8: troca de senha - digite a senha ANTIGA e #
S8: digite a NOVA senha e #
[LOG] senha alterada
S0: deep sleep
"""))
    E.append(caso("TC-23", "Troca a partir do desafio", "RF-06",
                  "Confirmar que a tecla C também funciona antes de responder ao desafio.",
                  "Senha atual conhecida.",
                  ["Acorde o cofre e, ainda no desafio, aperte <b>C</b>.", "Digite a senha antiga + # e uma nova + #."],
                  ["Aparece <font name='Mono'>S8: troca de senha</font> sem precisar do desafio.",
                   "A senha nova é salva (3 bipes crescentes)."],
                  "S8: troca de senha - digite a senha ANTIGA e #"))
    E.append(caso("TC-24", "Senha antiga errada na troca", "RF-06, RF-03",
                  "Confirmar que errar a senha antiga conta como tentativa e cancela a troca.",
                  "Senha atual conhecida.",
                  ["Acorde, aperte C.", "Digite uma senha antiga errada + #."],
                  ["<font name='Mono'>Falha 1/5</font> e o cofre dorme. A senha não muda."],
                  "Falha 1/5"))
    E.append(caso("TC-25", "C com a tranca aberta", "RF-06",
                  "Confirmar que a tecla C não faz nada enquanto a tranca está aberta.",
                  "Senha atual conhecida.",
                  ["Abra o cofre.", "Durante os 3 s abertos, aperte C."],
                  ["Nada muda: não aparece S8 e a tranca fecha normalmente após 3 s."]))
    E.append(caso("TC-26", "Senha nova sobrevive a desligar", "RF-16, RNF-03",
                  "Confirmar que a senha fica gravada na memória.",
                  "Senha trocada no TC-22.",
                  ["Desligue tudo por alguns segundos e religue.", "Abra com a senha nova."],
                  ["A senha nova abre; a antiga não."]))

    # ---------------- G. sons, stealth, saídas
    E.append(PageBreak())
    E.append(P("8. Som, modo stealth e fechadura", "h1"))
    E.append(caso("TC-27", "Sons de cada evento", "RF-08, RNF-04",
                  "Confirmar que cada evento tem um som diferente.",
                  "Stealth desligado.",
                  ["Provoque cada situação da lista ao lado."],
                  ["Tecla: 1 bipe curto ☐", "Senha/desafio errado: 2 bipes curtos ☐",
                   "Acesso: tiriri rápido ☐", "Tranca fechou: 1 bipe ☐", "Bloqueio: 1 bipe longo ☐",
                   "Entrada inválida / # com menos de 6: 2 bipes curtíssimos ☐",
                   "Acordar pelo teclado: 1 bipe ☐", "Desafio: <b>nenhum</b> som, só o LED pisca ☐"]))
    E.append(caso("TC-28", "Modo stealth", "RF-14",
                  "Confirmar que o modo stealth tira todo o som e fica salvo.",
                  "Cofre acordado.",
                  ["Segure <b>*</b> e <b>#</b> juntos por 3 s.", "Use o cofre (teclas, erro, acesso).",
                   "Desligue e religue.", "Segure * e # por 3 s de novo."],
                  ["No passo 1: <font name='Mono'>Stealth ON</font> e o LED pisca 2 vezes.",
                   "Nenhum som em nenhum evento; o LED continua piscando.",
                   "Depois de religar, o boot mostra <font name='Mono'>stealth=1</font>.",
                   "No passo 4: <font name='Mono'>Stealth OFF</font> e o som volta.",
                   "Soltar * e # depois do combo não limpa nem confirma nada."],
                  "Stealth ON"))
    E.append(caso("TC-29", "Fechadura não aciona sozinha", "RNF-01",
                  "Confirmar que a fechadura fica travada no boot e durante o sono (resistor de 10 kΩ).",
                  "Fechadura montada com bateria.",
                  ["Ligue a bateria e observe o boot.", "Deixe o cofre dormir e espere 1 minuto.",
                   "Aperte EN algumas vezes."],
                  ["A fechadura <b>nunca</b> recolhe a lingueta fora do acesso concedido."]))
    E.append(caso("TC-30", "Fechadura real abre a porta", "RF-05",
                  "Confirmar que 3 s bastam para abrir a porta do case.",
                  "Fechadura instalada no case, bateria nova.",
                  ["Abra com a senha e puxe a porta durante os 3 s.", "Feche a porta empurrando."],
                  ["A porta abre dentro dos 3 s.", "Ao fechar, a lingueta chanfrada trava sozinha.",
                   "Se 3 s for pouco, aumente <font name='Mono'>T_ACIO</font> (até 10 s)."]))

    # ---------------- H. bateria, memória e display
    E.append(PageBreak())
    E.append(P("9. Bateria, memória e display", "h1"))
    E.append(caso("TC-31", "Aviso de bateria fraca", "RF-11",
                  "Confirmar o aviso abaixo de 7 V.",
                  "Divisor 330 kΩ / 100 kΩ montado no VP. Uma bateria gasta ou fonte ajustável.",
                  ["Com bateria boa (acima de 7 V): acorde o cofre.", "Com 6,5 V: acorde o cofre."],
                  ["Com bateria boa: nenhum aviso.",
                   "Com 6,5 V: o LED pisca 5 vezes rápido (sem som) e aparece <font name='Mono'>Bateria baixa</font> no serial.",
                   "Sem o divisor, o pino fica solto e o aviso pode aparecer errado: ligue o VP no GND."],
                  "Bateria baixa: 6.48 V"))
    E.append(caso("TC-32", "Memória (flash) saudável", "RNF-03",
                  "Confirmar que as gravações na memória não falham.",
                  "Durante todos os testes acima.",
                  ["Fique de olho no serial durante os testes de erro, bloqueio e troca de senha."],
                  ["Não aparece <font name='Mono'>[NVS] falha na verificacao</font>.",
                   "Se aparecer só <font name='Mono'>tentativa 1/3</font> e o teste passar, o firmware se "
                   "recuperou. Se aparecer muito, troque a porta/cabo USB ou a bateria."]))
    E.append(caso("TC-33", "Display (quando chegar)", "RF-07",
                  "Confirmar o módulo TM1637.",
                  "Módulo ligado (VCC no 3V3, DIO no D18, CLK no D19) e <font name='Mono'>TEM_DISPLAY = true</font> gravado.",
                  ["Acorde o cofre.", "Digite o desafio e a senha.", "Abra o cofre; provoque um bloqueio."],
                  ["Desafio no meio do display (ex.: <font name='Mono'>  47  </font>); o ponto acende a cada dígito certo.",
                   "Senha aparece como <font name='Mono'>123___</font>.",
                   "Aberto: <font name='Mono'>OPEn</font>. Bloqueio: <font name='Mono'>bLOC</font>. Dormindo: apagado.",
                   "Dígitos fora de ordem: ajuste <font name='Mono'>POS_TM</font>."]))

    # ---------------- folha de resultados
    E.append(PageBreak())
    E.append(P("10. Folha de resultados", "h1"))
    E.append(P("Resumo para preencher no fim. Data: ____/____/______   Responsável: ______________________"))
    linhas = [["ID", "Caso", "Passou", "Falhou"]] + [[c, t, "☐", "☐"] for c, t in RESUMO]
    t = tabela(linhas, [44, None, 50, 50], destaque_col0=True)
    t.setStyle(TableStyle([("ALIGN", (2, 0), (3, -1), "CENTER")]))
    E.append(t)
    doc.multiBuild(E)


if __name__ == "__main__":
    construir()
    print("gerado:", SAIDA)

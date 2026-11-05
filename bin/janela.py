#!/usr/bin/env python3
"""Janela de acompanhamento do fluxo SDD (tkinter, sem dependências).

Aberta sempre, por padrão, pelo fluxo.py quando a feature é iniciada; não precisa ser chamada à mão.
Se não conseguir abrir (sem tkinter ou sem tela), o fluxo.py avisa e indica o painel de terminal (painel.py --watch). Lê os mesmos arquivos do
painel de terminal (specs/<f>/status.md e eventos.jsonl) a cada 2 s, sem servidor, sem rede e sem usar o modelo.
  python .agents/bin/janela.py <feature> [--raiz DIR] [--topo]
Fechar a janela é lembrado (specs/<f>/.janela-fechada): o fluxo.py não a reabre; `iniciar` limpa o lembrete.
Variáveis: SDD_SEM_JANELA=1 desliga a abertura automática; SDD_JANELA_ESPERA=N muda os 30 s em que a janela fica
aberta depois de a feature ser concluída.
"""
import argparse
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import painel  # noqa: E402

ANSI = re.compile(r"\x1b\[([0-9;]*)m")
CODIGOS = {"32": "ok", "1;36": "atual", "1;33": "alerta", "31": "erro", "2": "fraco", "1": "forte"}
ESTILOS = {"ok": {"foreground": "#6cc070"}, "atual": {"foreground": "#4fc1ff"}, "alerta": {"foreground": "#ffcc00"},
           "erro": {"foreground": "#ff6b6b"}, "fraco": {"foreground": "#8a8a8a"}, "forte": {"foreground": "#ffffff"}}
INTERVALO_MS = 2000
FUNDO = "#0b1224"
PAINEL = "#192440"
CORES = ["#42baff", "#ad70f8", "#f36acb", "#fb916c", "#51d7db", "#72d891", "#ed6e9d"]
ROTULOS = painel.ETAPAS  # A apresentação mantém os nomes e a ordem definidos pelo fluxo.


def progresso(campos):
    """Conta os passos anteriores ao atual; o passo em execução ainda não está completo."""
    etapas = [e for e in ROTULOS if not (e == "qa" and campos.get("QA") == "dispensado")]
    etapa = campos.get("Etapa", "")
    if "CONCLU" in campos.get("Situação", "").upper() or etapa.startswith("conclu"):
        completos = len(etapas)
    elif etapa in ROTULOS:
        completos = sum(ROTULOS.index(e) < ROTULOS.index(etapa) for e in etapas)
    else:
        completos = 0
    return completos, len(etapas), 100 * completos / len(etapas)


class Escritorio:
    """Escritório desenhado no Canvas; animação local independente da leitura do fluxo."""

    def __init__(self, tk, root):
        import tkinter.font as tkfont
        familias = set(tkfont.families(root))
        self.fonte = next((f for f in ("Pixel Operator", "VT323", "Fixedsys", "Terminal", "Consolas")
                           if f in familias), "Courier")
        self.medida = tkfont.Font(root=root, family=self.fonte, size=12, weight="bold")
        self.canvas = tk.Canvas(root, bg=FUNDO, height=400, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.campos = {}
        self.quadro = 0
        self.posicao = [140.0, 152.0]
        self.dev_acordado = False
        self.quadro_despertar = None
        self.canvas.bind("<Configure>", lambda _: self.desenhar())
        self.animar()

    def atualizar(self, campos):
        self.campos = campos

    def dev_no_sofa(self, x, y, acordado):
        """DEV maior que os agentes das mesas; desperta quando o orquestrador chega."""
        c = self.canvas
        cor = "#58ef9a" if acordado else "#b497f4"
        respiracao = (self.quadro//12 % 2) if not acordado else 0
        c.create_oval(x-61, y+38, x+65, y+49, fill="#17223c", outline="", tags="sofa")
        c.create_rectangle(x-55, y-4, x+55, y+38, fill="#55468c", outline="#8070ba", width=2, tags="sofa")
        c.create_rectangle(x-48, y+23, x+48, y+36, fill="#7963b4", outline="", tags="sofa")
        c.create_line(x, y+24, x, y+35, fill="#4a3c7c", width=2, tags="sofa")
        for lado in (-1, 1):
            c.create_rectangle(x+lado*53-7, y+13, x+lado*53+7, y+40,
                               fill="#8c77c8", outline="", tags="sofa")
            c.create_rectangle(x+lado*44-4, y+40, x+lado*44+4, y+47,
                               fill="#302b4b", outline="", tags="sofa")
        cabeca_y = y+respiracao
        if not acordado:
            # Cotovelos abertos e mãos encontrando-se atrás da cabeça.
            c.create_line(x-21, y+14, x-37, y-9, x-12, y-22,
                          fill=cor, width=7, joinstyle="miter", tags="dev-relaxado")
            c.create_line(x+9, y+14, x+24, y-9, x-4, y-22,
                          fill=cor, width=7, joinstyle="miter", tags="dev-relaxado")
        else:
            for lado in (-1, 1):
                c.create_line(x-7+lado*17, y+9, x-7+lado*23, y+27,
                              fill=cor, width=7, tags="dev-acordado")
        c.create_rectangle(x-23, cabeca_y-25, x+7, cabeca_y+1, fill=cor,
                           outline="#121b30", width=2, tags="dev")
        c.create_rectangle(x-18, cabeca_y-18, x+2, cabeca_y-5,
                           fill="#25314e", outline="", tags="dev")
        for olho_x in (x-13, x-3):
            if acordado:
                c.create_rectangle(olho_x-1, cabeca_y-15, olho_x+2, cabeca_y-9,
                                   fill="#e9fff2", outline="", tags="dev-acordado")
            else:
                c.create_line(olho_x-2, cabeca_y-10, olho_x+2, cabeca_y-10,
                              fill=cor, width=2, tags="dev-relaxado")
        c.create_rectangle(x-20, y+4, x+9, y+25, fill=cor, outline="", tags="dev")
        # Coxas apoiadas no assento; joelhos dobrados e canelas descendo à frente.
        for deslocamento in (-10, 5):
            c.create_line(x+deslocamento, y+25, x+deslocamento+7, y+32,
                          x+deslocamento+7, y+45, fill=cor, width=7,
                          joinstyle="miter", tags="dev")
            c.create_rectangle(x+deslocamento+4, y+43, x+deslocamento+16, y+49,
                               fill="#28334e", outline=cor, width=1, tags="dev")
        if not acordado:
            for i in range(3):
                subida = (self.quadro*0.7+i*13) % 40
                c.create_text(x+30+subida/3, y-12-subida, text="z" if i == 0 else "Z",
                              fill="#cab9f3", font=(self.fonte, 10+i*2, "bold"), tags="dev-sono")
        c.create_text(x, y+62, text="DEV", fill=cor,
                      font=(self.fonte, 12, "bold"), tags="dev-legenda")

    def boneco(self, x, y, cor, trabalhando=False, andando=False, escala=1, comemorando=False):
        c = self.canvas
        anteriores = set(c.find_all()) if escala != 1 else None
        balanco = (self.quadro // 3 % 2) * 3 if trabalhando or andando else 0
        c.create_oval(x-13, y+25, x+16, y+31, fill="#0b1220", outline="")
        c.create_rectangle(x-10, y-13, x+10, y+4, fill=cor, outline="#080e1b", width=2)
        c.create_rectangle(x-6, y-8, x+6, y-2, fill="#17253e", outline="")
        c.create_rectangle(x-4, y-7, x-2, y-4, fill="#e8f6ff", outline="")
        c.create_rectangle(x+2, y-7, x+4, y-4, fill="#e8f6ff", outline="")
        c.create_rectangle(x-7, y+6, x+7, y+19, fill=cor, outline="")
        for lado in (-1, 1):
            if comemorando:
                c.create_line(x+lado*9, y+10, x+lado*16, y+3, x+lado*16, y-17,
                              fill=cor, width=4, capstyle="butt", joinstyle="miter")
            else:
                c.create_rectangle(x+lado*10-2, y+8-balanco, x+lado*10+2, y+17-balanco,
                                   fill=cor, outline="")
            passo = balanco if lado == 1 else -balanco
            c.create_rectangle(x+lado*4-2, y+20+passo, x+lado*4+2, y+26+passo,
                               fill=cor, outline="")
        if anteriores is not None:
            for item in set(c.find_all())-anteriores:
                c.scale(item, x, y, escala, escala)

    def ambiente(self):
        """Cenário em pixel art desenhado localmente, sem arquivos de imagem."""
        c = self.canvas
        c.create_rectangle(0, 0, 1280, 440, fill="#1b284c", outline="")
        # Tijolos e luz ambiente na parede.
        for linha in range(16):
            y = linha*24
            c.create_line(0, y, 1280, y, fill="#202f57")
            for x in range(-50+(linha % 2)*50, 1280, 100):
                c.create_line(x, y, x, y+24, fill="#202f57")
        c.create_polygon(0, 0, 150, 30, 150, 380, 0, 440, fill="#232947", outline="#344163")
        # Janela e silhueta da cidade ao anoitecer.
        c.create_rectangle(5, 50, 95, 277, fill="#111b3c", outline="#665582", width=8)
        for faixa, cor in enumerate(("#182b61", "#303b7b", "#51427f", "#775084")):
            c.create_rectangle(10, 56+faixa*54, 89, 110+faixa*54, fill=cor, outline="")
        for i, (x, y) in enumerate(((11, 190), (30, 165), (50, 204), (70, 180))):
            c.create_rectangle(x, y, x+18, 270, fill="#14213e", outline="")
            for wx in range(x+4, x+17, 7):
                for wy in range(y+8, 265, 14):
                    c.create_rectangle(wx, wy, wx+2, wy+3, fill="#ad86bd" if i % 2 else "#efbf76", outline="")
        c.create_line(50, 55, 50, 273, fill="#4b4670", width=6)
        c.create_line(8, 150, 92, 150, fill="#4b4670", width=6)
        # Letreiro, armário e estante.
        c.create_rectangle(108, 65, 180, 127, fill="#172443", outline="#6a64ae", width=4)
        c.create_text(144, 96, text="SDD", fill="#65dcff", font=(self.fonte, 24, "bold"))
        c.create_rectangle(100, 264, 163, 379, fill="#344261", outline="#566488", width=2)
        for y in (267, 303, 339):
            c.create_rectangle(105, y, 158, y+32, outline="#1b2844", fill="#3d4d6c")
            c.create_rectangle(126, y+11, 138, y+14, fill="#9ca0ac", outline="")
        c.create_rectangle(1224, 155, 1278, 379, fill="#493f59", outline="#71617b", width=3)
        for y in (210, 267, 324, 375):
            c.create_rectangle(1228, y, 1276, y+5, fill="#9e7d85", outline="")
            for i, cor in enumerate(("#669bb0", "#ad796f", "#af9e7a", "#876b9e")):
                c.create_rectangle(1231+i*10, y-32+i % 2*8, 1238+i*10, y-1, fill=cor, outline="")
        c.create_rectangle(1218, 66, 1271, 129, fill="#172443", outline="#77627e", width=4)
        c.create_text(1245, 98, text="</>", fill="#93b7ee", font=(self.fonte, 15, "bold"))
        # Piso em perspectiva e plataformas sob cada fileira.
        c.create_rectangle(0, 383, 1280, 440, fill="#55475d", outline="")
        for y in (385, 404, 428):
            c.create_line(0, y, 1280, y, fill="#856375", width=2)
        for x in range(-400, 1600, 90):
            c.create_line(640+(x-640)*.75, 383, x, 440, fill="#393852", width=2)
        for y in (151, 263, 375):
            c.create_polygon(167, y-2, 1208, y-2, 1230, y+9, 145, y+9,
                             fill="#8d6c7b", outline="#b08587")
            c.create_rectangle(145, y+9, 1230, y+17, fill="#493f60", outline="")
        # Luminárias suspendidas.
        for x in (285, 520, 755, 990, 1180):
            c.create_line(x, 0, x, 18, fill="#0b1224", width=4)
            c.create_polygon(x-25, 34, x-15, 19, x+15, 19, x+25, 34,
                             fill="#0c162b", outline="#394264", width=2)
            c.create_rectangle(x-23, 34, x+23, 37, fill="#ffe5a0", outline="")
            c.create_rectangle(x-15, 38, x+15, 40, fill="#9f7972", outline="")
        for x, y in ((55, 373), (130, 257), (1193, 156), (1250, 373)):
            self.planta(x, y)

    def planta(self, x, y):
        c = self.canvas
        c.create_polygon(x-12, y-19, x+12, y-19, x+9, y+4, x-9, y+4,
                         fill="#65748b", outline="#98a1b0")
        c.create_line(x, y-19, x, y-62, fill="#427657", width=4)
        for dx, dy in ((-16, -40), (14, -48), (-12, -61), (10, -68), (-20, -54)):
            c.create_line(x, y-23, x+dx, y+dy, fill="#386d53", width=4)
            c.create_polygon(x+dx-8, y+dy-4, x+dx+2, y+dy-9, x+dx+9, y+dy+2,
                             x+dx, y+dy+5, fill="#5aaf72", outline="#366a50")

    def placa(self, x, y):
        x1, y1, x2, y2, raio = x-82, y-36, x+82, y-16, 6
        self.canvas.create_polygon(
            x1+raio, y1, x2-raio, y1, x2, y1, x2, y1+raio,
            x2, y2-raio, x2, y2, x2-raio, y2, x1+raio, y2,
            x1, y2, x1, y2-raio, x1, y1+raio, x1, y1,
            smooth=True, splinesteps=12, fill="#0d172c", outline="#45578a", tags="placa-mesa")

    def desenhar(self):
        c = self.canvas
        c.delete("all")
        self.ambiente()
        etapa = self.campos.get("Etapa", "")
        situacao = self.campos.get("Situação", "")
        concluida = "CONCLU" in situacao.upper() or etapa.startswith("conclu")
        if not concluida:
            self.dev_acordado = False
            self.quadro_despertar = None
        aguardando = "AGUARDANDO" in situacao.upper()
        atual = ROTULOS.index(etapa) if etapa in ROTULOS else -1
        destinos = []
        for i, nome in enumerate(ROTULOS):
            x, y = 245+(i % 5)*218, 112+(i//5)*112
            destinos.append((x, y+40))
            ativo = i == atual and not concluida
            dispensada = nome == "qa" and self.campos.get("QA") == "dispensado"
            completa = (concluida or 0 <= i < atual) and not dispensada
            cor = "#40ef9c" if completa else "#ffdc50" if ativo else CORES[i % len(CORES)]
            if ativo:
                c.create_rectangle(x-86, y-65, x+86, y+55, fill="#35304e", outline=cor, width=3,
                                   tags="mesa-atual")
            self.placa(x, y)
            c.create_text(x, y-26, text=f"{i+1:02d} · {nome}", fill=cor,
                          font=(self.fonte, 12, "bold"), tags="nome-mesa")
            if completa:
                c.create_oval(x-76, y-33, x-63, y-20, fill=cor, outline="")
                c.create_line(x-73, y-27, x-70, y-24, x-66, y-29, fill="#153c37", width=2)
            self.boneco(x+25, y, cor, trabalhando=ativo and not aguardando, comemorando=completa)
            # Tampo e pernas mantêm a cor original em todos os estados.
            c.create_rectangle(x-57, y+19, x+57, y+31, fill="#617fa6", outline="#17233c", width=2)
            c.create_rectangle(x-50, y+20, x+50, y+24, fill="#91abc5", outline="")
            for dx in (-46, 46):
                c.create_rectangle(x+dx-3, y+31, x+dx+3, y+46, fill="#263753", outline="#101a30")
            c.create_rectangle(x-40, y-14, x-3, y+15, fill="#0b1427", outline=cor, width=3)
            c.create_rectangle(x-27, y+16, x-17, y+19, fill=cor, outline="")
            if ativo and not aguardando:
                for barra in range(3):
                    h = 5+(self.quadro//3+barra*3) % 16
                    c.create_rectangle(x-33+barra*9, y+9-h, x-29+barra*9, y+9, fill=cor, outline="")
            else:
                c.create_line(x-34, y+2, x-10, y+2, fill=cor, width=2)
        destino_sofa = (1040, 376)
        destino = destino_sofa if concluida else destinos[atual] if atual >= 0 else (140, 385)
        x, y = self.posicao
        alvo_x, alvo_y = destino
        if abs(y-alvo_y) > 1:
            alvo_x = 140
            if abs(x-140) > 1:
                alvo_y = y
        distancia = max(abs(alvo_x-x), abs(alvo_y-y))
        if distancia > 1:
            fator = min(1, 10/distancia)
            self.posicao = [x+(alvo_x-x)*fator, y+(alvo_y-y)*fator]
        chegou_ao_sofa = concluida and max(abs(a-b) for a, b in zip(self.posicao, destino_sofa)) <= 1
        if chegou_ao_sofa and not self.dev_acordado:
            self.dev_acordado = True
            self.quadro_despertar = self.quadro
        chamando_dev = self.quadro_despertar is not None and self.quadro-self.quadro_despertar < 18
        self.dev_no_sofa(1117, 336, self.dev_acordado)
        antes_orquestrador = set(c.find_all())
        self.boneco(*self.posicao, "#ffdc50", andando=distancia > 1, comemorando=chamando_dev)
        c.create_rectangle(self.posicao[0]-72, self.posicao[1]-4,
                           self.posicao[0]-18, self.posicao[1]+20,
                           fill="#111b30", outline="#ffdc50", width=2)
        c.create_text(self.posicao[0]-45, self.posicao[1]+8, text="ORQ", fill="#ffdc50",
                      font=(self.fonte, 11, "bold"))
        for item in set(c.find_all())-antes_orquestrador:
            c.addtag_withtag("orquestrador", item)
        if concluida and self.dev_acordado:
            c.create_text(self.posicao[0]-10, self.posicao[1]-30, text="ACORDA, DEV!",
                          fill="#ffdc50", font=(self.fonte, 10, "bold"), tags="chamado-dev")
        # O cenário tem coordenadas próprias: redimensionar a janela não altera os corredores.
        largura, altura = max(1, c.winfo_width()), max(1, c.winfo_height())
        escala = min(largura/1280, altura/440)
        c.scale("all", 0, 0, escala, escala)
        c.move("all", (largura-1280*escala)/2, (altura-440*escala)/2)
        for item in c.find_all():
            if c.type(item) == "text":
                tamanho = 22 if c.itemcget(item, "text") == "SDD" else 12
                c.itemconfigure(item, font=(self.fonte, max(7, round(tamanho*escala)), "bold"))

    def animar(self):
        self.quadro += 1
        self.desenhar()
        self.canvas.after(80, self.animar)


def segmentos(texto):
    """Divide um texto com sequências ANSI em (trecho, tag|None)."""
    saida, tag, pos = [], None, 0
    for m in ANSI.finditer(texto):
        if m.start() > pos:
            saida.append((texto[pos:m.start()], tag))
        tag = CODIGOS.get(m.group(1))  # '0' (reset) e desconhecidos -> sem tag
        pos = m.end()
    if pos < len(texto):
        saida.append((texto[pos:], tag))
    return saida


def linhas_da_feature(raiz, feature, largura):
    fdir = painel.achar_feature(raiz, feature)
    if fdir is None or not (fdir / "status.md").exists():
        return None, [" Aguardando o início da feature..."], {}
    try:
        campos, _, qa = painel.ler_status(fdir / "status.md")
        campos["QA"] = qa
        campos["_eventos"] = painel.ler_eventos(fdir / "eventos.jsonl")
        return fdir, painel.montar(raiz, fdir, largura), campos
    except (OSError, ValueError) as erro:  # arquivo sendo gravado no momento
        return fdir, [f" Lendo... ({erro})"], {}


def formatar_detalhes(caixa):
    """Aplica hierarquia visual ao texto, preservando conteúdo e cores de estado."""
    for numero, linha in enumerate(caixa.get("1.0", "end-1c").splitlines(), 1):
        texto = linha.strip()
        if texto.startswith(("SDD ·", "DEMONSTRAÇÃO ·", "Últimos eventos", "Consumo dos subagentes")):
            caixa.tag_add("titulo_secao", f"{numero}.0", f"{numero}.end")
        elif re.match(r"Repo\s+Onda\s+Fase\s+Ciclo", texto):
            caixa.tag_add("cabecalho_tabela", f"{numero}.0", f"{numero}.end")
        # Destaca somente o rótulo; valores longos continuam com a fonte do corpo.
        for rotulo in re.finditer(
                r"(?:^\s*|\s{2,})(Agora|Próxima ação|Decisão pendente|Pendências|Arquivo|QA|"
                r"Contratos congelados|Etapa|Situação|por modelo):", linha):
            caixa.tag_add("rotulo", f"{numero}.{rotulo.start(1)}", f"{numero}.{rotulo.end()}")


def main(controles=None):
    ap = argparse.ArgumentParser(description="Janela de acompanhamento do fluxo SDD")
    ap.add_argument("feature")
    ap.add_argument("--raiz", default=".")
    ap.add_argument("--topo", action="store_true", help="mantém a janela sempre no topo")
    ap.add_argument("--uma-vez", action="store_true", help="monta o conteúdo uma vez, imprime o texto e sai (teste)")
    a = ap.parse_args()
    raiz = Path(a.raiz).resolve()
    fdir = raiz / "specs" / a.feature
    vivo, fechada = fdir / ".janela", fdir / ".janela-fechada"
    painel.usar_cor = True

    try:
        import tkinter as tk
        import tkinter.font as tkfont
        root = tk.Tk()
    except Exception:  # sem tkinter ou sem tela: o fluxo.py segue sem janela
        sys.exit(3)

    if not a.uma_vez and vivo.exists() and time.time() - vivo.stat().st_mtime < 8:
        if not vivo.read_text(encoding="utf-8").startswith("lancando"):  # "lancando" = marca do próprio fluxo.py
            sys.exit(0)  # já há uma janela viva para esta feature

    escondida = a.uma_vez or bool(os.environ.get("SDD_JANELA_TESTE"))
    root.title(f"SDD · {a.feature}")
    root.configure(bg=FUNDO)
    escritorio = Escritorio(tk, root)
    from interface import PainelAcompanhamento
    interface = PainelAcompanhamento(root, escritorio, a.feature, progresso, controles)
    caixa = interface.caixa
    fonte = tkfont.Font(family="Consolas", size=10)
    if a.topo:
        root.attributes("-topmost", True)
    largura_tela, altura_tela = root.winfo_screenwidth(), root.winfo_screenheight()
    largura_janela, altura_janela = min(1600, largura_tela-60), min(960, altura_tela-100)
    root.geometry(f"{largura_janela}x{altura_janela}+{max(0, largura_tela-largura_janela-30)}+30")
    root.minsize(min(1120, largura_tela-60), min(860, altura_tela-100))
    if escondida:
        root.withdraw()

    estado = {"texto": None, "aguardando": False, "concluida_em": None}

    def fechar(lembrar):
        if lembrar:
            try:
                fechada.write_text("fechada pelo usuário\n", encoding="utf-8")
            except OSError:
                pass
        try:
            vivo.unlink()
        except OSError:
            pass
        root.destroy()

    def desenhar(linhas):
        texto = "\n".join(linhas)
        if texto == estado["texto"]:
            return
        estado["texto"] = texto
        topo = caixa.yview()[0]
        caixa.configure(state="normal")
        caixa.delete("1.0", "end")
        for trecho, tag in segmentos(texto):
            caixa.insert("end", trecho, tag) if tag else caixa.insert("end", trecho)
        formatar_detalhes(caixa)
        caixa.configure(state="disabled")
        caixa.yview_moveto(topo)

    def passo():
        try:
            vivo.parent.mkdir(parents=True, exist_ok=True)
            vivo.write_text(f"{os.getpid()} {time.time():.0f}\n", encoding="utf-8")
        except OSError:
            pass
        largura = max(60, min(caixa.winfo_width() // max(1, fonte.measure("0")), 120))
        _, linhas, campos = linhas_da_feature(raiz, a.feature, largura)
        escritorio.atualizar(campos)
        interface.atualizar(campos)
        desenhar(linhas)
        situacao = campos.get("Situação", "").upper()
        aguardando, concluida = "AGUARDANDO" in situacao, "CONCLU" in situacao
        if aguardando and not estado["aguardando"] and not escondida:
            root.bell()
            root.lift()
            root.attributes("-topmost", True)
            root.after(2500, lambda: root.attributes("-topmost", a.topo))
        estado["aguardando"] = aguardando
        root.title(("⚠ AGUARDANDO VOCÊ · " if aguardando else "✔ concluída · " if concluida else "SDD · ") + a.feature)
        if concluida:
            estado["concluida_em"] = estado["concluida_em"] or time.time()
            if time.time() - estado["concluida_em"] > float(os.environ.get("SDD_JANELA_ESPERA", "30")):
                return fechar(False)
        else:
            estado["concluida_em"] = None
        root.after(500 if controles else INTERVALO_MS, passo)

    if a.uma_vez:
        _, linhas, _ = linhas_da_feature(raiz, a.feature, 100)
        desenhar(linhas)
        marcas = sorted({t for _, t in segmentos(estado["texto"]) if t})
        print(caixa.get("1.0", "end").rstrip())
        print(f"[tags usadas: {', '.join(marcas)}]")
        root.destroy()
        return
    root.protocol("WM_DELETE_WINDOW", lambda: fechar(True))
    root.bind("<<FecharPainel>>", lambda _: fechar(True))
    passo()
    root.mainloop()


if __name__ == "__main__":
    main()

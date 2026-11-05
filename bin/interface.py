"""Componentes do acompanhamento SDD em tkinter, sem dependências externas."""
import datetime
import tkinter as tk

import painel

FUNDO = "#0b1224"
PAINEL = "#101a30"
BORDA = "#526a9e"
TEXTO = "#e1e9ff"
FRACO = "#9baed3"
AMARELO = "#ffdc50"
VERDE = "#40ef9c"


def tempo(segundos):
    segundos = max(0, int(segundos))
    minutos, segundos = divmod(segundos, 60)
    return f"{minutos:02d}:{segundos:02d}"


class PainelAcompanhamento:
    def __init__(self, root, escritorio, feature, contar, controles=None):
        self.root, self.escritorio = root, escritorio
        self.controles = controles
        self.contar = contar
        self.assinatura_logs = None
        self.auto_scroll = tk.BooleanVar(value=True)
        escritorio.canvas.pack_forget()
        root.configure(bg=FUNDO)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=3, minsize=320)
        root.rowconfigure(2, weight=2, minsize=270)
        self.fonte = escritorio.fonte
        self.cabecalho = tk.Frame(root, bg=FUNDO, padx=22, pady=12)
        self.cabecalho.grid(row=0, column=0, sticky="ew")
        tk.Label(self.cabecalho, text="▣", fg=AMARELO, bg=FUNDO,
                 font=(self.fonte, 28)).pack(side="left", padx=(0, 18))
        titulos = tk.Frame(self.cabecalho, bg=FUNDO)
        titulos.pack(side="left")
        tk.Label(titulos, text="SDD / ESCRITÓRIO DOS AGENTES", fg=TEXTO, bg=FUNDO,
                 font=(self.fonte, 20, "bold")).pack(anchor="w")
        tk.Label(titulos, text="Orquestração de agentes com IA", fg=FRACO, bg=FUNDO,
                 font=("Consolas", 10)).pack(anchor="w", pady=(3, 0))
        self.situacao_topo = tk.Label(self.cabecalho, text="● EM ESPERA", fg=VERDE,
                                      bg="#0b2930", padx=16, pady=8,
                                      font=("Consolas", 11, "bold"), relief="solid", bd=1)
        self.situacao_topo.pack(side="right")

        superior = tk.Frame(root, bg=FUNDO)
        superior.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 10))
        superior.columnconfigure(0, weight=1)
        superior.columnconfigure(1, minsize=295)
        superior.rowconfigure(0, weight=1)
        escritorio.canvas.pack_forget()
        escritorio.canvas.configure(highlightthickness=1, highlightbackground=BORDA)
        escritorio.canvas.grid(in_=superior, row=0, column=0, sticky="nsew", padx=(0, 12))
        # O Canvas nasceu na raiz; deve ficar acima do frame que o hospeda visualmente.
        escritorio.canvas.tk.call("raise", str(escritorio.canvas))
        resumo = self.painel(superior, "⚙ EXECUÇÃO", 0, 1)
        resumo.configure(width=295)
        resumo.pack_propagate(False)
        resumo.grid_propagate(False)
        resumo.rowconfigure(1, weight=1)
        corpo = tk.Frame(resumo, bg=PAINEL, padx=14, pady=8)
        corpo.grid(row=1, column=0, sticky="nsew")
        corpo.columnconfigure(0, weight=1)
        barra_titulo = tk.Frame(corpo, bg=PAINEL)
        barra_titulo.pack(fill="x")
        tk.Label(barra_titulo, text="Progresso geral", bg=PAINEL, fg=FRACO,
                 font=("Consolas", 11)).pack(side="left")
        self.porcentagem = tk.Label(barra_titulo, text="0%", bg=PAINEL, fg=AMARELO,
                                    font=(self.fonte, 22, "bold"))
        self.porcentagem.pack(side="right")
        self.barra = tk.Canvas(corpo, height=18, bg="#202d47", highlightthickness=1,
                              highlightbackground=BORDA, width=200)
        self.barra.pack(fill="x", pady=8)
        self.contagem = tk.Label(corpo, text="0 etapas concluídas", bg=PAINEL, fg=FRACO,
                                 font=("Consolas", 10), anchor="w")
        self.contagem.pack(fill="x", pady=(0, 8))
        self.resumo = {}
        for chave, titulo in (("etapa", "Etapa atual"), ("situacao", "Situação"),
                              ("agente", "Agente responsável"), ("tempo_etapa", "Tempo da etapa"),
                              ("tempo_total", "Tempo total")):
            bloco = tk.Frame(corpo, bg="#0c1426", highlightthickness=1,
                             highlightbackground="#293e65", padx=10, pady=4)
            bloco.pack(fill="x", pady=2)
            rotulo = tk.Label(bloco, text=titulo, bg="#0c1426", fg=FRACO, font=("Consolas", 9))
            valor = tk.Label(bloco, text="—", bg="#0c1426", fg=AMARELO if chave == "etapa" else TEXTO,
                            font=("Consolas", 11, "bold"), anchor="w", justify="left", wraplength=245)
            if chave.startswith("tempo_"):
                rotulo.pack(side="left")
                valor.pack(side="right")
            else:
                rotulo.pack(anchor="w")
                valor.pack(fill="x")
            self.resumo[chave] = valor

        inferior = tk.Frame(root, bg=FUNDO)
        inferior.grid(row=2, column=0, sticky="nsew", padx=12)
        inferior.rowconfigure(0, weight=1)
        inferior.columnconfigure(0, minsize=250)
        inferior.columnconfigure(1, weight=5, uniform="conteudo")
        inferior.columnconfigure(2, weight=6, uniform="conteudo")
        etapas = self.painel(inferior, f"ETAPAS DO FLUXO ({len(painel.ETAPAS)})", 0, 0)
        etapas.grid_configure(padx=(0, 12))
        self.lista = tk.Text(etapas, bg=PAINEL, fg=FRACO, bd=0, highlightthickness=0,
                             width=25, height=14, cursor="arrow", font=("Consolas", 10),
                             padx=10, pady=8, spacing1=1, spacing3=1, wrap="none")
        self.lista.grid(row=1, column=0, sticky="nsew")
        self.lista.tag_configure("ok", foreground=VERDE)
        self.lista.tag_configure("atual", foreground=AMARELO, background="#263149",
                                 font=("Consolas", 10, "bold"))
        self.lista.tag_configure("dispensada", foreground="#657593")
        detalhes = self.painel(inferior, "DETALHES DA EXECUÇÃO", 0, 1)
        detalhes.grid_configure(padx=(0, 12))
        logs = self.painel(inferior, "›_ LOGS EM TEMPO REAL", 0, 2)
        self.caixa = self.texto_rolavel(detalhes)
        self.logs = self.texto_rolavel(logs)
        tk.Checkbutton(logs, text="Auto scroll", variable=self.auto_scroll, bg=PAINEL,
                       fg=FRACO, selectcolor="#243655", activebackground=PAINEL,
                       activeforeground=TEXTO, font=("Consolas", 9), bd=0,
                       command=lambda: self.logs.see("end") if self.auto_scroll.get() else None
                       ).grid(row=0, column=0, sticky="e", padx=8)
        rodape = tk.Frame(root, bg=FUNDO)
        rodape.grid(row=3, column=0, sticky="ew", padx=12, pady=12)
        self.indicadores = {}
        for chave, titulo in (("total", "Etapas no fluxo"), ("completas", "Concluídas"),
                              ("andamento", "Em andamento"), ("aguardando", "A executar"),
                              ("tempo", "Tempo total")):
            bloco = tk.Frame(rodape, bg=PAINEL, highlightbackground=BORDA, highlightthickness=1,
                             padx=12, pady=8)
            bloco.pack(side="left", fill="both", expand=True, padx=(0, 8))
            valor = tk.Label(bloco, text="—", bg=PAINEL, fg=VERDE if chave == "completas" else TEXTO,
                             font=(self.fonte, 17, "bold"))
            valor.pack()
            tk.Label(bloco, text=titulo, bg=PAINEL, fg=FRACO, font=("Consolas", 9)).pack()
            self.indicadores[chave] = valor
    def painel(self, pai, titulo, linha, coluna):
        quadro = tk.Frame(pai, bg=PAINEL, highlightbackground=BORDA, highlightthickness=1)
        quadro.grid(row=linha, column=coluna, sticky="nsew")
        quadro.columnconfigure(0, weight=1)
        quadro.rowconfigure(1, weight=1)
        tk.Label(quadro, text=titulo, bg="#15213b", fg=TEXTO, anchor="w", padx=14, pady=9,
                 font=(self.fonte, 12, "bold")).grid(row=0, column=0, sticky="ew")
        return quadro

    def texto_rolavel(self, pai):
        caixa = tk.Text(pai, bg="#0c1426", fg=TEXTO, wrap="word", bd=0, highlightthickness=0,
                        padx=12, pady=10, font=("Consolas", 10), spacing1=2, spacing3=3,
                        width=20, height=8, cursor="arrow")
        caixa.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=8)
        barra = tk.Scrollbar(pai, command=caixa.yview, bg="#263655", troughcolor=PAINEL, width=10)
        barra.grid(row=1, column=1, sticky="ns", padx=(0, 8), pady=8)
        caixa.configure(yscrollcommand=barra.set)
        for nome, cor in (("ok", VERDE), ("atual", AMARELO), ("alerta", AMARELO),
                          ("erro", "#ff7997"), ("fraco", FRACO), ("forte", TEXTO)):
            caixa.tag_configure(nome, foreground=cor)
        caixa.tag_configure("titulo_secao", foreground=AMARELO, background="#1b2943",
                            font=("Consolas", 12, "bold"), spacing1=10, spacing3=7)
        caixa.tag_configure("rotulo", foreground=TEXTO, font=("Consolas", 10, "bold"))
        caixa.tag_configure("cabecalho_tabela", foreground=TEXTO, background="#243252")
        caixa.configure(state="disabled")
        return caixa

    def atualizar(self, campos):
        etapa = campos.get("Etapa", "")
        indice = painel.ETAPAS.index(etapa) if etapa in painel.ETAPAS else -1
        concluida = "CONCLU" in campos.get("Situação", "") or etapa.startswith("conclu")
        aguardando = "AGUARDANDO" in campos.get("Situação", "")
        completos, total, porcentagem = self.contar(campos)
        self.porcentagem.configure(text=f"{porcentagem:.0f}%")
        self.barra.delete("all")
        largura = max(1, self.barra.winfo_width())
        if completos:
            self.barra.create_rectangle(0, 0, largura*porcentagem/100, 20, fill=AMARELO, outline="")
        self.contagem.configure(text=f"{completos} de {total} etapas concluídas")
        pausado = self.controles and self.controles.pausado
        estado = "CONCLUÍDO" if concluida else "PAUSADO" if pausado else "AGUARDANDO VOCÊ" if aguardando else "EM OPERAÇÃO" if indice >= 0 else "EM ESPERA"
        self.situacao_topo.configure(text="● "+estado, fg=AMARELO if aguardando or pausado else VERDE)
        self.resumo["etapa"].configure(text=f"{indice+1:02d} · {etapa}" if indice >= 0 else "Finalizado" if concluida else "—")
        self.resumo["situacao"].configure(text=campos.get("Situação", "Aguardando início"))
        eventos = campos.get("_eventos", [])
        abertos = {}
        for evento in eventos:
            chave = (evento.get("papel"), evento.get("repo"))
            if evento.get("tipo") == "inicio":
                abertos[chave] = evento
            elif evento.get("tipo") == "fim":
                abertos.pop(chave, None)
        responsavel = " · ".join(dict.fromkeys(e.get("papel", "") for e in abertos.values()))
        self.resumo["agente"].configure(text=responsavel or campos.get("Agentes em curso", "—"))
        marcas = [(painel.ts(e), e) for e in eventos if painel.ts(e)]
        duracao_total = duracao_etapa = "—"
        if marcas:
            inicio = marcas[0][0]
            fim = marcas[-1][0] if concluida else datetime.datetime.now(inicio.tzinfo)
            duracao_total = tempo((fim-inicio).total_seconds())
            transicoes = [t for t, e in marcas if e.get("tipo") == "etapa" and e.get("etapa") == etapa]
            if transicoes or etapa == "entrada":
                duracao_etapa = tempo((fim-(transicoes[-1] if transicoes else inicio)).total_seconds())
        if "_tempo_total" in campos:
            duracao_total = tempo(campos["_tempo_total"])
            duracao_etapa = tempo(campos["_tempo_etapa"])
        self.resumo["tempo_total"].configure(text=duracao_total)
        self.resumo["tempo_etapa"].configure(text=duracao_etapa)
        em_andamento = int(indice >= 0 and not concluida)
        for chave, valor in (("total", total), ("completas", completos), ("andamento", em_andamento),
                             ("aguardando", max(0, total-completos-em_andamento)), ("tempo", duracao_total)):
            self.indicadores[chave].configure(text=str(valor))
        topo = self.lista.yview()[0]
        self.lista.configure(state="normal")
        self.lista.delete("1.0", "end")
        for i, nome in enumerate(painel.ETAPAS):
            dispensada = nome == "qa" and campos.get("QA") == "dispensado"
            completa = (concluida or 0 <= i < indice) and not dispensada
            atual = i == indice and not concluida
            tag = "dispensada" if dispensada else "ok" if completa else "atual" if atual else ""
            marca = "–" if dispensada else "✓" if completa else "▶" if atual else "○"
            self.lista.insert("end", f"{marca}  {i+1:02d} · {nome}\n", tag)
        self.lista.configure(state="disabled")
        self.lista.yview_moveto(topo)
        self.atualizar_logs(eventos)

    def atualizar_logs(self, eventos):
        assinatura = repr(eventos)
        if assinatura == self.assinatura_logs:
            return
        self.assinatura_logs = assinatura
        topo = self.logs.yview()[0]
        self.logs.configure(state="normal")
        self.logs.delete("1.0", "end")
        for e in eventos[-300:]:
            data = painel.ts(e)
            hora = data.strftime("%H:%M:%S") if data else "--:--:--"
            tipo = e.get("tipo", "")
            tag = "ok" if tipo == "fim" else "atual" if tipo == "etapa" else "fraco"
            if tipo == "etapa":
                texto = "Etapa iniciada: "+e.get("etapa", "")
            elif tipo in ("inicio", "fim"):
                texto = " · ".join(str(e[k]) for k in ("papel", "repo", "modo", "resultado") if e.get(k))
                texto = ("Início: " if tipo == "inicio" else "Concluído: ")+texto
            else:
                texto = str(e.get("texto") or e.get("situacao") or tipo)
            self.logs.insert("end", f"[{hora}]  ", "fraco")
            self.logs.insert("end", texto+"\n", tag)
        if not eventos:
            self.logs.insert("end", "Aguardando os eventos do fluxo…", "fraco")
        self.logs.configure(state="disabled")
        self.logs.see("end") if self.auto_scroll.get() else self.logs.yview_moveto(topo)

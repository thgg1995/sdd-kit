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
        return fdir, painel.montar(raiz, fdir, largura), painel.ler_status(fdir / "status.md")[0]
    except (OSError, ValueError) as erro:  # arquivo sendo gravado no momento
        return fdir, [f" Lendo... ({erro})"], {}


def main():
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
    root.configure(bg="#1e1e1e")
    fonte = tkfont.Font(family="Consolas" if os.name == "nt" else "Menlo" if sys.platform == "darwin" else "DejaVu Sans Mono",
                        size=10)
    caixa = tk.Text(root, bg="#1e1e1e", fg="#d4d4d4", font=fonte, wrap="none", borderwidth=0, highlightthickness=0,
                    padx=6, pady=6, cursor="arrow", width=100, height=26)
    caixa.pack(fill="both", expand=True)
    for tag, estilo in ESTILOS.items():
        caixa.tag_configure(tag, **estilo, **({"font": tkfont.Font(family=fonte.cget("family"), size=10, weight="bold")}
                                             if tag in ("forte", "atual", "alerta") else {}))
    if a.topo:
        root.attributes("-topmost", True)
    largura_tela, altura_tela = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"820x470+{max(0, largura_tela - 840)}+{max(0, altura_tela - 570)}")
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
        root.after(INTERVALO_MS, passo)

    if a.uma_vez:
        _, linhas, _ = linhas_da_feature(raiz, a.feature, 100)
        desenhar(linhas)
        marcas = sorted({t for _, t in segmentos(estado["texto"]) if t})
        print(caixa.get("1.0", "end").rstrip())
        print(f"[tags usadas: {', '.join(marcas)}]")
        root.destroy()
        return
    root.protocol("WM_DELETE_WINDOW", lambda: fechar(True))
    passo()
    root.mainloop()


if __name__ == "__main__":
    main()

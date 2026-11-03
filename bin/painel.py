#!/usr/bin/env python3
"""Painel do fluxo SDD no terminal: lê specs/<f>/status.md e specs/<f>/eventos.jsonl (gravados por fluxo.py).

Não usa o modelo de IA nem rede: só lê arquivos. Uso, a partir da raiz do workspace:
  python .agents/bin/painel.py            # mostra uma vez
  python .agents/bin/painel.py --watch    # atualiza sozinho (Ctrl+C para sair)
  python .agents/bin/painel.py <feature> --watch --intervalo 5
Sem <feature>, usa a feature em andamento mais recente (ou a última, se todas estiverem concluídas).
"""
import argparse
import datetime
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

ETAPAS = ["entrada", "constitution", "specify", "clarify", "stack", "plan", "techlead", "tasks", "analyze",
          "contratos", "ambiente", "implement", "converge", "qa"]
COR = {"ok": "\033[32m", "atual": "\033[1;36m", "alerta": "\033[1;33m", "erro": "\033[31m",
       "fraco": "\033[2m", "forte": "\033[1m", "fim": "\033[0m"}
usar_cor = True


def c(tipo, txt):
    return f"{COR[tipo]}{txt}{COR['fim']}" if usar_cor else txt


def ler_status(p):
    campos, repos, qa = {}, [], ""
    for linha in p.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"^(Etapa|Situação|Próxima ação|Contratos congelados|Pendências do humano|Agentes em curso):\s*(.*)$", linha)
        if m:
            campos[m.group(1)] = m.group(2).strip()
        elif linha.startswith("QA:"):
            qa = linha[3:].strip()
        elif linha.startswith("|") and not linha.startswith("|---") and "| Repo |" not in linha:
            cel = [x.strip() for x in linha.strip().strip("|").split("|")]
            if len(cel) >= 5:
                repos.append(cel[:5])
    return campos, repos, qa


def ler_eventos(p):
    if not p.exists():
        return []
    evs = []
    for linha in p.read_text(encoding="utf-8").splitlines():
        try:
            evs.append(json.loads(linha))
        except ValueError:
            pass
    return evs


def ts(ev):
    try:
        return datetime.datetime.fromisoformat(ev["ts"])
    except (KeyError, ValueError):
        return None


def dur(seg):
    seg = int(seg)
    h, r = divmod(seg, 3600)
    m, s = divmod(r, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m{s:02d}s"


def ktok(n):
    return f"{n / 1000:.0f}k" if n < 1_000_000 else f"{n / 1_000_000:.2f}M"


def achar_feature(raiz, nome):
    specs = raiz / "specs"
    if nome:
        return specs / nome
    cand = [d for d in specs.iterdir() if (d / "status.md").exists()] if specs.exists() else []
    if not cand:
        return None
    ativas = [d for d in cand if "CONCLU" not in (ler_status(d / "status.md")[0].get("Situação", "").upper())]
    return max(ativas or cand, key=lambda d: (d / "status.md").stat().st_mtime)


def perguntas(arq):
    """Perguntas da última rodada de um arquivo de repasse (clarifications.md, techlead/perguntas.md...)."""
    txt = arq.read_text(encoding="utf-8")
    rodadas = [m.start() for m in re.finditer(r"^## Rodada", txt, re.M)]
    trecho = txt[rodadas[-1]:] if rodadas else txt
    titulo = trecho.split("\n", 1)[0].lstrip("# ").strip() if rodadas else ""
    itens = []
    for bloco in re.split(r"^### ", trecho, flags=re.M)[1:]:
        cab = bloco.split("\n", 1)[0].strip()
        if not re.match(r"T?Q[\w-]*\b", cab):  # Q (PM) e TQ (tech lead)
            continue
        rec = re.search(r"Recomendad[oa]:?\**:?\s*(?:Opção\s+)?([^\s—.,]+)", bloco)
        resp = re.search(r"Resposta do humano:[ \t]*(.*)", bloco)
        itens.append((re.sub(r"\s*\([^()]*\)\s*$", "", cab), rec.group(1) if rec else "",
                      (resp.group(1).strip() if resp else "")))
    return titulo, itens


def montar(raiz, fdir, largura):
    campos, repos, qa = ler_status(fdir / "status.md")
    evs = ler_eventos(fdir / "eventos.jsonl")
    etapa = campos.get("Etapa", "?")
    sit = campos.get("Situação", "?")
    aguardando = "AGUARDANDO" in sit.upper()
    concluido = "CONCLU" in sit.upper() or etapa.startswith("conclu")
    agora = datetime.datetime.now()
    marcas = [ts(e) for e in evs if ts(e)]
    decorrido = ""
    if marcas:
        fim_t = max(marcas) if concluido else agora
        decorrido = " · " + dur((fim_t - min(marcas)).total_seconds())

    cor_sit = "ok" if concluido else ("alerta" if aguardando else "atual")
    rot_sit = "⚠ AGUARDANDO VOCÊ" if aguardando else sit
    linhas = [c("forte", f" SDD · {fdir.name}") + "   " + c(cor_sit, rot_sit) + c("fraco", decorrido),
              c("fraco", " " + "─" * (largura - 2))]

    # barra de etapas
    pos = len(ETAPAS) if concluido else (ETAPAS.index(etapa) if etapa in ETAPAS else -1)
    partes = []
    for i, e in enumerate(ETAPAS):
        if i < pos:
            partes.append(c("ok", f"✔ {e}"))
        elif i == pos:
            partes.append(c("alerta" if aguardando else "atual", f"▶ {e}"))
        else:
            partes.append(c("fraco", f"· {e}"))
    linha, vis = " ", 1
    for p, e in zip(partes, ETAPAS):
        tam = len(e) + 4
        if vis + tam > largura:
            linhas.append(linha)
            linha, vis = " ", 1
        linha += p + "  "
        vis += tam
    linhas += [linha, ""]

    # agente em execução: último início sem fim correspondente
    abertos = {}
    for e in evs:
        chave = (e.get("papel"), e.get("repo"))
        if e.get("tipo") == "inicio":
            abertos[chave] = e
        elif e.get("tipo") == "fim":
            abertos.pop(chave, None)
    for (papel, repo), e in abertos.items():
        t = ts(e)
        desc = " · ".join(x for x in (papel, repo, e.get("modo")) if x)
        linhas.append(" " + c("atual", "Agora: ") + desc + (c("fraco", f" · há {dur((agora - t).total_seconds())}") if t else ""))
    linhas.append(" Próxima ação: " + campos.get("Próxima ação", "?"))

    # decisão pendente
    pend = campos.get("Pendências do humano", "")
    if aguardando:
        linhas += ["", " " + c("alerta", "Decisão pendente: ") + pend]
        for caminho in dict.fromkeys(re.findall(r"(specs/[^\s,;)]+\.md)", pend)):  # gate e triagem podem vir juntos
            arq = raiz / caminho
            if not arq.exists():
                continue
            titulo, itens = perguntas(arq)
            linhas.append(c("fraco", f" Arquivo: {caminho}" + (f" · {titulo}" if titulo else "")))
            for cab, rec, resp in itens:
                marca = c("ok", "✔") if resp else " "
                fim_l = f"resp.: {resp}" if resp else (f"rec.: {rec}" if rec else "")
                espaco = largura - len(fim_l) - 6
                linhas.append(f"  {marca} {cab[:espaco].ljust(espaco)} " + c("fraco", fim_l))
        linhas.append(c("fraco", " Responda no chat, ou preencha \"Resposta do humano:\" no arquivo e diga \"continue\"."))
    elif pend and pend.lower() != "nenhuma":
        linhas.append(" " + c("fraco", "Pendências: ") + pend)

    # repositórios
    if repos:
        linhas += ["", c("forte", f" {'Repo':<28}{'Onda':>4}  {'Fase':<10}{'Ciclo':>5}  Último relatório")]
        for nome, onda, fase, ciclo, rel in repos:
            cor = {"aprovado": "ok", "bloqueado": "erro", "dev": "atual", "review": "atual"}.get(fase)
            fase_txt = c(cor, f"{fase:<10}") if cor else f"{fase:<10}"
            linhas.append(f" {nome[:28]:<28}{onda:>4}  {fase_txt}{ciclo:>5}  {rel[:max(10, largura - 55)]}")
    linhas.append(" QA: " + (qa or "dispensado") + "   Contratos congelados: " + campos.get("Contratos congelados", "?"))

    # últimos eventos
    vistos = [e for e in evs if e.get("tipo") != "inicio"][-8:]
    if vistos:
        linhas += ["", c("forte", " Últimos eventos")]
        for e in reversed(vistos):
            t = ts(e)
            hora = t.strftime("%H:%M") if t else "--:--"
            tipo = e.get("tipo")
            if tipo == "fim":
                quem = " ".join(x for x in (e.get("papel"), e.get("repo"), e.get("modo")) if x)
                extra = " ".join(x for x in ((ktok(e["tokens"]) + " tok") if e.get("tokens") else "",
                                             dur(e["ms"] / 1000) if e.get("ms") else "") if x)
                txt = f"{quem:<34} {e.get('resultado', '')}"
                txt = txt[:largura - len(extra) - 10]
                linhas.append(f" {hora}  {txt}  " + c("fraco", extra))
            elif tipo == "consumo":
                quem = " ".join(x for x in (e.get("papel"), e.get("repo"), e.get("modo")) if x)
                extra = " · ".join(x for x in ((ktok(e["tokens"]) + " tok") if e.get("tokens") else "",
                                               f"{e['ferramentas']} ferr" if e.get("ferramentas") else "",
                                               dur(e["ms"] / 1000) if e.get("ms") else "") if x)
                linhas.append(f" {hora}  " + c("fraco", f"consumo {quem}: {extra}"))
            elif tipo == "etapa":
                linhas.append(f" {hora}  " + c("fraco", f"etapa → {e.get('etapa')}"))
            elif tipo == "situacao":
                linhas.append(f" {hora}  " + c("alerta" if "AGUARD" in e.get("situacao", "") else "fraco",
                                                f"situação → {e.get('situacao')}"))
            elif tipo == "repo":
                linhas.append(f" {hora}  " + c("fraco", f"{e.get('repo')} → {e.get('fase')} (ciclo {e.get('ciclo')})"))
            else:
                linhas.append(f" {hora}  " + c("fraco", str(e.get("texto", "")))[:largura + 12])

    # consumo por papel
    # eventos 'fim' contam as chamadas; 'fim' e 'consumo' somam tokens e tempo; cada 'consumo' cobre um 'fim' sem dados
    por_papel = {}
    for e in evs:
        if e.get("tipo") in ("fim", "consumo") and e.get("papel"):
            d = por_papel.setdefault(e["papel"], [0, 0, 0, 0])
            d[0] += e.get("tokens") or 0
            d[1] += e.get("ms") or 0
            if e["tipo"] == "fim":
                d[2] += 1
                if not (e.get("tokens") or e.get("ferramentas") or e.get("ms")):
                    d[3] += 1
            else:
                d[3] -= 1
    if por_papel:
        total = sum(v[0] for v in por_papel.values())
        sem = sum(max(0, v[3]) for v in por_papel.values())
        partes = [f"{p} {ktok(v[0])} ({v[2]}×, {dur(v[1] / 1000)})" + (f" ⚠ {v[3]} sem dados" if v[3] > 0 else "")
                  for p, v in por_papel.items()]
        aviso = c("alerta", f"  ⚠ {sem} chamada(s) sem consumo registrado") if sem else ""
        linhas += ["", c("forte", " Consumo dos subagentes ") + c("fraco", f"total {ktok(total)}") + aviso]
        linha = " "
        for p in partes:
            if len(linha) + len(p) + 3 > largura:
                linhas.append(linha)
                linha = " "
            linha += p + " · "
        linhas.append(linha.rstrip(" ·"))
    por_modelo = {}
    for e in evs:
        if e.get("tipo") in ("fim", "consumo") and e.get("papel"):
            k = e.get("modelo") or "?"
            por_modelo[k] = por_modelo.get(k, 0) + (e.get("tokens") or 0)
    if any(k != "?" for k in por_modelo):
        linhas.append(" " + c("fraco", "por modelo: ") + " · ".join(f"{k} {ktok(v)}" for k, v in por_modelo.items()))
    return linhas


def main():
    global usar_cor
    ap = argparse.ArgumentParser(description="Painel do fluxo SDD")
    ap.add_argument("feature", nargs="?")
    ap.add_argument("--raiz", default=".")
    ap.add_argument("--watch", action="store_true", help="atualiza sozinho")
    ap.add_argument("--intervalo", type=float, default=2.0)
    ap.add_argument("--sem-cor", action="store_true")
    a = ap.parse_args()
    usar_cor = not a.sem_cor and sys.stdout.isatty()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    if os.name == "nt":
        os.system("")  # habilita as sequências ANSI no console do Windows
    raiz = Path(a.raiz)
    try:
        laco(a, raiz)
    except KeyboardInterrupt:
        print()


def laco(a, raiz):
    while True:
        fdir = achar_feature(raiz, a.feature)
        largura = max(60, min(shutil.get_terminal_size((100, 30)).columns, 120))
        if fdir is None or not (fdir / "status.md").exists():
            saida = [" Nenhuma feature com status.md em specs/ ainda."]
        else:
            try:
                saida = montar(raiz, fdir, largura)
            except (OSError, ValueError) as erro:  # arquivo sendo gravado no momento
                saida = [f" Lendo... ({erro})"]
        texto = "\n".join(saida)
        if not a.watch:
            print(texto)
            return
        print("\033[2J\033[H" + texto + "\n\n" + c("fraco", f" atualizado {time.strftime('%H:%M:%S')} · Ctrl+C para sair"),
              end="", flush=True)
        time.sleep(a.intervalo)


if __name__ == "__main__":
    main()

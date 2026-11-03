#!/usr/bin/env python3
"""Registro do fluxo SDD: atualiza specs/<f>/status.md e acrescenta eventos em specs/<f>/eventos.jsonl.

O orquestrador usa este script em vez de editar o status.md à mão; o painel (painel.py) lê os dois arquivos.
Uso, a partir da raiz do workspace:
  python .agents/bin/fluxo.py iniciar <f> <repo> [<repo> ...]
  python .agents/bin/fluxo.py status <f> [--etapa E] [--situacao andamento|aguardando|concluido]
                                         [--proxima TXT] [--pendencias TXT] [--contratos sim|não]
                                         [--qa TXT] [--agente PAPEL=ID | PAPEL=-]
  python .agents/bin/fluxo.py repo <f> <repo> [--onda N] [--fase F] [--ciclo N] [--relatorio CAMINHO]
  python .agents/bin/fluxo.py inicio <f> <papel> [--repo R] [--modo M] [--modelo NOME]
  python .agents/bin/fluxo.py fim <f> <papel> [--repo R] [--modo M] [--modelo NOME] --resultado TXT
                                         [--tokens N] [--ferramentas N] [--ms N]
  python .agents/bin/fluxo.py consumo <f> <papel> [--repo R] [--modo M] [--modelo NOME] [--tokens N] [--ferramentas N] [--ms N]
                                         # consumo que chegou depois do 'fim' (notificação de conclusão do subagente)
  python .agents/bin/fluxo.py evento <f> TXT
  python .agents/bin/fluxo.py conferir-donos <f>      # confere o mapa de donos (AGENTS.md 4.3); sai com 1 se houver falha
  python .agents/bin/fluxo.py conferir-prontidao <f> <repo>   # confere, por arquivo, se o dev pode começar; sai com 1 se houver falha
Em --pendencias, inclua o caminho do arquivo a responder (ex.: "gate, rodada 2: specs/<f>/clarifications.md"):
o painel mostra as perguntas dele.
"""
import argparse
import datetime
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ETAPAS = ["entrada", "constitution", "specify", "clarify", "stack", "plan", "techlead", "tasks", "analyze",
          "contratos", "ambiente", "implement", "converge", "qa", "concluído"]
SITUACOES = {"andamento": "EM ANDAMENTO", "aguardando": "AGUARDANDO HUMANO", "concluido": "CONCLUÍDO",
             "concluído": "CONCLUÍDO"}
FASES = ["pendente", "dev", "review", "aprovado", "bloqueado"]
CAMPOS = [("etapa", "Etapa"), ("situacao", "Situação"), ("proxima", "Próxima ação"),
          ("contratos", "Contratos congelados"), ("pendencias", "Pendências do humano"),
          ("agentes", "Agentes em curso")]
CABECALHO_TABELA = "| Repo | Onda | Fase | Ciclo | Último relatório |"


def agora():
    return datetime.datetime.now().isoformat(timespec="seconds")


def pasta(raiz, f):
    p = Path(raiz) / "specs" / f
    p.mkdir(parents=True, exist_ok=True)
    return p


def evento(raiz, f, **dados):
    dados = {"ts": agora(), **{k: v for k, v in dados.items() if v is not None}}
    with open(pasta(raiz, f) / "eventos.jsonl", "a", encoding="utf-8") as arq:
        arq.write(json.dumps(dados, ensure_ascii=False) + "\n")


def ler(raiz, f):
    p = pasta(raiz, f) / "status.md"
    if not p.exists():
        sys.exit(f"status.md não existe: {p} (use 'iniciar')")
    return p, p.read_text(encoding="utf-8").split("\n")


def gravar(p, linhas):
    p.write_text("\n".join(linhas), encoding="utf-8", newline="\n")


def campo(linhas, rotulo, valor):
    prefixo = rotulo + ":"
    for i, linha in enumerate(linhas):
        if linha.startswith(prefixo):
            antigo = linha[len(prefixo):].strip()
            linhas[i] = f"{prefixo} {valor}"
            return antigo
    # campo ausente (status antigo): insere depois de "Pendências do humano" ou do título
    alvo = next((i for i, l in enumerate(linhas) if l.startswith("Pendências do humano:")), 0)
    linhas.insert(alvo + 1, f"{prefixo} {valor}")
    return None


def valor(linhas, rotulo):
    prefixo = rotulo + ":"
    return next((l[len(prefixo):].strip() for l in linhas if l.startswith(prefixo)), "")


# Versão do processo gravada no status.md por `iniciar`. Checagens novas do `conferir-donos` valem só para features
# cujo "Processo" é igual ou maior que a versão em que foram criadas (feature sem o campo = processo 1).
PROCESSO = 2


def cmd_iniciar(a):
    p = pasta(a.raiz, a.feature) / "status.md"
    if p.exists():
        sys.exit(f"status.md já existe: {p}")
    (p.parent / ".janela-fechada").unlink(missing_ok=True)
    (p.parent / ".janela-indisponivel").unlink(missing_ok=True)
    linhas = [f"# Status: {a.feature}", "Etapa: entrada", "Situação: EM ANDAMENTO", "Próxima ação: ?",
              "Contratos congelados: não", "Pendências do humano: nenhuma", "Agentes em curso: —",
              f"Processo: {PROCESSO}", "",
              CABECALHO_TABELA, "|---|---|---|---|---|"]
    linhas += [f"| {r} | ? | pendente | 0 | — |" for r in a.repos]
    linhas += ["", "QA: dispensado", ""]
    gravar(p, linhas)
    evento(a.raiz, a.feature, tipo="iniciar", texto=f"feature iniciada ({', '.join(a.repos)})")


def cmd_status(a):
    p, linhas = ler(a.raiz, a.feature)
    if a.etapa:
        if a.etapa not in ETAPAS:
            sys.exit(f"etapa inválida: {a.etapa} (use {', '.join(ETAPAS)})")
        if campo(linhas, "Etapa", a.etapa) != a.etapa:
            evento(a.raiz, a.feature, tipo="etapa", etapa=a.etapa)
    if a.situacao:
        sit = SITUACOES.get(a.situacao.lower())
        if not sit:
            sys.exit(f"situação inválida: {a.situacao} (use andamento, aguardando ou concluido)")
        if campo(linhas, "Situação", sit) != sit:
            evento(a.raiz, a.feature, tipo="situacao", situacao=sit, pendencias=a.pendencias)
    if a.proxima is not None:
        campo(linhas, "Próxima ação", a.proxima)
    if a.pendencias is not None:
        campo(linhas, "Pendências do humano", a.pendencias)
    if a.contratos:
        if campo(linhas, "Contratos congelados", a.contratos) != a.contratos:
            evento(a.raiz, a.feature, tipo="contratos", texto=f"contratos congelados: {a.contratos}")
    if a.qa:
        campo(linhas, "QA", a.qa)
        evento(a.raiz, a.feature, tipo="qa", texto=a.qa)
    for item in a.agente or []:
        papel, _, ident = item.partition("=")
        atual = valor(linhas, "Agentes em curso")
        pares = dict(x.split(": ", 1) for x in atual.split(" | ") if ": " in x)
        if ident in ("", "-"):
            pares.pop(papel, None)
        else:
            pares[papel] = ident
        campo(linhas, "Agentes em curso", " | ".join(f"{k}: {v}" for k, v in pares.items()) or "—")
    gravar(p, linhas)


def cmd_repo(a):
    p, linhas = ler(a.raiz, a.feature)
    if a.fase and a.fase not in FASES:
        sys.exit(f"fase inválida: {a.fase} (use {', '.join(FASES)})")
    idx = next((i for i, l in enumerate(linhas) if re.match(rf"\|\s*{re.escape(a.repo)}\s*\|", l)), None)
    if idx is None:
        ultimo = max((i for i, l in enumerate(linhas) if l.startswith("|")), default=None)
        if ultimo is None:
            sys.exit("tabela de repositórios não encontrada no status.md")
        linhas.insert(ultimo + 1, f"| {a.repo} | ? | pendente | 0 | — |")
        idx = ultimo + 1
    cel = [c.strip() for c in linhas[idx].strip().strip("|").split("|")]
    antes = cel[2]
    for pos, novo in ((1, a.onda), (2, a.fase), (3, a.ciclo), (4, a.relatorio)):
        if novo is not None:
            cel[pos] = str(novo)
    linhas[idx] = "| " + " | ".join(cel) + " |"
    gravar(p, linhas)
    if a.fase and a.fase != antes:
        evento(a.raiz, a.feature, tipo="repo", repo=a.repo, fase=a.fase, ciclo=cel[3])


def cmd_inicio(a):
    evento(a.raiz, a.feature, tipo="inicio", papel=a.papel, repo=a.repo, modo=a.modo, modelo=a.modelo)


def cmd_fim(a):
    evento(a.raiz, a.feature, tipo="fim", papel=a.papel, repo=a.repo, modo=a.modo, modelo=a.modelo, resultado=a.resultado,
           tokens=a.tokens, ferramentas=a.ferramentas, ms=a.ms)
    if a.tokens is None and a.ferramentas is None and a.ms is None:
        print("aviso: consumo não informado; registre-o com 'consumo' quando a notificação de conclusão do subagente chegar")


def cmd_consumo(a):
    if a.tokens is None and a.ferramentas is None and a.ms is None:
        sys.exit("informe ao menos um de --tokens, --ferramentas, --ms")
    evento(a.raiz, a.feature, tipo="consumo", papel=a.papel, repo=a.repo, modo=a.modo, modelo=a.modelo,
           tokens=a.tokens, ferramentas=a.ferramentas, ms=a.ms)


def cmd_evento(a):
    evento(a.raiz, a.feature, tipo="nota", texto=a.texto)


def _linhas_com(arq, padrao):
    achados = []
    for n, linha in enumerate(arq.read_text(encoding="utf-8").splitlines(), 1):
        if re.search(padrao, linha):
            achados.append(f"{arq.name}:{n}")
    return achados


def _processo(base):
    """Versão do processo da feature (campo 'Processo' do status.md); sem o campo, 1."""
    st = base / "status.md"
    m = re.search(r"^Processo:\s*(\d+)", st.read_text(encoding="utf-8"), re.M) if st.exists() else None
    return int(m.group(1)) if m else 1


def _conferir_verificacoes(pesq, rel):
    """Seção 'Verificações' do research.md: presente (ou 'nenhum aplicável' no relatório) e cada item com motor+versão ou 'lacuna'."""
    if re.search(r"^Verificações:\s*nenhum aplic", rel, re.M):
        return []
    m = re.search(r"^#+\s*Verificações\b[^\n]*\n(.*?)(?=^#+\s|\Z)", pesq, re.M | re.S)
    if not m:
        return ["research.md sem a seção 'Verificações' (e o relatório não diz 'Verificações: nenhum aplicável')"]
    itens = [l for l in m.group(1).splitlines()
             if re.match(r"^\s*(-|\*|\|)", l) and not re.match(r"^\s*\|[\s:|-]*\|?\s*$", l)]
    itens = [l for l in itens if not re.search(r"\|\s*(artefato|item)\s*\|", l, re.I)]
    if not itens:
        return ["research.md: seção 'Verificações' sem itens (use 'Verificações: nenhum aplicável' no relatório se não houver)"]
    return [f"research.md, 'Verificações': item sem motor/versão nem 'lacuna': {l.strip()[:80]}"
            for l in itens if not re.search(r"lacuna|\d+(\.\d+)+", l, re.I)][:3]


def cmd_conferir_donos(a):
    """Confere se o que é do tech lead existe e se nenhum marcador dele ficou pendente (mapa de donos, AGENTS.md 4.3)."""
    raiz = Path(a.raiz)
    base = raiz / "specs" / a.feature
    if not base.is_dir():
        sys.exit(f"feature não existe: {base}")
    falhas = []
    repos = sorted(d.name for d in (base / "repos").glob("*") if d.is_dir()) if (base / "repos").is_dir() else []
    relatorio = base / "reports" / "techlead.md"
    ws = (raiz / "workspace.yaml").read_text(encoding="utf-8") if (raiz / "workspace.yaml").exists() else ""
    blocos = {}
    for bloco in re.split(r"\n  - name: ", ws)[1:]:
        blocos[bloco.splitlines()[0].strip()] = bloco
    tem_lib = any(re.search(r"^\s+kind:\s*lib", blocos.get(r, ""), re.M) for r in repos)
    planos = {r: base / "repos" / r / "plan.md" for r in repos}
    exige = len(repos) >= 2 or tem_lib or relatorio.exists() or any(
        pl.exists() and re.search(r"^Desenho técnico:\s*sim", pl.read_text(encoding="utf-8"), re.M) for pl in planos.values())

    # 1. marcador do tech lead sem resolver (crases = menção explicativa, não pendência)
    pendente = r"(?<!`)\[TECH LEAD(:|\])(?!`)"
    for arq in [base / n for n in ("plan.md", "research.md", "data-model.md", "quickstart.md")] + list(planos.values()):
        if arq.exists():
            falhas += [f"marcador [TECH LEAD] sem resolver em {x}" for x in _linhas_com(arq, pendente)[:3]]

    # 2. toda linha 'Desenho técnico' decidida (sim|não), por repositório
    for r, pl in planos.items():
        txt = pl.read_text(encoding="utf-8") if pl.exists() else ""
        m = re.search(r"^Desenho técnico:\s*(sim|não)", txt, re.M)
        if not m:
            falhas.append(f"repos/{r}/plan.md: linha 'Desenho técnico: sim|não' ausente ou indecisa")
        elif m.group(1) == "sim" and not re.search(r"^## Desenho técnico", txt, re.M):
            falhas.append(f"repos/{r}/plan.md: 'Desenho técnico: sim' sem a seção '## Desenho técnico'")

    if exige:
        # 3. relatório do tech lead
        if not relatorio.exists():
            falhas.append("reports/techlead.md ausente (tech lead não rodou)")
        else:
            rel = relatorio.read_text(encoding="utf-8")
            if not re.search(r"^Status:\s*OK", rel, re.M):
                falhas.append("reports/techlead.md sem 'Status: OK'")
            # 4. limites da plataforma verificados
            pesq = (base / "research.md").read_text(encoding="utf-8") if (base / "research.md").exists() else ""
            if "Limites verificados" not in pesq and not re.search(r"Limites verificados:\s*nenhum aplic", rel):
                falhas.append("research.md sem a seção 'Limites verificados' (e o relatório não diz 'nenhum aplicável')")
            # 4b. verificações com motor real (processo >= 2)
            if _processo(base) >= 2:
                falhas += _conferir_verificacoes(pesq, rel)
        # 5. contratos com dono, consumidores e versão
        contratos = [c for c in (base / "contracts").glob("*") if c.is_file()] if (base / "contracts").is_dir() else []
        if len(repos) >= 2 and not contratos:
            falhas.append("contracts/ vazio numa feature com mais de um repositório")
        for c in contratos:
            txt = c.read_text(encoding="utf-8")
            faltam = [k for k in ("owner", "consumers", "version") if not re.search(rf"^(x-)?{k}:", txt, re.M)]
            if faltam:
                falhas.append(f"contracts/{c.name}: faltam {', '.join(faltam)}")
        # 6. parte física do modelo de dados
        dm = base / "data-model.md"
        if dm.exists() and "(tech lead)" not in dm.read_text(encoding="utf-8").lower():
            falhas.append("data-model.md sem seção '(tech lead)' (dono, tipos físicos, chaves)")
        # 7. depends_on decidido para cada repositório da feature
        if ws:
            for r in repos:
                if r in blocos and "depends_on:" not in blocos[r]:
                    falhas.append(f"workspace.yaml: '{r}' sem depends_on")

    modo = "tech lead exigido" if exige else "tech lead dispensado (trabalho pequeno)"
    if falhas:
        evento(a.raiz, a.feature, tipo="nota", texto=f"conferir-donos: {len(falhas)} falha(s)")
        print(f"conferir-donos: {len(falhas)} falha(s) ({modo})")
        for f in falhas[:12]:
            print(f"- {f}")
        sys.exit(1)
    evento(a.raiz, a.feature, tipo="nota", texto="conferir-donos: OK")
    print(f"conferir-donos: OK ({modo})")
    sys.exit(0)


def comando_painel(raiz):
    """Comando do painel de terminal, para o humano rodar em outro terminal quando a janela não abre."""
    rel = os.path.relpath(Path(__file__).resolve().with_name("painel.py"), Path(raiz).resolve()).replace(os.sep, "/")
    return f"python {rel} --watch" + ("" if str(raiz) in (".", "") else f" --raiz {raiz}")


def confirmar_janela(proc, vivo):
    """Espera a janela dar sinal de vida. Devolve o motivo da falha, ou None se abriu (ou se ainda está abrindo)."""
    limite = time.time() + 6
    while time.time() < limite:
        time.sleep(0.2)
        codigo = proc.poll()
        if codigo is not None:
            if codigo == 0:
                return None
            return ("sem ambiente gráfico ou sem tkinter" if codigo == 3
                    else f"a janela encerrou com erro (código {codigo})")
        try:
            if not vivo.read_text(encoding="utf-8").startswith("lancando"):
                return None
        except OSError:
            pass
    return None


def garantir_janela(raiz, f):
    """Abre por padrão a janela de acompanhamento (janela.py) se não houver uma viva.

    Devolve o motivo se ela não puder abrir (e grava .janela-indisponivel para não repetir o aviso); senão, None.
    Não reabre depois de o humano fechá-la (.janela-fechada) nem com SDD_SEM_JANELA=1.
    """
    if os.environ.get("SDD_SEM_JANELA"):
        return None
    fdir = Path(raiz) / "specs" / f
    status = fdir / "status.md"
    if not status.exists() or "Situação: CONCLUÍDO" in status.read_text(encoding="utf-8"):
        return None
    vivo = fdir / ".janela"
    if (fdir / ".janela-fechada").exists() or (fdir / ".janela-indisponivel").exists():
        return None
    if vivo.exists() and time.time() - vivo.stat().st_mtime < 8:
        return None
    motivo = None
    if importlib.util.find_spec("tkinter") is None:
        motivo = "o tkinter não está instalado"
    elif sys.platform.startswith("linux") and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        motivo = "não há ambiente gráfico"
    else:
        exe = sys.executable
        if os.name == "nt" and Path(exe).with_name("pythonw.exe").exists():
            exe = str(Path(exe).with_name("pythonw.exe"))
        cmd = [exe, str(Path(__file__).resolve().with_name("janela.py")), f, "--raiz", str(Path(raiz).resolve())]
        opcoes = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL,
                  "close_fds": True}
        if os.name == "nt":
            opcoes["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            opcoes["start_new_session"] = True
        try:
            vivo.write_text(f"lancando {time.time():.0f}\n", encoding="utf-8")  # evita abrir duas janelas em chamadas seguidas
            motivo = confirmar_janela(subprocess.Popen(cmd, **opcoes), vivo)
        except OSError as erro:
            motivo = f"falha ao iniciar ({erro.strerror or erro})"
    if motivo:
        try:
            vivo.unlink(missing_ok=True)
            (fdir / ".janela-indisponivel").write_text(motivo + "\n", encoding="utf-8")
        except OSError:
            pass
    return motivo


ROTULOS_DESENHO = ("Estrutura", "Padrões", "Convenções", "Contratos", "Lib", "Não fazer", "Documento de arquitetura")
RE_ROTULO = r"^([A-ZÀ-Ú][^\n:`|]{0,45}?)(?:\s*\([^)\n]*\))?:(?:\s|$)"


def _bloco_rotulo(secao, rotulo):
    """Texto do rótulo 'Rótulo: ...' (ou 'Rótulo (nota): ...') até o próximo rótulo; None se o rótulo não existe."""
    linhas = secao.splitlines()
    for i, l in enumerate(linhas):
        m = re.match(rf"^{re.escape(rotulo)}(?:\s*\([^)\n]*\))?:\s*(.*)$", l)
        if m:
            partes = [m.group(1)]
            for prox in linhas[i + 1:]:
                if re.match(RE_ROTULO, prox) and not prox.startswith(("`", " ", "-", "|")):
                    break
                partes.append(prox)
            return "\n".join(partes).strip()
    return None


def cmd_conferir_prontidao(a):
    """Confere, só por arquivo, se o repositório tem o que o dev precisa antes de começar (entrega do PM e do tech lead)."""
    raiz = Path(a.raiz)
    base = raiz / "specs" / a.feature
    if not base.is_dir():
        sys.exit(f"feature não existe: {base}")
    r = a.repo
    falhas, avisos = [], []
    plano, tarefas = base / "repos" / r / "plan.md", base / "repos" / r / "tasks.md"
    txt = plano.read_text(encoding="utf-8") if plano.exists() else ""
    if not plano.exists():
        falhas.append(f"repos/{r}/plan.md ausente")
    if not tarefas.exists():
        falhas.append(f"repos/{r}/tasks.md ausente")

    # 1. desenho técnico: decidido e, se 'sim', com todos os campos preenchidos
    m = re.search(r"^Desenho técnico:\s*(sim|não)", txt, re.M)
    if plano.exists() and not m:
        falhas.append(f"repos/{r}/plan.md: 'Desenho técnico: sim|não' ausente ou indecisa")
    secao = ""
    if m and m.group(1) == "sim":
        ms = re.search(r"^## Desenho técnico[^\n]*\n(.*?)(?=^## |\Z)", txt, re.M | re.S)
        if not ms:
            falhas.append(f"repos/{r}/plan.md: 'Desenho técnico: sim' sem a seção '## Desenho técnico'")
        else:
            secao = ms.group(1)
            for rot in ROTULOS_DESENHO:
                v = _bloco_rotulo(secao, rot)
                if v is None:
                    falhas.append(f"repos/{r}/plan.md: Desenho técnico sem o campo '{rot}'")
                elif v in ("", "?") or "[TECH LEAD" in v:
                    falhas.append(f"repos/{r}/plan.md: Desenho técnico, campo '{rot}' vazio ou pendente")
    if re.search(r"(?<!`)\[TECH LEAD(:|\])(?!`)", txt):
        falhas.append(f"repos/{r}/plan.md: marcador [TECH LEAD] sem resolver")

    # 2. contratos citados no desenho existem em contracts/
    cit = _bloco_rotulo(secao, "Contratos") or ""
    nomes = set(re.findall(r"[\w.-]+\.(?:ya?ml|json|md)", cit))
    existentes = {c.name for c in (base / "contracts").glob("*")} if (base / "contracts").is_dir() else set()
    falhas += [f"contrato citado no desenho não existe em contracts/: {n}" for n in sorted(nomes - existentes)]

    # 3. tarefas: caminho (falha) e requisito rastreável (aviso)
    sem_caminho, sem_req = [], []
    ttxt = tarefas.read_text(encoding="utf-8") if tarefas.exists() else ""
    for l in ttxt.splitlines():
        mt = re.match(r"^- \[[ xX]\] (T\d+)\b(.*)$", l)
        if not mt:
            continue
        if not re.search(r"`[^`\s]*[./][^`\s]*`", mt.group(2)):
            sem_caminho.append(mt.group(1))
        if not re.search(r"\b(?:FR|RNF?|CA|SC|NFR)-?\d+|\[US\d+\]", mt.group(2)):
            sem_req.append(mt.group(1))
    if tarefas.exists() and not re.search(r"^- \[[ xX]\] T\d+", ttxt, re.M):
        falhas.append(f"repos/{r}/tasks.md sem tarefas")
    if sem_caminho:
        falhas.append(f"tarefas sem caminho de arquivo entre crases: {', '.join(sem_caminho[:8])}")
    if sem_req:
        avisos.append(f"tarefas sem referência a requisito (FR/RN/CA/US): {', '.join(sem_req[:8])}")

    # 4. verificações com motor real (processo >= 2) e ambiente
    if _processo(base) >= 2:
        rel = base / "reports" / "techlead.md"
        pesq = base / "research.md"
        falhas += _conferir_verificacoes(pesq.read_text(encoding="utf-8") if pesq.exists() else "",
                                         rel.read_text(encoding="utf-8") if rel.exists() else "")
    if not (raiz / ".agents" / "env.md").exists():
        falhas.append(".agents/env.md ausente (etapa ambiente não rodou)")

    # 5. comandos do repositório (aviso: o dev define e reporta quando '?')
    nota = raiz / ".agents" / "repos" / f"{r}.md"
    if nota.exists() and re.search(r"^(Build|Testes unitários|Lint/format):\s*\?\s*$", nota.read_text(encoding="utf-8"), re.M):
        avisos.append("notas do repositório com comandos '?': o dev deve defini-los e reportar em 'Comandos'")

    for av in avisos:
        print(f"aviso: {av}")
    if falhas:
        print(f"conferir-prontidao {r}: {len(falhas)} falha(s)")
        for f in falhas:
            print(f"- {f}")
        sys.exit(1)
    print(f"conferir-prontidao {r}: OK")


def main():
    ap = argparse.ArgumentParser(description="Registro do fluxo SDD (status.md + eventos.jsonl)")
    ap.add_argument("--raiz", default=".", help="raiz do workspace (padrão: diretório atual)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("iniciar"); s.add_argument("feature"); s.add_argument("repos", nargs="+")
    s.set_defaults(fn=cmd_iniciar)

    s = sub.add_parser("status"); s.add_argument("feature")
    for opt in ("--etapa", "--situacao", "--proxima", "--pendencias", "--contratos", "--qa"):
        s.add_argument(opt)
    s.add_argument("--agente", action="append", help="PAPEL=ID (ou PAPEL=- para remover)")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("repo"); s.add_argument("feature"); s.add_argument("repo")
    s.add_argument("--onda"); s.add_argument("--fase"); s.add_argument("--ciclo"); s.add_argument("--relatorio")
    s.set_defaults(fn=cmd_repo)

    for nome, fn in (("inicio", cmd_inicio), ("fim", cmd_fim), ("consumo", cmd_consumo)):
        s = sub.add_parser(nome); s.add_argument("feature"); s.add_argument("papel")
        s.add_argument("--repo"); s.add_argument("--modo"); s.add_argument("--modelo")
        if nome == "fim":
            s.add_argument("--resultado", required=True)
        if nome in ("fim", "consumo"):
            s.add_argument("--tokens", type=int); s.add_argument("--ferramentas", type=int)
            s.add_argument("--ms", type=int)
        s.set_defaults(fn=fn)

    s = sub.add_parser("evento"); s.add_argument("feature"); s.add_argument("texto")
    s.set_defaults(fn=cmd_evento)

    s = sub.add_parser("conferir-donos"); s.add_argument("feature")
    s.set_defaults(fn=cmd_conferir_donos)

    s = sub.add_parser("conferir-prontidao"); s.add_argument("feature"); s.add_argument("repo")
    s.set_defaults(fn=cmd_conferir_prontidao)

    a = ap.parse_args()
    a.fn(a)
    motivo = garantir_janela(a.raiz, a.feature)
    if motivo:
        print(f"aviso: a janela de acompanhamento não abriu ({motivo}). "
              f"Para acompanhar, execute em outro terminal: {comando_painel(a.raiz)}")
    print("ok")


if __name__ == "__main__":
    main()

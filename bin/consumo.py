#!/usr/bin/env python3
"""Consumo real de tokens de uma feature, somado dos transcritos da ferramenta de IA (Claude Code ou Codex).

O `tokens` que o orquestrador registra no eventos.jsonl vem da notificação de conclusão do subagente: é o
contexto da última chamada, não o consumo. Aqui cada chamada ao modelo é somada, com entrada nova, escrita de
cache, leitura de cache e saída separadas, e as métricas da skill token-efficiency são conferidas. Os indicadores
de qualidade da execução (eventos e relatórios da feature) saem ao lado, para comparar consumo e qualidade.
Uso, a partir da raiz do workspace (rode fora do agente; dentro dele, só a linha de resumo entra no contexto):
  python .agents/bin/consumo.py <f> [--ferramenta auto|claude|codex] [--transcritos PASTA] [--sessao ID ...]
                                    [--desde AAAA-MM-DDTHH:MM] [--ate AAAA-MM-DDTHH:MM] [--saida ARQUIVO] [--raiz PASTA]
Grava o relatório em specs/<f>/reports/consumo.md (ou em --saida) e imprime uma linha de resumo.
Transcritos: Claude Code em ~/.claude/projects/<raiz codificada>/ ($CLAUDE_CONFIG_DIR muda a base);
Codex em ~/.codex/sessions/ ($CODEX_HOME muda a base), filtrados pela raiz do workspace.
--desde/--ate (hora local) recortam a sessão que tem outra conversa antes ou depois da feature; o relatório avisa.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

LIMITE_LINHAS = 200  # leitura inteira de arquivo acima disto conta na métrica (regra da skill)
LIMITE_RESULTADO = 3000  # resultado de ferramenta acima disto (tokens aprox., ~100 linhas) conta como grande
CARACTERES_POR_TOKEN = 3.5  # estimativa usada quando o log não traz a contagem de tokens do resultado
FOLGA_DEPOIS_DO_FIM = datetime.timedelta(minutes=10)  # o resumo final do orquestrador vem logo depois do CONCLUÍDO
FOLGA_ANTES_DO_INICIO = datetime.timedelta(hours=2)  # a preparação roda antes do primeiro evento da feature
PAPEIS = ("orquestrador", "pm", "techlead", "dev", "reviewer", "qa")
SINONIMOS = {"review": "reviewer", "revisar": "reviewer", "revisao": "reviewer"}
FERRAMENTAS_SHELL = {"Bash", "PowerShell", "exec", "shell", "exec_command", "local_shell"}
ESPERAS = {"wait_agent", "wait", "sleep", "BashOutput", "TaskOutput"}
ESCRITAS_CLAUDE = {"Edit", "MultiEdit", "NotebookEdit", "Write"}
REGISTRO = re.compile(r"fluxo\.py\s+(?:iniciar|status|repo|inicio|fim|consumo|evento|etapa|qa|situacao|nota)\b")
TRIVIAL = re.compile(r"^\s*(?:cd\b|Set-Location\b|export\b|\$env:|[A-Za-z_][A-Za-z0-9_]*=\S*\s*$)", re.IGNORECASE)
LEITURA_SHELL = re.compile(
    r"(?:Get-Content|\bcat|\btype)\s+(?:-Path\s+|-LiteralPath\s+)?['\"]?([^\s'\";|&>]+)", re.IGNORECASE
)
LEITURA_PARCIAL = re.compile(r"-TotalCount|-Tail|-First|-Skip|Select-Object|\bhead\b|\btail\b|sed\s+-n", re.IGNORECASE)
ESCRITA_SHELL = re.compile(
    r"(?:>>?|Set-Content|Out-File|Add-Content|sed\s+-i\S*)\s+(?:-Path\s+|-FilePath\s+)?['\"]?([^\s'\";|&]+)",
    re.IGNORECASE,
)
PATCH = re.compile(r"\*\*\* (?:Update|Add|Delete) File: ([^\n\\]+)")
CAMPOS_CODEX = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens")


@dataclass
class Chamada:
    entrada: int = 0
    escrita_cache: int = 0
    leitura_cache: int = 0
    saida: int = 0
    contexto: int = 0
    ferramentas: list = field(default_factory=list)  # (nome, alvo)

    @property
    def total(self) -> int:
        return self.entrada + self.escrita_cache + self.leitura_cache + self.saida


@dataclass
class Agente:
    ferramenta: str
    papel: str
    ident: str
    repo: str = ""
    tarefa: str = ""
    chamadas: list = field(default_factory=list)
    resultados: list = field(default_factory=list)  # (índice da chamada que o pediu, tokens, ferramenta, alvo)
    comandos: list = field(default_factory=list)
    leituras_repetidas: int = 0
    leituras_inteiras: list = field(default_factory=list)
    reescritas: list = field(default_factory=list)
    confere_reescritas: bool = True  # False quando o log não permite conferir reescritas
    primeira: datetime.datetime | None = None
    ultima: datetime.datetime | None = None

    def marcar(self, registro: dict):
        quando = momento(registro.get("timestamp"))
        if quando:
            self.primeira = self.primeira or quando
            self.ultima = quando

    @property
    def total(self) -> int:
        return sum(c.total for c in self.chamadas)


def ler_jsonl(caminho):
    with open(caminho, encoding="utf-8", errors="replace") as arquivo:
        for linha in arquivo:
            linha = linha.strip()
            if not linha:
                continue
            try:
                yield json.loads(linha)
            except json.JSONDecodeError:
                continue


def texto_de(conteudo) -> str:
    if isinstance(conteudo, str):
        return conteudo
    partes = []
    for parte in conteudo or []:
        if isinstance(parte, dict) and parte.get("type") == "text":
            partes.append(parte.get("text") or "")
        elif isinstance(parte, str):
            partes.append(parte)
    return "\n".join(partes)


def tokens_aprox(texto: str) -> int:
    return round(len(texto) / CARACTERES_POR_TOKEN)


def normalizar(caminho: str) -> str:
    return os.path.normcase(os.path.normpath(caminho)) if caminho else ""


def momento(texto):
    """Data e hora com fuso; texto sem fuso é hora local (eventos.jsonl e --desde/--ate)."""
    if not texto:
        return None
    try:
        # O Python 3.10 não aceita o sufixo "Z" no fromisoformat; o replace mantém o script compatível com ele.
        data = datetime.datetime.fromisoformat(str(texto).replace("Z", "+00:00"))  # noqa: FURB162
    except ValueError:
        return None
    return data if data.tzinfo else data.astimezone()


def fora_da_janela(registro: dict, janela) -> bool:
    if not janela:
        return False
    quando = momento(registro.get("timestamp"))
    desde, ate = janela
    return quando is not None and ((desde and quando < desde) or (ate and quando > ate))


def dados_da_delegacao(texto: str):
    """Papel, repositório e modo do prompt de delegação (template 5.4 do roteiro)."""
    papel = re.search(r"Papel:\s*([a-z]+)", texto or "")
    repo = re.search(r"Repo:\s*([^\s.,]+)", texto or "")
    modo = re.search(r"Modo:\s*([^\s.,]+)", texto or "")
    nome_repo = repo.group(1) if repo else ""
    return (papel.group(1) if papel else None, "" if nome_repo == "todos" else nome_repo, modo.group(1) if modo else "")


def so_registro(comando: str) -> bool:
    """Comando de shell que só registra no fluxo.py (fora atribuições de variável e mudança de pasta)."""
    partes = [p for p in re.split(r"&&|;|\n", comando or "") if p.strip()]
    tem_registro = False
    for parte in partes:
        if REGISTRO.search(parte):
            tem_registro = True
        elif not TRIVIAL.match(parte):
            return False
    return tem_registro


def invalidar(lidos: dict, caminho: str):
    for chave in [k for k in lidos if k[0] == caminho or k[0].endswith(os.sep + caminho)]:
        lidos[chave] = False


def leituras_do_comando(agente: Agente, lidos: dict, comando: str) -> list:
    """Registra as leituras feitas pelo shell (cat, type, Get-Content); devolve as que leram o arquivo inteiro."""
    inteiras = []
    for parte in re.split(r";|&&|\n", comando or ""):
        for escrito in ESCRITA_SHELL.findall(parte):
            invalidar(lidos, normalizar(escrito))
        achado = LEITURA_SHELL.search(parte)
        if not achado:
            continue
        caminho = normalizar(achado.group(1))
        parcial = bool(LEITURA_PARCIAL.search(parte))
        chave = (caminho, " ".join(parte.split()) if parcial else None)
        if lidos.get(chave):
            agente.leituras_repetidas += 1
        lidos[chave] = True
        if not parcial:
            inteiras.append(achado.group(1))
    return inteiras


def linhas_de(texto: str) -> int:
    return max(texto.count("\n"), texto.count("\\n")) + 1


# --- Claude Code -----------------------------------------------------------------------------------------------


def registrar_ferramenta_claude(agente, lidos, caminhos_lidos, nome, entrada) -> list:
    """Atualiza leituras e escritas; devolve os arquivos que o comando leu inteiros (para conferir o tamanho)."""
    if nome in FERRAMENTAS_SHELL and entrada.get("command"):
        agente.comandos.append(str(entrada["command"]))
        return leituras_do_comando(agente, lidos, str(entrada["command"]))
    caminho = normalizar(str(entrada.get("file_path") or entrada.get("notebook_path") or ""))
    if not caminho:
        return []
    if nome == "Read":
        chave = (caminho, entrada.get("offset"), entrada.get("limit"))
        if lidos.get(chave):
            agente.leituras_repetidas += 1
        lidos[chave] = True
        caminhos_lidos.add(caminho)
        return [] if ("offset" in entrada or "limit" in entrada) else [str(entrada.get("file_path"))]
    if nome in ESCRITAS_CLAUDE:
        if nome == "Write" and caminho in caminhos_lidos:
            agente.reescritas.append(str(entrada.get("file_path")))
        invalidar(lidos, caminho)
    return []


def ler_claude(caminho: Path, papel, ident: str, tarefa: str = "", janela=None) -> Agente:
    agente = Agente("claude", papel or "outro", ident, tarefa=tarefa)
    indices, usos, lidos, caminhos_lidos = {}, {}, {}, set()
    viu_delegacao = papel is not None
    for registro in ler_jsonl(caminho):
        if (papel == "orquestrador" and registro.get("isSidechain")) or fora_da_janela(registro, janela):
            continue
        mensagem = registro.get("message") or {}
        conteudo = mensagem.get("content")
        if registro.get("type") == "user":
            if not viu_delegacao and texto_de(conteudo).strip():
                viu_delegacao = True
                achado, agente.repo, modo = dados_da_delegacao(texto_de(conteudo))
                agente.papel = achado or "outro"
                agente.tarefa = agente.tarefa or modo
            for parte in conteudo if isinstance(conteudo, list) else []:
                if not (isinstance(parte, dict) and parte.get("type") == "tool_result"):
                    continue
                nome, alvo, inteiras, indice = usos.get(parte.get("tool_use_id"), ("?", "", [], len(indices) - 1))
                bruto = parte.get("content")
                texto = bruto if isinstance(bruto, str) else texto_de(bruto)
                agente.resultados.append((indice, tokens_aprox(texto), nome, alvo))
                if len(inteiras) == 1 and linhas_de(texto) > LIMITE_LINHAS:
                    agente.leituras_inteiras.append(inteiras[0])
            continue
        if registro.get("type") != "assistant" or not mensagem.get("id"):
            continue
        identificador = mensagem["id"]
        if identificador not in indices:
            indices[identificador] = len(indices)
            agente.chamadas.append(Chamada())
        agente.marcar(registro)
        chamada = agente.chamadas[indices[identificador]]
        uso = mensagem.get("usage") or {}
        chamada.entrada = max(chamada.entrada, uso.get("input_tokens") or 0)
        chamada.escrita_cache = max(chamada.escrita_cache, uso.get("cache_creation_input_tokens") or 0)
        chamada.leitura_cache = max(chamada.leitura_cache, uso.get("cache_read_input_tokens") or 0)
        chamada.saida = max(chamada.saida, uso.get("output_tokens") or 0)
        chamada.contexto = chamada.total
        for parte in conteudo if isinstance(conteudo, list) else []:
            if not (isinstance(parte, dict) and parte.get("type") == "tool_use") or parte.get("id") in usos:
                continue
            nome = parte.get("name") or "?"
            entrada = parte.get("input") or {}
            alvo = str(
                entrada.get("file_path")
                or entrada.get("command")
                or entrada.get("pattern")
                or entrada.get("path")
                or entrada.get("description")
                or ""
            )
            inteiras = registrar_ferramenta_claude(agente, lidos, caminhos_lidos, nome, entrada)
            usos[parte.get("id")] = (nome, alvo, inteiras, indices[identificador])
            chamada.ferramentas.append((nome, alvo))
    return agente


def pasta_claude(raiz: Path):
    base = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "projects"
    codificado = re.sub(r"[^A-Za-z0-9]", "-", str(raiz))
    for nome in (codificado, codificado[:1].lower() + codificado[1:], codificado[:1].upper() + codificado[1:]):
        if (base / nome).is_dir():
            return base / nome
    return None


def carregar_claude(pasta: Path, sessoes: set, janela=None) -> list:
    agentes = []
    for principal in sorted(pasta.glob("*.jsonl")):
        sessao = principal.stem
        if sessoes and sessao not in sessoes:
            continue
        agentes.append(ler_claude(principal, "orquestrador", sessao[:8], janela=janela))
        for sub in sorted((pasta / sessao / "subagents").glob("agent-*.jsonl")):
            descricao = ""
            meta = sub.with_name(sub.stem + ".meta.json")
            if meta.exists():
                try:
                    descricao = json.loads(meta.read_text(encoding="utf-8")).get("description") or ""
                except (OSError, ValueError):
                    descricao = ""
            agentes.append(ler_claude(sub, None, sub.stem.replace("agent-", "")[:8], descricao, janela))
    return [a for a in agentes if a.chamadas]


# --- Codex -----------------------------------------------------------------------------------------------------


def papel_codex(meta: dict):
    origem = meta.get("thread_source") or ""
    if origem == "user":
        return "orquestrador", ""
    if origem == "guardian_review":
        return "guardian", "revisão de permissão"
    nome = (meta.get("agent_path") or "").rstrip("/").split("/")[-1]
    primeiro = SINONIMOS.get(nome.split("_")[0].lower(), nome.split("_")[0].lower())
    return (primeiro if primeiro in PAPEIS else "outro"), nome


def desescapar(texto: str) -> str:
    try:
        return json.loads(f'"{texto}"')
    except ValueError:
        return texto


def comandos_codex(nome: str, bruto) -> list:
    if bruto is None:
        return []
    texto = bruto if isinstance(bruto, str) else json.dumps(bruto, ensure_ascii=False)
    if nome == "exec":  # JavaScript que compõe chamadas: tools.exec_command({cmd:"..."})
        return [desescapar(m) for m in re.findall(r'cmd\s*:\s*"((?:[^"\\]|\\.)*)"', texto)]
    if nome in FERRAMENTAS_SHELL:
        try:
            dados = json.loads(texto)
        except ValueError:
            return [texto]
        comando = dados.get("command") or dados.get("cmd") or ""
        return [" ".join(comando) if isinstance(comando, list) else str(comando)]
    return []


def meta_codex(caminho: Path):
    for registro in ler_jsonl(caminho):
        if registro.get("type") == "session_meta":
            return registro.get("payload") or {}
    return None


def ler_codex(caminho: Path, meta: dict, janela=None) -> Agente:
    papel, tarefa = papel_codex(meta)
    agente = Agente("codex", papel, (meta.get("id") or caminho.stem)[-8:], tarefa=tarefa, confere_reescritas=False)
    pendentes, usos, lidos, anterior = [], {}, {}, None
    for registro in ler_jsonl(caminho):
        tipo, carga = registro.get("type"), registro.get("payload") or {}
        if tipo == "response_item" and carga.get("type") in ("function_call", "custom_tool_call"):
            if fora_da_janela(registro, janela):
                continue
            nome = carga.get("name") or "?"
            bruto = carga.get("arguments") if carga.get("type") == "function_call" else carga.get("input")
            comandos = comandos_codex(nome, bruto)
            alvo = "; ".join(comandos) if comandos else str(bruto or "")[:200]
            inteiras = []
            for comando in comandos:
                inteiras += leituras_do_comando(agente, lidos, comando)
            for alterado in PATCH.findall(bruto if isinstance(bruto, str) else json.dumps(bruto or "")):
                invalidar(lidos, normalizar(alterado.strip()))
            pendentes.append((nome, alvo))
            usos[carga.get("call_id")] = (nome, alvo, inteiras, len(agente.chamadas))
            agente.comandos.extend(comandos)
        elif tipo == "response_item" and carga.get("type") in ("function_call_output", "custom_tool_call_output"):
            if fora_da_janela(registro, janela):
                continue
            nome, alvo, inteiras, indice = usos.get(carga.get("call_id"), ("?", "", [], len(agente.chamadas) - 1))
            saida = carga.get("output")
            texto = saida if isinstance(saida, str) else json.dumps(saida, ensure_ascii=False)
            contagem = re.search(r'original_token_count\\*"?\s*:\s*(\d+)', texto)
            agente.resultados.append((indice, int(contagem.group(1)) if contagem else tokens_aprox(texto), nome, alvo))
            if len(inteiras) == 1 and linhas_de(texto) > LIMITE_LINHAS:
                agente.leituras_inteiras.append(inteiras[0])
        elif tipo == "event_msg" and carga.get("type") == "token_count" and carga.get("info"):
            total = carga["info"].get("total_token_usage") or {}
            if anterior is not None and (total.get("total_tokens") or 0) <= (anterior.get("total_tokens") or 0):
                continue  # evento repetido: o total não mudou
            if fora_da_janela(registro, janela):
                anterior = total  # chamada fora do recorte: não soma, mas serve de base para a próxima
                continue
            delta = {c: (total.get(c) or 0) - ((anterior or {}).get(c) or 0) for c in CAMPOS_CODEX}
            ultimo = carga["info"].get("last_token_usage") or {}
            agente.chamadas.append(
                Chamada(
                    entrada=max(
                        delta["input_tokens"] - delta["cached_input_tokens"] - delta["cache_write_input_tokens"], 0
                    ),
                    escrita_cache=delta["cache_write_input_tokens"],
                    leitura_cache=delta["cached_input_tokens"],
                    saida=delta["output_tokens"],
                    contexto=(ultimo.get("input_tokens") or 0) + (ultimo.get("output_tokens") or 0),
                    ferramentas=pendentes,
                )
            )
            agente.marcar(registro)
            pendentes, anterior = [], total
    return agente


def pasta_codex():
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "sessions"


def carregar_codex(pasta: Path, raiz: Path, sessoes: set, janela=None) -> list:
    alvo = normalizar(str(raiz))
    lidos = []
    for arquivo in sorted(pasta.rglob("rollout-*.jsonl")):
        meta = meta_codex(arquivo)
        if meta is None or normalizar(meta.get("cwd") or "") != alvo:
            continue
        lidos.append((ler_codex(arquivo, meta, janela), meta))
    if sessoes:
        pai = {m.get("id"): m.get("parent_thread_id") for _, m in lidos}

        def incluido(ident):
            vistos = set()
            while ident and ident not in vistos:
                if ident in sessoes:
                    return True
                vistos.add(ident)
                ident = pai.get(ident)
            return False

        lidos = [(a, m) for a, m in lidos if incluido(m.get("id"))]
    return [a for a, _ in lidos if a.chamadas]


# --- Artefatos e eventos ---------------------------------------------------------------------------------------


def paragrafos_repetidos(pasta_feature: Path) -> list:
    """Parágrafos longos copiados entre artefatos da feature (a cópia de tarefas em repos/*/tasks.md é do fluxo)."""
    ocorrencias = defaultdict(set)
    for arquivo in sorted(pasta_feature.rglob("*.md")):
        relativo = arquivo.relative_to(pasta_feature).as_posix()
        if relativo in ("status.md", "reports/consumo.md"):
            continue
        for bloco in re.split(r"\n\s*\n", arquivo.read_text(encoding="utf-8", errors="replace")):
            normal = " ".join(bloco.split())
            if len(normal) >= 120:
                ocorrencias[normal].add(relativo)
    pares = defaultdict(lambda: [0, 0])
    for normal, arquivos in ocorrencias.items():
        if len(arquivos) < 2 or all(Path(a).name == "tasks.md" for a in arquivos):
            continue
        chave = " e ".join(sorted(arquivos))
        pares[chave][0] += 1
        pares[chave][1] += tokens_aprox(normal) * (len(arquivos) - 1)
    return sorted(pares.items(), key=lambda kv: -kv[1][1])


def ler_eventos(eventos: Path):
    """Tokens registrados por papel, o início da feature e o fim: o último CONCLUÍDO ou, sem ele, o último evento."""
    registrado, horarios, concluido = defaultdict(int), [], None
    if eventos.exists():
        for evento in ler_jsonl(eventos):
            quando = momento(evento.get("ts"))
            if quando:
                horarios.append(quando)
                if evento.get("tipo") == "situacao" and "CONCLU" in (evento.get("situacao") or "").upper():
                    concluido = quando
            if evento.get("tipo") in ("fim", "consumo") and evento.get("papel") and evento.get("tokens"):
                registrado[evento["papel"]] += evento["tokens"]
    fim = concluido or (max(horarios) if horarios else None)
    return dict(registrado), (min(horarios) if horarios else None), fim


def avisos_de_recorte(agentes: list, inicio, fim, recortou_inicio: bool, recortou_fim: bool) -> list:
    """Avisa quando a sessão tem chamadas longe do intervalo da feature (outra conversa ou outra feature)."""
    avisos = []
    if inicio and not recortou_inicio:
        antes = [a for a in agentes if a.primeira and a.primeira < inicio - FOLGA_ANTES_DO_INICIO]
        if antes:
            sugestao = (inicio - datetime.timedelta(minutes=30)).astimezone()
            avisos.append(
                f"há chamadas mais de 2 h antes do primeiro evento da feature ({inicio.astimezone():%Y-%m-%d %H:%M}), "
                f"em {', '.join(rotulo(a) for a in antes)}. Se forem de outra conversa ou feature, recorte com "
                f"`--desde` no pedido que iniciou a execução (ex.: `--desde {sugestao:%Y-%m-%dT%H:%M}`)."
            )
    if fim and not recortou_fim:
        depois = [a for a in agentes if a.ultima and a.ultima > fim + FOLGA_DEPOIS_DO_FIM]
        if depois:
            sugestao = (fim + datetime.timedelta(minutes=2)).astimezone()
            avisos.append(
                f"há chamadas depois do fim da feature ({fim.astimezone():%Y-%m-%d %H:%M}), em "
                f"{', '.join(rotulo(a) for a in depois)}. Se forem de outra conversa, recorte com "
                f"`--ate {sugestao:%Y-%m-%dT%H:%M}`."
            )
    return avisos


def qualidade(pasta_feature: Path) -> list:
    """Indicadores de qualidade da execução, lidos do eventos.jsonl e dos relatórios, para pôr ao lado do consumo."""
    arquivo_eventos = pasta_feature / "eventos.jsonl"
    eventos = list(ler_jsonl(arquivo_eventos)) if arquivo_eventos.exists() else []
    if not eventos:
        return ["Sem `eventos.jsonl`: indicadores indisponíveis."]
    inicios = [e for e in eventos if e.get("tipo") == "inicio"]
    fins = [e for e in eventos if e.get("tipo") == "fim"]

    def quantos(papel, prefixo=""):
        return sum(1 for e in inicios if e.get("papel") == papel and (e.get("modo") or "").startswith(prefixo))

    def resultado(papel, prefixo):
        achados = [e for e in fins if e.get("papel") == papel and (e.get("modo") or "").startswith(prefixo)]
        return celula(achados[-1].get("resultado") or "", 100) if achados else "—"

    def linha(relativo, padrao):
        arquivo = pasta_feature / relativo
        if not arquivo.exists():
            return ""
        achado = re.search(padrao, arquivo.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)
        return f" — {celula(achado.group(0).strip(), 100)}" if achado else ""

    reports = pasta_feature / "reports"
    handoff = sum(
        r.read_text(encoding="utf-8", errors="replace").count("[handoff]") for r in reports.glob("*/review.md")
    )
    situacoes = [e.get("situacao") for e in eventos if e.get("tipo") == "situacao" and e.get("situacao")]
    qa = linha("reports/integration/qa.md", r"^Resultado:.*$") + linha(
        "reports/integration/qa.md", r"^Critérios de aceite:.*$"
    )
    linhas = [
        (
            "Cada execução do dev depois da primeira é um ciclo de correção ou de convergência. Compare com a linha "
            "de base: valores maiores indicam retrabalho."
        ),
        "",
        "| Indicador | Valor |",
        "|---|---|",
        f"| Rodadas do tech lead | {quantos('techlead')} |",
        f"| Paradas para o humano | {sum(1 for s in situacoes if 'AGUARDANDO' in s.upper())} |",
        f"| Analyze | {resultado('pm', 'analyze')} |",
        f"| Passagens do converge | {quantos('pm', 'converge')}{linha('reports/converge.md', r'^.*Resultado.*$')} |",
        f"| Rodadas de QA | {quantos('qa')}{qa} |",
        f"| Achados `[handoff]` no review | {handoff} |",
        f"| Situação final | {situacoes[-1] if situacoes else '—'} |",
    ]
    repos = sorted({e.get("repo") for e in inicios if e.get("repo") and e.get("papel") in ("dev", "reviewer")})
    if repos:
        linhas += ["", "| Repositório | Execuções do dev | Revisões | Revisões reprovadas |", "|---|---:|---:|---:|"]
        for repo in repos:
            revisoes = [e for e in fins if e.get("papel") == "reviewer" and e.get("repo") == repo]
            reprovadas = sum(1 for e in revisoes if (e.get("resultado") or "").strip().upper().startswith("REPROVADO"))
            execucoes = sum(1 for e in inicios if e.get("papel") == "dev" and e.get("repo") == repo)
            linhas.append(f"| {repo} | {execucoes} | {len(revisoes)} | {reprovadas} |")
    return linhas


# --- Relatório -------------------------------------------------------------------------------------------------


def fmt(numero: float) -> str:
    return f"{round(numero):,}".replace(",", ".")


def pct(parte: float, todo: float) -> str:
    return f"{100 * parte / todo:.1f}%".replace(".", ",") if todo else "—"


def celula(texto: str, limite: int = 90) -> str:
    texto = " ".join(str(texto).split()).replace("|", "\\|")
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"


def rotulo(agente: Agente) -> str:
    detalhe = agente.tarefa or agente.repo
    return celula(f"{agente.papel} · {detalhe}" if detalhe else agente.papel, 60) + f" `{agente.ident}`"


def metricas(agente: Agente) -> dict:
    ferramentas = sum(len(c.ferramentas) for c in agente.chamadas)
    so_registro_ = sum(
        1
        for c in agente.chamadas
        if c.ferramentas and all(n in FERRAMENTAS_SHELL and so_registro(a) for n, a in c.ferramentas)
    )
    repetidos = Counter(" ".join(c.split()) for c in agente.comandos if not REGISTRO.search(c))
    return {
        "por_chamada": f"{ferramentas / len(agente.chamadas):.2f}".replace(".", ",") if agente.chamadas else "—",
        "so_registro": so_registro_,
        "esperas": sum(1 for c in agente.chamadas for n, _ in c.ferramentas if n in ESPERAS),
        "repetidos": sum(v for v in repetidos.values() if v >= 3),
        "maior": max((r[1] for r in agente.resultados), default=0),
        "grandes": sum(1 for r in agente.resultados if r[1] > LIMITE_RESULTADO),
    }


def relatorio(
    feature: str, agentes: list, fontes: list, registrado: dict, repetidos: list, avisos: list, indicadores: list
) -> str:
    total = sum(a.total for a in agentes)
    linhas = [
        f"# Consumo de tokens — {feature}",
        "",
        f"Gerado por `consumo.py` em {datetime.date.today().isoformat()}, a partir de: {'; '.join(fontes)}.",
        (
            "Cada chamada ao modelo é somada. O `tokens` do `eventos.jsonl` é o contexto da última chamada de cada "
            "subagente, não o consumo. Tokens aprox. = caracteres ÷ 3,5 quando o log não traz a contagem."
        ),
    ]
    linhas += [f"\n**Aviso:** {aviso}" for aviso in avisos]
    linhas += ["", "## Resumo", "", "| Tipo | Tokens | % |", "|---|---:|---:|"]
    for nome, atributo in (
        ("Entrada nova", "entrada"),
        ("Escrita de cache", "escrita_cache"),
        ("Leitura de cache", "leitura_cache"),
        ("Saída", "saida"),
    ):
        valor = sum(getattr(c, atributo) for a in agentes for c in a.chamadas)
        linhas.append(f"| {nome} | {fmt(valor)} | {pct(valor, total)} |")
    linhas += [f"| **Total** | **{fmt(total)}** | 100% |", "", "## Por papel", ""]
    linhas += [
        "| Papel | Agentes | Chamadas | Total | % | Registrado no eventos.jsonl |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    por_papel = defaultdict(list)
    for agente in agentes:
        por_papel[agente.papel].append(agente)
    for papel, grupo in sorted(por_papel.items(), key=lambda kv: -sum(a.total for a in kv[1])):
        soma = sum(a.total for a in grupo)
        anotado = fmt(registrado[papel]) if papel in registrado else "—"
        chamadas = sum(len(a.chamadas) for a in grupo)
        linhas.append(f"| {papel} | {len(grupo)} | {chamadas} | {fmt(soma)} | {pct(soma, total)} | {anotado} |")
    linhas += ["", "## Qualidade", ""] + indicadores
    linhas += ["", "## Por agente", ""]
    linhas += [
        "| Agente | Chamadas | Contexto inicial | Contexto final | Total | % |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    ordenados = sorted(agentes, key=lambda a: -a.total)
    for a in ordenados:
        linhas.append(
            f"| {rotulo(a)} | {len(a.chamadas)} | {fmt(a.chamadas[0].contexto)} | {fmt(a.chamadas[-1].contexto)} "
            f"| {fmt(a.total)} | {pct(a.total, total)} |"
        )
    linhas += ["", "## Métricas da token-efficiency", ""]
    linhas += [
        (
            "Regras em `skills/token-efficiency/SKILL.md`. São indícios para investigar, não portões: uma leitura conta "
            "como repetida mesmo quando outro agente ou um script alterou o arquivo no meio. Leituras pelo shell "
            "(`cat`, `type`, `Get-Content`) entram nas contagens; n/d = o log desta ferramenta não permite conferir."
        ),
        "",
        (
            "| Agente | Ferramentas por chamada | Leituras repetidas | Leituras inteiras | Maior resultado | "
            "Resultados grandes | Reescritas | Só registro | Esperas | Comandos repetidos |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for a in ordenados:
        m = metricas(a)
        reescritas = str(len(a.reescritas)) if a.confere_reescritas else "n/d"
        linhas.append(
            f"| {rotulo(a)} | {m['por_chamada']} | {a.leituras_repetidas} | {len(a.leituras_inteiras)} "
            f"| {fmt(m['maior'])} | {m['grandes']} | {reescritas} | {m['so_registro']} | {m['esperas']} "
            f"| {m['repetidos']} |"
        )
    caros = []
    for a in agentes:
        for indice, tokens, nome, alvo in a.resultados:
            releituras = max(len(a.chamadas) - 1 - indice, 0)
            caros.append((tokens * releituras, tokens, releituras, a, nome, alvo))
    linhas += ["", "## Resultados de ferramenta mais caros", ""]
    linhas += [
        "Cada resultado volta em todas as chamadas seguintes do agente: custo = tokens × releituras.",
        "",
        "| Custo | Tokens × releituras | Agente | Ferramenta | Alvo |",
        "|---:|---|---|---|---|",
    ]
    for custo, tokens, releituras, a, nome, alvo in sorted(caros, key=lambda c: -c[0])[:10]:
        linhas.append(f"| {fmt(custo)} | {fmt(tokens)} × {releituras} | {rotulo(a)} | {nome} | {celula(alvo)} |")
    linhas += ["", "## Parágrafos repetidos entre artefatos", ""]
    if repetidos:
        linhas += ["| Arquivos | Parágrafos | Tokens aprox. |", "|---|---:|---:|"]
        linhas += [f"| {celula(chave, 120)} | {n} | {fmt(t)} |" for chave, (n, t) in repetidos[:15]]
    else:
        linhas.append("Nenhum parágrafo longo copiado entre artefatos.")
    return "\n".join(linhas) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Consumo real de tokens de uma feature, pelos transcritos da ferramenta")
    ap.add_argument("feature")
    ap.add_argument("--raiz", default=".", help="raiz do workspace (padrão: diretório atual)")
    ap.add_argument("--ferramenta", choices=("auto", "claude", "codex"), default="auto")
    ap.add_argument("--transcritos", help="pasta dos transcritos (Claude Code: a do projeto; Codex: a sessions)")
    ap.add_argument("--sessao", action="append", default=[], help="só esta sessão (repita para mais de uma)")
    ap.add_argument("--desde", help="ignora chamadas antes deste horário local (AAAA-MM-DDTHH:MM)")
    ap.add_argument("--ate", help="ignora chamadas depois deste horário local (AAAA-MM-DDTHH:MM)")
    ap.add_argument("--saida", help="arquivo do relatório (padrão: specs/<f>/reports/consumo.md)")
    a = ap.parse_args(argv)
    if a.transcritos and a.ferramenta == "auto":
        ap.error("com --transcritos, informe --ferramenta claude ou codex")
    janela = (momento(a.desde), momento(a.ate)) if (a.desde or a.ate) else None
    if janela and ((a.desde and not janela[0]) or (a.ate and not janela[1])):
        ap.error("--desde/--ate no formato AAAA-MM-DDTHH:MM")
    raiz = Path(a.raiz).resolve()
    sessoes = set(a.sessao)
    agentes, fontes = [], []
    if a.ferramenta in ("auto", "claude"):
        pasta = Path(a.transcritos) if a.transcritos else pasta_claude(raiz)
        achados = carregar_claude(pasta, sessoes, janela) if pasta and pasta.is_dir() else []
        if achados:
            agentes += achados
            fontes.append(f"Claude Code ({pasta})")
    if a.ferramenta in ("auto", "codex"):
        pasta = Path(a.transcritos) if a.transcritos else pasta_codex()
        achados = carregar_codex(pasta, raiz, sessoes, janela) if pasta.is_dir() else []
        if achados:
            agentes += achados
            fontes.append(f"Codex ({pasta})")
    if not agentes:
        sys.exit(f"nenhum transcrito encontrado para {raiz}; informe --ferramenta e --transcritos")
    pasta_feature = raiz / "specs" / a.feature
    registrado, inicio_da_feature, fim_da_feature = ler_eventos(pasta_feature / "eventos.jsonl")
    avisos = avisos_de_recorte(agentes, inicio_da_feature, fim_da_feature, bool(a.desde), bool(a.ate))
    texto = relatorio(
        a.feature,
        agentes,
        fontes,
        registrado,
        paragrafos_repetidos(pasta_feature) if pasta_feature.is_dir() else [],
        avisos,
        qualidade(pasta_feature),
    )
    saida = Path(a.saida) if a.saida else pasta_feature / "reports" / "consumo.md"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(texto, encoding="utf-8")
    total = sum(ag.total for ag in agentes)
    orquestrador = sum(ag.total for ag in agentes if ag.papel == "orquestrador")
    alerta = "; há chamadas fora do intervalo da feature (ver aviso)" if avisos else ""
    print(
        f"consumo: {fmt(total)} tokens em {len(agentes)} agentes (orquestrador {pct(orquestrador, total)}){alerta}; "
        f"relatório em {saida}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Verificações do consumo.py: python -B -m unittest discover -s tests."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
import consumo


def gravar_jsonl(caminho, registros):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in registros) + "\n", encoding="utf-8")


def resposta(ident, ferramentas=(), quando="2026-11-01T10:00:00Z"):
    """Resposta do modelo no formato do Claude Code: uma linha por bloco, todas com o mesmo id e o mesmo uso."""
    uso = {"input_tokens": 10, "cache_read_input_tokens": 100, "cache_creation_input_tokens": 5, "output_tokens": 7}
    blocos = [{"type": "tool_use", "id": i, "name": nome, "input": dados} for i, nome, dados in ferramentas]
    return [
        {"type": "assistant", "timestamp": quando, "message": {"id": ident, "usage": uso, "content": [bloco]}}
        for bloco in blocos or [{"type": "text", "text": "ok"}]
    ]


def resultado(ident, texto):
    conteudo = [{"type": "tool_result", "tool_use_id": ident, "content": texto}]
    return {"type": "user", "timestamp": "2026-11-01T10:00:01Z", "message": {"content": conteudo}}


def pedido(texto):
    return {"type": "user", "timestamp": "2026-11-01T09:59:00Z", "message": {"content": texto}}


class ClaudeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.arquivo = Path(self.tmp.name) / "agente.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def ler(self, registros, papel=None, janela=None):
        gravar_jsonl(self.arquivo, registros)
        return consumo.ler_claude(self.arquivo, papel, "x", janela=janela)

    def test_soma_cada_resposta_uma_vez_e_le_o_papel_da_delegacao(self):
        registros = [pedido("Papel: dev. Repo: api em ./api. Stack: python. Feature: 001. Idioma: pt-BR.")]
        registros += resposta("m1", [("t1", "Read", {"file_path": "a.py"}), ("t2", "Read", {"file_path": "b.py"})])
        registros += [resultado("t1", "x"), resultado("t2", "y")] + resposta("m2")
        agente = self.ler(registros)
        self.assertEqual((agente.papel, agente.repo), ("dev", "api"))
        self.assertEqual(len(agente.chamadas), 2)
        self.assertEqual(agente.total, 2 * (10 + 100 + 5 + 7))
        self.assertEqual(len(agente.chamadas[0].ferramentas), 2)

    def test_leitura_repetida_so_quando_o_arquivo_nao_mudou_e_reescrita_depois_de_ler(self):
        passos = [
            ("Read", {"file_path": "a.py"}),
            ("Read", {"file_path": "a.py"}),  # repetida
            ("Edit", {"file_path": "a.py"}),
            ("Read", {"file_path": "a.py"}),  # o arquivo mudou: não conta
            ("Bash", {"command": "cat b.md"}),
            ("Bash", {"command": "cat b.md"}),  # repetida, pelo shell
            ("Write", {"file_path": "a.py"}),  # reescrita de arquivo já lido
        ]
        registros = []
        for numero, (nome, dados) in enumerate(passos):
            registros += resposta(f"m{numero}", [(f"t{numero}", nome, dados)]) + [resultado(f"t{numero}", "x")]
        agente = self.ler(registros, "dev")
        self.assertEqual(agente.leituras_repetidas, 2)
        self.assertEqual(agente.reescritas, ["a.py"])

    def test_leitura_inteira_so_de_arquivo_grande_sem_intervalo(self):
        grande = "\n".join(f"linha {numero}" for numero in range(250))
        passos = [
            ("Read", {"file_path": "a.py"}),
            ("Read", {"file_path": "b.py", "offset": 1, "limit": 250}),
            ("Bash", {"command": "cat c.md"}),
            ("Bash", {"command": "sed -n '1,250p' d.md"}),
        ]
        registros = []
        for numero, (nome, dados) in enumerate(passos):
            registros += resposta(f"m{numero}", [(f"t{numero}", nome, dados)]) + [resultado(f"t{numero}", grande)]
        agente = self.ler(registros, "dev")
        self.assertEqual(agente.leituras_inteiras, ["a.py", "c.md"])

    def test_janela_ignora_chamadas_fora_do_recorte(self):
        registros = resposta("m1", quando="2026-11-01T10:00:00Z") + resposta("m2", quando="2026-11-02T10:00:00Z")
        agente = self.ler(registros, "orquestrador", janela=(None, consumo.momento("2026-11-01T23:00:00+00:00")))
        self.assertEqual(len(agente.chamadas), 1)


class RegistroTest(unittest.TestCase):
    def test_so_registro_aceita_variavel_e_pasta_mas_nao_outro_comando(self):
        self.assertTrue(consumo.so_registro("F=001 && python .agents/bin/fluxo.py fim $F pm --resultado ok"))
        self.assertTrue(consumo.so_registro("cd /w; python .agents/bin/fluxo.py inicio 001 dev --repo api"))
        self.assertFalse(consumo.so_registro("python .agents/bin/fluxo.py fim 001 pm && cat specs/001/spec.md"))
        self.assertFalse(consumo.so_registro("python .agents/bin/fluxo.py conferir-donos 001"))


class CodexTest(unittest.TestCase):
    def test_papel_soma_por_chamada_comandos_resultado_e_esperas(self):
        def contagem(entrada, cache, saida):
            total = {
                "input_tokens": entrada,
                "cached_input_tokens": cache,
                "cache_write_input_tokens": 0,
                "output_tokens": saida,
                "total_tokens": entrada + saida,
            }
            info = {"total_token_usage": total, "last_token_usage": {"input_tokens": entrada, "output_tokens": saida}}
            return {"type": "event_msg", "payload": {"type": "token_count", "info": info}}

        comando = "Get-Content a.md; python .agents/bin/fluxo.py fim 001 dev"
        registros = [
            {
                "type": "session_meta",
                "payload": {"id": "abc", "thread_source": "subagent", "agent_path": "/root/review_x"},
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "exec",
                    "call_id": "c1",
                    "input": f'text(await tools.exec_command({{cmd:"{comando}"}}))',
                },
            },
            contagem(100, 60, 10),
            contagem(100, 60, 10),  # evento repetido: não é chamada nova
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call_output",
                    "call_id": "c1",
                    "output": '{"original_token_count":4321}',
                },
            },
            {
                "type": "response_item",
                "payload": {"type": "function_call", "name": "wait_agent", "call_id": "c2", "arguments": "{}"},
            },
            contagem(250, 200, 30),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            arquivo = Path(tmp) / "rollout-1.jsonl"
            gravar_jsonl(arquivo, registros)
            agente = consumo.ler_codex(arquivo, consumo.meta_codex(arquivo))
        self.assertEqual((agente.papel, agente.tarefa), ("reviewer", "review_x"))
        self.assertEqual(len(agente.chamadas), 2)
        self.assertEqual(agente.total, 280)
        self.assertEqual(agente.chamadas[1].leitura_cache, 140)
        self.assertEqual(agente.comandos, [comando])
        self.assertEqual(agente.resultados[0][1], 4321)
        self.assertEqual(consumo.metricas(agente)["esperas"], 1)


class ArtefatosTest(unittest.TestCase):
    def test_paragrafo_copiado_entre_artefatos_conta_e_copia_de_tarefas_nao(self):
        longo = "Requisito de exemplo com texto suficiente. " * 4
        tarefa = "- [ ] T001 tarefa com caminho e descrição longa. " * 4
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            (pasta / "repos" / "api").mkdir(parents=True)
            (pasta / "spec.md").write_text(f"# Spec\n\n{longo}\n", encoding="utf-8")
            (pasta / "plan.md").write_text(f"# Plano\n\n{longo}\n", encoding="utf-8")
            (pasta / "tasks.md").write_text(f"{tarefa}\n", encoding="utf-8")
            (pasta / "repos" / "api" / "tasks.md").write_text(f"{tarefa}\n", encoding="utf-8")
            repetidos = consumo.paragrafos_repetidos(pasta)
        self.assertEqual([chave for chave, _ in repetidos], ["plan.md e spec.md"])


class QualidadeTest(unittest.TestCase):
    def test_indicadores_vem_dos_eventos_e_dos_relatorios(self):
        eventos = [
            {"ts": "2026-11-01T10:00:00", "tipo": "inicio", "papel": "techlead"},
            {"ts": "2026-11-01T10:05:00", "tipo": "situacao", "situacao": "AGUARDANDO HUMANO"},
            {"ts": "2026-11-01T10:06:00", "tipo": "fim", "papel": "pm", "modo": "analyze", "resultado": "0 críticos"},
            {"ts": "2026-11-01T10:10:00", "tipo": "inicio", "papel": "dev", "repo": "api"},
            {
                "ts": "2026-11-01T10:20:00",
                "tipo": "fim",
                "papel": "reviewer",
                "repo": "api",
                "resultado": "REPROVADO: 1",
            },
            {"ts": "2026-11-01T10:21:00", "tipo": "inicio", "papel": "dev", "repo": "api", "modo": "correcao1"},
            {"ts": "2026-11-01T10:30:00", "tipo": "fim", "papel": "reviewer", "repo": "api", "resultado": "APROVADO"},
            {"ts": "2026-11-01T10:40:00", "tipo": "inicio", "papel": "pm", "modo": "converge"},
            {"ts": "2026-11-01T10:50:00", "tipo": "inicio", "papel": "qa"},
            {"ts": "2026-11-01T11:00:00", "tipo": "situacao", "situacao": "CONCLUÍDO"},
        ]
        relatorios = {
            "integration/qa.md": "Resultado: APROVADO\nRodada: 1\nCritérios de aceite: 13/14 (não cobertos: 1)\n",
            "converge.md": "Resultado: CONVERGIDO\n",
            "api/review.md": "Veredito: APROVADO\nSugestões:\n- [a.py:1] regra ambígua no plano [handoff]\n",
        }
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            gravar_jsonl(pasta / "eventos.jsonl", eventos)
            for relativo, conteudo in relatorios.items():
                (pasta / "reports" / relativo).parent.mkdir(parents=True, exist_ok=True)
                (pasta / "reports" / relativo).write_text(conteudo, encoding="utf-8")
            texto = "\n".join(consumo.qualidade(pasta))
        self.assertIn("| Rodadas do tech lead | 1 |", texto)
        self.assertIn("| Paradas para o humano | 1 |", texto)
        self.assertIn("| Analyze | 0 críticos |", texto)
        self.assertIn("| Passagens do converge | 1 — Resultado: CONVERGIDO |", texto)
        self.assertIn(
            "| Rodadas de QA | 1 — Resultado: APROVADO — Critérios de aceite: 13/14 (não cobertos: 1) |", texto
        )
        self.assertIn("| Achados `[handoff]` no review | 1 |", texto)
        self.assertIn("| Situação final | CONCLUÍDO |", texto)
        self.assertIn("| api | 2 | 2 | 1 |", texto)

    def test_avisa_chamadas_antes_do_inicio_e_depois_do_fim_salvo_com_recorte(self):
        inicio = consumo.momento("2026-11-01T10:00:00+00:00")
        fim = consumo.momento("2026-11-01T12:00:00+00:00")
        cedo = consumo.Agente("claude", "orquestrador", "a", primeira=consumo.momento("2026-11-01T06:00:00+00:00"))
        tarde = consumo.Agente(
            "claude", "pm", "b", primeira=inicio, ultima=consumo.momento("2026-11-01T14:00:00+00:00")
        )
        dentro = consumo.Agente("claude", "dev", "c", primeira=inicio, ultima=fim)
        avisos = consumo.avisos_de_recorte([cedo, tarde, dentro], inicio, fim, False, False)
        self.assertEqual(len(avisos), 2)
        self.assertIn("antes do primeiro evento", avisos[0])
        self.assertIn("orquestrador `a`", avisos[0])
        self.assertIn("pm `b`", avisos[1])
        self.assertEqual(consumo.avisos_de_recorte([cedo, tarde], inicio, fim, True, True), [])

    def test_fim_da_feature_e_o_concluido_e_nao_o_ultimo_evento(self):
        eventos = [
            {"ts": "2026-11-01T10:00:00+00:00", "tipo": "iniciar"},
            {"ts": "2026-11-01T11:00:00+00:00", "tipo": "situacao", "situacao": "CONCLUÍDO"},
            {"ts": "2026-11-01T12:00:00+00:00", "tipo": "nota", "texto": "conferir-donos: OK"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            arquivo = Path(tmp) / "eventos.jsonl"
            gravar_jsonl(arquivo, eventos)
            _, inicio, fim = consumo.ler_eventos(arquivo)
        self.assertEqual((inicio.hour, fim.hour), (10, 11))


class PrincipalTest(unittest.TestCase):
    def test_grava_relatorio_imprime_resumo_e_avisa_chamada_depois_do_fim(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz, transcritos, saida = Path(tmp) / "ws", Path(tmp) / "projeto", Path(tmp) / "consumo.md"
            orquestrador = resposta("m1") + resposta("m2", quando="2026-11-03T10:00:00Z")
            gravar_jsonl(transcritos / "s1.jsonl", orquestrador)
            subagente = [pedido("Papel: pm. Repo: todos da feature. Modo: specify.")] + resposta("m3")
            gravar_jsonl(transcritos / "s1" / "subagents" / "agent-a1.jsonl", subagente)
            evento = {"ts": "2026-11-01T07:00:00", "tipo": "fim", "papel": "pm", "tokens": 50}
            gravar_jsonl(raiz / "specs" / "001" / "eventos.jsonl", [evento])
            argumentos = ["001", "--raiz", str(raiz), "--ferramenta", "claude", "--transcritos", str(transcritos)]
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                consumo.main(argumentos + ["--saida", str(saida)])
            texto = saida.read_text(encoding="utf-8")
        self.assertIn("consumo: 366 tokens em 2 agentes", buffer.getvalue())
        self.assertIn("| pm | 1 | 1 | 122 | 33,3% | 50 |", texto)
        self.assertIn("**Aviso:** há chamadas depois do fim da feature", texto)


if __name__ == "__main__":
    unittest.main()

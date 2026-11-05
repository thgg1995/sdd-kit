"""Verificações do acompanhamento: python -B -m unittest discover -s tests."""
import datetime
import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
import janela
from demo_janela import ControleDemonstracao
from interface import PainelAcompanhamento


class DemonstracaoTest(unittest.TestCase):
    def test_pausa_congela_relogio_e_retomada_nao_conta_intervalo_pausado(self):
        with patch("demo_janela.time.monotonic", return_value=0) as relogio:
            controle = ControleDemonstracao()
            relogio.return_value = 3
            controle.alternar_pausa()
            relogio.return_value = 100
            controle.atualizar_relogio()
            self.assertEqual(controle.tempo_total, 3)
            controle.alternar_pausa()
            relogio.return_value = 102
            controle.atualizar_relogio()
            self.assertEqual(controle.tempo_total, 5)
            self.assertEqual(controle.indice, 0)

    def test_avanco_no_limite_do_timer_nao_pula_duas_etapas(self):
        with patch("demo_janela.time.monotonic", return_value=0) as relogio:
            controle = ControleDemonstracao()
            relogio.return_value = 8
            controle.avancar()
            self.assertEqual(controle.indice, 1)
            self.assertEqual(controle.cenas[controle.indice][0], "constitution")


class InterfaceTest(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.geometry("1600x960+0+0")
        self.escritorio = janela.Escritorio(tk, self.root)
        self.controle = ControleDemonstracao()
        self.painel = PainelAcompanhamento(self.root, self.escritorio, "teste", janela.progresso, self.controle)
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def atualizar(self):
        _, _, campos = self.controle.dados(Path("."), "teste", 100)
        self.painel.atualizar(campos)
        self.escritorio.atualizar(campos)
        self.escritorio.desenhar()
        self.root.update_idletasks()
        return campos

    def test_inicio_espera_e_conclusao_coerentes_em_todos_os_paineis(self):
        self.atualizar()
        self.assertEqual(self.painel.porcentagem.cget("text"), "0%")
        self.assertTrue(self.escritorio.canvas.find_withtag("dev-sono"))
        for _ in range(3):
            self.controle.avancar()
        self.atualizar()
        self.assertIn("AGUARDANDO", self.painel.situacao_topo.cget("text"))
        self.assertEqual(self.painel.resumo["etapa"].cget("text"), "04 · clarify")
        self.assertEqual(len(self.escritorio.canvas.find_withtag("mesa-atual")), 1)
        for _ in range(11):
            self.controle.avancar()
        self.atualizar()
        self.assertEqual(self.painel.porcentagem.cget("text"), "100%")
        self.assertEqual(self.painel.indicadores["aguardando"].cget("text"), "0")
        self.assertTrue(self.escritorio.canvas.find_withtag("dev-sono"))
        for _ in range(200):
            self.escritorio.quadro += 1
            self.escritorio.desenhar()
            if self.escritorio.dev_acordado:
                break
        self.assertTrue(self.escritorio.dev_acordado)
        self.assertEqual(self.escritorio.posicao, [1040, 376])
        self.assertFalse(self.escritorio.canvas.find_withtag("dev-sono"))
        self.assertTrue(self.escritorio.canvas.find_withtag("chamado-dev"))
        self.escritorio.atualizar({"Etapa": "entrada", "Situação": "EM ANDAMENTO"})
        self.escritorio.desenhar()
        self.assertFalse(self.escritorio.dev_acordado)
        self.assertTrue(self.escritorio.canvas.find_withtag("dev-sono"))
        self.escritorio.atualizar({"Etapa": "concluído", "Situação": "CONCLUÍDO"})
        self.escritorio.desenhar()
        self.assertEqual(self.painel.logs.get("1.0", "end").count("Etapa iniciada:"), 15)
        self.assertFalse(self.escritorio.canvas.find_withtag("mesa-atual"))

    def test_resumo_detalhes_e_logs_visiveis_na_janela_menor(self):
        self.root.geometry("1120x860")
        self.root.update()
        self.atualizar()
        for campo in self.painel.resumo.values():
            self.assertTrue(campo.winfo_ismapped())
        for caixa in (self.painel.caixa, self.painel.logs, self.painel.lista):
            self.assertGreater(caixa.winfo_height(), 150)
            self.assertGreater(caixa.winfo_width(), 150)
        self.assertEqual(len(self.escritorio.canvas.find_withtag("nome-mesa")), 14)

    def test_leitura_real_e_qa_dispensado(self):
        with tempfile.TemporaryDirectory() as pasta:
            fdir = Path(pasta) / "specs" / "teste"
            fdir.mkdir(parents=True)
            (fdir / "status.md").write_text(
                "Etapa: implement\nSituação: EM ANDAMENTO\nPróxima ação: Implementar\nQA: dispensado\n",
                encoding="utf-8")
            agora = datetime.datetime.now().isoformat()
            (fdir / "eventos.jsonl").write_text(
                '{"ts":"'+agora+'","tipo":"inicio","papel":"dev","repo":"app"}\n', encoding="utf-8")
            _, _, campos = janela.linhas_da_feature(Path(pasta), "teste", 100)
            self.painel.atualizar(campos)
            self.assertEqual(janela.progresso(campos)[:2], (11, 13))
            self.assertEqual(self.painel.resumo["agente"].cget("text"), "dev")
            self.assertIn("Início: dev · app", self.painel.logs.get("1.0", "end"))
            self.assertIn("–  14 · qa", self.painel.lista.get("1.0", "end"))


if __name__ == "__main__":
    unittest.main()

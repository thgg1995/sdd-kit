#!/usr/bin/env python3
"""Demonstração interativa do painel SDD, sem agentes ou trabalho real.

Uso: python bin/demo_janela.py
Os arquivos temporários são removidos ao fechar a janela.
"""
import datetime
import sys
import tempfile
import time
from pathlib import Path

import janela


class ControleDemonstracao:
    def __init__(self):
        self.pausado = False
        self.indice = 0
        self.tempo_cena = 0.0
        self.tempo_total = 0.0
        self.ultimo = time.monotonic()
        self.eventos = []
        self.cenas = [
            ("entrada", "EM ANDAMENTO", "PM recebendo o pedido da funcionalidade."),
            ("constitution", "EM ANDAMENTO", "Conferindo os princípios do projeto."),
            ("specify", "EM ANDAMENTO", "PM escrevendo os requisitos e critérios de aceite."),
            ("clarify", "AGUARDANDO HUMANO", "Aguardando sua escolha para continuar."),
            ("stack", "EM ANDAMENTO", "Conferindo a stack do projeto."),
            ("plan", "EM ANDAMENTO", "PM organizando o plano de entrega."),
            ("techlead", "EM ANDAMENTO", "Tech lead definindo o desenho técnico."),
            ("tasks", "EM ANDAMENTO", "PM dividindo o trabalho em tarefas."),
            ("analyze", "EM ANDAMENTO", "Conferindo a consistência dos artefatos."),
            ("contratos", "EM ANDAMENTO", "Congelando os contratos da aplicação."),
            ("ambiente", "EM ANDAMENTO", "Preparando o ambiente de execução."),
            ("implement", "EM ANDAMENTO", "Dev implementando os requisitos; reviewer verificará a entrega."),
            ("converge", "EM ANDAMENTO", "PM conferindo a entrega com os requisitos."),
            ("qa", "EM ANDAMENTO", "QA verificando a integração da entrega."),
            ("concluído", "CONCLUÍDO", "Fluxo finalizado. O orquestrador vai chamar o DEV no sofá."),
        ]
        self.registrar(tipo="iniciar", texto="Demonstração iniciada — dados simulados")
        self.iniciar_cena()

    def registrar(self, **dados):
        self.eventos.append({"ts": datetime.datetime.now().isoformat(timespec="seconds"), **dados})

    def papel(self):
        etapa = self.cenas[self.indice][0]
        return "techlead" if etapa == "techlead" else "dev" if etapa == "implement" else "qa" if etapa == "qa" else "pm"

    def iniciar_cena(self):
        etapa = self.cenas[self.indice][0]
        self.registrar(tipo="etapa", etapa=etapa)
        if etapa != "concluído":
            self.registrar(tipo="inicio", papel=self.papel(), modo=etapa)
        else:
            self.registrar(tipo="situacao", situacao="CONCLUÍDO")

    def atualizar_relogio(self, avancar_automatico=True):
        agora = time.monotonic()
        delta, self.ultimo = agora-self.ultimo, agora
        if not self.pausado and self.indice < len(self.cenas)-1:
            self.tempo_cena += delta
            self.tempo_total += delta
            if avancar_automatico and self.tempo_cena >= 8:
                self.proxima()

    def proxima(self):
        if self.indice >= len(self.cenas)-1:
            return
        self.registrar(tipo="fim", papel=self.papel(), modo=self.cenas[self.indice][0], resultado="Etapa concluída")
        self.indice += 1
        self.tempo_cena = 0
        self.iniciar_cena()

    def avancar(self):
        self.atualizar_relogio(avancar_automatico=False)
        self.proxima()
        self.ultimo = time.monotonic()

    def alternar_pausa(self):
        self.atualizar_relogio()
        self.pausado = not self.pausado
        self.ultimo = time.monotonic()

    def dados(self, raiz, feature, largura):
        self.atualizar_relogio()
        etapa, situacao, acao = self.cenas[self.indice]
        campos = {"Etapa": etapa, "Situação": situacao, "Próxima ação": acao, "QA": "pendente",
                  "_eventos": self.eventos, "_tempo_total": self.tempo_total,
                  "_tempo_etapa": self.tempo_cena, "Agentes em curso": "—"}
        linhas = [
            " DEMONSTRAÇÃO · dados simulados",
            " Nenhum agente real em execução.",
            f" Cena {self.indice+1}/{len(self.cenas)} · cada cena dura 8 segundos",
            "",
            f" Etapa: {etapa}",
            f" Situação: {situacao}",
            f" Próxima ação: {acao}",
            "",
            " O bonequinho amarelo é o orquestrador.",
            " Etapas concluídas ficam verdes e comemoram.",
            " Ao finalizar, o orquestrador vai ao sofá e acorda o DEV.",
        ]
        return raiz / "specs" / feature, linhas, campos


def main():
    controle = ControleDemonstracao()
    janela.linhas_da_feature = controle.dados
    with tempfile.TemporaryDirectory(prefix="sdd-demo-") as pasta:
        sys.argv = [str(Path(janela.__file__)), "demonstracao-visual", "--raiz", pasta]
        janela.main(controles=controle)


if __name__ == "__main__":
    main()

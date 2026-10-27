"""Abre o programa: carrega os dados e mostra a janela principal em tela cheia."""

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from classificador.interface.janela import JanelaPrincipal
from classificador.interface.servico import Servico
from classificador.normas.carregador import ErroNorma


def main() -> int:
    app = QApplication(sys.argv)
    try:
        servico = Servico.carregar()
    except ErroNorma as erro:
        QMessageBox.critical(None, "Erro ao carregar os dados das normas", str(erro))
        return 1
    janela = JanelaPrincipal(servico)
    janela.showMaximized()
    return app.exec()

"""Abre o programa: carrega os dados, abre o histórico e mostra a janela em tela cheia."""

import ctypes
import sqlite3
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from classificador.historico.repositorio import RepositorioHistorico
from classificador.interface.janela import JanelaPrincipal
from classificador.interface.servico import Servico, pasta_dados_padrao
from classificador.normas.carregador import ErroNorma


def main() -> int:
    if sys.platform == "win32":
        # Sem isso o Windows agrupa a janela sob o python.exe e mostra o ícone do Python
        # na barra de tarefas.
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MG.ClassificacaoMateriais")
    app = QApplication(sys.argv)
    pasta = pasta_dados_padrao()
    try:
        servico = Servico.carregar(pasta)
    except ErroNorma as erro:
        QMessageBox.critical(None, "Erro ao carregar os dados das normas", str(erro))
        return 1
    try:
        historico = RepositorioHistorico.abrir(pasta)  # historico.db + backup do dia
    except (sqlite3.Error, OSError) as erro:
        QMessageBox.critical(None, "Erro ao abrir o histórico", str(erro))
        return 1
    if servico.icone:
        app.setWindowIcon(QIcon(str(servico.icone)))
    janela = JanelaPrincipal(servico, historico)
    janela.showMaximized()
    try:
        return app.exec()
    finally:
        historico.fechar()

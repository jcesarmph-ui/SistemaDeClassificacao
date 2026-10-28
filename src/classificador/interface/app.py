"""Abre o programa: carrega os dados e mostra a janela principal em tela cheia."""

import ctypes
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from classificador.interface.janela import JanelaPrincipal
from classificador.interface.servico import Servico
from classificador.normas.carregador import ErroNorma


def main() -> int:
    if sys.platform == "win32":
        # Sem isso o Windows agrupa a janela sob o python.exe e mostra o ícone do Python
        # na barra de tarefas.
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MG.ClassificacaoMateriais")
    app = QApplication(sys.argv)
    try:
        servico = Servico.carregar()
    except ErroNorma as erro:
        QMessageBox.critical(None, "Erro ao carregar os dados das normas", str(erro))
        return 1
    if servico.icone:
        app.setWindowIcon(QIcon(str(servico.icone)))
    janela = JanelaPrincipal(servico)
    janela.showMaximized()
    return app.exec()

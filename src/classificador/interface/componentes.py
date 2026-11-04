"""Comportamentos da tela que valem para o programa inteiro (padrão de todos os programas da MG)."""

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabBar,
    QVBoxLayout,
    QWidget,
)


class FiltroRodaDoMouse(QObject):
    """A roda do mouse só rola a tela: nunca troca a opção de uma lista, número ou aba.

    Em cima de uma lista de opções (ex.: acabamento), a rolagem vai para quem está por trás.
    Também põe a mãozinha do mouse em tudo o que é clicável (desligado fica com a seta).
    """

    SEM_RODA = (QComboBox, QAbstractSpinBox, QTabBar)
    CLICAVEIS = (QAbstractButton, QComboBox, QTabBar)

    def eventFilter(self, objeto, evento) -> bool:  # noqa: N802 — nome exigido pelo Qt
        if (evento.type() in (QEvent.Polish, QEvent.EnabledChange)
                and isinstance(objeto, self.CLICAVEIS)):
            objeto.setCursor(Qt.PointingHandCursor if objeto.isEnabled() else Qt.ArrowCursor)
        if evento.type() == QEvent.Wheel and isinstance(objeto, self.SEM_RODA):
            pai = objeto.parentWidget()
            if pai is not None:
                QApplication.sendEvent(pai, evento)
            return True
        return False


def instalar_filtro_roda() -> None:
    """Liga o filtro para o programa inteiro (janelas e diálogos), uma vez só."""
    app = QApplication.instance()
    if app is not None and not hasattr(app, "_filtro_roda"):
        app._filtro_roda = FiltroRodaDoMouse(app)
        app.installEventFilter(app._filtro_roda)


class DialogoConfirmacao(QDialog):
    """Pergunta "tem certeza?" no visual do programa (a caixa do Windows fica toda branca).

    Sem a barra de título do Windows: o título vai dentro da caixa, com o símbolo de aviso em
    amarelo. "Cancelar" já vem selecionado (um Enter sem querer não apaga nada); Esc cancela.
    As cores vêm do estilo da janela principal (`#dialogo`, `#excluir`).
    """

    def __init__(self, pai: QWidget | None, titulo: str, texto: str, sim: str):
        super().__init__(pai, Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle(titulo)
        self.setModal(True)
        moldura = QFrame(objectName="dialogo")
        simbolo = QLabel("⚠", objectName="simbolo_aviso", alignment=Qt.AlignTop)
        self.titulo = QLabel(titulo, objectName="titulo_dialogo")
        self.texto = QLabel(texto, wordWrap=True)
        self.texto.setMinimumWidth(460)
        self.botao_sim = QPushButton(sim, objectName="excluir")
        self.botao_sim.clicked.connect(self.accept)
        self.botao_cancelar = QPushButton("Cancelar")
        self.botao_cancelar.clicked.connect(self.reject)
        self.botao_cancelar.setDefault(True)
        self.botao_cancelar.setFocus()

        textos = QVBoxLayout()
        textos.addWidget(self.titulo)
        textos.addWidget(self.texto)
        linha = QHBoxLayout()
        linha.addWidget(simbolo)
        linha.addLayout(textos, 1)
        botoes = QHBoxLayout()
        botoes.addStretch()
        botoes.addWidget(self.botao_cancelar)
        botoes.addWidget(self.botao_sim)
        caixa = QVBoxLayout(moldura)
        caixa.setContentsMargins(24, 20, 24, 20)
        caixa.setSpacing(18)
        caixa.addLayout(linha)
        caixa.addLayout(botoes)
        fora = QVBoxLayout(self)
        fora.setContentsMargins(0, 0, 0, 0)
        fora.addWidget(moldura)


def confirmar(pai: QWidget | None, titulo: str, texto: str, sim: str) -> bool:
    """Mostra o `DialogoConfirmacao` e espera a resposta: True só se clicar em `sim`."""
    return DialogoConfirmacao(pai, titulo, texto, sim).exec() == QDialog.Accepted

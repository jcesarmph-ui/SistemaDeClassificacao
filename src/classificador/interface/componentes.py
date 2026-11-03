"""Comportamentos da tela que valem para o programa inteiro (padrão de todos os programas da MG)."""

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QTabBar,
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

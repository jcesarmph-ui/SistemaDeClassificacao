"""Aba Divergências e a janela "Registrar divergência" (melhoria contínua do programa).

Divergência = uma classificação salva que estava errada: alguém informa qual era a correta e por
quê. A lista fica pendente até o programa ser corrigido (norma/regra + caso de teste); aí é
marcada como resolvida. Decisões do usuário (2026-11-04): registrar numa janela própria; aba em
lista | detalhes com Pendentes/Resolvidas; só uma divergência pendente por registro (regra no
`RepositorioHistorico`).
"""

from collections.abc import Callable
from html import escape

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from classificador.historico.repositorio import (
    Divergencia,
    ErroDeValidacao,
    Registro,
    RepositorioHistorico,
)
from classificador.interface.abas_historico import (
    PROPORCAO_DETALHES,
    PROPORCAO_LISTA,
    detalhes_html,
    mostrar_situacao,
    nova_tabela,
)
from classificador.interface.componentes import confirmar

COLUNAS = ["Data", "Volume", "Classificado como", "Correta"]
PARA_QUE_SERVE = (
    "Para que serve: quando uma classificação salva estiver errada, registre a divergência "
    "(aba Histórico → botão Registrar divergência) dizendo qual era a correta e por quê. "
    "Cada divergência vira uma correção no programa (norma ou regra + teste) e, depois de "
    "corrigida, é marcada como resolvida. Assim o mesmo erro não se repete."
)


class DialogoDivergencia(QDialog):
    """Janela no visual do programa para informar a classificação correta e o motivo.

    `gravar(correta, motivo)` grava no histórico; se recusar (`ErroDeValidacao`, ex.: campo
    vazio), o erro aparece em vermelho dentro da janela e ela continua aberta.
    """

    def __init__(
        self, pai: QWidget | None, registro: Registro,
        gravar: Callable[[str, str], object],
    ):
        super().__init__(pai, Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle("Registrar divergência")
        self.setModal(True)
        self._gravar = gravar

        titulo = QLabel("Registrar divergência", objectName="titulo_dialogo")
        origem = QLabel(
            f"Registro nº {registro.id} — volume {escape(registro.volume)}<br>"
            f"Classificado como: <b>{escape(registro.resultado or '—')}</b>"
        )
        self.correta = QLineEdit(placeholderText="ex.: ZEE G4 - Z275")
        self.correta.setToolTip("Qual classificação o material deveria ter recebido")
        self.motivo = QPlainTextEdit(placeholderText="Por que a classificação estava errada?")
        self.motivo.setTabChangesFocus(True)
        self.motivo.setMinimumSize(520, 110)
        dica = QLabel("Os dois campos são obrigatórios.", objectName="dica")
        self.erro = QLabel(objectName="erro", wordWrap=True)

        self.botao_salvar = QPushButton("Salvar", objectName="restaurar")
        self.botao_salvar.clicked.connect(self.salvar)
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        botoes = QHBoxLayout()
        botoes.addStretch()
        botoes.addWidget(cancelar)
        botoes.addWidget(self.botao_salvar)

        moldura = QFrame(objectName="dialogo")
        caixa = QVBoxLayout(moldura)
        caixa.setContentsMargins(24, 20, 24, 20)
        caixa.addWidget(titulo)
        caixa.addWidget(origem)
        caixa.addSpacing(8)
        caixa.addWidget(QLabel("Classificação correta"))
        caixa.addWidget(self.correta)
        caixa.addWidget(QLabel("Motivo"))
        caixa.addWidget(self.motivo)
        caixa.addWidget(dica)
        caixa.addWidget(self.erro)
        caixa.addLayout(botoes)
        fora = QVBoxLayout(self)
        fora.setContentsMargins(0, 0, 0, 0)
        fora.addWidget(moldura)
        self.correta.setFocus()

    def salvar(self) -> None:
        try:
            self._gravar(self.correta.text(), self.motivo.toPlainText())
        except ErroDeValidacao as erro:
            self.erro.setText("\n".join(f"✖ {m}" for m in erro.mensagens))
            return
        self.accept()


class PainelDivergencias(QWidget):
    """Lista de divergências (2/5) | detalhes com o registro completo (3/5)."""

    mudou = Signal()  # uma divergência foi resolvida: o Histórico deve se atualizar

    def __init__(self, historico: RepositorioHistorico | None):
        super().__init__()
        self.historico = historico
        self._divergencias: list[Divergencia] = []
        # Pergunta "tem certeza?"; os testes trocam por uma função que responde sozinha.
        self.confirmar: Callable[[str, str, str], bool] = (
            lambda titulo, texto, sim: confirmar(self, titulo, texto, sim, estilo="restaurar")
        )

        nota = QLabel(PARA_QUE_SERVE, objectName="dica", wordWrap=True)
        self.pendentes = QRadioButton("Pendentes", checked=True)
        self.pendentes.setToolTip("Ainda não corrigidas no programa")
        self.resolvidas = QRadioButton("Resolvidas")
        self.resolvidas.setToolTip("Já corrigidas no programa")
        self.pendentes.toggled.connect(self.atualizar)
        self.contagem = QLabel(objectName="dica")
        self.tabela = nova_tabela(COLUNAS, esticar=3)
        self.tabela.itemSelectionChanged.connect(self._mostrar_detalhes)

        self.detalhes = QLabel(wordWrap=True)
        self.detalhes.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.detalhes.setTextInteractionFlags(Qt.TextSelectableByMouse)
        rolagem = QScrollArea(widgetResizable=True)
        rolagem.setWidget(self.detalhes)
        rolagem.setFrameShape(QScrollArea.NoFrame)
        self.situacao = QLabel(wordWrap=True)
        self.botao_resolver = QPushButton("Marcar como resolvida", objectName="restaurar")
        self.botao_resolver.setToolTip("Use depois que o programa foi corrigido")
        self.botao_resolver.clicked.connect(self.resolver)

        lista = QGroupBox("Divergências")
        caixa = QVBoxLayout(lista)
        caixa.addWidget(nota)
        linha = QHBoxLayout()
        linha.addWidget(self.pendentes)
        linha.addWidget(self.resolvidas)
        linha.addStretch()
        linha.addWidget(self.contagem)
        caixa.addLayout(linha)
        caixa.addWidget(self.tabela)

        detalhes = QGroupBox("Detalhes")
        caixa = QVBoxLayout(detalhes)
        caixa.addWidget(rolagem, 1)
        caixa.addWidget(self.situacao)
        caixa.addWidget(self.botao_resolver)

        faixa = QHBoxLayout(self)
        faixa.setContentsMargins(0, 0, 0, 0)
        faixa.addWidget(lista, PROPORCAO_LISTA)  # 2/5 | 3/5, igual ao Histórico
        faixa.addWidget(detalhes, PROPORCAO_DETALHES)
        self.atualizar()

    def atualizar(self) -> None:
        """Relê o banco mantendo a divergência selecionada."""
        so_resolvidas = self.resolvidas.isChecked()
        self.botao_resolver.setVisible(not so_resolvidas)
        if self.historico is None:
            self._divergencias = []
            self.contagem.setText("Histórico indisponível")
        else:
            self._divergencias = self.historico.listar_divergencias(resolvidas=so_resolvidas)
            n = len(self._divergencias)
            self.contagem.setText(f"{n} divergência" + ("" if n == 1 else "s"))
        anterior = self.selecionada()
        self.tabela.blockSignals(True)
        self.tabela.clearSelection()
        self.tabela.setRowCount(len(self._divergencias))
        for linha, d in enumerate(self._divergencias):
            textos = [
                d.criado_em.strftime("%d/%m/%Y %H:%M"),
                d.classificacao.volume,
                d.classificacao.resultado or "",
                d.correta,
            ]
            for coluna, texto in enumerate(textos):
                self.tabela.setItem(linha, coluna, QTableWidgetItem(texto))
            if anterior and d.id == anterior.id:
                self.tabela.selectRow(linha)
        self.tabela.blockSignals(False)
        self._mostrar_detalhes()

    def selecionada(self) -> Divergencia | None:
        linhas = self.tabela.selectionModel().selectedRows()
        if not linhas or linhas[0].row() >= len(self._divergencias):
            return None
        return self._divergencias[linhas[0].row()]

    def _mostrar_detalhes(self) -> None:
        d = self.selecionada()
        self.botao_resolver.setEnabled(d is not None)
        if d is None:
            self.detalhes.setText(
                '<span style="color:#9e9e9e"><i>Clique numa divergência para ver os '
                "detalhes.</i></span>"
            )
            return
        self.detalhes.setText(divergencia_html(d))

    def resolver(self) -> None:
        d = self.selecionada()
        if d is None or self.historico is None:
            return
        pergunta = (
            f"Marcar como resolvida a divergência do volume {d.classificacao.volume} "
            f"(classificado como {d.classificacao.resultado}, correta {d.correta})?\n\n"
            "Faça isso só depois que o programa foi corrigido (norma ou regra + teste)."
        )
        if not self.confirmar("Marcar como resolvida", pergunta, "Marcar como resolvida"):
            return
        try:
            self.historico.resolver_divergencia(d.id)
        except ErroDeValidacao as erro:
            mostrar_situacao(self.situacao, "erro", "\n".join(f"✖ {m}" for m in erro.mensagens))
            return
        self.atualizar()
        mostrar_situacao(
            self.situacao, "salvo", f"✔ Divergência do volume {d.classificacao.volume} resolvida"
        )
        self.mudou.emit()


def divergencia_html(d: Divergencia) -> str:
    """Correta + motivo + quem registrou/resolveu, e embaixo o registro completo."""
    partes = [
        '<p style="color:#9e9e9e; margin:0">Classificação correta</p>',
        f'<p style="font-size:20pt; font-weight:bold; margin:0">{escape(d.correta)}</p>',
        f'<p><b>Motivo:</b> {escape(d.motivo).replace(chr(10), "<br>")}</p>',
        f'<p style="color:#9e9e9e">Registrada em {d.criado_em:%d/%m/%Y %H:%M} por '
        f"{escape(d.usuario)} — {escape(d.computador)}",
    ]
    if d.resolvida_em:
        partes.append(
            f"<br>Resolvida em {d.resolvida_em:%d/%m/%Y %H:%M} por "
            f"{escape(d.resolvida_por or '?')}"
        )
    partes.append("</p><hr><p><b>Classificação salva (como saiu na hora)</b></p>")
    partes.append(detalhes_html(d.classificacao))
    return "".join(partes)

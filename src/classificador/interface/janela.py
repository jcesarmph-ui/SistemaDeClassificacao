"""Janela principal (PySide6): só desenha a tela e liga os botões ao `Servico`.

Nenhuma regra de norma aqui — tudo vem pronto do motor (via `Servico`).
Layout do esboço do usuário: esquerda (logo, acabamento, camada), centro (mecânicas e espessura),
direita (químicas e pesquisa reversa); embaixo, CLASSIFICAR e o resultado.
"""

from html import escape

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from classificador.dominio.amostra import Acabamento
from classificador.dominio.propriedades import Propriedade
from classificador.interface.entrada import ErroEntrada
from classificador.interface.servico import Servico, fabricante
from classificador.motor.reversa import ResultadoPesquisa
from classificador.motor.sequencia import ErroClassificacao

MECANICAS = [
    (Propriedade.LE, "LE", "MPa"),
    (Propriedade.LR, "LR", "MPa"),
    (Propriedade.AL_LO50, "Lo50", "%"),
    (Propriedade.AL_LO80, "Lo80", "%"),
    (Propriedade.EMBUTIMENTO, "Embutimento", "mm"),
]
ESPESSURA = [
    ("espessura_nominal", "Espessura nominal", "mm"),
    ("espessura_real", "Espessura real", "mm"),
    ("largura", "Largura", "mm"),
]

_ESTILO = """
QWidget { font-size: 11pt; }
QGroupBox { font-weight: bold; border: 1px solid #b0b0b0; border-radius: 6px; margin-top: 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
QLineEdit { padding: 3px; }
#cabecalho { background: #2f2f2f; border-radius: 6px; }
#cabecalho QLabel { color: white; }
#titulo { font-size: 15pt; font-weight: bold; }
#classificar { background: #c62828; color: white; font-size: 20pt; font-weight: bold;
               padding: 14px; border-radius: 8px; }
#classificar:hover { background: #e53935; }
#resultado { font-size: 22pt; font-weight: bold; padding: 6px; background: #fffde7; }
#dica { color: #757575; font-style: italic; }
#erro { color: #c62828; }
"""

_CORES_TOLERANCIA = {
    True: "background:#c8e6c9; color:#1b5e20;",
    False: "background:#ffcdd2; color:#b71c1c;",
    None: "background:#eeeeee; color:#424242;",
}


class JanelaPrincipal(QMainWindow):
    def __init__(self, servico: Servico) -> None:
        super().__init__()
        self.servico = servico
        self.campos: dict[str, QLineEdit] = {}  # nome do campo → caixa de texto
        self.dicas: dict[str, QLabel] = {}  # nome do campo → faixa exigida (pesquisa reversa)
        self._resultados_pesquisa: list[ResultadoPesquisa] = []

        self.setWindowTitle("Classificação de Materiais — MG Centro de Serviço")
        self.setStyleSheet(_ESTILO)

        colunas = QHBoxLayout()
        colunas.addWidget(self._coluna_esquerda(), 1)
        colunas.addWidget(self._coluna_centro(), 1)
        colunas.addWidget(self._coluna_direita(), 1)

        tela = QVBoxLayout()
        tela.addLayout(colunas, 2)
        tela.addWidget(self._painel_resultado(), 1)
        central = QWidget()
        central.setLayout(tela)
        self.setCentralWidget(central)

        self._ordem = list(self.campos.values())  # ordem do Enter → próximo campo
        for campo in self._ordem:
            campo.returnPressed.connect(self._enter_no_campo)
        self.limpar_resultado()

    # --- Montagem da tela -------------------------------------------------------------------

    def _coluna_esquerda(self) -> QWidget:
        cabecalho = QFrame(objectName="cabecalho")
        caixa = QVBoxLayout(cabecalho)
        if self.servico.logo:
            logo = QLabel()
            logo.setPixmap(
                QPixmap(str(self.servico.logo)).scaledToWidth(360, Qt.SmoothTransformation)
            )
            caixa.addWidget(logo)
        else:
            caixa.addWidget(QLabel("MG Centro de Serviço"))
        caixa.addWidget(QLabel("CLASSIFICAÇÃO DE MATERIAIS", objectName="titulo"))

        self.acabamento = QComboBox()
        for acabamento in Acabamento:
            self.acabamento.addItem(acabamento.value)
            self.acabamento.setItemData(
                self.acabamento.count() - 1, acabamento.descricao, Qt.ToolTipRole
            )
        self.acabamento.currentTextChanged.connect(self._acabamento_mudou)

        grupo = QGroupBox("Material")
        grade = QGridLayout(grupo)
        grade.addWidget(QLabel("Acabamento"), 0, 0)
        grade.addWidget(self.acabamento, 0, 1, 1, 2)
        grade.addWidget(QLabel("Camada"), 1, 0)
        grade.addWidget(self._novo_campo("camada", "Camada de revestimento"), 1, 1)
        grade.addWidget(QLabel("g/m²"), 1, 2)
        self.dica_camada = QLabel(objectName="dica")
        self.dica_camada.setWordWrap(True)
        grade.addWidget(self.dica_camada, 2, 0, 1, 3)

        nova = QPushButton("Nova classificação")
        nova.clicked.connect(self.nova_classificacao)
        limpar = QPushButton("Limpar valores")
        limpar.clicked.connect(self.limpar_valores)

        coluna = QVBoxLayout()
        coluna.addWidget(cabecalho)
        coluna.addWidget(grupo)
        coluna.addStretch()
        coluna.addWidget(nova)
        coluna.addWidget(limpar)
        return self._embrulhar(coluna)

    def _coluna_centro(self) -> QWidget:
        mecanicas = QGroupBox("Propriedades mecânicas")
        grade = QGridLayout(mecanicas)
        for linha, (prop, rotulo, unidade) in enumerate(MECANICAS):
            self._linha_campo(grade, linha, prop.value, rotulo, unidade, prop.nome_extenso)

        espessura = QGroupBox("Espessura e tolerância")
        grade = QGridLayout(espessura)
        for linha, (nome, rotulo, unidade) in enumerate(ESPESSURA):
            self._linha_campo(grade, linha, nome, rotulo, unidade, rotulo)
        self.tolerancia = QLabel()
        self.tolerancia.setWordWrap(True)
        grade.addWidget(self.tolerancia, len(ESPESSURA), 0, 1, 4)

        coluna = QVBoxLayout()
        coluna.addWidget(mecanicas)
        coluna.addWidget(espessura)
        coluna.addStretch()
        return self._embrulhar(coluna)

    def _coluna_direita(self) -> QWidget:
        quimicas = QGroupBox("Propriedades químicas (%)")
        grade = QGridLayout(quimicas)
        for indice, prop in enumerate(Propriedade.quimicas()):
            linha, coluna = divmod(indice, 4)
            rotulo = QLabel(prop.value)
            rotulo.setToolTip(prop.nome_extenso)
            campo = self._novo_campo(prop.value, prop.nome_extenso)
            dica = QLabel(objectName="dica")
            self.dicas[prop.value] = dica
            caixa = QVBoxLayout()
            caixa.setSpacing(0)
            caixa.addWidget(rotulo)
            caixa.addWidget(campo)
            caixa.addWidget(dica)
            grade.addLayout(caixa, linha, coluna)

        reversa = QGroupBox("Pesquisa reversa — normas correlatas")
        caixa = QVBoxLayout(reversa)
        self.pesquisa = QLineEdit(placeholderText="Digite uma norma (ex.: DC04, EEP G2, GMW 2M)")
        completar = QCompleter(self.servico.nomes_para_autocompletar(), self)
        completar.setCaseSensitivity(Qt.CaseInsensitive)
        completar.setFilterMode(Qt.MatchContains)
        self.pesquisa.setCompleter(completar)
        self.pesquisa.returnPressed.connect(self.pesquisar)
        botao = QPushButton("Pesquisar")
        botao.clicked.connect(self.pesquisar)
        linha = QHBoxLayout()
        linha.addWidget(self.pesquisa)
        linha.addWidget(botao)
        self.escolha_pesquisa = QComboBox()
        self.escolha_pesquisa.currentIndexChanged.connect(self._mostrar_pesquisa)
        self.info_pesquisa = QLabel(objectName="dica")
        self.info_pesquisa.setWordWrap(True)
        caixa.addLayout(linha)
        caixa.addWidget(self.escolha_pesquisa)
        caixa.addWidget(self.info_pesquisa)

        coluna = QVBoxLayout()
        coluna.addWidget(quimicas)
        coluna.addWidget(reversa)
        coluna.addStretch()
        return self._embrulhar(coluna)

    def _painel_resultado(self) -> QWidget:
        classificar = QPushButton("CLASSIFICAR", objectName="classificar")
        classificar.clicked.connect(self.classificar)

        self.resultado = QLineEdit(objectName="resultado", readOnly=True)
        self.resultado.setPlaceholderText("RESULTADO")
        self.norma = QLabel()
        self.correlatas = QLabel(wordWrap=True)
        self.correlatas.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
        self.correlatas.linkHovered.connect(self._mostrar_fabricante)
        self.avisos = QLabel(wordWrap=True)

        topo = QHBoxLayout()
        topo.addWidget(classificar, 1)
        topo.addWidget(self.resultado, 3)
        painel = QVBoxLayout()
        painel.addLayout(topo)
        painel.addWidget(self.norma)
        painel.addWidget(self.correlatas)
        painel.addWidget(self.avisos)
        painel.addStretch()
        grupo = QGroupBox("Resultado")
        grupo.setLayout(painel)
        return grupo

    def _linha_campo(self, grade, linha, nome, rotulo, unidade, dica_mouse) -> None:
        texto = QLabel(rotulo)
        texto.setToolTip(dica_mouse)
        dica = QLabel(objectName="dica")
        self.dicas[nome] = dica
        grade.addWidget(texto, linha, 0)
        grade.addWidget(self._novo_campo(nome, dica_mouse), linha, 1)
        grade.addWidget(QLabel(unidade), linha, 2)
        grade.addWidget(dica, linha, 3)

    def _novo_campo(self, nome: str, dica_mouse: str) -> QLineEdit:
        campo = QLineEdit()
        campo.setToolTip(dica_mouse)
        self.campos[nome] = campo
        return campo

    @staticmethod
    def _embrulhar(layout) -> QWidget:
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    # --- Ações ---------------------------------------------------------------------------

    def classificar(self) -> None:
        textos = {nome: campo.text() for nome, campo in self.campos.items()}
        try:
            saida = self.servico.classificar(self.acabamento.currentText(), textos)
        except (ErroEntrada, ErroClassificacao) as erro:
            self.limpar_resultado()
            self.avisos.setObjectName("erro")
            self.avisos.setText("✖ " + str(erro).replace("\n", "\n✖ "))
            self._repintar(self.avisos)
            return

        self.resultado.setText(saida.resultado or "—")
        self.norma.setText(saida.norma or "")
        if saida.correlatas:
            links = ", ".join(
                f'<a href="{escape(n)}" style="color:#1a4c8b; text-decoration:none">{escape(n)}</a>'
                for n in saida.correlatas
            )
            self.correlatas.setText(f"<b>Normas correlatas:</b> {links}")
        else:
            self.correlatas.setText("")
        self.avisos.setObjectName("")
        self.avisos.setText("\n".join(f"⚠ {a}" for a in saida.avisos))
        self._repintar(self.avisos)
        if saida.tolerancia is not None:
            self.tolerancia.setText(saida.tolerancia.texto)
            self.tolerancia.setStyleSheet(
                _CORES_TOLERANCIA[saida.tolerancia.dentro] + "padding:6px; border-radius:4px;"
            )
        else:
            self.tolerancia.setText("")
            self.tolerancia.setStyleSheet("")

    def pesquisar(self) -> None:
        texto = self.pesquisa.text()
        self._resultados_pesquisa = self.servico.pesquisar(
            texto, self.campos["espessura_nominal"].text()
        ) if texto.strip() else []
        self.escolha_pesquisa.blockSignals(True)
        self.escolha_pesquisa.clear()
        self.escolha_pesquisa.addItems([r.grupo.nbr for r in self._resultados_pesquisa])
        self.escolha_pesquisa.blockSignals(False)
        self.escolha_pesquisa.setVisible(len(self._resultados_pesquisa) > 1)
        if not self._resultados_pesquisa:
            self._limpar_dicas()
            self.info_pesquisa.setText(f"Nenhuma norma encontrada para “{texto.strip()}”.")
            return
        self._mostrar_pesquisa(0)

    def _mostrar_pesquisa(self, indice: int) -> None:
        if not 0 <= indice < len(self._resultados_pesquisa):
            return
        achado = self._resultados_pesquisa[indice]
        self._limpar_dicas()
        linhas = [f"<b>{escape(achado.grupo.nbr)}</b>"]
        if achado.grupo.correlatas:
            linhas.append("Equivalentes: " + escape(", ".join(achado.grupo.correlatas)))
        exigido = achado.requisitos
        if exigido is None:
            linhas.append("Fora do escopo do programa: só equivalências, sem valores exigidos.")
        else:
            for item in exigido.itens:
                if item.propriedade.value in self.dicas:
                    self.dicas[item.propriedade.value].setText(f"[{item.texto}]")
            linhas += [escape(s) for s in exigido.somas]
            if exigido.embutimento:
                linhas.append("Embutimento: " + escape(exigido.embutimento))
            linhas += [escape(n) for n in exigido.notas]
            linhas += [escape(a) for a in exigido.avisos]
        self.info_pesquisa.setText("<br>".join(linhas))

    def nova_classificacao(self) -> None:
        for campo in self.campos.values():
            campo.clear()
        self.acabamento.setCurrentIndex(0)
        self.pesquisa.clear()
        self.escolha_pesquisa.clear()
        self.escolha_pesquisa.setVisible(False)
        self.info_pesquisa.clear()
        self._limpar_dicas()
        self.limpar_resultado()
        self.campos[Propriedade.LE.value].setFocus()

    def limpar_valores(self) -> None:
        """Apaga os números digitados; mantém acabamento e camada."""
        for nome, campo in self.campos.items():
            if nome != "camada":
                campo.clear()
        self.limpar_resultado()

    def limpar_resultado(self) -> None:
        self.resultado.clear()
        self.norma.clear()
        self.correlatas.clear()
        self.avisos.clear()
        self.tolerancia.clear()
        self.tolerancia.setStyleSheet("")
        self._acabamento_mudou(self.acabamento.currentText())

    # --- Detalhes ----------------------------------------------------------------------

    def _enter_no_campo(self) -> None:
        """Enter: tira o "%" e espaços do campo e vai para o próximo."""
        campo = self.sender()
        campo.setText(campo.text().strip().removesuffix("%").strip())
        indice = self._ordem.index(campo)
        if indice + 1 < len(self._ordem):
            self._ordem[indice + 1].setFocus()
            self._ordem[indice + 1].selectAll()

    def _acabamento_mudou(self, texto: str) -> None:
        revestimento = Acabamento(texto).revestimento if texto else None
        self.campos["camada"].setEnabled(revestimento is not None)
        dicas = {
            None: "Sem revestimento: a camada não é usada.",
            "GI": "Duas faces, ex.: 100 → Z100. Vazio ou zero = sem revestimento.",
            "GA": "Duas faces, ex.: 100 → ZF100. Vazio ou zero = sem revestimento.",
            "EG": "Por face, ex.: 50 → 50/50. Vazio ou zero = sem revestimento.",
        }
        self.dica_camada.setText(dicas[revestimento])

    def _limpar_dicas(self) -> None:
        for dica in self.dicas.values():
            dica.clear()

    def _mostrar_fabricante(self, norma: str) -> None:
        if norma:
            QToolTip.showText(QCursor.pos(), fabricante(norma) or "Fabricante não identificado")

    @staticmethod
    def _repintar(widget: QWidget) -> None:
        """Reaplica o estilo depois de trocar o objectName (ex.: avisos ↔ erro)."""
        widget.style().unpolish(widget)
        widget.style().polish(widget)

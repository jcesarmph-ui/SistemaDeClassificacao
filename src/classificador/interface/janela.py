"""Janela principal (PySide6): só desenha a tela e liga os botões ao `Servico`.

Nenhuma regra de norma aqui — tudo vem pronto do motor (via `Servico`).
Cabeçalho em cima e 4 abas: Classificar | Histórico | Divergências | Lixeira. A aba Classificar
é em faixas: entradas (material + espessura | mecânicas | químicas); botões; resultado | pesquisa
reversa. Tema escuro.
"""

from html import escape

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from classificador import __version__
from classificador.dominio.amostra import Acabamento
from classificador.dominio.propriedades import Propriedade
from classificador.historico.repositorio import (
    ErroDeValidacao,
    NovaClassificacao,
    RepositorioHistorico,
)
from classificador.interface.abas_historico import PainelRegistros
from classificador.interface.componentes import instalar_filtro_roda
from classificador.interface.entrada import ErroEntrada
from classificador.interface.servico import Servico, fabricante
from classificador.motor.reversa import ResultadoPesquisa
from classificador.motor.saida import Saida
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

# Tema escolhido pelo usuário: fundo preto, contornos e títulos brancos; vermelho só no botão
# CLASSIFICAR e em erros/problemas; amarelo em avisos; verde no que está certo.
_CORES = {
    "fundo": "#000000", "caixa": "#0a0a0a", "campo": "#161616", "campo_borda": "#3a3a3a",
    "borda": "#e0e0e0", "titulo": "#ffffff", "selecao": "#424242", "botao": "#c62828",
    "botao_mouse": "#e53935", "certo": "#43a047", "aviso": "#ffd54f", "erro": "#ef5350",
}

_ESTILO = """
QWidget {{ font-size: 13pt; color: #f0f0f0; font-family: "Segoe UI"; }}
QMainWindow, #central {{ background: {fundo}; }}
QGroupBox {{ font-weight: bold; background: {caixa}; border: 1px solid {borda};
             border-radius: 6px; margin-top: 12px; padding: 8px 8px 4px 8px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {titulo}; }}
QGroupBox QLabel {{ font-weight: normal; }}
QLineEdit, QComboBox {{ background: {campo}; border: 1px solid {campo_borda}; border-radius: 4px;
                        padding: 6px; color: #ffffff; selection-background-color: {selecao}; }}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {borda}; }}
QLineEdit:disabled {{ background: {caixa}; color: #616161; }}
QComboBox QAbstractItemView {{ background: {campo}; selection-background-color: {selecao}; }}
QPushButton {{ background: {campo}; border: 1px solid {borda}; border-radius: 6px; padding: 10px; }}
QPushButton:hover {{ background: {caixa}; }}
QPushButton:disabled {{ color: #616161; border: 1px solid {campo_borda}; }}
QToolTip {{ background: {campo}; color: #f0f0f0; border: 1px solid {borda}; }}
#titulo {{ font-size: 22pt; font-weight: bold; letter-spacing: 3px; color: {titulo}; }}
#classificar {{ background: {botao}; color: #ffffff; border: none; font-size: 20pt;
                font-weight: bold; letter-spacing: 4px; }}
#classificar:hover {{ background: {botao_mouse}; }}
#resultado {{ font-size: 28pt; font-weight: bold; padding: 6px; border: 2px solid {campo_borda}; }}
#resultado[classificado="true"] {{ border: 2px solid {certo}; }}
#dica {{ color: #9e9e9e; font-style: italic; }}
#avisos {{ color: {aviso}; }}
#erro {{ color: {erro}; }}
#salvo {{ color: {certo}; }}
QTabWidget::pane {{ border: 1px solid {borda}; border-radius: 6px; top: -1px; }}
QTabBar::tab {{ background: {campo}; border: 1px solid {campo_borda}; border-bottom: none;
               border-top-left-radius: 6px; border-top-right-radius: 6px;
               padding: 8px 28px; margin-right: 4px; color: #9e9e9e; }}
QTabBar::tab:selected {{ background: {caixa}; border: 1px solid {borda}; border-bottom: none;
                        color: {titulo}; font-weight: bold; }}
QTabBar::tab:disabled {{ color: #616161; }}
QTableWidget {{ background: {campo}; alternate-background-color: {caixa};
                border: 1px solid {campo_borda}; gridline-color: {campo_borda};
                selection-background-color: {selecao}; selection-color: #ffffff; }}
QHeaderView::section {{ background: {caixa}; color: {titulo}; font-weight: bold;
                        border: none; border-bottom: 1px solid {borda}; padding: 6px; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; }}
"""

_CORES_TOLERANCIA = {
    True: "background:#1b5e20; color:#e8f5e9;",
    False: "background:#b71c1c; color:#ffebee;",
    None: "background:#ffd54f; color:#000000;",  # não avaliada = aviso (amarelo)
}


class JanelaPrincipal(QMainWindow):
    def __init__(
        self, servico: Servico, historico: RepositorioHistorico | None = None
    ) -> None:
        super().__init__()
        instalar_filtro_roda()  # roda do mouse só rola a tela (nunca troca o acabamento)
        self.servico = servico
        self.historico = historico
        # O que foi classificado por último (acabamento, textos digitados, saída): é isso que o
        # Salvar grava. Volta a None quando algo é digitado de novo — aí precisa reclassificar.
        self._classificado: tuple[str, dict[str, str], Saida] | None = None
        self.campos: dict[str, QLineEdit] = {}  # nome do campo → caixa de texto
        self.dicas: dict[str, QLabel] = {}  # nome do campo → faixa exigida (pesquisa reversa)
        self._resultados_pesquisa: list[ResultadoPesquisa] = []

        self.setWindowTitle(
            f"Classificação de Materiais — MG Centro de Serviços — versão {__version__}"
        )
        self.setStyleSheet(_ESTILO.format(**_CORES))

        # Faixas horizontais; dentro de cada faixa, caixas da mesma altura e larguras iguais.
        entradas = QHBoxLayout()
        entradas.addWidget(self._coluna_material(), 1)
        entradas.addWidget(self._caixa_mecanicas(), 1)
        entradas.addWidget(self._caixa_quimicas(), 1)

        saida = QHBoxLayout()
        saida.addWidget(self._caixa_resultado(), 2)
        saida.addWidget(self._caixa_pesquisa(), 1)

        aba_classificar = QVBoxLayout()
        aba_classificar.addLayout(entradas, 2)
        aba_classificar.addLayout(self._botoes())
        aba_classificar.addLayout(saida, 1)

        tela = QVBoxLayout()
        tela.addLayout(self._cabecalho())
        tela.addWidget(self._abas(self._embrulhar(aba_classificar)), 1)
        central = QWidget(objectName="central")
        central.setLayout(tela)
        self.setCentralWidget(central)

        self._ordem = list(self.campos.values())  # ordem do Enter → próximo campo
        for campo in self._ordem:
            campo.returnPressed.connect(self._enter_no_campo)
            campo.textEdited.connect(self._entrada_mudou)
        self.acabamento.currentTextChanged.connect(self._entrada_mudou)
        self.limpar_resultado()

    # --- Montagem da tela -------------------------------------------------------------------

    def _cabecalho(self) -> QGridLayout:
        """Logo à esquerda e título centralizado na largura toda da tela."""
        if self.servico.logo:
            logo = QLabel()
            logo.setPixmap(
                QPixmap(str(self.servico.logo)).scaledToHeight(80, Qt.SmoothTransformation)
            )
        else:
            logo = QLabel("MG Centro de Serviços")
        grade = QGridLayout()
        grade.addWidget(logo, 0, 0, Qt.AlignLeft)
        grade.addWidget(QLabel("CLASSIFICAÇÃO DE MATERIAIS", objectName="titulo"), 0, 1)
        versao = QLabel(f"versão {__version__}", objectName="dica")
        grade.addWidget(versao, 0, 2, Qt.AlignRight | Qt.AlignBottom)
        grade.setColumnStretch(0, 1)
        grade.setColumnStretch(2, 1)  # coluna vazia do mesmo tamanho → título no centro
        return grade

    def _abas(self, classificar: QWidget) -> QTabWidget:
        """Classificar | Histórico | Divergências | Lixeira (sem histórico: só Classificar)."""
        self.historico_aba = PainelRegistros(self.historico)
        self.lixeira_aba = PainelRegistros(self.historico, lixeira=True)
        divergencias = QLabel("A lista de divergências será feita na próxima etapa.",
                              objectName="dica", alignment=Qt.AlignCenter)
        # Excluir no Histórico aparece na Lixeira e vice-versa.
        self.historico_aba.mudou.connect(self.lixeira_aba.atualizar)
        self.lixeira_aba.mudou.connect(self.historico_aba.atualizar)

        self.abas = QTabWidget()
        self.abas.addTab(classificar, "Classificar")
        self.abas.addTab(self.historico_aba, "Histórico")
        self.abas.addTab(divergencias, "Divergências")
        self.abas.addTab(self.lixeira_aba, "Lixeira")
        if self.historico is None:
            for indice in range(1, self.abas.count()):
                self.abas.setTabEnabled(indice, False)
                self.abas.setTabToolTip(indice, "Histórico indisponível")
        self.abas.currentChanged.connect(self._aba_mudou)
        return self.abas

    def _aba_mudou(self, _indice: int) -> None:
        """Ao abrir uma aba, relê o banco (outra pessoa pode ter salvo algo nesse meio-tempo)."""
        atual = self.abas.currentWidget()
        if isinstance(atual, PainelRegistros):
            atual.atualizar()

    def _coluna_material(self) -> QWidget:
        self.acabamento = QComboBox()
        for acabamento in Acabamento:
            self.acabamento.addItem(acabamento.value)
            self.acabamento.setItemData(
                self.acabamento.count() - 1, acabamento.descricao, Qt.ToolTipRole
            )
        self.acabamento.currentTextChanged.connect(self._acabamento_mudou)

        material = QGroupBox("Material")
        grade = QGridLayout(material)
        grade.addWidget(QLabel("Acabamento"), 0, 0)
        grade.addWidget(self.acabamento, 0, 1, 1, 2)
        grade.addWidget(QLabel("Camada"), 1, 0)
        grade.addWidget(self._novo_campo("camada", "Camada de revestimento"), 1, 1)
        grade.addWidget(QLabel("g/m²"), 1, 2)
        self.dica_camada = QLabel(objectName="dica")
        self.dica_camada.setWordWrap(True)
        grade.addWidget(self.dica_camada, 2, 0, 1, 3)

        espessura = QGroupBox("Espessura e tolerância")
        grade = QGridLayout(espessura)
        for linha, (nome, rotulo, unidade) in enumerate(ESPESSURA):
            self._linha_campo(grade, linha, nome, rotulo, unidade, rotulo)
        self.tolerancia = QLabel()
        self.tolerancia.setWordWrap(True)
        self.tolerancia.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        grade.addWidget(self.tolerancia, len(ESPESSURA), 0, 1, 4)

        coluna = QVBoxLayout()
        coluna.setContentsMargins(0, 0, 0, 0)
        coluna.addWidget(material)
        coluna.addWidget(espessura)
        return self._embrulhar(coluna)

    def _caixa_mecanicas(self) -> QGroupBox:
        mecanicas = QGroupBox("Propriedades mecânicas")
        grade = QGridLayout(mecanicas)
        for linha, (prop, rotulo, unidade) in enumerate(MECANICAS):
            self._linha_campo(grade, linha, prop.value, rotulo, unidade, prop.nome_extenso)
        return mecanicas

    def _caixa_quimicas(self) -> QGroupBox:
        """13 elementos em 3 colunas → 5 linhas, alinhadas com as 5 das mecânicas."""
        quimicas = QGroupBox("Propriedades químicas (%)")
        grade = QGridLayout(quimicas)
        for indice, prop in enumerate(Propriedade.quimicas()):
            linha, coluna = divmod(indice, 3)
            rotulo = QLabel(prop.value)
            rotulo.setToolTip(prop.nome_extenso)
            dica = QLabel(objectName="dica")
            self.dicas[prop.value] = dica
            celula = QGridLayout()
            celula.setVerticalSpacing(0)
            celula.addWidget(rotulo, 0, 0)
            celula.addWidget(self._novo_campo(prop.value, prop.nome_extenso), 0, 1)
            celula.addWidget(dica, 1, 1)
            celula.setColumnMinimumWidth(0, 28)
            grade.addLayout(celula, linha, coluna)
        return quimicas

    def _botoes(self) -> QHBoxLayout:
        nova = QPushButton("Nova classificação")
        nova.clicked.connect(self.nova_classificacao)
        limpar = QPushButton("Limpar valores")
        limpar.clicked.connect(self.limpar_valores)
        classificar = QPushButton("CLASSIFICAR", objectName="classificar")
        classificar.clicked.connect(self.classificar)
        self.volume = QLineEdit(placeholderText="nº do volume")
        self.volume.setToolTip("Número do volume (obrigatório para salvar no histórico)")
        self.volume.returnPressed.connect(self.salvar)
        self.volume.textEdited.connect(self._limpar_situacao_salvar)
        self.botao_salvar = QPushButton("Salvar")
        self.botao_salvar.setToolTip("Salva esta classificação no histórico")
        self.botao_salvar.clicked.connect(self.salvar)
        faixa = QHBoxLayout()
        faixa.addWidget(nova, 1)
        faixa.addWidget(limpar, 1)
        faixa.addWidget(classificar, 3)
        faixa.addWidget(QLabel("Volume"))
        faixa.addWidget(self.volume, 1)
        faixa.addWidget(self.botao_salvar, 1)
        return faixa

    def _caixa_resultado(self) -> QGroupBox:
        self.resultado = QLineEdit(objectName="resultado", readOnly=True)
        self.resultado.setPlaceholderText("RESULTADO")
        self.norma = QLabel()
        self.correlatas = QLabel(wordWrap=True)
        self.correlatas.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
        self.correlatas.linkHovered.connect(self._mostrar_fabricante)
        self.avisos = QLabel(wordWrap=True, objectName="avisos")
        self.situacao_salvar = QLabel(wordWrap=True)  # "✔ Salvo…" (verde) ou erro (vermelho)

        grupo = QGroupBox("Resultado")
        caixa = QVBoxLayout(grupo)
        caixa.addWidget(self.resultado)
        caixa.addWidget(self.norma)
        caixa.addWidget(self.correlatas)
        caixa.addWidget(self.avisos)
        caixa.addWidget(self.situacao_salvar)
        caixa.addStretch()
        return grupo

    def _caixa_pesquisa(self) -> QGroupBox:
        self.pesquisa = QLineEdit(placeholderText="Digite uma norma (ex.: DC04, EEP G2, GMW 2M)")
        completar = QCompleter(self.servico.nomes_para_autocompletar(), self)
        completar.setCaseSensitivity(Qt.CaseInsensitive)
        completar.setFilterMode(Qt.MatchContains)
        self.pesquisa.setCompleter(completar)
        self.pesquisa.returnPressed.connect(self.pesquisar)
        botao = QPushButton("Pesquisar")
        botao.setStyleSheet("padding: 4px 12px;")
        botao.clicked.connect(self.pesquisar)
        linha = QHBoxLayout()
        linha.addWidget(self.pesquisa)
        linha.addWidget(botao)
        self.escolha_pesquisa = QComboBox()
        self.escolha_pesquisa.setVisible(False)
        self.escolha_pesquisa.currentIndexChanged.connect(self._mostrar_pesquisa)
        self.info_pesquisa = QLabel(objectName="dica")
        self.info_pesquisa.setWordWrap(True)

        grupo = QGroupBox("Pesquisa reversa — normas correlatas")
        caixa = QVBoxLayout(grupo)
        caixa.addLayout(linha)
        caixa.addWidget(self.escolha_pesquisa)
        caixa.addWidget(self.info_pesquisa)
        caixa.addStretch()
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

        self._classificado = (self.acabamento.currentText(), textos, saida)
        self._atualizar_salvar()
        self._mostrar_situacao_salvar(None, "")
        self.resultado.setText(saida.resultado or "—")
        self._marcar_resultado(saida.resultado is not None)
        self.norma.setText(saida.norma or "")
        if saida.correlatas:
            estilo = "color:#64b5f6; text-decoration:none"
            links = ", ".join(
                f'<a href="{escape(n)}" style="{estilo}">{escape(n)}</a>'
                for n in saida.correlatas
            )
            self.correlatas.setText(f"<b>Normas correlatas:</b> {links}")
        else:
            self.correlatas.setText("")
        self.avisos.setObjectName("avisos")
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

    def salvar(self) -> None:
        """Grava no histórico o que foi classificado por último, com o volume."""
        if self.historico is None or self._classificado is None:
            return
        acabamento, textos, saida = self._classificado
        tolerancia = saida.tolerancia
        nova = NovaClassificacao(
            volume=self.volume.text(),
            acabamento=acabamento,
            valores=textos,
            resultado=saida.resultado,
            norma=saida.norma,
            correlatas=list(saida.correlatas),
            avisos=list(saida.avisos),
            tolerancia=tolerancia.texto if tolerancia else None,
            tolerancia_dentro=tolerancia.dentro if tolerancia else None,
        )
        try:
            numero = self.historico.salvar(nova)
        except ErroDeValidacao as erro:
            self._mostrar_situacao_salvar("erro", "\n".join(f"✖ {m}" for m in erro.mensagens))
            if not self.volume.text().strip():
                self.volume.setFocus()
            return
        self._classificado = None  # já salvo: não grava duas vezes o mesmo
        self._atualizar_salvar()
        self._mostrar_situacao_salvar(
            "salvo", f"✔ Salvo no histórico (nº {numero}) — volume {self.volume.text().strip()}"
        )

    def nova_classificacao(self) -> None:
        self.volume.clear()
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
        self._classificado = None
        self._atualizar_salvar()
        self._mostrar_situacao_salvar(None, "")
        self.resultado.clear()
        self._marcar_resultado(False)
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

    def _entrada_mudou(self, *_) -> None:
        """Digitou depois de classificar: o resultado na tela não vale mais para salvar."""
        if self._classificado is not None:
            self._classificado = None
            self._atualizar_salvar()

    def _atualizar_salvar(self) -> None:
        pode = self.historico is not None and self._classificado is not None
        if pode and not self._classificado[2].resultado:
            pode = False  # sem resultado não há o que salvar
        self.botao_salvar.setEnabled(pode)
        if self.historico is None:
            dica = "Histórico indisponível"
        elif pode:
            dica = "Salva esta classificação no histórico"
        else:
            dica = "Classifique para poder salvar"
        self.botao_salvar.setToolTip(dica)

    def _mostrar_situacao_salvar(self, tipo: str | None, texto: str) -> None:
        self.situacao_salvar.setObjectName(tipo or "")
        self.situacao_salvar.setText(texto)
        self._repintar(self.situacao_salvar)

    def _limpar_situacao_salvar(self, *_) -> None:
        if self.situacao_salvar.objectName() == "erro":
            self._mostrar_situacao_salvar(None, "")

    def _marcar_resultado(self, classificado: bool) -> None:
        """Contorno verde quando há classificação ("deu certo"); neutro se vazio ou erro."""
        self.resultado.setProperty("classificado", classificado)
        self._repintar(self.resultado)

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

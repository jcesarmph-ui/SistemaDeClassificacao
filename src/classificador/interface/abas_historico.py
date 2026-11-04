"""Abas Histórico e Lixeira: lista de classificações salvas (2/3) | detalhes do registro (1/3).

As duas abas têm o mesmo desenho; muda só o que os botões fazem:
- Histórico: pesquisar e **Excluir** (manda para a Lixeira).
- Lixeira: pesquisar, **Restaurar** (volta ao Histórico) e **Excluir permanentemente**.
Toda exclusão pede confirmação (decisão do usuário, 2026-11-04). Nenhuma regra aqui: quem lê e
grava é o `RepositorioHistorico`.
"""

from collections.abc import Callable
from html import escape

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from classificador.dominio.propriedades import Propriedade
from classificador.historico.repositorio import (
    ErroDeValidacao,
    Registro,
    RepositorioHistorico,
)
from classificador.interface.componentes import confirmar

COLUNAS = ["Data/hora", "Volume", "Resultado"]

# Campos que não são propriedades da norma: nome na tela e unidade.
_OUTROS_CAMPOS = {
    "camada": ("Camada", "g/m²"),
    "espessura_nominal": ("Espessura nominal", "mm"),
    "espessura_real": ("Espessura real", "mm"),
    "largura": ("Largura", "mm"),
}
_CORES_TOLERANCIA = {True: "#43a047", False: "#ef5350", None: "#ffd54f"}


class PainelRegistros(QWidget):
    """Lista + detalhes. `lixeira=False` → aba Histórico; `True` → aba Lixeira."""

    mudou = Signal()  # algo foi excluído/restaurado: as outras abas devem se atualizar

    def __init__(self, historico: RepositorioHistorico | None, lixeira: bool = False):
        super().__init__()
        self.historico = historico
        self.lixeira = lixeira
        self._registros: list[Registro] = []
        # Pergunta "tem certeza?"; os testes trocam por uma função que responde sozinha.
        self.confirmar: Callable[[str, str, str], bool] = (
            lambda titulo, texto, sim: confirmar(self, titulo, texto, sim)
        )

        self.pesquisa = QLineEdit(
            placeholderText="Pesquisar (volume, resultado, acabamento, data, usuário…)"
        )
        self.pesquisa.setToolTip(
            "Procura em tudo o que foi salvo; várias palavras = todas têm de aparecer"
        )
        self.pesquisa.textChanged.connect(self.atualizar)
        self.contagem = QLabel(objectName="dica")

        self.tabela = QTableWidget(0, len(COLUNAS))
        self.tabela.setHorizontalHeaderLabels(COLUNAS)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)  # registro não é editável
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setAlternatingRowColors(True)
        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        cabecalho.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        cabecalho.setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabela.itemSelectionChanged.connect(self._mostrar_detalhes)

        self.detalhes = QLabel(wordWrap=True)
        self.detalhes.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.detalhes.setTextInteractionFlags(Qt.TextSelectableByMouse)
        rolagem = QScrollArea(widgetResizable=True)
        rolagem.setWidget(self.detalhes)
        rolagem.setFrameShape(QScrollArea.NoFrame)

        self.situacao = QLabel(wordWrap=True)  # erro (vermelho) ou "✔ Restaurado…" (verde)
        if lixeira:
            self.botao_restaurar = QPushButton("Restaurar", objectName="restaurar")
            self.botao_restaurar.setToolTip("Devolve o registro ao Histórico")
            self.botao_restaurar.clicked.connect(self.restaurar)
            self.botao_excluir = QPushButton("Excluir permanentemente", objectName="excluir")
            self.botao_excluir.setToolTip("Apaga de vez: não dá para desfazer")
            botoes = [self.botao_restaurar, self.botao_excluir]
        else:
            self.botao_excluir = QPushButton("Excluir", objectName="excluir")
            self.botao_excluir.setToolTip("Manda para a Lixeira (dá para restaurar depois)")
            botoes = [self.botao_excluir]
        self.botao_excluir.clicked.connect(self.excluir)

        lista = QGroupBox("Lixeira" if lixeira else "Classificações salvas")
        caixa = QVBoxLayout(lista)
        linha = QHBoxLayout()
        linha.addWidget(self.pesquisa, 1)
        linha.addWidget(self.contagem)
        caixa.addLayout(linha)
        caixa.addWidget(self.tabela)

        detalhes = QGroupBox("Detalhes")
        caixa = QVBoxLayout(detalhes)
        caixa.addWidget(rolagem, 1)
        caixa.addWidget(self.situacao)
        for botao in botoes:
            caixa.addWidget(botao)

        faixa = QHBoxLayout(self)
        faixa.setContentsMargins(0, 0, 0, 0)
        faixa.addWidget(lista, 2)
        faixa.addWidget(detalhes, 1)
        self.atualizar()

    # --- Lista ------------------------------------------------------------------------

    def atualizar(self) -> None:
        """Relê o banco (outra pessoa pode ter salvo algo) mantendo o registro selecionado."""
        if self.historico is None:
            self._registros = []
            self.contagem.setText("Histórico indisponível")
        else:
            self._registros = self.historico.listar(self.pesquisa.text(), lixeira=self.lixeira)
            n = len(self._registros)
            self.contagem.setText(f"{n} registro" + ("" if n == 1 else "s"))
        anterior = self.selecionado()
        self.tabela.blockSignals(True)
        self.tabela.clearSelection()
        self.tabela.setRowCount(len(self._registros))
        for linha, registro in enumerate(self._registros):
            textos = [
                registro.criado_em.strftime("%d/%m/%Y %H:%M") if registro.criado_em else "",
                registro.volume,
                registro.resultado or "",
            ]
            for coluna, texto in enumerate(textos):
                self.tabela.setItem(linha, coluna, QTableWidgetItem(texto))
            if anterior and registro.id == anterior.id:
                self.tabela.selectRow(linha)
        self.tabela.blockSignals(False)
        self._mostrar_detalhes()

    def selecionado(self) -> Registro | None:
        linhas = self.tabela.selectionModel().selectedRows()
        if not linhas or linhas[0].row() >= len(self._registros):
            return None
        return self._registros[linhas[0].row()]

    def _mostrar_detalhes(self) -> None:
        registro = self.selecionado()
        for botao in self._botoes():
            botao.setEnabled(registro is not None)
        if registro is None:
            onde = "da Lixeira" if self.lixeira else "do Histórico"
            self.detalhes.setText(
                f'<span style="color:#9e9e9e"><i>Clique num registro {onde} '
                "para ver os detalhes.</i></span>"
            )
            return
        self.detalhes.setText(detalhes_html(registro))

    def _botoes(self) -> list[QPushButton]:
        if self.lixeira:
            return [self.botao_restaurar, self.botao_excluir]
        return [self.botao_excluir]

    # --- Ações ------------------------------------------------------------------------

    def excluir(self) -> None:
        registro = self.selecionado()
        if registro is None or self.historico is None:
            return
        nome = f"o registro nº {registro.id} (volume {registro.volume}, {registro.resultado})"
        if self.lixeira:
            pergunta = f"Excluir permanentemente {nome}?\n\nIsso não pode ser desfeito."
            sim, acao = "Excluir permanentemente", self.historico.excluir_permanentemente
            feito = f"✔ Registro nº {registro.id} excluído permanentemente"
        else:
            pergunta = (
                f"Mandar {nome} para a Lixeira?\n\nDá para restaurar depois, pela aba Lixeira."
            )
            sim, acao = "Mandar para a Lixeira", self.historico.excluir
            feito = f"✔ Registro nº {registro.id} enviado para a Lixeira"
        if not self.confirmar("Confirmar exclusão", pergunta, sim):
            return
        self._executar(acao, registro.id, feito)

    def restaurar(self) -> None:
        registro = self.selecionado()
        if registro is None or self.historico is None:
            return
        self._executar(
            self.historico.restaurar, registro.id,
            f"✔ Registro nº {registro.id} devolvido ao Histórico",
        )

    def _executar(self, acao, id_: int, feito: str) -> None:
        try:
            acao(id_)
        except ErroDeValidacao as erro:
            self._mostrar_situacao("erro", "\n".join(f"✖ {m}" for m in erro.mensagens))
            return
        self.atualizar()
        self._mostrar_situacao("salvo", feito)
        self.mudou.emit()

    def _mostrar_situacao(self, tipo: str, texto: str) -> None:
        self.situacao.setObjectName(tipo)
        self.situacao.setText(texto)
        self.situacao.style().unpolish(self.situacao)
        self.situacao.style().polish(self.situacao)


def detalhes_html(r: Registro) -> str:
    """O "retrato" do registro, como saiu na hora em que foi salvo."""
    partes = [
        f'<p style="font-size:20pt; font-weight:bold; margin:0">{escape(r.resultado or "—")}</p>',
    ]
    if r.norma:
        partes.append(f"<p>{escape(r.norma)}</p>")
    if r.correlatas:
        partes.append(f"<p><b>Normas correlatas:</b> {escape(', '.join(r.correlatas))}</p>")
    if r.tolerancia:
        cor = _CORES_TOLERANCIA[r.tolerancia_dentro]
        partes.append(f'<p style="color:{cor}">{escape(r.tolerancia)}</p>')
    if r.avisos:
        avisos = "<br>".join(f"⚠ {escape(a)}" for a in r.avisos)
        partes.append(f'<p style="color:#ffd54f">{avisos}</p>')

    linhas = [
        ("Nº", str(r.id)),
        ("Volume", r.volume),
        ("Acabamento", r.acabamento),
        ("Salvo em", r.criado_em.strftime("%d/%m/%Y %H:%M") if r.criado_em else ""),
        ("Por", f"{r.usuario} — {r.computador}"),
        ("Versão do programa", r.versao_programa),
    ]
    if r.excluido_em:
        linhas.append(
            ("Excluído em", f"{r.excluido_em:%d/%m/%Y %H:%M} por {r.excluido_por or '?'}")
        )
    partes.append(_tabela(linhas))
    valores = valores_digitados(r.valores)
    if valores:
        partes.append("<p><b>Valores digitados</b></p>" + _tabela(valores))
    return "".join(partes)


def valores_digitados(valores) -> list[tuple[str, str]]:
    """Só os campos preenchidos, na ordem da tela: camada, espessura, mecânicas, químicas."""
    ordem = [*_OUTROS_CAMPOS, *(p.value for p in Propriedade)]
    linhas = []
    for nome in ordem:
        texto = (valores.get(nome) or "").strip()
        if not texto:
            continue
        if nome in _OUTROS_CAMPOS:
            rotulo, unidade = _OUTROS_CAMPOS[nome]
        else:
            prop = Propriedade(nome)
            rotulo, unidade = prop.nome_extenso, prop.unidade
            if prop in Propriedade.quimicas():
                rotulo = f"{prop.value} ({prop.nome_extenso})"
        linhas.append((rotulo, f"{texto} {unidade}"))
    return linhas


def _tabela(linhas: list[tuple[str, str]]) -> str:
    celulas = "".join(
        f'<tr><td style="color:#9e9e9e; padding-right:12px">{escape(a)}</td>'
        f"<td>{escape(b)}</td></tr>"
        for a, b in linhas
    )
    return f"<table>{celulas}</table>"

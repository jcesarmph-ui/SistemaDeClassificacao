"""Teste de fumaça da janela: abre sem mostrar (offscreen), preenche, classifica e pesquisa."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # sem abrir janela de verdade
QtWidgets = pytest.importorskip("PySide6.QtWidgets")

from classificador.interface.janela import JanelaPrincipal  # noqa: E402
from classificador.interface.servico import Servico  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def janela(app, pasta):
    return JanelaPrincipal(Servico.carregar(pasta))


def preencher(janela, valores, acabamento="FF"):
    janela.acabamento.setCurrentText(acabamento)
    for nome, texto in valores.items():
        janela.campos[nome].setText(texto)


VALORES = {
    "C": "0,10", "Al": "0,02", "LE": "200", "AL_LO50": "35",
    "espessura_nominal": "0,60", "espessura_real": "0,62", "largura": "1000",
}


def test_tem_os_7_acabamentos_e_todos_os_campos(janela):
    acabamentos = [janela.acabamento.itemText(i) for i in range(janela.acabamento.count())]
    assert acabamentos == ["FF", "FQ", "FQ DO", "GI ZN", "GI ZM", "GA ZF", "EG"]
    assert {"LE", "LR", "AL_LO50", "AL_LO80", "EMBUTIMENTO", "Mo", "B", "largura"} <= set(
        janela.campos
    )
    assert janela.campos["Mn"].toolTip() == "Manganês"


def test_classificar_mostra_resultado_correlatas_e_tolerancia(janela):
    preencher(janela, VALORES)
    janela.classificar()
    assert janela.resultado.text() == "AAA"
    assert janela.norma.text() == "De acordo com a norma NBR 0000-1:2026"
    assert "EN 10130 DC01" in janela.correlatas.text()
    assert janela.tolerancia.text().startswith("Dentro da tolerância")


def test_erro_de_digitacao_aparece_nos_avisos_sem_resultado(janela):
    preencher(janela, VALORES | {"LE": "abc"})
    janela.classificar()
    assert janela.resultado.text() == ""
    assert "Limite de escoamento: 'abc' não é um número" in janela.avisos.text()


def test_enter_tira_porcentagem_e_vai_para_o_proximo_campo(janela):
    campo = janela.campos["AL_LO50"]
    campo.setText("46,7 %")
    campo.returnPressed.emit()
    assert campo.text() == "46,7"


def test_camada_desabilitada_sem_revestimento(janela):
    janela.acabamento.setCurrentText("FF")
    assert not janela.campos["camada"].isEnabled()
    janela.acabamento.setCurrentText("EG")
    assert janela.campos["camada"].isEnabled()
    assert "50/50" in janela.dica_camada.text()


def test_pesquisa_reversa_mostra_faixas_ao_lado_dos_campos(janela):
    janela.pesquisa.setText("dc04")
    janela.pesquisar()
    assert janela.dicas["LE"].text() == "[120 – 160 MPa]"
    assert janela.dicas["C"].text() == "[≤ 0,007 %]"
    assert "NBR 0000-1 BBB G1" in janela.info_pesquisa.text()


def test_pesquisa_fora_do_escopo_e_sem_resultado(janela):
    janela.pesquisa.setText("CR180B2")
    janela.pesquisar()
    assert "Fora do escopo" in janela.info_pesquisa.text()
    assert janela.dicas["LE"].text() == ""
    janela.pesquisa.setText("zzzz")
    janela.pesquisar()
    assert "Nenhuma norma encontrada" in janela.info_pesquisa.text()


def test_limpar_valores_mantem_acabamento_e_nova_classificacao_apaga_tudo(janela):
    preencher(janela, VALORES | {"camada": "100"}, acabamento="GI ZN")
    janela.limpar_valores()
    assert janela.campos["LE"].text() == "" and janela.campos["camada"].text() == "100"
    assert janela.acabamento.currentText() == "GI ZN"
    janela.nova_classificacao()
    assert janela.campos["camada"].text() == ""
    assert janela.acabamento.currentText() == "FF"

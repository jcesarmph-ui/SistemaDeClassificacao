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
    assert janela.resultado.property("classificado") is True  # contorno verde
    assert janela.norma.text() == "De acordo com a norma NBR 0000-1:2026"
    assert "EN 10130 DC01" in janela.correlatas.text()
    assert janela.tolerancia.text().startswith("Dentro da tolerância")


def test_erro_de_digitacao_aparece_nos_avisos_sem_resultado(janela):
    preencher(janela, VALORES | {"LE": "abc"})
    janela.classificar()
    assert janela.resultado.text() == ""
    assert janela.resultado.property("classificado") is False
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


def test_roda_do_mouse_nao_troca_o_acabamento(janela):
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtGui import QWheelEvent

    janela.show()  # a lista só reage à roda quando está visível
    janela.acabamento.setCurrentText("FF")
    roda = QWheelEvent(  # um passo para baixo: sem o filtro, trocaria FF → FQ
        QPointF(5, 5), QPointF(5, 5), QPoint(0, 0), QPoint(0, -120),
        Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False,
    )
    QtWidgets.QApplication.sendEvent(janela.acabamento, roda)
    assert janela.acabamento.currentText() == "FF"
    janela.close()


def test_maozinha_nos_botoes(janela):
    from PySide6.QtCore import Qt

    janela.show()
    botoes = janela.findChildren(QtWidgets.QPushButton)
    assert botoes
    for botao in botoes:  # ligado → mãozinha; desligado (ex.: Salvar) → seta
        esperado = Qt.PointingHandCursor if botao.isEnabled() else Qt.ArrowCursor
        assert botao.cursor().shape() == esperado, botao.text()
    janela.close()


# --- Salvar no histórico ------------------------------------------------------------------


@pytest.fixture
def janela_com_historico(app, pasta):
    from classificador.historico.repositorio import RepositorioHistorico

    historico = RepositorioHistorico.abrir(pasta, quem=("ana", "PC-01"))
    yield JanelaPrincipal(Servico.carregar(pasta), historico)
    historico.fechar()


def test_salvar_so_depois_de_classificar(janela_com_historico):
    janela = janela_com_historico
    assert not janela.botao_salvar.isEnabled()
    preencher(janela, VALORES)
    janela.classificar()
    assert janela.botao_salvar.isEnabled()
    janela.campos["LE"].textEdited.emit("210")  # digitou de novo → precisa reclassificar
    assert not janela.botao_salvar.isEnabled()


def test_salvar_grava_o_retrato_com_o_volume(janela_com_historico):
    janela = janela_com_historico
    preencher(janela, VALORES)
    janela.classificar()
    janela.volume.setText("V-123")
    janela.salvar()
    [registro] = janela.historico.listar()
    assert (registro.volume, registro.resultado, registro.acabamento) == ("V-123", "AAA", "FF")
    assert registro.valores["LE"] == "200"
    assert registro.tolerancia_dentro is True
    assert janela.situacao_salvar.text().startswith("✔ Salvo no histórico")
    assert janela.situacao_salvar.objectName() == "salvo"  # verde
    assert not janela.botao_salvar.isEnabled()  # não salva duas vezes o mesmo


def test_volume_vazio_e_erro_em_vermelho_e_nao_grava(janela_com_historico):
    janela = janela_com_historico
    preencher(janela, VALORES)
    janela.classificar()
    janela.salvar()
    assert janela.historico.listar() == []
    assert janela.situacao_salvar.objectName() == "erro"
    assert "Informe o volume" in janela.situacao_salvar.text()
    assert janela.resultado.text() == "AAA"  # o resultado continua na tela


def test_sem_historico_o_salvar_fica_desligado(janela):
    preencher(janela, VALORES)
    janela.classificar()
    assert not janela.botao_salvar.isEnabled()


def test_nova_classificacao_limpa_o_volume_e_limpar_valores_mantem(janela_com_historico):
    janela = janela_com_historico
    janela.volume.setText("V-9")
    janela.limpar_valores()
    assert janela.volume.text() == "V-9"
    janela.nova_classificacao()
    assert janela.volume.text() == ""


# --- Abas Histórico e Lixeira -------------------------------------------------------------


def salvar_volume(janela, volume, valores=VALORES):
    preencher(janela, valores)
    janela.classificar()
    janela.volume.setText(volume)
    janela.salvar()


def responde(painel, resposta):
    """Troca a pergunta "tem certeza?" por uma resposta automática e guarda o que foi perguntado."""
    perguntas = []

    def confirmar(titulo, texto, sim):
        perguntas.append((titulo, texto, sim))
        return resposta

    painel.confirmar = confirmar
    return perguntas


def test_tem_as_4_abas(janela_com_historico):
    abas = janela_com_historico.abas
    assert [abas.tabText(i) for i in range(abas.count())] == [
        "Classificar", "Histórico", "Divergências", "Lixeira"
    ]
    assert all(abas.isTabEnabled(i) for i in range(abas.count()))


def test_sem_historico_so_a_aba_classificar_funciona(janela):
    assert janela.abas.isTabEnabled(0)
    assert not any(janela.abas.isTabEnabled(i) for i in range(1, janela.abas.count()))


def test_historico_lista_e_mostra_detalhes(janela_com_historico):
    janela = janela_com_historico
    salvar_volume(janela, "V-1")
    janela.abas.setCurrentWidget(janela.historico_aba)  # abrir a aba relê o banco
    painel = janela.historico_aba
    assert painel.tabela.rowCount() == 1
    assert painel.tabela.item(0, 1).text() == "V-1"
    assert painel.tabela.item(0, 2).text() == "AAA"
    assert not painel.botao_excluir.isEnabled()  # nada selecionado
    painel.tabela.selectRow(0)
    assert painel.botao_excluir.isEnabled()
    detalhes = painel.detalhes.text()
    assert "AAA" in detalhes and "ana — PC-01" in detalhes
    assert "Limite de escoamento" in detalhes and "200 MPa" in detalhes
    assert "Ni (Níquel)" not in detalhes  # campo vazio não aparece


def test_pesquisa_do_historico(janela_com_historico):
    janela = janela_com_historico
    salvar_volume(janela, "V-1")
    salvar_volume(janela, "X-2")
    painel = janela.historico_aba
    painel.pesquisa.setText("x-2")
    assert painel.tabela.rowCount() == 1 and painel.tabela.item(0, 1).text() == "X-2"
    assert painel.contagem.text() == "1 registro"
    painel.pesquisa.setText("")
    assert painel.contagem.text() == "2 registros"


def test_excluir_pergunta_e_cancelar_nao_apaga(janela_com_historico):
    janela = janela_com_historico
    salvar_volume(janela, "V-1")
    painel = janela.historico_aba
    painel.atualizar()
    painel.tabela.selectRow(0)
    perguntas = responde(painel, False)
    painel.excluir()
    assert perguntas[0][2] == "Mandar para a Lixeira"
    assert len(janela.historico.listar()) == 1


def test_excluir_manda_para_a_lixeira_e_restaurar_devolve(janela_com_historico):
    janela = janela_com_historico
    salvar_volume(janela, "V-1")
    historico, lixeira = janela.historico_aba, janela.lixeira_aba
    historico.atualizar()
    historico.tabela.selectRow(0)
    responde(historico, True)
    historico.excluir()
    assert historico.tabela.rowCount() == 0
    assert "enviado para a Lixeira" in historico.situacao.text()
    assert lixeira.tabela.rowCount() == 1  # a Lixeira se atualizou sozinha
    lixeira.tabela.selectRow(0)
    assert "Excluído em" in lixeira.detalhes.text()
    lixeira.restaurar()
    assert lixeira.tabela.rowCount() == 0
    assert historico.tabela.rowCount() == 1


def test_excluir_permanentemente_pergunta_e_apaga_de_vez(janela_com_historico):
    janela = janela_com_historico
    salvar_volume(janela, "V-1")
    [registro] = janela.historico.listar()
    janela.historico.excluir(registro.id)
    lixeira = janela.lixeira_aba
    lixeira.atualizar()
    lixeira.tabela.selectRow(0)
    perguntas = responde(lixeira, True)
    lixeira.excluir()
    assert "não pode ser desfeito" in perguntas[0][1]
    assert janela.historico.obter(registro.id) is None
    assert lixeira.tabela.rowCount() == 0


def test_confirmacao_no_visual_do_programa(janela_com_historico):
    from classificador.interface.componentes import DialogoConfirmacao

    dialogo = DialogoConfirmacao(janela_com_historico, "Confirmar exclusão", "Tem certeza?", "Sim")
    assert dialogo.botao_cancelar.isDefault()  # Enter sem querer = cancelar
    assert dialogo.botao_sim.objectName() == "excluir"  # contorno vermelho
    dialogo.botao_sim.click()
    assert dialogo.result() == QtWidgets.QDialog.Accepted

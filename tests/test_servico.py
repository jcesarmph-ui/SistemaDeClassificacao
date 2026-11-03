"""Testes do serviço da aplicação (carrega os dados e atende a tela), com dados fictícios."""

import shutil

import pytest

from classificador.interface.entrada import ErroEntrada
from classificador.interface.servico import Servico, fabricante
from classificador.motor.sequencia import ErroClassificacao
from classificador.normas.carregador import ErroNorma

CAMPOS = {
    "C": "0,10", "Al": "0,02", "LE": "200", "AL_LO50": "35",
    "espessura_nominal": "0,60", "espessura_real": "0,62", "largura": "1000",
}


def test_classifica_a_partir_dos_textos_da_tela(pasta):
    saida = Servico.carregar(pasta).classificar("FF", CAMPOS)
    assert saida.resultado == "AAA"
    assert saida.correlatas == ["EN 10130 DC01", "GMW 2M CR1"]
    assert saida.tolerancia.dentro is True


def test_erro_de_digitacao_vira_erro_de_entrada(pasta):
    with pytest.raises(ErroEntrada, match="Limite de escoamento"):
        Servico.carregar(pasta).classificar("FF", CAMPOS | {"LE": "abc"})


def test_acabamento_fora_da_folha(pasta):
    with pytest.raises(ErroClassificacao, match="GI ZN"):
        Servico.carregar(pasta).classificar("GI ZN", CAMPOS)


def test_pesquisa_reversa_com_espessura_digitada(pasta):
    [resultado] = Servico.carregar(pasta).pesquisar("dc04", "0,45")
    textos = {r.propriedade.value: r.texto for r in resultado.requisitos.itens}
    assert textos["LE"] == "120 – 200 MPa"


def test_autocompletar(pasta):
    assert "EN 10130 DC04" in Servico.carregar(pasta).nomes_para_autocompletar()


def test_sem_correlatas_nem_tolerancias_ainda_classifica(pasta):
    (pasta / "correlatas.yaml").unlink()
    shutil.rmtree(pasta / "tolerancias")
    servico = Servico.carregar(pasta)
    saida = servico.classificar("FF", CAMPOS)
    assert saida.resultado == "AAA"
    assert saida.correlatas == []
    # a folha pede uma norma de tolerância que não está na pasta: avisa em vez de esconder
    assert saida.tolerancia.dentro is None
    assert "ainda não foi transcrita" in saida.tolerancia.texto
    # sem correlatas, o autocompletar ainda traz os graus das normas transcritas
    assert servico.nomes_para_autocompletar() == ["NBR 0000-1 AAA", "NBR 0000-1 BBB G1"]


def test_logo_opcional(pasta):
    assert Servico.carregar(pasta).logo is None
    (pasta / "logo_mg.png").write_bytes(b"png")
    assert Servico.carregar(pasta).logo == pasta / "logo_mg.png"


def test_pasta_sem_folha_e_erro_claro(tmp_path):
    with pytest.raises(ErroNorma, match="não encontrado"):
        Servico.carregar(tmp_path)


@pytest.mark.parametrize(
    ("norma", "esperado"),
    [
        ("HES-C052 JSC270D", "Honda (Honda Engineering Standard)"),
        ("TSG3100G SPC270D", "Toyota"),
        ("GMW 2M CR3", "General Motors"),
        ("GMW EMS ME 1508 EEP", "General Motors"),
        ("VW 50065 CR3", "Volkswagen"),
        ("MS 50002 CR04", "Stellantis (ex-Fiat Chrysler/FCA)"),
        ("FG 52806 FEP04", "Fiat (Stellantis) — a confirmar"),
        ("EN 10130 DC04", "Norma europeia (CEN) — não é montadora"),
        ("JIS G3131 SPHC", "Norma japonesa (JSA) — não é montadora"),
        ("NBR 7008-4 ZARBH-180", "ABNT"),
        ("XYZ 1", None),
    ],
)
def test_fabricante_pelo_prefixo(norma, esperado):
    assert fabricante(norma) == esperado


def test_pesquisa_acha_grau_sem_correlatas(pasta):
    # Na correlata fictícia só há AAA e BBB G1; tirando o BBB G1, ele precisa continuar achável
    texto = (pasta / "correlatas.yaml").read_text(encoding="utf-8")
    inicio = texto.index("  - nbr: NBR 0000-1 BBB G1")
    fim = texto.index("  # Fora do escopo")
    (pasta / "correlatas.yaml").write_text(texto[:inicio] + texto[fim:], encoding="utf-8")
    servico = Servico.carregar(pasta)
    [achado] = servico.pesquisar("BBB G1")
    assert achado.grupo.nbr == "NBR 0000-1 BBB G1"
    assert achado.grupo.correlatas == []
    assert achado.requisitos is not None
    assert "NBR 0000-1 BBB G1" in servico.nomes_para_autocompletar()


def test_pesquisa_funciona_sem_arquivo_de_correlatas(pasta):
    (pasta / "correlatas.yaml").unlink()
    [achado] = Servico.carregar(pasta).pesquisar("AAA")
    assert achado.grupo.nbr == "NBR 0000-1 AAA"

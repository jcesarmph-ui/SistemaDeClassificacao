"""Testes das normas correlatas: lista do resultado e pesquisa reversa por qualquer norma."""

from decimal import Decimal
from pathlib import Path

import pytest

from classificador.dominio.amostra import Acabamento, Amostra
from classificador.dominio.modelos import Correlatas, FolhaClassificacoes
from classificador.dominio.propriedades import Propriedade as P
from classificador.motor.reversa import pesquisar
from classificador.motor.saida import formatar
from classificador.motor.sequencia import classificar
from classificador.normas.carregador import ErroNorma, carregar_correlatas, carregar_norma

DADOS = Path(__file__).parent / "dados"
D = Decimal


@pytest.fixture(scope="module")
def correlatas():
    return carregar_correlatas(DADOS / "correlatas-ficticias.yaml")


@pytest.fixture(scope="module")
def normas():
    norma = carregar_norma(DADOS / "norma-ficticia.yaml")
    return {norma.codigo: norma}


# --- Lista no resultado -----------------------------------------------------------

def test_correlatas_de_um_grau(correlatas):
    assert correlatas.de("NBR 0000-1:2026", "AAA", Acabamento.FF) == [
        "EN 10130 DC01",
        "GMW 2M CR1",
    ]


def test_correlatas_so_do_eg(correlatas):
    assert correlatas.de("NBR 0000-1:2026", "AAA", Acabamento.EG)[-1] == "EN 10152 DC01"


def test_grau_sem_correlatas(correlatas):
    assert correlatas.de("NBR 0000-1:2026", "ZZZ") == []


def test_correlatas_na_saida_da_classificacao(correlatas, normas):
    folha = FolhaClassificacoes.model_validate(
        {
            "acabamentos": {
                "FF": {"tabelas": [{"norma": "NBR 0000-1:2026"}], "se_nenhum": {"resultado": "X"}},
                "EG": {"tabelas": [{"norma": "NBR 0000-1:2026"}], "se_nenhum": {"resultado": "X"}},
            }
        }
    )
    valores = {P.C: D("0.10"), P.Al: D("0.02"), P.LE: D("200"), P.AL_LO50: D("35")}  # → AAA

    def saida(acabamento):
        amostra = Amostra(acabamento, valores, D("0.80"))
        return formatar(classificar(amostra, folha, normas), amostra, correlatas)

    assert saida(Acabamento.FF).correlatas == ["EN 10130 DC01", "GMW 2M CR1"]
    assert saida(Acabamento.EG).correlatas == ["EN 10130 DC01", "GMW 2M CR1", "EN 10152 DC01"]


# --- Busca -------------------------------------------------------------------------

@pytest.mark.parametrize("texto", ["DC04", "dc04", "EN 10130 DC04", "en10130-dc04"])
def test_busca_ignora_maiusculas_espacos_e_hifens(correlatas, texto):
    assert [g.grau for g in correlatas.buscar(texto)] == ["BBB G1"]


def test_busca_prefere_nome_que_termina_com_o_texto(correlatas):
    # "CR1" termina "GMW 2M CR1"; em "CR180B2" o CR1 só aparece no meio
    assert [g.nbr for g in correlatas.buscar("CR1")] == ["NBR 0000-1 AAA"]
    # sem nenhum nome terminando com o texto, procura em qualquer parte
    assert [g.nbr for g in correlatas.buscar("CR180")] == ["NBR 5915-4 BH-180"]


def test_busca_pelo_proprio_grau_nbr(correlatas):
    assert [g.nbr for g in correlatas.buscar("BH-180")] == ["NBR 5915-4 BH-180"]


def test_busca_vazia(correlatas):
    assert correlatas.buscar("  -  ") == []


def test_autocompletar(correlatas):
    nomes = correlatas.todos_os_nomes()
    assert "EN 10130 DC04" in nomes and "NBR 5915-4 BH-180" in nomes
    assert nomes == sorted(nomes)


# --- Pesquisa reversa por qualquer norma --------------------------------------------

def test_pesquisa_reversa_por_correlata_traz_requisitos(correlatas, normas):
    [resultado] = pesquisar("DC04", correlatas, normas)
    assert resultado.grupo.grau == "BBB G1"
    exigido = {r.propriedade: r.texto for r in resultado.requisitos.itens}
    assert exigido[P.LE] == "120 – 160 MPa"


def test_pesquisa_reversa_com_espessura(correlatas, normas):
    [resultado] = pesquisar("DC04", correlatas, normas, D("0.45"))
    exigido = {r.propriedade: r.texto for r in resultado.requisitos.itens}
    assert exigido[P.LE] == "120 – 200 MPa"


def test_pesquisa_reversa_fora_do_escopo_so_equivalencias(correlatas, normas):
    [resultado] = pesquisar("CR180B2", correlatas, normas)
    assert resultado.requisitos is None
    assert resultado.grupo.correlatas == ["GMW 3032M CR180B2", "MS 50002 BHC180Y290T"]


# --- Validação ---------------------------------------------------------------------

def test_grupo_com_norma_sem_grau_e_recusado():
    with pytest.raises(ValueError, match="juntos"):
        Correlatas.model_validate({"grupos": [{"nbr": "X", "norma": "NBR 0000-1:2026"}]})


def test_arquivo_de_correlatas_invalido(tmp_path):
    arquivo = tmp_path / "c.yaml"
    arquivo.write_text("grupos:\n  - correlatas: [X]\n", encoding="utf-8")
    with pytest.raises(ErroNorma, match="nbr"):
        carregar_correlatas(arquivo)

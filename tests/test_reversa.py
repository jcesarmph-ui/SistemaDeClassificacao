"""Testes da pesquisa reversa: valores exigidos por um grau, com ou sem espessura."""

from decimal import Decimal
from pathlib import Path

import pytest

from classificador.dominio.propriedades import Propriedade as P
from classificador.motor.reversa import requisitos
from classificador.normas.carregador import carregar_norma

NORMA_FICTICIA = Path(__file__).parent / "dados" / "norma-ficticia.yaml"
D = Decimal


@pytest.fixture(scope="module")
def norma():
    return carregar_norma(NORMA_FICTICIA)


def textos(resultado):
    return {r.propriedade: r.texto for r in resultado.itens}


def test_sem_espessura_limites_da_tabela_e_notas_em_texto(norma):
    resultado = requisitos(norma, "BBB G1")
    assert textos(resultado) == {
        P.LE: "120 – 160 MPa",
        P.AL_LO50: "≥ 42 %",
        P.AL_LO80: "≥ 40 %",
        P.C: "≤ 0,007 %",
        P.Ti: "≤ 0,200 %",
    }
    nota_a = "Tabela 2, nota a — e < 0,50 mm: LE máx +40, alongamento Lo50 mín -4"
    assert resultado.notas == [nota_a]
    assert resultado.embutimento == "Depende da espessura (tabela de 0,30 a 0,35 mm)"


def test_itens_na_ordem_da_tela_mecanicas_depois_quimicas(norma):
    ordem = [r.propriedade for r in requisitos(norma, "BBB G1").itens]
    assert ordem == [P.LE, P.AL_LO50, P.AL_LO80, P.C, P.Ti]


def test_somas_e_avisos_do_grau(norma):
    resultado = requisitos(norma, "BBB G1")
    assert resultado.somas == ["Ti + Nb ≤ 0,20 %"]
    assert resultado.avisos == ["BBB G1 não substitui AAA sem autorização."]


def test_com_espessura_limites_ja_ajustados(norma):
    resultado = requisitos(norma, "BBB G1", D("0.32"))
    assert textos(resultado)[P.LE] == "120 – 200 MPa"  # nota a: máx +40
    assert textos(resultado)[P.AL_LO50] == "≥ 38 %"  # nota a: mín −4
    assert textos(resultado)[P.EMBUTIMENTO] == "≥ 9,5 mm"  # linha 0,30
    assert resultado.notas == ["Aplicada: Tabela 2, nota a"]
    assert resultado.embutimento == "Linha de 0,30 mm da tabela"


def test_com_espessura_sem_nota_e_fora_da_tabela_de_embutimento(norma):
    resultado = requisitos(norma, "BBB G1", D("0.80"))
    assert textos(resultado)[P.LE] == "120 – 160 MPa"
    assert P.EMBUTIMENTO not in textos(resultado)
    assert resultado.notas == []
    assert resultado.embutimento == "Não exigido: espessura fora da tabela (0,30 a 0,35 mm)"


def test_grau_sem_coluna_de_embutimento(norma):
    resultado = requisitos(norma, "AAA")
    assert resultado.embutimento is None
    assert textos(resultado)[P.Al] == "≥ 0,010 %"


def test_grau_inexistente(norma):
    with pytest.raises(KeyError, match="ZZZ"):
        requisitos(norma, "ZZZ")

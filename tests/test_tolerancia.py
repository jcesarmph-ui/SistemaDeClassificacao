"""Testes da verificação de tolerância de espessura."""

from decimal import Decimal
from pathlib import Path

import pytest

from classificador.dominio.amostra import Acabamento, Amostra
from classificador.dominio.modelos import Grau, Limite
from classificador.dominio.propriedades import Propriedade as P
from classificador.tolerancia.verificar import verificar_tolerancia

DADOS = Path(__file__).parent / "dados"
D = Decimal


@pytest.fixture(scope="module")
def norma(tmp_path_factory):
    from classificador.normas.carregador import carregar_tolerancias

    pasta = tmp_path_factory.mktemp("tol")
    texto = (DADOS / "tolerancia-ficticia.yaml").read_text(encoding="utf-8")
    (pasta / "t.yaml").write_text(texto, encoding="utf-8")
    return carregar_tolerancias(pasta)["NBR 0000-T"]


def grau(le_min):
    limites = {P.LE: Limite(min=le_min, max=900)} if le_min is not None else {}
    return Grau(sigla="G", nome_na_norma="G", limites=limites)


def verificar(norma, nominal="0.60", real="0.62", largura="1000", le_min=140,
              acabamento=Acabamento.GI_ZN, camada=None):
    amostra = Amostra(
        acabamento,
        espessura_nominal=D(nominal) if nominal else None,
        espessura_real=D(real) if real else None,
        largura=D(largura) if largura else None,
        camada=D(camada) if camada else None,
    )
    return verificar_tolerancia(amostra, grau(le_min), norma)


def test_dentro_da_tolerancia(norma):
    resultado = verificar(norma)  # Tabela 1 (LE ≤ 260), 0,40 < e ≤ 0,80, L ≤ 1200 → ± 0,05
    assert resultado.dentro is True
    assert (resultado.minimo, resultado.maximo, resultado.tolerancia) == (
        D("0.55"), D("0.65"), D("0.05")
    )
    assert resultado.texto == "Dentro da tolerância: 0,55 a 0,65 mm (± 0,05) — NBR 0000-T, Tabela 1"


def test_limite_e_inclusive(norma):
    assert verificar(norma, real="0.65").dentro is True
    assert verificar(norma, real="0.55").dentro is True


def test_fora_da_tolerancia(norma):
    resultado = verificar(norma, real="0.66")
    assert resultado.dentro is False
    assert resultado.texto.startswith("Fora da tolerância: 0,55 a 0,65 mm")


def test_coluna_pela_largura(norma):
    assert verificar(norma, largura="1200").tolerancia == D("0.05")
    assert verificar(norma, largura="1300").tolerancia == D("0.06")
    assert verificar(norma, largura="1600").tolerancia == D("0.07")


def test_tabela_pelo_le_minimo_do_grau(norma):
    resultado = verificar(norma, le_min=280)  # Tabela 2 (260 < LE < 360)
    assert resultado.tolerancia == D("0.06")
    assert resultado.texto.endswith("Tabela 2")


def test_acrescimo_do_revestimento_z275(norma):
    resultado = verificar(norma, camada="275")
    assert resultado.tolerancia == D("0.06")  # 0,05 + 0,01
    assert "(± 0,06, com +0,01 do revestimento ≥ 275 g/m²)" in resultado.texto
    assert verificar(norma, camada="274").tolerancia == D("0.05")
    # EG não está na lista de acabamentos do acréscimo
    assert verificar(norma, camada="300", acabamento=Acabamento.EG).tolerancia == D("0.05")


@pytest.mark.parametrize(
    ("kwargs", "motivo"),
    [
        ({"largura": None}, "informe a largura"),
        ({"real": None}, "informe a espessura real"),
        ({"nominal": None, "real": None}, "informe a espessura nominal, a espessura real"),
        ({"le_min": 400}, "LE mínimo 400 MPa fora das tabelas"),
        ({"nominal": "0.90", "real": "0.90"}, "espessura nominal 0,90 mm fora da Tabela 1"),
        ({"nominal": "0.40", "real": "0.40", "largura": "1600"}, "não definida na norma"),
    ],
)
def test_nao_avaliada_com_motivo(norma, kwargs, motivo):
    resultado = verificar(norma, **kwargs)
    assert resultado.dentro is None
    assert resultado.texto.startswith("Tolerância não avaliada:")
    assert motivo in resultado.texto


def test_resultado_fixo_sem_grau_usa_a_tabela_sem_le(norma):
    # ZC (último recurso de GI/GA) e 1006/08 EG: sem grau → mesma tabela do grau sem LE
    amostra = Amostra(Acabamento.GI_ZN, espessura_nominal=D("0.60"),
                      espessura_real=D("0.60"), largura=D("1000"))
    resultado = verificar_tolerancia(amostra, None, norma)
    assert resultado.dentro is True
    assert resultado.tolerancia == D("0.06")


def test_grau_sem_le_minimo_usa_a_tabela_indicada_pela_norma(norma):
    resultado = verificar(norma, le_min=None)  # ex.: ZC na NBR 7013 → Tabela 2
    assert resultado.dentro is True
    assert resultado.tolerancia == D("0.06")
    assert resultado.texto.endswith("Tabela 2")


def test_grau_sem_le_e_norma_sem_tabela_indicada_nao_avalia(norma):
    sem_indicacao = norma.model_copy(update={"tabela_sem_le": None})
    amostra = Amostra(Acabamento.GI_ZN, espessura_nominal=D("0.60"),
                      espessura_real=D("0.60"), largura=D("1000"))
    resultado = verificar_tolerancia(amostra, grau(None), sem_indicacao)
    assert resultado.dentro is None
    assert "o grau não tem LE mínimo" in resultado.texto

"""Testes da conversão do texto digitado na tela em números e na Amostra."""

from decimal import Decimal

import pytest

from classificador.dominio.amostra import Acabamento
from classificador.dominio.propriedades import Propriedade as P
from classificador.interface.entrada import ErroEntrada, ler_numero, montar_amostra

D = Decimal


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("46,7", "46.7"),
        ("46.7", "46.7"),
        ("46,7%", "46.7"),
        (" 46,7 % ", "46.7"),
        ("304", "304"),
        ("0,0306", "0.0306"),
        ("0", "0"),
    ],
)
def test_le_numero_com_virgula_ponto_e_porcentagem(texto, esperado):
    assert ler_numero(texto) == D(esperado)
    assert str(ler_numero(texto)) == esperado  # Decimal exato, sem float


@pytest.mark.parametrize("texto", ["", "   ", "%"])
def test_vazio(texto):
    assert ler_numero(texto) is None


@pytest.mark.parametrize("texto", ["abc", "4,5,6", "1.244,5", "--3", "1e3"])
def test_texto_invalido(texto):
    with pytest.raises(ValueError, match="não é um número"):
        ler_numero(texto)


def test_monta_amostra_a_partir_dos_campos():
    amostra = montar_amostra(
        "GI ZN",
        {
            "LE": "304", "LR": "361", "AL_LO50": "46,7%", "AL_LO80": "", "C": "0,0306",
            "espessura_nominal": "0,67", "espessura_real": "0.67", "largura": "1244",
            "camada": "100",
        },
    )
    assert amostra.acabamento == Acabamento.GI_ZN
    assert amostra.valor(P.LE) == D("304")
    assert amostra.valor(P.AL_LO50) == D("46.7")
    assert not amostra.preenchido(P.AL_LO80)
    assert (amostra.espessura_nominal, amostra.largura, amostra.camada) == (
        D("0.67"), D("1244"), D("100")
    )


def test_junta_todos_os_erros_numa_mensagem_so():
    with pytest.raises(ErroEntrada) as erro:
        montar_amostra("FF", {"LE": "abc", "Mn": "-0,2", "largura": "1,2,3"})
    mensagem = str(erro.value)
    assert "Limite de escoamento: 'abc' não é um número" in mensagem
    assert "Manganês: não pode ser negativo" in mensagem
    assert "Largura: '1,2,3' não é um número" in mensagem


def test_acabamento_invalido():
    with pytest.raises(ErroEntrada, match="acabamento"):
        montar_amostra("XX", {})


def test_campo_desconhecido_e_erro_de_programacao():
    with pytest.raises(KeyError):
        montar_amostra("FF", {"Zn": "1"})

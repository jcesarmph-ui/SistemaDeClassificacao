"""Testes da lista de propriedades (entradas da tela que as normas podem limitar)."""

from classificador.dominio.propriedades import Propriedade


def test_quimicas_incluem_molibdenio():
    assert Propriedade.Mo.nome_extenso == "Molibdênio"
    assert Propriedade.Mo.unidade == "%"


def test_lista_de_quimicas_na_ordem_da_tela():
    simbolos = [p.value for p in Propriedade.quimicas()]
    assert simbolos == [
        "C", "Mn", "P", "S", "Al", "Ni", "Ti", "V", "Nb", "Cr", "Si", "B", "Mo",
    ]


def test_rotulo_curto_usado_nos_avisos():
    assert Propriedade.LE.rotulo == "LE"
    assert Propriedade.AL_LO50.rotulo == "alongamento Lo50"
    assert Propriedade.EMBUTIMENTO.rotulo == "embutimento"
    assert Propriedade.Mn.rotulo == "Mn"


def test_mecanicas_e_unidades():
    assert Propriedade.LE.unidade == "MPa"
    assert Propriedade.AL_LO50.unidade == "%"
    assert Propriedade.EMBUTIMENTO.unidade == "mm"
    assert Propriedade.LE not in Propriedade.quimicas()

"""Testes da entrada do motor: acabamento e amostra (valores digitados pelo usuário)."""

from decimal import Decimal

import pytest

from classificador.dominio.amostra import Acabamento, Amostra
from classificador.dominio.propriedades import Propriedade


def test_acabamentos_da_folha_de_classificacoes():
    assert [a.value for a in Acabamento] == ["FF", "FQ", "FQ DO", "GI ZN", "GI ZM", "GA ZF", "EG"]
    assert Acabamento.GA_ZF.descricao.startswith("Produto plano zincado por imersão")


def test_tipo_de_revestimento_de_cada_acabamento():
    assert Acabamento.FF.revestimento is None
    assert Acabamento.FQ_DO.revestimento is None
    assert Acabamento.GI_ZN.revestimento == "GI"
    assert Acabamento.GI_ZM.revestimento == "GI"
    assert Acabamento.GA_ZF.revestimento == "GA"
    assert Acabamento.EG.revestimento == "EG"


def test_valor_vazio_e_preenchido():
    amostra = Amostra(
        acabamento=Acabamento.FF,
        valores={Propriedade.LE: Decimal("150"), Propriedade.C: None},
        espessura_nominal=Decimal("0.80"),
    )
    assert amostra.valor(Propriedade.LE) == Decimal("150")
    assert amostra.preenchido(Propriedade.LE)
    # vazio explícito (None) e propriedade não informada são a mesma coisa: vazio
    assert not amostra.preenchido(Propriedade.C)
    assert not amostra.preenchido(Propriedade.Mn)
    assert amostra.valor(Propriedade.Mn) is None


def test_zero_digitado_conta_como_preenchido():
    amostra = Amostra(acabamento=Acabamento.FF, valores={Propriedade.Ti: Decimal("0")})
    assert amostra.preenchido(Propriedade.Ti)


def test_camada_vazia_ou_zero_e_sem_revestimento():
    assert not Amostra(acabamento=Acabamento.GI_ZN).tem_camada
    assert not Amostra(acabamento=Acabamento.GI_ZN, camada=Decimal("0")).tem_camada
    assert Amostra(acabamento=Acabamento.GI_ZN, camada=Decimal("100")).tem_camada


def test_valor_negativo_e_recusado():
    with pytest.raises(ValueError, match="negativo"):
        Amostra(acabamento=Acabamento.FF, valores={Propriedade.LE: Decimal("-1")})
    with pytest.raises(ValueError, match="negativ"):
        Amostra(acabamento=Acabamento.FF, espessura_nominal=Decimal("-0.5"))

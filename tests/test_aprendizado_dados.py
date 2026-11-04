"""ML, etapa 2: histórico → exemplos com números (dados fictícios)."""

import math

import pytest

from classificador.aprendizado.dados import CAMPOS, exemplos, grau, numeros
from classificador.historico.repositorio import NovaClassificacao, RepositorioHistorico


@pytest.fixture
def repo(tmp_path):
    r = RepositorioHistorico.abrir(tmp_path, quem=("ana", "PC-01"))
    yield r
    r.fechar()


def salvar(repo, volume, resultado, valores, acabamento="GI ZN"):
    return repo.salvar(NovaClassificacao(
        volume=volume, acabamento=acabamento, valores=valores, resultado=resultado, norma=None,
    ))


@pytest.mark.parametrize(("resultado", "esperado"), [
    ("ZEE G2 - Z275", "ZEE G2"),
    ("ZE - ZF100", "ZE"),
    ("ZAR-230 - Z275", "ZAR-230"),
    ("EEP G3 EG 50/50", "EEP G3 EG"),
    ("1006/08 EG _/_", "1006/08 EG"),
    ("1006/08", "1006/08"),
    ("EEP G2", "EEP G2"),
    (None, None),
    ("", None),
])
def test_grau_tira_so_a_camada(resultado, esperado):
    assert grau(resultado) == esperado


def test_numeros_na_ordem_dos_campos_e_vazio_vira_nan():
    n = numeros({"LE": "200", "Mn": "0,15 %", "C": "", "espessura_nominal": "0.8", "S": "abc"})
    assert len(n) == len(CAMPOS)
    assert n[CAMPOS.index("LE")] == 200.0
    assert n[CAMPOS.index("Mn")] == 0.15
    assert n[CAMPOS.index("espessura_nominal")] == 0.8
    assert math.isnan(n[CAMPOS.index("C")])  # vazio
    assert math.isnan(n[CAMPOS.index("S")])  # ilegível
    assert math.isnan(n[CAMPOS.index("Ni")])  # não veio


def test_exemplo_sem_divergencia_aprende_com_o_resultado_do_programa(repo):
    salvar(repo, "V-1", "ZEE G2 - Z275", {"LE": "180"})
    (e,) = exemplos(repo)
    assert (e.volume, e.acabamento, e.grau_programa) == ("V-1", "GI ZN", "ZEE G2")
    assert not e.divergente
    assert e.grau_certo == "ZEE G2"


def test_exemplo_com_divergencia_aprende_com_a_correta(repo):
    id_ = salvar(repo, "V-2", "ZEE G2 - Z275", {"LE": "180"})
    repo.registrar_divergencia(id_, "ZEE G1 - Z275", "LE fora do certificado")
    (e,) = exemplos(repo)
    assert e.divergente
    assert e.grau_programa == "ZEE G2"  # o que o programa deu continua guardado
    assert e.grau_certo == "ZEE G1"
    assert e.motivo == "LE fora do certificado"


def test_divergencia_resolvida_continua_ensinando_e_vale_a_mais_recente(repo):
    id_ = salvar(repo, "V-3", "ZE - Z100", {})
    primeira = repo.registrar_divergencia(id_, "ZEE G1", "motivo antigo")
    repo.resolver_divergencia(primeira)
    repo.registrar_divergencia(id_, "ZEE G2", "motivo novo")
    (e,) = exemplos(repo)
    assert (e.correta, e.motivo) == ("ZEE G2", "motivo novo")


def test_registro_na_lixeira_nao_ensina(repo):
    id_ = salvar(repo, "V-4", "ZE - Z100", {})
    salvar(repo, "V-5", "ZE - Z100", {})
    repo.excluir(id_)
    assert [e.volume for e in exemplos(repo)] == ["V-5"]

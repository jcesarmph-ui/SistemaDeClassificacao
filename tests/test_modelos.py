"""Testes dos modelos do domínio: cada modelo recusa dados inválidos ao ser criado."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from classificador.dominio.modelos import FaixaEspessura, Limite, Norma
from classificador.dominio.propriedades import Propriedade


def norma_valida(**alteracoes):
    """Dicionário de uma norma fictícia válida; `alteracoes` substitui campos de topo."""
    dados = {
        "codigo": "NBR 0000-1",
        "titulo": "Norma fictícia para testes",
        "graus": [
            {"sigla": "AAA", "nome_na_norma": "AAA", "limites": {"C": {"max": "0.10"}}},
            {
                "sigla": "BBB",
                "nome_na_norma": "BBB grau 1",
                "limites": {"C": {"max": "0.06"}, "LE": {"min": 140, "max": 220}},
                "somas": [{"elementos": ["Ti", "Nb"], "max": "0.20"}],
                "avisos": ["BBB não substitui AAA sem autorização."],
            },
        ],
        "ajustes": [
            {
                "nota": "nota a",
                "quando": {"max": "0.50", "max_inclusivo": False},
                "efeito": {"LE": {"max": 40}, "AL_LO50": {"min": -4}},
            }
        ],
        "tabela_embutimento": {
            "linhas": [
                {"espessura": "0.30", "minimos": {"BBB": "9.4"}},
                {"espessura": "0.35", "minimos": {"BBB": "9.5"}},
            ]
        },
    }
    dados.update(alteracoes)
    return dados


# --- Limite ---------------------------------------------------------------

def test_limite_precisa_de_min_ou_max():
    with pytest.raises(ValidationError, match="pelo menos"):
        Limite()


def test_limite_min_maior_que_max_e_recusado():
    with pytest.raises(ValidationError, match="maior que o máximo"):
        Limite(min=300, max=200)


def test_limite_recusa_campo_com_nome_errado():
    with pytest.raises(ValidationError):
        Limite(maximo=200)


# --- Faixa de espessura (condição das notas de rodapé) -----------------------

def test_faixa_com_limites_inclusivos_e_exclusivos():
    faixa = FaixaEspessura(min="0.50", max="0.70")  # 0,50 ≤ e ≤ 0,70
    assert faixa.contem(Decimal("0.50"))
    assert faixa.contem(Decimal("0.70"))
    assert not faixa.contem(Decimal("0.71"))

    menor = FaixaEspessura(max="0.50", max_inclusivo=False)  # e < 0,50
    assert menor.contem(Decimal("0.49"))
    assert not menor.contem(Decimal("0.50"))


# --- Norma ------------------------------------------------------------------

def test_norma_valida_preserva_ordem_e_valores_decimais():
    norma = Norma.model_validate(norma_valida())
    assert [g.sigla for g in norma.graus] == ["AAA", "BBB"]  # último = mais nobre
    bbb = norma.grau("BBB")
    assert bbb.limites[Propriedade.C].max == Decimal("0.06")
    assert bbb.somas[0].elementos == [Propriedade.Ti, Propriedade.Nb]


def test_propriedade_desconhecida_e_recusada():
    graus = [{"sigla": "AAA", "nome_na_norma": "AAA", "limites": {"Mb": {"max": "0.1"}}}]
    with pytest.raises(ValidationError):
        Norma.model_validate(norma_valida(graus=graus, ajustes=[], tabela_embutimento=None))


def test_sigla_repetida_e_recusada():
    graus = [
        {"sigla": "AAA", "nome_na_norma": "AAA", "limites": {}},
        {"sigla": "AAA", "nome_na_norma": "AAA", "limites": {}},
    ]
    with pytest.raises(ValidationError, match="repetida"):
        Norma.model_validate(norma_valida(graus=graus, ajustes=[], tabela_embutimento=None))


def test_ajuste_para_grau_inexistente_e_recusado():
    ajustes = [{"nota": "x", "graus": ["ZZZ"], "quando": {"max": 2}, "efeito": {"LE": {"max": 20}}}]
    with pytest.raises(ValidationError, match="ZZZ"):
        Norma.model_validate(norma_valida(ajustes=ajustes))


def test_tabela_embutimento_fora_de_ordem_e_recusada():
    tabela = {
        "linhas": [
            {"espessura": "0.35", "minimos": {"BBB": "9.5"}},
            {"espessura": "0.30", "minimos": {"BBB": "9.4"}},
        ]
    }
    with pytest.raises(ValidationError, match="crescente"):
        Norma.model_validate(norma_valida(tabela_embutimento=tabela))


def test_tabela_embutimento_com_grau_inexistente_e_recusada():
    tabela = {"linhas": [{"espessura": "0.30", "minimos": {"ZZZ": "9.4"}}]}
    with pytest.raises(ValidationError, match="ZZZ"):
        Norma.model_validate(norma_valida(tabela_embutimento=tabela))


def test_ajuste_precisa_de_condicao_e_de_efeito():
    def com_ajustes(ajustes):
        graus = [{"sigla": "AAA", "nome_na_norma": "AAA", "limites": {}}]
        return norma_valida(graus=graus, ajustes=ajustes, tabela_embutimento=None)

    with pytest.raises(ValidationError, match="espessura.*acabamento"):
        Norma.model_validate(com_ajustes([{"nota": "x", "efeito": {"LE": {"max": 20}}}]))
    with pytest.raises(ValidationError, match="efeito.*remover"):
        Norma.model_validate(com_ajustes([{"nota": "x", "quando": {"max": 1}}]))

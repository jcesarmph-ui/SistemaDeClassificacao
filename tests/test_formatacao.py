"""Testes da descrição de notas de rodapé em texto."""

from classificador.dominio.formatacao import descrever_ajuste
from classificador.dominio.modelos import Ajuste


def test_nota_por_espessura():
    ajuste = Ajuste.model_validate(
        {"nota": "d", "quando": {"max": "0.50", "max_inclusivo": False},
         "efeito": {"LE": {"max": 40}, "AL_LO50": {"min": -4}}}
    )
    assert descrever_ajuste(ajuste) == "e < 0,50 mm: LE máx +40, alongamento Lo50 mín -4"


def test_nota_por_acabamento():
    ajuste = Ajuste.model_validate(
        {"nota": "c", "acabamentos": ["GA ZF"], "efeito": {"AL_LO50": {"min": -2}}}
    )
    assert descrever_ajuste(ajuste) == "acabamento GA ZF: alongamento Lo50 mín -2"


def test_nota_que_remove_exigencia():
    ajuste = Ajuste.model_validate(
        {"nota": "col", "quando": {"min": "3.0"}, "efeito": {"AL_LO50": {"min": 2}},
         "remover": ["AL_LO80"]}
    )
    assert descrever_ajuste(ajuste) == (
        "e ≥ 3,0 mm: alongamento Lo50 mín +2; sem exigência de alongamento Lo80"
    )

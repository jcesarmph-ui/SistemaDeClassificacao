"""Testes da saída formatada: RESULTADO com camada, norma e avisos."""

from decimal import Decimal

from classificador.dominio.amostra import Acabamento, Amostra
from classificador.dominio.modelos import FolhaClassificacoes, Norma
from classificador.dominio.propriedades import Propriedade as P
from classificador.motor.saida import formatar
from classificador.motor.sequencia import classificar

D = Decimal


def _grau(sigla, le_max, avisos=()):
    limites = {"LE": {"min": 100, "max": le_max}, "AL_LO50": {"min": 30}, "AL_LO80": {"min": 28}}
    return {"sigla": sigla, "nome_na_norma": sigla, "limites": limites, "avisos": list(avisos)}


NOTA_X = {"nota": "Tabela 2, nota x", "quando": {"max": "0.50"}, "efeito": {"LE": {"max": 20}}}
FRIO = Norma.model_validate(
    {
        "codigo": "NBR 0000-1:2026",
        "titulo": "Frio",
        "graus": [
            _grau("AAA", 300),
            _grau("BBB", 250),
            _grau("CCC", 200, ["CCC exige autorização."]),
        ],
        "ajustes": [NOTA_X],
    }
)
ZINC_1 = Norma.model_validate(
    {
        "codigo": "NBR 0000-2:2026",
        "titulo": "Zincado",
        "graus": [_grau("XE", 300), _grau("XEE", 220)],
    }
)
ZINC_2 = Norma.model_validate(
    {
        "codigo": "NBR 0000-3:2026",
        "titulo": "Estrutural",
        "graus": [
            {"sigla": "XAR-1", "nome_na_norma": "XAR-1", "limites": {"LE": {"min": 250}}},
            {"sigla": "XAR-2", "nome_na_norma": "XAR-2", "limites": {"LE": {"min": 350}}},
        ],
    }
)
NORMAS = {n.codigo: n for n in (FRIO, ZINC_1, ZINC_2)}
ZINCADO = {
    "tabelas": [{"norma": "NBR 0000-2:2026"}, {"norma": "NBR 0000-3:2026"}],
    "se_nenhum": {"aviso": "Material mais duro que o último XAR"},
}
FOLHA = FolhaClassificacoes.model_validate(
    {
        "acabamentos": {
            "FF": {
                "tabelas": [{"norma": "NBR 0000-1:2026"}],
                "se_nenhum": {"resultado": "1006/08"},
            },
            "EG": {
                "tabelas": [{"norma": "NBR 0000-1:2026", "graus": ["AAA", "BBB"]}],
                "se_nenhum": {"resultado": "1006/08"},
            },
            "GI ZN": ZINCADO,
            "GA ZF": ZINCADO,
        }
    }
)

OK = {P.LE: D("180"), P.AL_LO50: D("40"), P.AL_LO80: D("38")}


def saida(acabamento, valores=OK, camada=None, espessura="0.80"):
    amostra = Amostra(
        acabamento,
        valores,
        D(espessura) if espessura else None,
        D(camada) if camada is not None else None,
    )
    return formatar(classificar(amostra, FOLHA, NORMAS), amostra)


# --- RESULTADO ------------------------------------------------------------------

def test_ff_so_a_sigla_e_ignora_camada():
    assert saida(Acabamento.FF).resultado == "CCC"
    assert saida(Acabamento.FF, camada="100").resultado == "CCC"


def test_gi_e_ga_com_camada():
    assert saida(Acabamento.GI_ZN, camada="100").resultado == "XEE - Z100"
    assert saida(Acabamento.GA_ZF, camada="100").resultado == "XEE - ZF100"


def test_gi_sem_camada_ou_camada_zero():
    assert saida(Acabamento.GI_ZN).resultado == "XEE"
    assert saida(Acabamento.GI_ZN, camada="0").resultado == "XEE"


def test_camada_sai_como_digitada_sem_zeros_a_toa():
    assert saida(Acabamento.GI_ZN, camada="275.0").resultado == "XEE - Z275"
    assert saida(Acabamento.GI_ZN, camada="113").resultado == "XEE - Z113"


def test_eg_camada_por_face():
    assert saida(Acabamento.EG, camada="50").resultado == "BBB EG 50/50"
    assert saida(Acabamento.EG, camada="7.5").resultado == "BBB EG 7,5/7,5"
    assert saida(Acabamento.EG).resultado == "BBB EG"


def test_segunda_tabela_com_camada():
    resultado = saida(Acabamento.GI_ZN, {P.LE: D("304")}, camada="100")
    assert resultado.resultado == "XAR-1 - Z100"
    assert resultado.norma == "De acordo com a norma NBR 0000-3:2026"


def test_nenhum_grau_resultado_padrao():
    ruim = OK | {P.LE: D("320")}
    assert saida(Acabamento.FF, ruim).resultado == "1006/08"
    assert saida(Acabamento.EG, ruim, camada="50").resultado == "1006/08 EG 50/50"


def test_gi_sem_nenhum_grau_resultado_vazio_e_aviso_em_destaque():
    resultado = saida(Acabamento.GI_ZN, {P.LE: D("50")}, camada="100")
    assert resultado.resultado is None
    assert resultado.norma is None
    assert resultado.avisos[0] == "Material mais duro que o último XAR"


# --- Norma e avisos -----------------------------------------------------------------

def test_norma_do_resultado():
    assert saida(Acabamento.FF).norma == "De acordo com a norma NBR 0000-1:2026"


def test_nenhum_grau_avisa_e_traz_quase_passou():
    resultado = saida(Acabamento.FF, OK | {P.LE: D("320")})
    assert resultado.norma is None
    assert resultado.avisos == [
        "Nenhum grau da NBR 0000-1:2026 atendido",
        "Seria CCC, mas o LE (320 > 200 máx) rebaixou",
    ]


def test_quase_passou():
    resultado = saida(Acabamento.FF, OK | {P.LE: D("210")})
    assert resultado.resultado == "BBB"
    assert "Seria CCC, mas o LE (210 > 200 máx) rebaixou" in resultado.avisos


def test_eg_rebaixado_por_nao_existir_o_grau():
    resultado = saida(Acabamento.EG, camada="50")
    assert "Atende CCC, que não existe para EG; resultado no mais nobre disponível (BBB)" in (
        resultado.avisos
    )


def test_valores_faltando_e_nao_avaliados():
    resultado = saida(Acabamento.FF, {P.LE: D("180"), P.AL_LO50: D("40")})
    assert "Não avaliado (outro campo preenchido / vazio): alongamento Lo80" in resultado.avisos

    resultado = saida(Acabamento.FF, {P.LE: D("180")})
    assert "Valores não informados (considerados zero): alongamento Lo50, alongamento Lo80" in (
        resultado.avisos
    )


def test_espessura_nao_informada_com_notas_na_norma():
    resultado = saida(Acabamento.FF, espessura=None)
    assert (
        "Espessura nominal não informada: notas de rodapé e embutimento não aplicados"
        in resultado.avisos
    )


def test_notas_aplicadas_e_aviso_do_grau():
    resultado = saida(Acabamento.FF, espessura="0.45")
    assert "Limites ajustados pela espessura: Tabela 2, nota x" in resultado.avisos
    assert "CCC exige autorização." in resultado.avisos


def test_correlatas_vazias_ate_a_fase_3():
    assert saida(Acabamento.FF).correlatas == []

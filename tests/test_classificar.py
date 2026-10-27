"""Testes da classificação numa norma: grau mais nobre, "quase passou" e valores faltando."""

from decimal import Decimal

from classificador.dominio.amostra import Acabamento, Amostra
from classificador.dominio.modelos import Norma
from classificador.dominio.propriedades import Propriedade as P
from classificador.motor.classificar import classificar_na_norma

D = Decimal

# Norma fictícia: AAA < BBB < CCC (cada grau mais exigente que o anterior)
NORMA = Norma.model_validate(
    {
        "codigo": "NBR 0000-3",
        "titulo": "Três graus",
        "graus": [
            {
                "sigla": "AAA",
                "nome_na_norma": "AAA",
                "limites": {"Mn": {"max": "0.60"}, "LE": {"min": 140, "max": 300}},
            },
            {
                "sigla": "BBB",
                "nome_na_norma": "BBB",
                "limites": {
                    "Mn": {"max": "0.45"},
                    "Al": {"min": "0.010"},
                    "LE": {"min": 140, "max": 260},
                },
            },
            {
                "sigla": "CCC",
                "nome_na_norma": "CCC",
                "limites": {
                    "Mn": {"max": "0.35"},
                    "Al": {"min": "0.010"},
                    "Ti": {"max": "0.200"},
                    "LE": {"min": 140, "max": 200},
                    "AL_LO50": {"min": 40},
                },
            },
        ],
        "ajustes": [
            {"nota": "nota x", "quando": {"max": "0.50"}, "efeito": {"LE": {"max": 20}}},
        ],
    }
)

BASE = {P.Mn: D("0.30"), P.Al: D("0.030"), P.Ti: D("0.01"), P.LE: D("180"), P.AL_LO50: D("42")}


def classificar(valores, espessura="0.80"):
    amostra = Amostra(Acabamento.FF, valores, D(espessura) if espessura else None)
    return classificar_na_norma(NORMA, amostra)


def test_atende_todos_resultado_e_o_mais_nobre():
    resultado = classificar(BASE)
    assert resultado.grau.sigla == "CCC"
    assert resultado.quase_passou is None
    assert resultado.faltando == []


def test_resultado_e_o_mais_nobre_que_atende():
    resultado = classificar(BASE | {P.LE: D("250"), P.AL_LO50: D("30")})
    assert resultado.grau.sigla == "BBB"
    assert [a.grau.sigla for a in resultado.avaliacoes] == ["AAA", "BBB", "CCC"]


def test_quase_passou_falhou_por_uma_unica_variavel():
    resultado = classificar(BASE | {P.LE: D("210")})  # CCC falha só no LE
    assert resultado.grau.sigla == "BBB"
    assert resultado.quase_passou.grau.sigla == "CCC"
    assert resultado.quase_passou.texto == "Seria CCC, mas o LE (210 > 200 máx) rebaixou"


def test_duas_falhas_nao_e_quase_passou():
    resultado = classificar(BASE | {P.LE: D("210"), P.AL_LO50: D("30")})
    assert resultado.grau.sigla == "BBB"
    assert resultado.quase_passou is None


def test_quase_passou_avisa_so_o_mais_nobre():
    # Mn 0,50: BBB (máx 0,45) e CCC (máx 0,35) falham só no Mn → avisa só CCC, o mais nobre
    resultado = classificar(BASE | {P.Mn: D("0.50")})
    assert resultado.grau.sigla == "AAA"
    assert resultado.quase_passou.grau.sigla == "CCC"


def test_nenhum_grau_atende_tambem_avisa_quase_passou():
    resultado = classificar(BASE | {P.Mn: D("0.70"), P.LE: D("150")})
    assert resultado.grau is None
    assert resultado.quase_passou.grau.sigla == "CCC"
    assert resultado.quase_passou.texto == "Seria CCC, mas o Mn (0,70 > 0,35 máx) rebaixou"


def test_faltando_inclui_vazio_que_barrou_grau_mais_nobre():
    resultado = classificar(BASE | {P.Al: None})  # Al vazio = 0 barra BBB e CCC
    assert resultado.grau.sigla == "AAA"
    assert resultado.faltando == [P.Al]


def test_faltando_ignora_vazio_que_nao_atrapalhou():
    # Ti vazio = 0 passa no Ti máx de CCC; AAA (resultado) não exige Ti
    resultado = classificar(BASE | {P.Ti: None, P.LE: D("280")})
    assert resultado.grau.sigla == "AAA"
    assert resultado.faltando == []


def test_faltando_inclui_vazio_exigido_pelo_grau_do_resultado():
    resultado = classificar(BASE | {P.Ti: None})  # CCC exige Ti (vazio passa, mas falta)
    assert resultado.grau.sigla == "CCC"
    assert resultado.faltando == [P.Ti]


def test_notas_aplicadas_pela_espessura():
    assert classificar(BASE, "0.45").notas_aplicadas == ["nota x"]
    assert classificar(BASE, "0.80").notas_aplicadas == []
    # LE 210 passa em CCC com a nota x (máx 200 + 20)
    assert classificar(BASE | {P.LE: D("210")}, "0.45").grau.sigla == "CCC"


def test_sem_espessura_usa_limites_da_tabela():
    resultado = classificar(BASE | {P.LE: D("210")}, espessura=None)
    assert resultado.grau.sigla == "BBB"

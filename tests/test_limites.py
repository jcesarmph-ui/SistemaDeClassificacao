"""Testes dos limites efetivos: notas de rodapé por espessura e linha do embutimento."""

from decimal import Decimal
from pathlib import Path

import pytest

from classificador.dominio.amostra import Acabamento
from classificador.dominio.modelos import Norma
from classificador.dominio.propriedades import Propriedade
from classificador.motor.limites import limites_efetivos
from classificador.normas.carregador import carregar_norma

NORMA_FICTICIA = Path(__file__).parent / "dados" / "norma-ficticia.yaml"
D = Decimal


@pytest.fixture(scope="module")
def norma():
    return carregar_norma(NORMA_FICTICIA)


def lim(efetivos, prop):
    limite = efetivos.limites[prop]
    return limite.min, limite.max


# --- Notas de rodapé ----------------------------------------------------------

def test_sem_espessura_usa_limites_da_tabela(norma):
    efetivos = limites_efetivos(norma, norma.grau("BBB G1"), None)
    assert lim(efetivos, Propriedade.LE) == (120, 160)
    assert efetivos.notas_aplicadas == []
    assert Propriedade.EMBUTIMENTO not in efetivos.limites


def test_espessura_fora_da_nota_nao_muda_nada(norma):
    efetivos = limites_efetivos(norma, norma.grau("BBB G1"), D("0.80"))
    assert lim(efetivos, Propriedade.LE) == (120, 160)
    assert lim(efetivos, Propriedade.AL_LO50) == (42, None)


def test_nota_aplicada_soma_ao_maximo_e_reduz_o_minimo(norma):
    efetivos = limites_efetivos(norma, norma.grau("BBB G1"), D("0.45"))
    assert lim(efetivos, Propriedade.LE) == (120, 200)  # máx 160 + 40
    assert lim(efetivos, Propriedade.AL_LO50) == (38, None)  # mín 42 − 4
    assert lim(efetivos, Propriedade.AL_LO80) == (40, None)  # nota não cita Lo80
    assert efetivos.notas_aplicadas == ["Tabela 2, nota a"]


def test_limite_da_nota_exclusivo(norma):
    # nota a vale para e < 0,50: exatamente 0,50 fica de fora
    efetivos = limites_efetivos(norma, norma.grau("AAA"), D("0.50"))
    assert lim(efetivos, Propriedade.LE) == (140, 280)


def test_nota_nao_cria_limite_que_o_grau_nao_tem(norma):
    # AAA não tem AL_LO80; a nota não pode inventar um limite
    efetivos = limites_efetivos(norma, norma.grau("AAA"), D("0.40"))
    assert Propriedade.AL_LO80 not in efetivos.limites
    assert lim(efetivos, Propriedade.AL_LO50) == (26, None)


def norma_com_notas(ajustes):
    return Norma.model_validate(
        {
            "codigo": "NBR 0000-2",
            "titulo": "Notas sobrepostas",
            "graus": [
                {"sigla": "AAA", "nome_na_norma": "AAA", "limites": {"AL_LO50": {"min": 30}}},
                {"sigla": "BBB", "nome_na_norma": "BBB", "limites": {"AL_LO50": {"min": 40}}},
            ],
            "ajustes": ajustes,
        }
    )


def test_notas_sobrepostas_vale_a_maior_variacao_sem_acumular():
    norma = norma_com_notas(
        [
            {"nota": "b", "quando": {"max": "0.70"}, "efeito": {"AL_LO50": {"min": -2}}},
            {"nota": "d", "quando": {"max": "0.50"}, "efeito": {"AL_LO50": {"min": -4}}},
        ]
    )
    efetivos = limites_efetivos(norma, norma.grau("BBB"), D("0.40"))
    assert lim(efetivos, Propriedade.AL_LO50) == (36, None)  # −4, não −6
    assert efetivos.notas_aplicadas == ["d"]


def test_nota_restrita_a_alguns_graus():
    so_bbb = {"nota": "só BBB", "graus": ["BBB"], "quando": {"max": 1}}
    norma = norma_com_notas([so_bbb | {"efeito": {"AL_LO50": {"min": -1}}}])
    aaa = limites_efetivos(norma, norma.grau("AAA"), D("0.5"))
    bbb = limites_efetivos(norma, norma.grau("BBB"), D("0.5"))
    assert lim(aaa, Propriedade.AL_LO50) == (30, None)
    assert lim(bbb, Propriedade.AL_LO50) == (39, None)


# --- Embutimento --------------------------------------------------------------

@pytest.mark.parametrize(
    ("espessura", "minimo"),
    [
        ("0.30", "9.5"),  # linha exata
        ("0.32", "9.5"),  # mais próxima: 0,30
        ("0.325", "9.6"),  # empate entre 0,30 e 0,35 → linha maior
        ("0.34", "9.6"),  # mais próxima: 0,35
        ("0.35", "9.6"),  # última linha
    ],
)
def test_embutimento_linha_mais_proxima(norma, espessura, minimo):
    efetivos = limites_efetivos(norma, norma.grau("BBB G1"), D(espessura))
    assert lim(efetivos, Propriedade.EMBUTIMENTO) == (D(minimo), None)


@pytest.mark.parametrize("espessura", ["0.29", "0.36"])
def test_embutimento_fora_da_faixa_nao_e_avaliado(norma, espessura):
    efetivos = limites_efetivos(norma, norma.grau("BBB G1"), D(espessura))
    assert Propriedade.EMBUTIMENTO not in efetivos.limites


def test_grau_sem_coluna_de_embutimento(norma):
    efetivos = limites_efetivos(norma, norma.grau("AAA"), D("0.30"))
    assert Propriedade.EMBUTIMENTO not in efetivos.limites


# --- Motivos, acabamento e remoção (Fase 3) ---------------------------------------

def test_motivos_diferentes_se_somam():
    norma = norma_com_notas(
        [
            {"nota": "b", "quando": {"max": "0.70", "max_inclusivo": False},
             "efeito": {"AL_LO50": {"min": -2}}},
            {"nota": "c", "motivo": "revestimento", "acabamentos": ["GA ZF"],
             "efeito": {"AL_LO50": {"min": -2}}},
        ]
    )
    ga = limites_efetivos(norma, norma.grau("BBB"), D("0.60"), Acabamento.GA_ZF)
    gi = limites_efetivos(norma, norma.grau("BBB"), D("0.60"), Acabamento.GI_ZN)
    assert lim(ga, Propriedade.AL_LO50) == (36, None)  # 40 − 2 − 2
    assert ga.notas_aplicadas == ["b", "c"]
    assert lim(gi, Propriedade.AL_LO50) == (38, None)  # só a de espessura


def test_nota_por_acabamento_vale_sem_espessura():
    norma = norma_com_notas(
        [{"nota": "c", "motivo": "revestimento", "acabamentos": ["GA ZF"],
          "efeito": {"AL_LO50": {"min": -2}}}]
    )
    efetivos = limites_efetivos(norma, norma.grau("BBB"), None, Acabamento.GA_ZF)
    assert lim(efetivos, Propriedade.AL_LO50) == (38, None)
    # sem acabamento informado, a nota de acabamento não vale
    assert lim(limites_efetivos(norma, norma.grau("BBB"), None), Propriedade.AL_LO50) == (40, None)


def test_nota_que_remove_uma_exigencia():
    norma = Norma.model_validate(
        {
            "codigo": "NBR 0000-4",
            "titulo": "Remoção",
            "graus": [
                {"sigla": "AAA", "nome_na_norma": "AAA",
                 "limites": {"AL_LO50": {"min": 28}, "AL_LO80": {"min": 26}}},
                {"sigla": "BBB", "nome_na_norma": "BBB", "limites": {"AL_LO50": {"min": 30}}},
            ],
            "ajustes": [
                {"nota": "coluna e ≥ 3,0", "quando": {"min": "3.0"},
                 "efeito": {"AL_LO50": {"min": 2}}, "remover": ["AL_LO80"]},
            ],
        }
    )
    grosso = limites_efetivos(norma, norma.grau("AAA"), D("3.0"))
    assert lim(grosso, Propriedade.AL_LO50) == (30, None)
    assert Propriedade.AL_LO80 not in grosso.limites
    assert grosso.notas_aplicadas == ["coluna e ≥ 3,0"]
    fino = limites_efetivos(norma, norma.grau("AAA"), D("2.5"))
    assert lim(fino, Propriedade.AL_LO80) == (26, None)
    # remover algo que o grau não tem não conta como nota aplicada
    assert limites_efetivos(norma, norma.grau("BBB"), D("3.0")).notas_aplicadas == [
        "coluna e ≥ 3,0"
    ]  # aplicada pelo efeito no Lo50

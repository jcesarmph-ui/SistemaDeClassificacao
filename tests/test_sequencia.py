"""Testes da sequência de tabelas por acabamento (folha de classificações)."""

from decimal import Decimal

import pytest

from classificador.dominio.amostra import Acabamento, Amostra
from classificador.dominio.modelos import FolhaClassificacoes, Norma
from classificador.dominio.propriedades import Propriedade as P
from classificador.motor.classificar import classificar_na_norma
from classificador.motor.sequencia import ErroClassificacao, classificar

D = Decimal


def norma(codigo, graus):
    """Norma fictícia: cada grau é (sigla, LE máx); todos exigem LE mín 100."""
    return Norma.model_validate(
        {
            "codigo": codigo,
            "titulo": codigo,
            "graus": [
                {"sigla": s, "nome_na_norma": s, "limites": {"LE": {"min": 100, "max": m}}}
                for s, m in graus
            ],
        }
    )


# Estampagem: quanto mais nobre, menor o LE máx
FRIO = norma("FRIO", [("AAA", 300), ("BBB", 250), ("CCC", 200)])
# Zincado: XC (nunca resultado) sem limite prático; XE/XEE como estampagem
ZINC_1 = norma("ZINC-1", [("XC", 900), ("XE", 300), ("XEE", 220)])
# Estrutural: LE alto é mais nobre — modelado com LE mín crescente
ZINC_2 = Norma.model_validate(
    {
        "codigo": "ZINC-2",
        "titulo": "ZINC-2",
        "graus": [
            {"sigla": "XAR-1", "nome_na_norma": "XAR-1", "limites": {"LE": {"min": 250}}},
            {"sigla": "XAR-2", "nome_na_norma": "XAR-2", "limites": {"LE": {"min": 350}}},
        ],
    }
)
NORMAS = {n.codigo: n for n in (FRIO, ZINC_1, ZINC_2)}

FOLHA = FolhaClassificacoes.model_validate(
    {
        "acabamentos": {
            "FF": {
                "tabelas": [{"norma": "FRIO"}],
                "se_nenhum": {"resultado": "1006/08"},
            },
            "EG": {
                "tabelas": [{"norma": "FRIO", "graus": ["AAA", "BBB"]}],
                "se_nenhum": {"resultado": "1006/08"},
            },
            "GI ZN": {
                "tabelas": [{"norma": "ZINC-1", "graus": ["XE", "XEE"]}, {"norma": "ZINC-2"}],
                "se_nenhum": {"resultado": "XC", "aviso": "Material mais duro que o último XAR"},
            },
        }
    }
)


def classificar_le(acabamento, le):
    return classificar(Amostra(acabamento, {P.LE: D(le)}), FOLHA, NORMAS)


# --- Recorte de graus disponíveis numa norma -------------------------------------

def test_recorte_desce_para_o_mais_nobre_disponivel():
    resultado = classificar_na_norma(FRIO, Amostra(Acabamento.EG, {P.LE: D(180)}), ["AAA", "BBB"])
    assert resultado.grau.sigla == "BBB"
    assert resultado.rebaixado_de.sigla == "CCC"


def test_sem_disponivel_abaixo_nao_ha_resultado():
    amostra = Amostra(Acabamento.GI_ZN, {P.LE: D(800)})  # só XC atende
    resultado = classificar_na_norma(ZINC_1, amostra, ["XE", "XEE"])
    assert resultado.grau is None
    assert resultado.rebaixado_de is None


def test_quase_passou_so_entre_os_disponiveis():
    # EG: AAA atende (LE 260); CCC não está disponível; BBB falha por uma variável
    resultado = classificar_na_norma(FRIO, Amostra(Acabamento.EG, {P.LE: D(260)}), ["AAA", "BBB"])
    assert resultado.grau.sigla == "AAA"
    assert resultado.quase_passou.grau.sigla == "BBB"


def test_grau_disponivel_inexistente_na_norma_e_erro():
    with pytest.raises(ValueError, match="ZZZ"):
        classificar_na_norma(FRIO, Amostra(Acabamento.FF, {P.LE: D(180)}), ["AAA", "ZZZ"])


# --- Sequência por acabamento ------------------------------------------------------

def test_ff_resultado_na_primeira_tabela():
    resultado = classificar_le(Acabamento.FF, 180)
    assert (resultado.norma.codigo, resultado.grau.sigla) == ("FRIO", "CCC")
    assert resultado.resultado_padrao is None


def test_ff_nenhum_grau_vira_1006_08_com_quase_passou():
    resultado = classificar_le(Acabamento.FF, 320)
    assert resultado.grau is None
    assert resultado.resultado_padrao == "1006/08"
    assert resultado.detalhe.quase_passou.grau.sigla == "CCC"  # falhou só no LE


def test_eg_que_atende_o_grau_mais_nobre_sai_no_mais_nobre_do_eg():
    resultado = classificar_le(Acabamento.EG, 180)
    assert resultado.grau.sigla == "BBB"
    assert resultado.detalhe.rebaixado_de.sigla == "CCC"


def test_gi_resultado_na_primeira_tabela():
    resultado = classificar_le(Acabamento.GI_ZN, 280)
    assert (resultado.norma.codigo, resultado.grau.sigla) == ("ZINC-1", "XE")
    assert len(resultado.tentativas) == 1


def test_gi_so_atende_o_grau_que_nunca_e_resultado_vai_para_a_segunda_tabela():
    # LE 304: só XC atende na ZINC-1 → XC não pode sair → ZINC-2 → XAR-1
    resultado = classificar_le(Acabamento.GI_ZN, 304)
    assert (resultado.norma.codigo, resultado.grau.sigla) == ("ZINC-2", "XAR-1")
    assert [t.norma.codigo for t in resultado.tentativas] == ["ZINC-1", "ZINC-2"]
    assert resultado.detalhe.quase_passou.grau.sigla == "XAR-2"  # só da tabela do resultado


def test_gi_nenhuma_tabela_atende_vira_resultado_padrao_com_aviso():
    resultado = classificar(Amostra(Acabamento.GI_ZN, {P.LE: D(50)}), FOLHA, NORMAS)
    assert resultado.grau is None
    assert resultado.resultado_padrao == "XC"
    assert resultado.aviso_sem_grau == "Material mais duro que o último XAR"
    assert resultado.detalhe.norma.codigo == "ZINC-2"


def test_acabamento_fora_da_folha_e_erro():
    with pytest.raises(ErroClassificacao, match="FQ"):
        classificar_le(Acabamento.FQ, 180)


def test_norma_ainda_nao_transcrita_e_erro_claro():
    with pytest.raises(ErroClassificacao, match="ZINC-2.*não foi transcrita"):
        classificar(Amostra(Acabamento.GI_ZN, {P.LE: D(50)}), FOLHA, {"ZINC-1": ZINC_1})

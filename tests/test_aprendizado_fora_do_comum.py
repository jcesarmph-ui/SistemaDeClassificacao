"""ML, etapa 4: aviso de valor fora do comum (dados fictícios)."""

import pytest

from classificador.aprendizado.dados import Exemplo, numeros
from classificador.aprendizado.fora_do_comum import avisos_fora_do_comum, numero_br


def historico(quantos=20, acabamento="GI ZN", grau_programa="ZEE G2", correta=None):
    """`quantos` classificações normais: LE 170–189, C 0,0010–0,0029, espessura 0,80."""
    return [
        Exemplo(i, f"V-{i}", acabamento, grau_programa, correta, "motivo" if correta else None,
                numeros({"LE": str(170 + i), "C": f"0,00{10 + i}", "espessura_nominal": "0,80"}))
        for i in range(quantos)
    ]


def avisos(exemplos, valores, acabamento="GI ZN", resultado="ZEE G2 - Z275"):
    return avisos_fora_do_comum(exemplos, acabamento, resultado, numeros(valores))


@pytest.mark.parametrize(("valor", "texto"), [
    (0.0015, "0,0015"), (185.0, "185"), (0.4, "0,4"), (0.0, "0"),
])
def test_numero_br(valor, texto):
    assert numero_br(valor) == texto


def test_valor_muito_fora_avisa_qual_e_o_normal():
    (aviso,) = avisos(historico(), {"LE": "180", "C": "0,40"})
    assert aviso.startswith("C (0,4) fora do comum para ZEE G2 em GI ZN (costuma ficar entre 0,001")
    assert aviso.endswith("Confira a digitação.")


def test_erro_de_digitacao_no_le_avisa_com_o_nome_do_valor():
    (aviso,) = avisos(historico(), {"LE": "1800"})
    assert aviso.startswith("LE (1800) fora do comum")


def test_valor_so_incomum_nao_avisa():
    # LE normal 170–189: mediana 179,5 e faixa central 10 (mínimo = meia margem) → muito fora só
    # acima de 179,5 + 4 × 10 = 219,5. 210 é incomum, mas não "muito fora".
    assert avisos(historico(), {"LE": "210", "C": "0,0035"}) == []
    assert avisos(historico(), {"LE": "219,5"}) == []  # no limite: não avisa
    assert len(avisos(historico(), {"LE": "220"})) == 1


def test_menos_de_20_no_grupo_nao_avisa():
    assert avisos(historico(19), {"C": "0,40"}) == []


def test_grupo_e_mesmo_acabamento_e_mesmo_grau_sem_camada():
    assert avisos(historico(), {"C": "0,40"}, acabamento="GA ZF") == []
    assert avisos(historico(), {"C": "0,40"}, resultado="ZEE G3 - Z275") == []
    assert len(avisos(historico(), {"C": "0,40"}, resultado="ZEE G2 - Z100")) == 1


def test_divergencia_entra_no_grupo_do_grau_certo():
    corrigidos = historico(grau_programa="ZE", correta="ZEE G2 - Z275")
    assert len(avisos(corrigidos, {"C": "0,40"})) == 1  # aprendeu como ZEE G2
    assert avisos(corrigidos, {"C": "0,40"}, resultado="ZE - Z275") == []


def test_vazio_e_espessura_nao_sao_avaliados():
    assert avisos(historico(), {"C": "", "espessura_nominal": "3,00"}) == []


def test_faixa_minima_evita_alarme_quando_tudo_salvo_e_igual():
    iguais = [Exemplo(i, "V", "GI ZN", "ZEE G2", None, None, numeros({"C": "0,002"}))
              for i in range(20)]
    assert avisos(iguais, {"C": "0,003"}) == []  # faixa mínima = meia margem (0,0025)
    assert len(avisos(iguais, {"C": "0,02"})) == 1


def test_sem_resultado_nao_avisa():
    assert avisos(historico(), {"C": "0,40"}, resultado=None) == []

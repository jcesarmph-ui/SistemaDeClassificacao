"""ML, etapa 3: aviso por divergência em caso parecido (dados fictícios)."""

from classificador.aprendizado.dados import CAMPOS, Exemplo, numeros
from classificador.aprendizado.semelhanca import MARGENS, Margem, caso_parecido

BASE = {"LE": "180", "LR": "310", "AL_LO50": "40", "C": "0,002", "espessura_nominal": "0,80"}


def exemplo(valores=BASE, volume="V-2", acabamento="GI ZN", grau_programa="ZEE G2",
            correta="ZEE G1 - Z275", motivo="LE fora do certificado", id_=1):
    return Exemplo(id_, volume, acabamento, grau_programa, correta, motivo, numeros(valores))


def procurar(exemplos, valores, acabamento="GI ZN", resultado="ZEE G2 - Z100"):
    return caso_parecido(exemplos, acabamento, resultado, numeros(valores))


def test_todo_campo_tem_margem():
    assert set(MARGENS) == set(CAMPOS)


def test_margem_quimica_usa_o_maior_entre_25_por_cento_e_o_piso():
    m = Margem(relativa=0.25, piso=0.005)
    assert m.para(0.002) == 0.005  # piso
    assert m.para(0.40) == 0.10  # 25 %


def test_exemplo_do_usuario_avisa_com_volume_correta_e_motivo():
    agora = {"LE": "185", "LR": "300", "AL_LO50": "39", "C": "0,0025", "espessura_nominal": "0,80"}
    achado = procurar([exemplo()], agora)
    assert achado is not None
    assert achado.comparados == 5
    assert achado.aviso == ("Em um caso parecido (volume V-2), a classificação correta foi "
                            "ZEE G1 - Z275. Motivo: LE fora do certificado. Confira.")


def test_um_valor_fora_da_margem_basta_para_nao_ser_parecido():
    assert procurar([exemplo()], {**BASE, "LE": "201"}) is None  # 21 MPa > 20
    assert procurar([exemplo()], {**BASE, "LE": "200"}) is not None  # no limite = próximo


def test_precisa_mesmo_acabamento_e_mesmo_grau_camada_nao_conta():
    assert procurar([exemplo()], BASE, acabamento="GA ZF") is None
    assert procurar([exemplo()], BASE, resultado="ZEE G3 - Z275") is None
    assert procurar([exemplo()], BASE, resultado="ZEE G2 - Z275") is not None


def test_caso_sem_divergencia_nunca_avisa():
    assert procurar([exemplo(correta=None, motivo=None)], BASE) is None


def test_vazio_em_qualquer_lado_e_ignorado_mas_precisa_de_3_comparados():
    so_dois = exemplo(valores={"LE": "180", "LR": "310"})
    assert procurar([so_dois], BASE) is None  # só LE e LR em comum
    tres = exemplo(valores={"LE": "180", "LR": "310", "C": "0,002", "Mn": "9"})
    assert procurar([tres], BASE).comparados == 3  # Mn vazio agora: não conta
    assert procurar([exemplo()], {"LE": "180", "LR": "310"}) is None  # agora só 2 preenchidos


def test_mostra_so_o_mais_proximo():
    longe = exemplo(valores={**BASE, "LE": "198"}, volume="LONGE", id_=1)
    perto = exemplo(valores={**BASE, "LE": "182"}, volume="PERTO", id_=2)
    assert procurar([longe, perto], BASE).exemplo.volume == "PERTO"


def test_sem_casos_com_divergencia_nao_avisa():
    assert procurar([], BASE) is None

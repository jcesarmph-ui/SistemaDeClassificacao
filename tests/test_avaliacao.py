"""Testes da avaliação de um grau: falhas, valores vazios e campos não avaliados."""

from decimal import Decimal

from classificador.dominio.amostra import Acabamento, Amostra
from classificador.dominio.modelos import Grau, Limite
from classificador.dominio.propriedades import Propriedade as P
from classificador.motor.avaliacao import avaliar_grau
from classificador.motor.limites import LimitesEfetivos

D = Decimal

GRAU = Grau(
    sigla="BBB",
    nome_na_norma="BBB",
    limites={
        P.C: Limite(max=D("0.10")),
        P.Al: Limite(min=D("0.010")),
        P.LE: Limite(min=140, max=300),
        P.AL_LO50: Limite(min=34),
        P.AL_LO80: Limite(min=32),
    },
    somas=[{"elementos": ["Ti", "Nb"], "max": D("0.20")}],
)


def avaliar(valores, extras=None):
    limites = dict(GRAU.limites) | (extras or {})
    amostra = Amostra(acabamento=Acabamento.FF, valores=valores)
    return avaliar_grau(GRAU, LimitesEfetivos(limites, []), amostra)


VALORES_OK = {
    P.C: D("0.05"),
    P.Al: D("0.030"),
    P.LE: D("200"),
    P.AL_LO50: D("40"),
    P.AL_LO80: D("38"),
    P.Ti: D("0.05"),
    P.Nb: D("0.01"),
}


def test_atende_quando_tudo_dentro_dos_limites():
    resultado = avaliar(VALORES_OK)
    assert resultado.atende
    assert resultado.falhas == []
    assert resultado.faltando == []


def test_falha_traz_valor_limite_e_texto():
    resultado = avaliar(VALORES_OK | {P.LE: D("304")})
    assert not resultado.atende
    [falha] = resultado.falhas
    assert falha.variavel == "LE"
    assert (falha.valor, falha.limite, falha.lado) == (D("304"), 300, "max")
    assert falha.texto == "LE (304 > 300 máx)"


def test_comparacao_exata_sem_arredondar():
    resultado = avaliar(VALORES_OK | {P.C: D("0.1001")})
    assert [f.texto for f in resultado.falhas] == ["C (0,1001 > 0,10 máx)"]


def test_valor_igual_ao_limite_atende():
    assert avaliar(VALORES_OK | {P.LE: D("300"), P.AL_LO50: D("34")}).atende


def test_vazio_vale_zero_e_entra_em_faltando():
    valores = VALORES_OK | {P.Al: None, P.C: None}
    resultado = avaliar(valores)
    # C vazio = 0 passa no máximo; Al vazio = 0 reprova no mínimo
    assert [f.texto for f in resultado.falhas] == ["Al (vazio < 0,010 mín)"]
    assert resultado.falhas[0].vazio
    assert resultado.faltando == [P.C, P.Al]


def test_campo_que_a_norma_nao_exige_nao_entra_em_faltando():
    resultado = avaliar(VALORES_OK)  # Ni, Mo, Cr... vazios
    assert resultado.faltando == []


def test_soma_de_elementos():
    resultado = avaliar(VALORES_OK | {P.Ti: D("0.15"), P.Nb: D("0.06")})
    assert [f.texto for f in resultado.falhas] == ["Ti + Nb (0,21 > 0,20 máx)"]


def test_elemento_da_soma_vazio_vale_zero_e_entra_em_faltando():
    resultado = avaliar(VALORES_OK | {P.Nb: None})
    assert resultado.atende
    assert resultado.faltando == [P.Nb]


def test_embutimento_vazio_nao_e_avaliado():
    resultado = avaliar(VALORES_OK, {P.EMBUTIMENTO: Limite(min=D("9.5"))})
    assert resultado.atende
    assert resultado.nao_avaliados == [P.EMBUTIMENTO]
    assert resultado.faltando == []


def test_embutimento_preenchido_e_avaliado():
    limite_embutimento = {P.EMBUTIMENTO: Limite(min=D("9.5"))}
    resultado = avaliar(VALORES_OK | {P.EMBUTIMENTO: D("9.4")}, limite_embutimento)
    assert [f.texto for f in resultado.falhas] == ["embutimento (9,4 < 9,5 mín)"]


def test_so_lo50_preenchido_lo80_nao_e_avaliado():
    resultado = avaliar(VALORES_OK | {P.AL_LO80: None})
    assert resultado.atende
    assert resultado.nao_avaliados == [P.AL_LO80]
    assert resultado.faltando == []


def test_so_lo80_preenchido_lo50_nao_e_avaliado():
    resultado = avaliar(VALORES_OK | {P.AL_LO50: None, P.AL_LO80: D("30")})
    assert [f.variavel for f in resultado.falhas] == ["alongamento Lo80"]
    assert resultado.nao_avaliados == [P.AL_LO50]


def test_lo50_e_lo80_vazios_valem_zero_e_contam_separado():
    resultado = avaliar(VALORES_OK | {P.AL_LO50: None, P.AL_LO80: None})
    assert [f.variavel for f in resultado.falhas] == ["alongamento Lo50", "alongamento Lo80"]
    assert resultado.faltando == [P.AL_LO50, P.AL_LO80]

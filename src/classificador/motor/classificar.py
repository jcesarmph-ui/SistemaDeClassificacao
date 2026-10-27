"""Classifica uma amostra numa norma: grau mais nobre atendido, "quase passou" e valores faltando.

Avalia todos os graus da norma. `disponiveis` (da folha de classificações) recorta os graus que
podem ser resultado: se o melhor atendido não está disponível, desce para o mais nobre disponível
abaixo dele (EG: EEP G4 → EEP G3); se não há nenhum abaixo, a norma não dá resultado (ZC).
"""

from dataclasses import dataclass

from classificador.dominio.amostra import Amostra
from classificador.dominio.modelos import Grau, Norma
from classificador.dominio.propriedades import Propriedade
from classificador.motor.avaliacao import Avaliacao, Falha, avaliar_grau
from classificador.motor.limites import limites_efetivos


@dataclass(frozen=True)
class QuasePassou:
    grau: Grau
    falha: Falha

    @property
    def texto(self) -> str:
        return f"Seria {self.grau.sigla}, mas o {self.falha.texto} rebaixou"


@dataclass(frozen=True)
class ResultadoNorma:
    norma: Norma
    grau: Grau | None  # None = nenhum grau atende
    avaliacoes: list[Avaliacao]  # na ordem da norma (menos → mais nobre)
    quase_passou: QuasePassou | None
    faltando: list[Propriedade]
    notas_aplicadas: list[str]
    rebaixado_de: Grau | None = None  # grau atendido que não está disponível (EG: EEP G4)


def classificar_na_norma(
    norma: Norma, amostra: Amostra, disponiveis: list[str] | None = None
) -> ResultadoNorma:
    siglas = [g.sigla for g in norma.graus]
    if disponiveis is None:
        disponiveis = siglas
    inexistentes = [s for s in disponiveis if s not in siglas]
    if inexistentes:
        raise ValueError(f"grau(s) {', '.join(inexistentes)} não existe(m) na {norma.codigo}")

    avaliacoes = []
    notas: list[str] = []
    for grau in norma.graus:
        efetivos = limites_efetivos(norma, grau, amostra.espessura_nominal)
        avaliacoes.append(avaliar_grau(grau, efetivos, amostra))
        notas += [n for n in efetivos.notas_aplicadas if n not in notas]

    atendidos = [i for i, a in enumerate(avaliacoes) if a.atende]
    melhor = atendidos[-1] if atendidos else -1
    # Mais nobre disponível até o melhor atendido (-1 = nenhum)
    posicao = max((i for i in range(melhor + 1) if siglas[i] in disponiveis), default=-1)
    resultado = avaliacoes[posicao] if posicao >= 0 else None
    rebaixado_de = avaliacoes[melhor].grau if 0 <= posicao < melhor else None
    # graus disponíveis mais nobres que o resultado
    acima = [a for a in avaliacoes[posicao + 1 :] if a.grau.sigla in disponiveis]

    return ResultadoNorma(
        norma=norma,
        grau=resultado.grau if resultado else None,
        avaliacoes=avaliacoes,
        quase_passou=_quase_passou(acima),
        faltando=_faltando(resultado, acima),
        notas_aplicadas=notas,
        rebaixado_de=rebaixado_de,
    )


def _quase_passou(acima: list[Avaliacao]) -> QuasePassou | None:
    """O grau mais nobre, acima do resultado, que falhou por uma única variável."""
    for avaliacao in reversed(acima):
        if len(avaliacao.falhas) == 1:
            return QuasePassou(avaliacao.grau, avaliacao.falhas[0])
    return None


def _faltando(resultado: Avaliacao | None, acima: list[Avaliacao]) -> list[Propriedade]:
    """Vazios exigidos pelo grau do resultado + vazios que barraram um grau mais nobre."""
    faltando = set(resultado.faltando if resultado else [])
    for avaliacao in acima:
        faltando |= {f.propriedade for f in avaliacao.falhas if f.vazio and f.propriedade}
    ordem = list(Propriedade)
    return sorted(faltando, key=ordem.index)

"""Aviso por divergência: acha, entre os casos que tiveram divergência, um **parecido** com a
classificação de agora (decisões do usuário, 2026-11-04).

Parecido =
1. mesmo acabamento;
2. o programa deu o **mesmo grau** que deu no caso errado (camada não conta);
3. valores próximos: cada valor preenchido **nos dois** casos fica dentro da sua margem
   (`MARGENS`); vazio em qualquer lado é ignorado; precisam ser comparados pelo menos
   `MINIMO_COMPARADOS` valores.

Como o scikit-learn entra: cada diferença é dividida pela margem do valor. Assim "dentro da
margem" vira "distância ≤ 1" na métrica de Chebyshev (a maior das diferenças), e o
`NearestNeighbors` devolve os casos dentro desse raio, do mais próximo para o mais distante.

O aviso é só um alerta amarelo: **nunca muda o resultado**, que é sempre o da norma.
"""

from dataclasses import dataclass

import numpy as np
from sklearn.neighbors import NearestNeighbors

from classificador.aprendizado.dados import CAMPOS, Exemplo, grau


@dataclass(frozen=True)
class Margem:
    """Quanto um valor pode se afastar e ainda ser "próximo".

    `fixa`: margem absoluta (ex.: LE ± 20 MPa). `relativa` + `piso`: fração do valor de agora,
    nunca menor que o piso (ex.: químicos ± 25 %, C nunca menos que 0,005).
    """

    fixa: float = 0.0
    relativa: float = 0.0
    piso: float = 0.0

    def para(self, valor: float) -> float:
        return max(self.fixa, self.relativa * abs(valor), self.piso)


def _quimico(piso: float) -> Margem:
    return Margem(relativa=0.25, piso=piso)


# Margens conferidas pelo usuário em 2026-11-04.
MARGENS: dict[str, Margem] = {
    "LE": Margem(fixa=20),
    "LR": Margem(fixa=20),
    "AL_LO50": Margem(fixa=3),
    "AL_LO80": Margem(fixa=3),
    "EMBUTIMENTO": Margem(fixa=0.5),
    "C": _quimico(0.005),
    "Mn": _quimico(0.05),
    "P": _quimico(0.005),
    "S": _quimico(0.005),
    "Al": _quimico(0.01),
    "Ni": _quimico(0.01),
    "Ti": _quimico(0.005),
    "V": _quimico(0.005),
    "Nb": _quimico(0.005),
    "Cr": _quimico(0.01),
    "Si": _quimico(0.01),
    "B": _quimico(0.0005),
    "Mo": _quimico(0.005),
    "espessura_nominal": Margem(fixa=0.2),
}

MINIMO_COMPARADOS = 3


@dataclass(frozen=True)
class CasoParecido:
    exemplo: Exemplo
    distancia: float  # maior diferença, em "margens" (0 = igual; 1 = no limite)
    comparados: int  # quantos valores entraram na comparação

    @property
    def aviso(self) -> str:
        e = self.exemplo
        return (f"Em um caso parecido (volume {e.volume}), a classificação correta foi "
                f"{e.correta}. Motivo: {e.motivo}. Confira.")


def caso_parecido(
    exemplos: list[Exemplo], acabamento: str, resultado: str | None, numeros: tuple[float, ...],
) -> CasoParecido | None:
    """O caso com divergência mais parecido com a classificação de agora, ou None."""
    grau_agora = grau(resultado)
    candidatos = [e for e in exemplos
                  if e.divergente and e.acabamento == acabamento and e.grau_programa == grau_agora]
    agora = np.array(numeros, dtype=float)
    preenchidos = ~np.isnan(agora)
    if not candidatos or preenchidos.sum() < MINIMO_COMPARADOS:
        return None

    # Só as colunas preenchidas agora; cada diferença medida em "margens".
    colunas = np.flatnonzero(preenchidos)
    margens = np.array([MARGENS[CAMPOS[i]].para(agora[i]) for i in colunas])
    base = np.array([e.numeros for e in candidatos], dtype=float)[:, colunas]
    comparados = (~np.isnan(base)).sum(axis=1)
    # Vazio no caso antigo não é comparado: recebe o valor de agora (diferença zero).
    base = np.where(np.isnan(base), agora[colunas], base)

    busca = NearestNeighbors(metric="chebyshev").fit(base / margens)
    distancias, indices = busca.radius_neighbors(
        [agora[colunas] / margens], radius=1.0 + 1e-9, sort_results=True,
    )
    for distancia, i in zip(distancias[0], indices[0], strict=True):
        if comparados[i] >= MINIMO_COMPARADOS:
            return CasoParecido(candidatos[i], float(distancia), int(comparados[i]))
    return None


"""De onde vêm os dados do ML: cada classificação salva no histórico vira um `Exemplo`.

Um exemplo guarda os valores digitados já como números (o que o scikit-learn entende) e o que se
sabe sobre a classificação: o resultado que o programa deu e, se alguém registrou uma divergência,
a classificação correta e o motivo. Registros com divergência ensinam com a classificação
**correta** (não se aprende com o erro).

Campo vazio vira NaN ("sem valor"), e não zero: para o motor da norma vazio vale zero, mas para o
ML "não informado" é diferente de "zero" e não pode puxar a média para baixo.
"""

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass

from classificador.dominio.propriedades import Propriedade
from classificador.historico.repositorio import RepositorioHistorico
from classificador.interface.entrada import ler_numero

# Valores usados pelo ML, sempre nesta ordem: mecânicas, químicas e a espessura nominal (que muda
# os limites das normas). Espessura real, largura e camada ficam de fora: não dizem nada sobre o
# grau do aço.
CAMPOS: tuple[str, ...] = (*(p.value for p in Propriedade), "espessura_nominal")

_CAMADA_ZINCO = re.compile(r"\s+-\s+ZF?\d+$")  # "ZEE G2 - Z275", "ZE - ZF100"
_CAMADA_POR_FACE = re.compile(r"\s+\S+/\S+$")  # "EEP G3 EG 50/50", "1006/08 EG _/_"


def grau(resultado: str | None) -> str | None:
    """Resultado sem a camada: "ZEE G2 - Z275" → "ZEE G2"; "EEP G3 EG 50/50" → "EEP G3 EG".

    A camada não muda a química nem a parte mecânica; por isso o ML compara graus, não camadas.
    """
    if not resultado:
        return None
    texto = _CAMADA_ZINCO.sub("", resultado.strip())
    return _CAMADA_POR_FACE.sub("", texto).strip() or None


def numeros(valores: Mapping[str, str]) -> tuple[float, ...]:
    """Textos digitados → um número por item de `CAMPOS`; vazio ou ilegível → NaN."""
    lista = []
    for campo in CAMPOS:
        try:
            numero = ler_numero(valores.get(campo, ""))
        except ValueError:
            numero = None
        lista.append(float(numero) if numero is not None else math.nan)
    return tuple(lista)


@dataclass(frozen=True)
class Exemplo:
    """Uma classificação do histórico, pronta para o ML."""

    registro_id: int
    volume: str
    acabamento: str
    grau_programa: str | None  # o que o programa deu (pela regra da norma), sem camada
    correta: str | None  # classificação correta registrada na divergência, como digitada
    motivo: str | None  # motivo da divergência (None = sem divergência)
    numeros: tuple[float, ...]  # um por item de CAMPOS; NaN = vazio

    @property
    def divergente(self) -> bool:
        return self.motivo is not None

    @property
    def grau_certo(self) -> str | None:
        """O grau que vale para aprender: o correto da divergência, senão o do programa."""
        return grau(self.correta) if self.divergente else self.grau_programa


def exemplos(repositorio: RepositorioHistorico) -> list[Exemplo]:
    """Todas as classificações do histórico (fora da Lixeira) como exemplos.

    Divergências pendentes e resolvidas contam. Se um registro tiver mais de uma (uma resolvida e
    outra registrada depois), vale a mais recente.
    """
    ultima: dict[int, tuple[str, str]] = {}
    divergencias = [*repositorio.listar_divergencias(resolvidas=True),
                    *repositorio.listar_divergencias(resolvidas=False)]
    for d in sorted(divergencias, key=lambda d: (d.criado_em, d.id)):
        ultima[d.classificacao.id] = (d.correta, d.motivo)

    lista = []
    for r in repositorio.listar():
        correta, motivo = ultima.get(r.id, (None, None))
        lista.append(Exemplo(
            registro_id=r.id,
            volume=r.volume,
            acabamento=r.acabamento,
            grau_programa=grau(r.resultado),
            correta=correta,
            motivo=motivo,
            numeros=numeros(r.valores),
        ))
    return lista

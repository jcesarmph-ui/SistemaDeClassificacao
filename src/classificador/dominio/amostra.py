"""Entrada do motor: o acabamento escolhido e os valores digitados pelo usuário.

A interface monta uma `Amostra`; o motor só lê. Valor vazio = `None` ou propriedade ausente.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from classificador.dominio.propriedades import Propriedade


class Acabamento(StrEnum):
    """Acabamentos da folha de classificações (item 5)."""

    FF = "FF"
    FQ = "FQ"
    FQ_DO = "FQ DO"
    GI_ZN = "GI ZN"
    GI_ZM = "GI ZM"
    GA_ZF = "GA ZF"
    EG = "EG"

    @property
    def descricao(self) -> str:
        return _DESCRICOES[self]

    @property
    def revestimento(self) -> str | None:
        """Tipo de camada: "GI" (Z100), "GA" (ZF100), "EG" (50/50) ou None (sem revestimento)."""
        return _REVESTIMENTOS.get(self)


_DESCRICOES = {
    Acabamento.FF: "Produto plano laminado a frio",
    Acabamento.FQ: "Produto plano laminado a quente",
    Acabamento.FQ_DO: "Produto plano laminado a quente - decapado e oleado",
    Acabamento.GI_ZN: "Produto plano zincado por imersão a quente - cristais normais",
    Acabamento.GI_ZM: "Produto plano zincado por imersão a quente - cristais minimizados",
    Acabamento.GA_ZF: "Produto plano zincado por imersão a quente - liga de zinco-ferro (Galvanew)",
    Acabamento.EG: "Produto plano zincado por processo eletrolítico",
}

_REVESTIMENTOS = {
    Acabamento.GI_ZN: "GI",
    Acabamento.GI_ZM: "GI",
    Acabamento.GA_ZF: "GA",
    Acabamento.EG: "EG",
}


@dataclass(frozen=True)
class Amostra:
    acabamento: Acabamento
    valores: Mapping[Propriedade, Decimal | None] = field(default_factory=dict)
    espessura_nominal: Decimal | None = None  # mm — usada nas notas de rodapé e no embutimento
    camada: Decimal | None = None  # g/m² (EG: por face); vazio ou zero = sem revestimento
    espessura_real: Decimal | None = None  # mm medida — comparada com a nominal na tolerância
    largura: Decimal | None = None  # mm — escolhe a coluna da tabela de tolerância

    def __post_init__(self) -> None:
        for prop, valor in self.valores.items():
            if valor is not None and valor < 0:
                raise ValueError(f"{prop.nome_extenso} não pode ser negativo ({valor})")
        for nome in ("espessura_nominal", "camada", "espessura_real", "largura"):
            valor = getattr(self, nome)
            if valor is not None and valor < 0:
                raise ValueError(f"{nome.replace('_', ' ')} não pode ser negativa ({valor})")

    def valor(self, prop: Propriedade) -> Decimal | None:
        return self.valores.get(prop)

    def preenchido(self, prop: Propriedade) -> bool:
        return self.valores.get(prop) is not None

    @property
    def tem_camada(self) -> bool:
        return self.camada is not None and self.camada > 0

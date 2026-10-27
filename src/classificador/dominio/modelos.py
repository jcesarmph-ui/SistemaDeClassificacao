"""Modelos de uma norma: graus, limites, notas de rodapé (ajustes) e tabela de embutimento.

Cada modelo se valida ao ser criado (pydantic): dado inválido gera erro antes de qualquer
classificação. Todos os números são `Decimal`, para comparar sem erro de arredondamento.
"""

from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from classificador.dominio.amostra import Acabamento
from classificador.dominio.propriedades import Propriedade


class _Modelo(BaseModel):
    # extra="forbid": campo com nome errado no YAML (ex.: "maximo") vira erro, não é ignorado.
    # frozen=True: depois de carregada, a norma não pode ser alterada por engano.
    model_config = ConfigDict(extra="forbid", frozen=True)


class Limite(_Modelo):
    """Faixa exigida para uma propriedade. Sem `min` ou sem `max` = sem limite daquele lado."""

    min: Decimal | None = None
    max: Decimal | None = None

    @model_validator(mode="after")
    def _conferir(self) -> Self:
        if self.min is None and self.max is None:
            raise ValueError("o limite precisa ter pelo menos 'min' ou 'max'")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError(f"mínimo ({self.min}) maior que o máximo ({self.max})")
        return self


class Variacao(_Modelo):
    """Quanto uma nota de rodapé soma ao mínimo e/ou ao máximo de um limite (pode ser negativo)."""

    min: Decimal | None = None
    max: Decimal | None = None


class Soma(_Modelo):
    """Limite para a soma de vários elementos (ex.: Ti + Nb ≤ 0,20 %)."""

    elementos: list[Propriedade] = Field(min_length=2)
    max: Decimal


class Grau(_Modelo):
    sigla: str  # como sai no resultado, ex.: "EEP G1"
    nome_na_norma: str  # como está escrito na tabela, ex.: "EEP grau 1"
    limites: dict[Propriedade, Limite] = {}
    somas: list[Soma] = []
    avisos: list[str] = []  # avisos informativos mostrados quando o resultado é este grau


class FaixaEspessura(_Modelo):
    """Faixa de espessura (mm) em que uma nota de rodapé vale. Limites inclusivos por padrão."""

    min: Decimal | None = None
    max: Decimal | None = None
    min_inclusivo: bool = True
    max_inclusivo: bool = True

    @model_validator(mode="after")
    def _conferir(self) -> Self:
        if self.min is None and self.max is None:
            raise ValueError("a faixa de espessura precisa ter pelo menos 'min' ou 'max'")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError(f"espessura mínima ({self.min}) maior que a máxima ({self.max})")
        return self

    def contem(self, espessura: Decimal) -> bool:
        if self.min is not None:
            if espessura < self.min or (espessura == self.min and not self.min_inclusivo):
                return False
        if self.max is not None:
            if espessura > self.max or (espessura == self.max and not self.max_inclusivo):
                return False
        return True


class Ajuste(_Modelo):
    """Nota de rodapé: se a condição vale, os limites mudam conforme `efeito` e `remover`.

    Condição: faixa de espessura (`quando`) e/ou acabamento (`acabamentos`) — ambas, se dadas.
    Notas do mesmo `motivo` valem pela maior variação; motivos diferentes se somam.
    """

    nota: str  # referência na norma, ex.: "Tabela 2, nota d"
    motivo: str = "espessura"  # ex.: "espessura", "revestimento"
    graus: list[str] | None = None  # None = vale para todos os graus
    quando: FaixaEspessura | None = None
    acabamentos: list[Acabamento] | None = Field(default=None, min_length=1)
    efeito: dict[Propriedade, Variacao] = {}
    remover: list[Propriedade] = []  # exigências que deixam de valer (ex.: Lo80 se e ≥ 3,0)

    @model_validator(mode="after")
    def _conferir(self) -> Self:
        if self.quando is None and self.acabamentos is None:
            raise ValueError(f"a nota '{self.nota}' precisa de condição: espessura ou acabamento")
        if not self.efeito and not self.remover:
            raise ValueError(f"a nota '{self.nota}' precisa de 'efeito' ou 'remover'")
        return self


class LinhaEmbutimento(_Modelo):
    espessura: Decimal
    minimos: dict[str, Decimal]  # sigla do grau → altura mínima (mm)


class TabelaEmbutimento(_Modelo):
    """Tabela de embutimento Erichsen: mínimo exigido por espessura nominal e grau."""

    linhas: list[LinhaEmbutimento] = Field(min_length=1)

    @model_validator(mode="after")
    def _conferir(self) -> Self:
        espessuras = [linha.espessura for linha in self.linhas]
        for anterior, atual in zip(espessuras, espessuras[1:], strict=False):
            if atual <= anterior:
                raise ValueError(
                    f"as espessuras da tabela de embutimento devem estar em ordem crescente "
                    f"({atual} aparece depois de {anterior})"
                )
        return self


class Norma(_Modelo):
    codigo: str  # ex.: "NBR 5915-2:2013"
    titulo: str
    graus: list[Grau] = Field(min_length=1)  # ordem da tabela: o último é o mais nobre
    ajustes: list[Ajuste] = []
    tabela_embutimento: TabelaEmbutimento | None = None

    @model_validator(mode="after")
    def _conferir(self) -> Self:
        siglas = [g.sigla for g in self.graus]
        repetidas = {s for s in siglas if siglas.count(s) > 1}
        if repetidas:
            raise ValueError(f"sigla de grau repetida: {', '.join(sorted(repetidas))}")

        for ajuste in self.ajustes:
            for sigla in ajuste.graus or []:
                if sigla not in siglas:
                    raise ValueError(
                        f"o ajuste '{ajuste.nota}' cita o grau '{sigla}', que não existe"
                    )

        if self.tabela_embutimento is not None:
            for linha in self.tabela_embutimento.linhas:
                for sigla in linha.minimos:
                    if sigla not in siglas:
                        raise ValueError(
                            f"a tabela de embutimento ({linha.espessura} mm) cita o grau "
                            f"'{sigla}', que não existe"
                        )
        return self

    def grau(self, sigla: str) -> Grau:
        for g in self.graus:
            if g.sigla == sigla:
                return g
        raise KeyError(f"grau '{sigla}' não existe na {self.codigo}")


# --- Folha de classificações: quais tabelas e graus valem para cada acabamento ---------------


class TabelaDoAcabamento(_Modelo):
    norma: str  # código da norma, igual ao campo `codigo` do YAML dela
    # Graus que podem ser resultado, na folha de classificações. None = todos os da norma.
    graus: list[str] | None = Field(default=None, min_length=1)


class SemGrau(_Modelo):
    """O que fazer quando nenhuma tabela do acabamento é atendida: um resultado fixo OU um aviso."""

    resultado: str | None = None  # ex.: "1006/08"
    aviso: str | None = None  # ex.: "Material mais duro que o último ZAR"

    @model_validator(mode="after")
    def _conferir(self) -> Self:
        if (self.resultado is None) == (self.aviso is None):
            raise ValueError("informe 'resultado' ou 'aviso' (um dos dois, não ambos)")
        return self


class RegraAcabamento(_Modelo):
    tabelas: list[TabelaDoAcabamento] = Field(min_length=1)  # na ordem em que são testadas
    se_nenhum: SemGrau


class FolhaClassificacoes(_Modelo):
    acabamentos: dict[Acabamento, RegraAcabamento]

    def regra(self, acabamento: Acabamento) -> RegraAcabamento:
        if acabamento not in self.acabamentos:
            raise KeyError(f"acabamento '{acabamento}' não está na folha de classificações")
        return self.acabamentos[acabamento]


# --- Normas correlatas: equivalências entre um grau NBR e normas de montadoras/europeias -----


def _chave(texto: str) -> str:
    """Forma de comparar nomes de norma ignorando maiúsculas, espaços e hífens."""
    return "".join(c for c in texto.upper() if c.isalnum())


class GrupoCorrelatas(_Modelo):
    nbr: str  # rótulo do grau NBR, ex.: "NBR 5915-2 EEP G2" (fora do escopo: "NBR 5915-4 BH-180")
    norma: str | None = None  # código do YAML da norma, quando o programa classifica esse grau
    grau: str | None = None  # sigla do grau nesse YAML
    correlatas: list[str] = []  # ex.: ["EN 10130 DC04", "GMW 2M CR3"]
    so_eg: list[str] = []  # correlatas que valem só para o acabamento EG (ex.: EN 10152)

    @model_validator(mode="after")
    def _conferir(self) -> Self:
        if (self.norma is None) != (self.grau is None):
            raise ValueError(f"grupo '{self.nbr}': informe 'norma' e 'grau' juntos")
        return self


class Correlatas(_Modelo):
    grupos: list[GrupoCorrelatas]

    def de(self, norma: str, grau: str, acabamento: Acabamento | None = None) -> list[str]:
        """Correlatas de um grau classificado, sem repetição, na ordem do arquivo."""
        nomes: list[str] = []
        for grupo in self.grupos:
            if grupo.norma == norma and grupo.grau == grau:
                nomes += grupo.correlatas
                if acabamento == Acabamento.EG:
                    nomes += grupo.so_eg
        return list(dict.fromkeys(nomes))

    def buscar(self, texto: str) -> list[GrupoCorrelatas]:
        """Grupos em que o texto aparece (rótulo NBR ou correlata), ex.: "dc04", "EN 10130 DC04".

        Prefere nomes que TERMINAM com o texto ("CR1" acha "GMW 2M CR1", não "… CR180B2");
        se nenhum terminar, procura em qualquer parte do nome.
        """
        procurado = _chave(texto)
        if not procurado:
            return []

        def nomes(g: GrupoCorrelatas) -> list[str]:
            return [_chave(n) for n in [g.nbr, *g.correlatas, *g.so_eg]]

        no_fim = [g for g in self.grupos if any(n.endswith(procurado) for n in nomes(g))]
        return no_fim or [g for g in self.grupos if any(procurado in n for n in nomes(g))]

    def todos_os_nomes(self) -> list[str]:
        """Todos os nomes de norma conhecidos (para o autocompletar da pesquisa reversa)."""
        nomes = [n for g in self.grupos for n in [g.nbr, *g.correlatas, *g.so_eg]]
        return sorted(set(nomes))

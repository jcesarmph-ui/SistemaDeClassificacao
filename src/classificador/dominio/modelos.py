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


class Faixa(_Modelo):
    """Faixa de valores (espessura em mm, LE em MPa…). Limites inclusivos por padrão."""

    min: Decimal | None = None
    max: Decimal | None = None
    min_inclusivo: bool = True
    max_inclusivo: bool = True

    @model_validator(mode="after")
    def _conferir(self) -> Self:
        if self.min is None and self.max is None:
            raise ValueError("a faixa precisa ter pelo menos 'min' ou 'max'")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError(f"início da faixa ({self.min}) maior que o fim ({self.max})")
        return self

    def contem(self, valor: Decimal) -> bool:
        if self.min is not None:
            if valor < self.min or (valor == self.min and not self.min_inclusivo):
                return False
        if self.max is not None:
            if valor > self.max or (valor == self.max and not self.max_inclusivo):
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
    quando: Faixa | None = None
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
    tolerancia: str | None = None  # código da norma de tolerância de espessura (ex.: "NBR 11888")


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


# --- Tolerância de espessura: grades espessura × largura → ± valor (NBR 11888, NBR 7013) ------


class LinhaTolerancia(_Modelo):
    espessura: Faixa  # mm
    tolerancias: list[Decimal | None]  # ± mm, uma por faixa de largura; None = "–" na norma


class TabelaTolerancia(_Modelo):
    nome: str  # ex.: "Tabela 11"
    le_min: Faixa | None = None  # faixa de LE mínimo do grau (MPa) em que vale; None = sempre
    linhas: list[LinhaTolerancia] = Field(min_length=1)


class Acrescimo(_Modelo):
    """Acréscimo à tolerância, ex.: revestimento ≥ Z275 → +0,01 mm (NBR 7013)."""

    acabamentos: list[Acabamento] = Field(min_length=1)
    camada_min: Decimal  # g/m²
    valor: Decimal  # mm


class NormaTolerancia(_Modelo):
    codigo: str  # ex.: "NBR 11888"
    titulo: str
    # Limites superiores (inclusivos) das faixas de largura, em mm: [1200, 1500] →
    # L ≤ 1200 | 1200 < L ≤ 1500 | L > 1500 (decisão do usuário, igual em todas as tabelas).
    larguras: list[Decimal] = Field(min_length=1)
    tabelas: list[TabelaTolerancia] = Field(min_length=1)
    acrescimos: list[Acrescimo] = []
    # Tabela para grau SEM LE mínimo definido (NBR 7013: ZC → Tabela 2). Sem grau não usa.
    tabela_sem_le: str | None = None

    @model_validator(mode="after")
    def _conferir(self) -> Self:
        if any(b <= a for a, b in zip(self.larguras, self.larguras[1:], strict=False)):
            raise ValueError("as larguras devem estar em ordem crescente")
        nomes = [t.nome for t in self.tabelas]
        if self.tabela_sem_le is not None and self.tabela_sem_le not in nomes:
            raise ValueError(
                f"tabela_sem_le '{self.tabela_sem_le}' não existe ({', '.join(nomes)})"
            )
        colunas = len(self.larguras) + 1
        for tabela in self.tabelas:
            for linha in tabela.linhas:
                if len(linha.tolerancias) != colunas:
                    raise ValueError(
                        f"{tabela.nome}: a linha de espessura {linha.espessura.min}–"
                        f"{linha.espessura.max} tem {len(linha.tolerancias)} tolerâncias; "
                        f"esperadas {colunas} (uma por faixa de largura)"
                    )
        return self

    def coluna(self, largura: Decimal) -> int:
        """Índice da faixa de largura: L ≤ 1º limite → 0, …, acima do último → última."""
        for indice, limite in enumerate(self.larguras):
            if largura <= limite:
                return indice
        return len(self.larguras)

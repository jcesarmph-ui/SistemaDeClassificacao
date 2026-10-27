"""Serviço da aplicação: carrega os dados uma vez e atende a tela (sem Qt).

Estrutura esperada da pasta de dados (padrão: `dados/` na pasta do projeto):
    folha-classificacoes.yaml   (obrigatória)
    normas/*.yaml               (obrigatória)
    correlatas.yaml             (opcional)
    tolerancias/*.yaml          (opcional)
    logo_mg.png                 (opcional)
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from classificador.dominio.modelos import (
    Correlatas,
    FolhaClassificacoes,
    Norma,
    NormaTolerancia,
)
from classificador.interface.entrada import ler_numero, montar_amostra
from classificador.motor.reversa import ResultadoPesquisa, pesquisar
from classificador.motor.saida import Saida, formatar
from classificador.motor.sequencia import classificar
from classificador.normas.carregador import (
    carregar_correlatas,
    carregar_folha,
    carregar_normas,
    carregar_tolerancias,
)

# Prefixo da norma correlata → fabricante/emissor (tabela do CLAUDE.md), do mais específico
# para o mais geral.
_FABRICANTES = [
    ("HES", "Honda (Honda Engineering Standard)"),
    ("TSG", "Toyota"),
    ("GMW", "General Motors"),
    ("VW", "Volkswagen"),
    ("MS 50002", "Stellantis (ex-Fiat Chrysler/FCA)"),
    ("FG 528", "Fiat (Stellantis) — a confirmar"),
    ("DIN EN", "Norma europeia (CEN/DIN) — não é montadora"),
    ("EN", "Norma europeia (CEN) — não é montadora"),
    ("JIS", "Norma japonesa (JSA) — não é montadora"),
    ("NBR", "ABNT"),
]


def fabricante(norma: str) -> str | None:
    """Fabricante/emissor pelo prefixo, ex.: "HES-C052 JSC270D" → "Honda (…)"."""
    for prefixo, nome in _FABRICANTES:
        if norma.upper().startswith(prefixo):
            return nome
    return None


def pasta_dados_padrao() -> Path:
    """Variável CLASSIFICADOR_DADOS, senão dados/ na pasta atual, senão na pasta do projeto."""
    if os.environ.get("CLASSIFICADOR_DADOS"):
        return Path(os.environ["CLASSIFICADOR_DADOS"])
    if (Path.cwd() / "dados").is_dir():
        return Path.cwd() / "dados"
    return Path(__file__).resolve().parents[3] / "dados"


@dataclass(frozen=True)
class Servico:
    folha: FolhaClassificacoes
    normas: Mapping[str, Norma]
    correlatas: Correlatas | None = None
    tolerancias: Mapping[str, NormaTolerancia] = field(default_factory=dict)
    logo: Path | None = None

    @classmethod
    def carregar(cls, pasta: Path | None = None) -> "Servico":
        pasta = pasta or pasta_dados_padrao()
        arquivo_correlatas = pasta / "correlatas.yaml"
        pasta_tolerancias = pasta / "tolerancias"
        logo = pasta / "logo_mg.png"
        return cls(
            folha=carregar_folha(pasta / "folha-classificacoes.yaml"),
            normas=carregar_normas(pasta / "normas"),
            correlatas=(
                carregar_correlatas(arquivo_correlatas) if arquivo_correlatas.is_file() else None
            ),
            tolerancias=(
                carregar_tolerancias(pasta_tolerancias) if pasta_tolerancias.is_dir() else {}
            ),
            logo=logo if logo.is_file() else None,
        )

    def classificar(self, acabamento: str, campos: Mapping[str, str]) -> Saida:
        """Textos da tela → resultado. Erros: ErroEntrada (digitação), ErroClassificacao."""
        amostra = montar_amostra(acabamento, campos)
        classificacao = classificar(amostra, self.folha, self.normas)
        return formatar(classificacao, amostra, self.correlatas, self.tolerancias)

    def pesquisar(self, texto: str, espessura: str = "") -> list[ResultadoPesquisa]:
        if self.correlatas is None:
            return []
        return pesquisar(texto, self.correlatas, self.normas, ler_numero(espessura))

    def nomes_para_autocompletar(self) -> list[str]:
        return self.correlatas.todos_os_nomes() if self.correlatas else []

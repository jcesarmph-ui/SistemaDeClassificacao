"""Sequência de tabelas por acabamento, conforme a folha de classificações.

Testa as tabelas do acabamento em ordem e para na primeira que dá resultado. Se nenhuma der,
aplica o `se_nenhum` da folha: um resultado fixo (ex.: "1006/08") ou um aviso.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from classificador.dominio.amostra import Acabamento, Amostra
from classificador.dominio.modelos import FolhaClassificacoes, Grau, Norma
from classificador.motor.classificar import ResultadoNorma, classificar_na_norma


class ErroClassificacao(Exception):
    """Configuração impede classificar (acabamento fora da folha, norma não transcrita…)."""


@dataclass(frozen=True)
class Classificacao:
    acabamento: Acabamento
    norma: Norma | None  # norma que deu o resultado (None se nenhuma tabela deu)
    grau: Grau | None
    resultado_padrao: str | None  # ex.: "1006/08", quando nenhuma tabela dá resultado
    aviso_sem_grau: str | None  # ex.: "Material mais duro que o último ZAR"
    detalhe: ResultadoNorma  # tabela do resultado; se não houve, a última testada
    tentativas: list[ResultadoNorma]  # todas as tabelas testadas, em ordem
    norma_tolerancia: str | None = None  # código da norma de tolerância do acabamento


def classificar(
    amostra: Amostra, folha: FolhaClassificacoes, normas: Mapping[str, Norma]
) -> Classificacao:
    try:
        regra = folha.regra(amostra.acabamento)
    except KeyError as erro:
        raise ErroClassificacao(erro.args[0]) from erro

    tentativas: list[ResultadoNorma] = []
    for tabela in regra.tabelas:
        norma = normas.get(tabela.norma)
        if norma is None:
            raise ErroClassificacao(
                f"a norma {tabela.norma} (acabamento {amostra.acabamento}) ainda não foi "
                f"transcrita em dados/normas/"
            )
        try:
            resultado = classificar_na_norma(norma, amostra, tabela.graus)
        except ValueError as erro:
            raise ErroClassificacao(f"folha de classificações: {erro}") from erro
        tentativas.append(resultado)
        if resultado.grau is not None:
            return Classificacao(
                amostra.acabamento, norma, resultado.grau, None, None, resultado, tentativas,
                regra.tolerancia,
            )

    return Classificacao(
        acabamento=amostra.acabamento,
        norma=None,
        grau=None,
        resultado_padrao=regra.se_nenhum.resultado,
        aviso_sem_grau=regra.se_nenhum.aviso,
        detalhe=tentativas[-1],
        tentativas=tentativas,
        norma_tolerancia=regra.tolerancia,
    )

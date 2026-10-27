"""Lê os arquivos YAML (normas e folha de classificações) e devolve os modelos validados,
ou um erro claro com arquivo, linha e campo.

Cuidados em relação ao leitor padrão do PyYAML:
- números com ponto viram `Decimal` direto do texto (nunca passam por `float`);
- chave repetida no mesmo bloco é erro (o PyYAML, por padrão, fica com a última em silêncio).
"""

from decimal import Decimal
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

from classificador.dominio.modelos import Correlatas, FolhaClassificacoes, Norma


class ErroNorma(Exception):
    """Arquivo de norma (ou da folha de classificações) ausente, mal escrito ou inválido."""


class _Leitor(yaml.SafeLoader):
    pass


def _ler_decimal(leitor: _Leitor, no: yaml.ScalarNode) -> Decimal:
    return Decimal(leitor.construct_scalar(no).replace("_", ""))


def _ler_bloco(leitor: _Leitor, no: yaml.MappingNode, deep: bool = False) -> dict:
    vistas = set()
    for no_chave, _ in no.value:
        chave = leitor.construct_object(no_chave, deep=deep)
        if chave in vistas:
            raise yaml.constructor.ConstructorError(
                None, None, f"chave '{chave}' repetida no mesmo bloco", no_chave.start_mark
            )
        vistas.add(chave)
    return leitor.construct_mapping(no, deep=deep)


_Leitor.add_constructor("tag:yaml.org,2002:float", _ler_decimal)
_Leitor.add_constructor("tag:yaml.org,2002:map", _ler_bloco)

# Tradução das mensagens mais comuns do pydantic
_MENSAGENS = {
    "extra_forbidden": "campo não reconhecido (nome escrito errado?)",
    "missing": "campo obrigatório faltando",
    "decimal_parsing": "não é um número",
    "decimal_type": "não é um número",
    "too_short": "lista com itens de menos",
    "string_type": "deveria ser um texto",
    "list_type": "deveria ser uma lista",
    "dict_type": "deveria ser um bloco de campos",
    "model_type": "deveria ser um bloco de campos",
}


def carregar_norma(caminho: str | Path) -> Norma:
    return _carregar(Path(caminho), Norma)


def carregar_normas(pasta: str | Path) -> dict[str, Norma]:
    """Todas as normas `*.yaml` da pasta, por código. Junta os erros de todos os arquivos."""
    normas: dict[str, Norma] = {}
    erros: list[str] = []
    for caminho in sorted(Path(pasta).glob("*.yaml")):
        try:
            norma = carregar_norma(caminho)
        except ErroNorma as erro:
            erros.append(str(erro))
            continue
        if norma.codigo in normas:
            erros.append(f"{caminho.name}: código '{norma.codigo}' repetido em outro arquivo")
        normas[norma.codigo] = norma
    if erros:
        raise ErroNorma("\n".join(erros))
    return normas


def carregar_folha(caminho: str | Path) -> FolhaClassificacoes:
    return _carregar(Path(caminho), FolhaClassificacoes)


def carregar_correlatas(caminho: str | Path) -> Correlatas:
    return _carregar(Path(caminho), Correlatas)


def _carregar[M: BaseModel](caminho: Path, modelo: type[M]) -> M:
    if not caminho.is_file():
        raise ErroNorma(f"Arquivo não encontrado: {caminho}")

    texto = caminho.read_text(encoding="utf-8")
    try:
        raiz = yaml.compose(texto, Loader=_Leitor)
        dados = _Leitor(texto).construct_document(raiz) if raiz is not None else None
    except yaml.YAMLError as erro:
        marca = getattr(erro, "problem_mark", None)
        linha = f", linha {marca.line + 1}" if marca else ""
        problema = getattr(erro, "problem", None) or erro
        raise ErroNorma(f"{caminho.name}{linha}: YAML mal escrito — {problema}") from erro

    try:
        return modelo.model_validate(dados)
    except ValidationError as erro:
        linhas = [_descrever(caminho.name, raiz, e) for e in erro.errors()]
        raise ErroNorma("\n".join(linhas)) from erro


def _descrever(arquivo: str, raiz: yaml.Node | None, erro: dict) -> str:
    # O pydantic acrescenta o nome do tipo esperado ao caminho (ex.: "function-after[...]");
    # só interessam as partes que existem no YAML.
    caminho = [str(p) for p in erro["loc"] if "[" not in str(p)]
    no, existentes = _localizar(raiz, caminho)
    linha = f", linha {no.start_mark.line + 1}" if no is not None else ""

    # No YAML a contagem de itens começa em 1; no Python, em 0.
    legivel = [str(int(p) + 1) if p.isdigit() else p for p in caminho]
    onde = f" ({' → '.join(legivel)})" if legivel else ""

    if erro["type"] == "value_error":
        mensagem = str(erro["ctx"]["error"])
    elif erro["type"] == "enum":
        mensagem = f"nome desconhecido '{erro['input']}'"
    else:
        mensagem = _MENSAGENS.get(erro["type"], erro["msg"])
    if erro["type"] == "missing" and existentes < len(caminho):
        mensagem = f"campo obrigatório '{caminho[-1]}' faltando"
        onde = f" ({' → '.join(legivel[:-1])})" if len(legivel) > 1 else ""
    return f"{arquivo}{linha}{onde}: {mensagem}"


def _localizar(raiz: yaml.Node | None, caminho: list[str]) -> tuple[yaml.Node | None, int]:
    """Segue o caminho do erro dentro da árvore do YAML; devolve o nó mais fundo encontrado."""
    no = raiz
    for profundidade, parte in enumerate(caminho):
        proximo = None
        if isinstance(no, yaml.MappingNode):
            proximo = next((v for k, v in no.value if str(k.value) == parte), None)
        elif isinstance(no, yaml.SequenceNode) and parte.isdigit() and int(parte) < len(no.value):
            proximo = no.value[int(parte)]
        if proximo is None:
            return no, profundidade
        no = proximo
    return no, len(caminho)

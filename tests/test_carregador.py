"""Testes do carregador: leitura do YAML, números exatos e mensagens de erro claras."""

from decimal import Decimal
from pathlib import Path

import pytest

from classificador.dominio.amostra import Acabamento
from classificador.dominio.propriedades import Propriedade
from classificador.normas.carregador import (
    ErroNorma,
    carregar_folha,
    carregar_norma,
    carregar_normas,
)

NORMA_FICTICIA = Path(__file__).parent / "dados" / "norma-ficticia.yaml"


def escrever(tmp_path: Path, texto: str) -> Path:
    arquivo = tmp_path / "teste.yaml"
    arquivo.write_text(texto, encoding="utf-8")
    return arquivo


def test_carrega_norma_ficticia():
    norma = carregar_norma(NORMA_FICTICIA)
    assert norma.codigo == "NBR 0000-1:2026"
    assert [g.sigla for g in norma.graus] == ["AAA", "BBB G1"]
    assert norma.ajustes[0].efeito[Propriedade.LE].max == 40


def test_numeros_viram_decimal_exato_sem_passar_por_float():
    norma = carregar_norma(NORMA_FICTICIA)
    c_max = norma.grau("BBB G1").limites[Propriedade.C].max
    assert isinstance(c_max, Decimal)
    assert c_max == Decimal("0.007")
    # Decimal guarda a escrita original: 0.30 continua com duas casas
    assert str(norma.tabela_embutimento.linhas[0].espessura) == "0.30"


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(ErroNorma, match="não encontrado"):
        carregar_norma(tmp_path / "nao-existe.yaml")


def test_erro_de_sintaxe_informa_a_linha(tmp_path):
    arquivo = escrever(tmp_path, "codigo: X\ngraus:\n  - sigla: [AAA\n")
    with pytest.raises(ErroNorma, match=r"teste\.yaml.*linha"):
        carregar_norma(arquivo)


def test_chave_repetida_e_recusada(tmp_path):
    texto = """\
codigo: X
titulo: Y
graus:
  - sigla: AAA
    nome_na_norma: AAA
    limites:
      C: {max: 0.10}
      C: {max: 0.20}
"""
    with pytest.raises(ErroNorma, match=r"linha 8.*'C' repetida"):
        carregar_norma(escrever(tmp_path, texto))


def test_valor_invalido_informa_linha_e_campo(tmp_path):
    texto = """\
codigo: X
titulo: Y
graus:
  - sigla: AAA
    nome_na_norma: AAA
    limites:
      LE: {min: 300, max: 200}
"""
    with pytest.raises(ErroNorma) as erro:
        carregar_norma(escrever(tmp_path, texto))
    mensagem = str(erro.value)
    assert "linha 7" in mensagem
    assert "graus → 1 → limites → LE" in mensagem
    assert "maior que o máximo" in mensagem


def test_campo_com_nome_errado_e_propriedade_desconhecida(tmp_path):
    texto = """\
codigo: X
titulo: Y
graus:
  - sigla: AAA
    nome_na_norma: AAA
    limites:
      Mb: {maximo: 0.10}
"""
    with pytest.raises(ErroNorma) as erro:
        carregar_norma(escrever(tmp_path, texto))
    mensagem = str(erro.value)
    assert "nome desconhecido 'Mb'" in mensagem
    assert "campo não reconhecido" in mensagem


# --- Várias normas e folha de classificações ------------------------------------

FOLHA_FICTICIA = Path(__file__).parent / "dados" / "folha-ficticia.yaml"


def test_carrega_todas_as_normas_da_pasta_por_codigo(tmp_path):
    (tmp_path / "a.yaml").write_text(NORMA_FICTICIA.read_text(encoding="utf-8"), encoding="utf-8")
    normas = carregar_normas(tmp_path)
    assert list(normas) == ["NBR 0000-1:2026"]


def test_codigo_repetido_entre_arquivos_e_erro(tmp_path):
    texto = NORMA_FICTICIA.read_text(encoding="utf-8")
    (tmp_path / "a.yaml").write_text(texto, encoding="utf-8")
    (tmp_path / "b.yaml").write_text(texto, encoding="utf-8")
    with pytest.raises(ErroNorma, match=r"b\.yaml.*repetido"):
        carregar_normas(tmp_path)


def test_carrega_folha_ficticia():
    folha = carregar_folha(FOLHA_FICTICIA)
    regra = folha.regra(Acabamento.EG)
    assert regra.tabelas[0].norma == "NBR 0000-1:2026"
    assert regra.tabelas[0].graus == ["AAA"]
    assert regra.se_nenhum.resultado == "1006/08"
    with pytest.raises(KeyError, match="GI ZN"):
        folha.regra(Acabamento.GI_ZN)


def test_folha_sem_resultado_nem_aviso(tmp_path):
    texto = """\
acabamentos:
  FF:
    tabelas: [{norma: X}]
    se_nenhum: {}
"""
    with pytest.raises(ErroNorma, match="'resultado' e/ou 'aviso'"):
        carregar_folha(escrever(tmp_path, texto))


def test_folha_com_acabamento_desconhecido(tmp_path):
    texto = """\
acabamentos:
  XX:
    tabelas: [{norma: X}]
    se_nenhum: {resultado: "1006/08"}
"""
    with pytest.raises(ErroNorma, match="nome desconhecido 'XX'"):
        carregar_folha(escrever(tmp_path, texto))

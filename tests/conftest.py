"""Peças compartilhadas pelos testes (o pytest carrega este arquivo sozinho)."""

import shutil
from pathlib import Path

import pytest

FICTICIOS = Path(__file__).parent / "dados"


@pytest.fixture
def pasta(tmp_path):
    """Pasta dados/ fictícia com a estrutura da real (folha, normas, correlatas, tolerâncias)."""
    (tmp_path / "normas").mkdir()
    (tmp_path / "tolerancias").mkdir()
    shutil.copy(FICTICIOS / "norma-ficticia.yaml", tmp_path / "normas")
    shutil.copy(FICTICIOS / "tolerancia-ficticia.yaml", tmp_path / "tolerancias")
    shutil.copy(FICTICIOS / "correlatas-ficticias.yaml", tmp_path / "correlatas.yaml")
    folha = (FICTICIOS / "folha-ficticia.yaml").read_text(encoding="utf-8")
    fim = 'se_nenhum: {resultado: "1006/08"}\n'
    folha = folha.replace(fim, fim + '    tolerancia: "NBR 0000-T"\n')
    (tmp_path / "folha-classificacoes.yaml").write_text(folha, encoding="utf-8")
    return tmp_path

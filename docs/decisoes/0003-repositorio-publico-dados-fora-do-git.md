# 0003 — Repositório público com dados das normas fora do Git

- **Status:** aceita
- **Data:** 2026-10-27

## Contexto
O código fica no GitHub em um repositório **público**. As normas ABNT são protegidas por direitos
autorais: nem as imagens das tabelas (`normas_claude/`) nem os valores transcritos delas podem ser
publicados. Os casos reais de classificação da MG também são dados internos. Ainda assim, o código
precisa ser testado automaticamente.

## Decisão
- `normas_claude/` (imagens, PDFs, planilha de equivalência) e `dados/` (normas transcritas em YAML,
  folha de siglas, casos reais) ficam no `.gitignore` e **nunca** são versionados.
- Os testes versionados usam uma **norma fictícia** (`tests/fixtures/norma_ficticia.yaml`), com
  valores inventados que exercitam as mesmas regras (limites mín/máx, ajustes, ordem de nobreza).
- Os testes com normas reais rodam **só localmente**, marcados como `normas_reais`, e são pulados
  automaticamente quando `dados/` não existe.
- O `.exe` procura a pasta `dados/` ao lado do executável.
- Backup de `dados/` fora do GitHub (OneDrive ou pasta de rede).

## Alternativas consideradas
- **Repositório privado:** permitiria versionar tudo junto, mas o usuário optou por manter público.
- **Normas embutidas no código:** violaria direitos autorais e misturaria dados com lógica.

## Consequências
- ✅ Nenhum conteúdo protegido publicado; o código pode ser mostrado livremente.
- ✅ Separação clara entre **código** (versionado) e **dados** (locais).
- ⚠️ `dados/` não tem histórico no Git: cada alteração nas normas transcritas depende de backup manual.
- ⚠️ Quem clonar o repositório não consegue classificar materiais reais sem receber `dados/` à parte.

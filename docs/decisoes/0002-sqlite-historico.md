# 0002 — SQLite para o histórico de classificações

- **Status:** aceita
- **Data:** 2026-10-27

## Contexto
As classificações precisam ser salvas e pesquisadas depois. Deve existir uma aba de **lixeira** que
mostre as classificações excluídas, com opção de **restaurar** e outra de **excluir permanentemente**.
O programa roda em **um PC só**; não haverá várias pessoas gravando ao mesmo tempo.

## Decisão
- Banco **SQLite** — um único arquivo (`historico.db`), já embutido no Python, sem servidor.
- Exclusão em dois níveis:
  - **Excluir** = exclusão lógica (o registro recebe a data de exclusão e passa a aparecer só na lixeira).
  - **Excluir permanentemente** (só pela lixeira) = remove o registro do banco.
- Todo acesso ao banco passa pela classe `RepositorioHistorico`; o resto do programa não escreve SQL.

## Alternativas consideradas
- **Planilha Excel:** fácil de abrir, mas lenta para pesquisar, sem garantia contra arquivo corrompido
  e exige biblioteca extra.
- **Arquivos JSON/CSV:** simples, mas a pesquisa e a lixeira teriam de ser programadas à mão.
- **PostgreSQL / servidor:** necessário só se várias pessoas usassem ao mesmo tempo — complexidade
  sem benefício hoje.

## Consequências
- ✅ Arquitetura simples para uma tarefa simples, em vez de arquitetura complicada para tarefa simples.
- ✅ Backup = copiar um arquivo.
- ⚠️ Não serve para várias pessoas gravando ao mesmo tempo. Se isso mudar, troca-se o banco
  **apenas** dentro do `RepositorioHistorico`.

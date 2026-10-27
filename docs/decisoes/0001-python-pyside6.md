# 0001 — Python + PySide6 para o programa desktop

- **Status:** aceita
- **Data:** 2026-10-27

## Contexto
O programa será usado todos os dias em **um PC Windows** da MG Centro de Serviço. Precisa de uma tela
com três colunas (acabamento, propriedades mecânicas, químicas), abas (classificação, histórico,
lixeira), tooltips e tela cheia. O núcleo do trabalho é comparar valores com limites de tabelas —
lógica de regras e dados, que precisa ser testada automaticamente.

## Decisão
- Linguagem **Python 3.12+**.
- Interface **PySide6** (biblioteca oficial do Qt para Python).
- Distribuição como **`.exe`** gerado pelo PyInstaller.
- O **motor de classificação não conhece a interface**: a tela só coleta valores, chama o motor e
  mostra o resultado.

## Alternativas consideradas
- **Streamlit (web local):** mais rápido de começar, mas abre no navegador e limita o layout
  (tela cheia, tooltips, abas personalizadas).
- **Excel com macros:** familiar, mas difícil de testar, versionar e manter.

## Consequências
- ✅ Programa Windows nativo, com o visual do esboço e tela cheia.
- ✅ Motor testável sem abrir janela (pytest); reaproveitável se um dia houver versão web.
- ✅ Python é a linguagem mais simples para quem está aprendendo.
- ⚠️ PySide6 tem curva de aprendizado média; o `.exe` fica grande (~100 MB).

# 0004 — Base de normas em arquivos YAML

- **Status:** aceita
- **Data:** 2026-10-27

## Contexto
O motor precisa conhecer, para cada norma: os graus (na ordem de nobreza da tabela), os limites
mínimo/máximo de cada propriedade, as notas de rodapé que ajustam limites (por espessura, revestimento
etc.) e as tabelas de tolerância. Esses valores vêm de imagens e serão transcritos e conferidos pelo
usuário. Corrigir um limite não pode exigir reprogramar.

## Decisão
- Cada norma em um arquivo **YAML** em `dados/normas/` (ex.: `nbr-5915-2.yaml`).
- Os graus são listados **na mesma ordem das linhas da tabela** (último = mais nobre).
- Notas de rodapé viram **ajustes declarativos** (`quando` → `efeito`); regras que não cabem nesse
  formato (ex.: Ti + Nb ≤ 0,20 %) viram funções nomeadas no motor.
- Ao carregar, cada arquivo é **validado** (pydantic): campo faltando ou valor inválido gera erro claro,
  com o nome do arquivo e da linha, antes de qualquer classificação.

Exemplo de formato (valores fictícios):
```yaml
norma: NBR 0000-1
graus:            # do menos nobre para o mais nobre
  - sigla: AAA
    LE:  {max: 280}
    C:   {max: 0.10}
  - sigla: BBB
    LE:  {min: 140, max: 220}
    C:   {max: 0.06}
ajustes:
  - quando: {espessura_max_exclusiva: 0.50}
    efeito: {LE_max: +40, alongamento_min: -4}
```

## Alternativas consideradas
- **Planilha Excel:** fácil de editar, mas difícil de validar e de ver o que mudou entre versões.
- **JSON:** equivalente ao YAML, porém menos legível (aspas e chaves por toda parte, sem comentários).
- **Valores no código Python:** cada correção exigiria programar e gerar um novo `.exe`.

## Consequências
- ✅ Corrigir uma norma = editar um arquivo de texto legível, sem mexer no código.
- ✅ Validação automática pega erros de digitação na transcrição.
- ✅ Comentários no YAML guardam a referência (tabela, nota) de onde veio cada valor.
- ⚠️ YAML é sensível a indentação — a validação existe justamente para avisar esses erros.

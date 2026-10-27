# 0008 — Tolerância de espessura

- **Status:** aceita
- **Data:** 2026-10-27
- **Complementa:** [0004](0004-normas-em-yaml.md), [0006](0006-motor-de-classificacao.md)

## Contexto
Além do grau, a tela precisa dizer se a espessura **real** da bobina está dentro da tolerância da
espessura **nominal** (verde/vermelho), mostrando o intervalo e a norma usada. Sem revestimento,
a NBR 11888 (Tab. 11) dá a tolerância por espessura × largura. Nos revestidos, a NBR 7013 tem
quatro tabelas, escolhidas pelo limite de escoamento mínimo do grau.

## Decisão — formato (`dados/tolerancias/*.yaml`)
Exemplo versionado: `tests/dados/tolerancia-ficticia.yaml`.

| Campo | Conteúdo |
|---|---|
| `larguras` | Limites superiores das faixas de largura: `[1200, 1500]` → L ≤ 1200 · 1200 < L ≤ 1500 · L > 1500 |
| `tabelas` | Cada uma com `le_min` (faixa de LE mínimo do grau; ausente = sempre) e `linhas` (faixa de espessura → uma tolerância por faixa de largura; `null` = "–" na norma) |
| `tabela_sem_le` | Tabela para grau sem LE mínimo definido (NBR 7013: Tabela 2, como a norma diz para o ZC) |
| `acrescimos` | Acréscimo por acabamento e camada (NBR 7013: +0,01 mm para GI e GA com camada ≥ 275) |

A faixa de valores (`Faixa`: `min`/`max` com inclusivo) é a mesma das notas de rodapé. A folha de
classificações diz, por acabamento, qual norma de tolerância vale (`tolerancia:`).

## Decisão — regras (decididas com o usuário)
- Linha pela espessura **nominal**; comparação com a espessura **real**; limite **inclusive**.
- Sempre a coluna de tolerâncias **normais**.
- **Sem grau** no resultado (ex.: EG 1006/08) com norma que depende do LE → **não avalia** e avisa.
  Grau **sem LE** definido → `tabela_sem_le`.
- Espessura fora da tabela, "–" na norma, espessura real ou largura vazias → **não avalia** e avisa.
- Valores fora da progressão são transcritos como impressos (7013 Tab. 3, 2,50–3,00, L > 1500 = 0,23).
- O dobro da tolerância nos 15 m de solda (NBR 11888 4.7.1.3) não é tratado: a tela não tem essa
  informação.

## Consequências
- ✅ `verificar_tolerancia()` (em `src/classificador/tolerancia/`) devolve dentro/fora/não avaliada,
  o intervalo, a tolerância usada e o texto pronto; `formatar()` o coloca na saída.
- ✅ O comando de conferência imprime também as tabelas de tolerância.
- ⚠️ A NBR 11888 Tab. 12 (alta resistência) não foi transcrita: fora do escopo atual.

# 0012 — Machine learning: avisos aprendidos do histórico

- **Status:** aceita
- **Data:** 2026-11-04
- **Complementa:** [0006](0006-motor-de-classificacao.md), [0010](0010-historico-lixeira-e-divergencias.md)

## Contexto
A classificação pela norma é determinística e explicável, mas não enxerga dois tipos de problema:

1. **Erro de digitação que a norma aceita.** Exemplo: LR 29 em vez de 290 num zincado. A NBR 7008-2
   só limita o máximo do LR, então o resultado sai normal.
2. **Caso em que a regra já errou antes.** Quando uma divergência é registrada, a regra só é
   corrigida depois. Até lá, um material parecido pode receber a mesma classificação errada.

O histórico (ADR 0010) guarda cada classificação e cada divergência. São os dados de que o ML
precisa.

## Decisão — o ML só avisa, nunca classifica
- O **resultado é sempre o da norma**. O ML acrescenta avisos **amarelos**, começando com
  **"Histórico:"**, para separá-los dos avisos da norma.
- Os avisos entram no "retrato" da classificação e ficam gravados ao salvar.
- Se o histórico não puder ser lido, a classificação sai normalmente, sem avisos do ML.
- O ML fica numa camada própria, `aprendizado/`. Ela lê o histórico e não conhece a tela nem muda
  o motor.

## Decisão — dados (`aprendizado/dados.py`)
- Cada classificação salva vira um exemplo com 19 números: mecânicas, 13 químicas e espessura
  nominal. Espessura real, largura e camada ficam de fora.
- **Vazio = "sem valor" (NaN), não zero.** Para a norma vazio vale zero, mas para o ML "não
  informado" não pode puxar a estatística para baixo.
- Compara-se o **grau sem a camada** (`ZEE G2 - Z275` → `ZEE G2`).
- Registro com divergência ensina com a **classificação correta**, nunca com o erro. Divergências
  pendentes e resolvidas contam (vale a mais recente); a Lixeira não conta.
- **Aprende na hora:** o histórico é lido a cada CLASSIFICAR. Uma divergência registrada vale na
  classificação seguinte, sem mudar código.

## Decisão — aviso por divergência em caso parecido (`aprendizado/semelhanca.py`)
"Parecido" (decisão do usuário) é tudo isto ao mesmo tempo:
- **mesmo acabamento**;
- o programa deu o **mesmo grau** que deu no caso errado;
- valores próximos, por **margem fixa por valor**:

| Valor | Margem |
|---|---|
| LE, LR | ± 20 MPa |
| Lo50, Lo80 | ± 3 |
| Embutimento | ± 0,5 mm |
| Espessura nominal | ± 0,2 mm |
| Químicos | ± 25 % do valor de agora, nunca menos que o piso (C, P, S, Ti, V, Nb, Mo 0,005; Mn 0,05; Al, Ni, Cr, Si 0,01; B 0,0005) |

- Só entram valores preenchidos **nos dois** casos. **Todos** precisam estar dentro da margem, e
  são necessários **pelo menos 3** comparados.
- Implementação: cada diferença é dividida pela margem, e o `NearestNeighbors` do **scikit-learn**
  (métrica de Chebyshev, raio 1) devolve os casos dentro de todas as margens, do mais próximo para
  o mais distante. **Mostra só o mais próximo.**

## Decisão — aviso de valor fora do comum (`aprendizado/fora_do_comum.py`)
- O grupo de comparação é o **mesmo acabamento + mesmo grau** (o grau certo, quando houve
  divergência). Cada valor só é avaliado com **20 preenchidos** no grupo.
- Sensibilidade **"só muito fora"** (decisão do usuário): o valor está a mais de **4 vezes a faixa
  central** (distância entre os quartis) da **mediana**. A faixa nunca é considerada menor que meia
  margem, para não haver alarme quando todos os valores salvos são quase iguais.
- Mediana e quartis, e não média e desvio-padrão, para que um erro antigo salvo no histórico não
  esconda os próximos.
- A espessura nominal não entra, porque varia conforme o pedido.
- O aviso diz qual valor está fora e o que é normal, arredondado para ler de relance: *"LR (29)
  fora do comum para ZEE G4 em GI ZN (costuma ficar entre 270 e 311). Confira a digitação."*
- **IsolationForest descartado:** ele marca sempre uma fração fixa dos registros como estranhos
  (mesmo quando todos são normais) e não diz qual valor está fora.

## Decisão — scikit-learn
O usuário escolheu o **scikit-learn** em vez de escrever tudo em Python puro: é a biblioteca de ML
de referência em Python. O preço é o executável maior (numpy + scipy). O tamanho deve ser medido
na próxima geração da entrega.

## Demonstração (dados fictícios)
Foram usados um histórico inventado de 340 classificações e 5 divergências inventadas. Ao
reclassificar as 335 normais:
- **fora do comum: 0 alarmes**;
- **caso parecido: 19 (≈ 6 %)**. São casos de fato dentro das margens de uma divergência; se o
  aviso aparecer demais no uso real, apertar as margens (ex.: LE ± 10).

## Consequências
- ✅ Pega erros que a norma não pega (digitação plausível para a norma) e repete o alerta de
  divergências passadas até a regra ser corrigida.
- ✅ Cada aviso diz o porquê (qual valor, qual caso, qual motivo). Nenhum resultado muda.
- ✅ Funciona desde a primeira divergência; o "fora do comum" liga sozinho quando cada grau chega a
  20 registros.
- ⚠️ Lê o histórico inteiro a cada classificação. Serve para o volume esperado (5–10 por dia); com
  muitos anos de dados, guardar os exemplos em memória.
- ⚠️ Executável maior por causa do scikit-learn.

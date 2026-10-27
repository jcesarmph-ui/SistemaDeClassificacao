# 0007 — Notas de rodapé por motivo/acabamento e normas correlatas

- **Status:** aceita
- **Data:** 2026-10-27
- **Complementa:** [0005](0005-formato-yaml-normas.md), [0006](0006-motor-de-classificacao.md)

## Contexto
A transcrição da NBR 5906 e das NBR 7008-2/-3 (Fase 3) trouxe notas de rodapé que o formato da
ADR 0005 não representava: uma nota que depende do **acabamento** e não da espessura (zinco-ferro),
notas de **motivos diferentes** que valem ao mesmo tempo, e uma coluna da tabela que **retira** uma
exigência (Lo80 na 5906 com e ≥ 3,0 mm). Também entraram as normas correlatas (equivalências com
normas de montadoras e europeias), que aparecem no resultado e alimentam a pesquisa reversa.

## Decisão — notas de rodapé
Cada `ajuste` do YAML ganha três campos opcionais:

| Campo | Para quê | Exemplo |
|---|---|---|
| `motivo` | Notas do **mesmo** motivo valem pela maior variação; de motivos **diferentes**, somam | `espessura` (padrão), `revestimento` |
| `acabamentos` | Condição por acabamento; a faixa de espessura (`quando`) passa a ser opcional | `[GA ZF]` |
| `remover` | Exigência que deixa de valer na condição | `[AL_LO80]` |

Toda nota precisa de ao menos uma condição (`quando` ou `acabamentos`) e de ao menos um efeito
(`efeito` ou `remover`). Exemplo (GA 0,60 mm na 7008-2): nota b (espessura, −2) + nota c
(revestimento, −2) = alongamento −4.

## Decisão — normas correlatas
- Arquivo `dados/correlatas.yaml` (fora do Git), exemplo versionado em
  `tests/dados/correlatas-ficticias.yaml`. Um **grupo** por grau NBR: `nbr` (rótulo), `norma`/`grau`
  (ligação ao YAML da norma, quando o programa classifica o grau), `correlatas` e `so_eg` (as que
  valem só no acabamento EG, como a EN 10152).
- Conteúdo: **união** da folha de classificações e da planilha de equivalência, nomes padronizados
  (`<norma> <grau>`); divergências entre as fontes aparecem as duas (decisão do usuário).
- No resultado: lista simples, separada por vírgula.
- Pesquisa reversa por qualquer nome (NBR ou correlata), ignorando maiúsculas, espaços e hífens;
  prefere nomes que **terminam** com o texto digitado ("CR1" acha "GMW 2M CR1", não "CR180B2").
  Graus fora do escopo (IF, BH, ARBL) aparecem só com as equivalências, sem valores exigidos.

## Alternativa considerada
- **Ler a planilha .xlsx direto:** o usuário mantém só o Excel. Descartada por ora: a planilha atual
  tem cabeçalhos deslocados e grafias diferentes da folha; ler direto seria frágil. O usuário pediu
  simplicidade; o YAML foi gerado uma vez a partir das duas fontes e conferido.

## Consequências
- ✅ A 5915-2 não mudou (o `motivo` padrão é `espessura`).
- ✅ Novas notas por acabamento ou que retiram exigências entram só no YAML.
- ⚠️ Atualizar uma correlata é editar `dados/correlatas.yaml`, não a planilha.

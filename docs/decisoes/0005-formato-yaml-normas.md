# 0005 — Formato detalhado do YAML das normas e regras de interpretação

- **Status:** aceita
- **Data:** 2026-10-27
- **Complementa:** [0004](0004-normas-em-yaml.md)

## Contexto
A ADR 0004 decidiu guardar as normas em YAML validado. Ao transcrever a primeira norma real
(NBR 5915-2, piloto) surgiram estruturas que o exemplo da 0004 não cobria — soma de elementos,
notas de rodapé com faixa de espessura, tabela de embutimento por espessura — e dúvidas de
interpretação que foram decididas com o usuário.

## Decisão — formato
O exemplo completo e versionado está em [`tests/dados/norma-ficticia.yaml`](../../tests/dados/norma-ficticia.yaml).

| Bloco | Conteúdo |
|---|---|
| `codigo`, `titulo` | Identificação da norma |
| `graus` | Lista na ordem das linhas da tabela (último = mais nobre). Cada grau: `sigla` (como sai no resultado, ex. `EEP G1`), `nome_na_norma` (ex. `EEP grau 1`), `limites`, `somas`, `avisos` |
| `limites` | `{Propriedade: {min, max}}` — só as propriedades da tela (`LE`, `LR`, `AL_LO50`, `AL_LO80`, `EMBUTIMENTO`, `C` … `Mo`) |
| `somas` | Soma de elementos com máximo, ex. `{elementos: [Ti, Nb], max: 0.20}` |
| `avisos` | Texto informativo mostrado quando o resultado é aquele grau |
| `ajustes` | Notas de rodapé: `quando` (faixa de espessura, com `min_inclusivo`/`max_inclusivo`) → `efeito` (quanto somar ao `min`/`max` de cada propriedade); `graus` opcional (padrão: todos) |
| `tabela_embutimento` | Linhas `{espessura, minimos: {sigla: valor}}` em ordem crescente de espessura |

Regras de leitura: números viram `Decimal` direto do texto; chave repetida, campo desconhecido,
propriedade desconhecida, `min > max`, sigla repetida ou grau inexistente citado são **erros**,
informados com arquivo, linha e caminho do campo. Os modelos ficam em `src/classificador/dominio/`.

## Decisão — interpretação (decidida com o usuário)
- **Espessura usada nas notas e no embutimento:** a **nominal**.
- **Tabela de embutimento:** usa a linha de espessura **mais próxima**; empate → **linha maior**.
  Espessura fora da faixa da tabela → embutimento **não é avaliado**.
- **Embutimento vazio:** **não é avaliado** (com aviso) — exceção à regra geral "vazio = zero".
- **Alongamento Lo50 e Lo80:** quando a norma define os dois, **ambos são avaliados**; se só um foi
  preenchido, o outro não é avaliado.
- **Notas que se sobrepõem** (mesma propriedade, mesma faixa): vale a **maior redução**, sem acumular.
  Na NBR 5915-2 isso significa aplicar só a nota d (a nota b não entra).
- **Valores impressos de forma estranha** (sufixo sem explicação, valor fora da progressão da
  tabela) são transcritos **como impressos**, com comentário no YAML, após confirmação do usuário.
- Notas que dependem de algo fora da tela (planicidade, exigência do comprador, anisotropia) não são
  transcritas como ajuste; ficam como comentário no YAML.

## Testes
- Versionados (`tests/`): só a norma fictícia.
- Com valores reais (`dados/testes/`, fora do Git): conferem valores-âncora de cada norma transcrita;
  o pytest procura nessa pasta quando ela existe.

## Consequências
- ✅ `python -m classificador.normas.conferir <arquivo.yaml>` imprime a norma no formato das tabelas
  da ABNT, para conferência lado a lado com as imagens.
- ✅ `somas` e `ajustes` com `graus` cobrem as próximas normas (microligantes da 7008-3, notas
  específicas do EPA na 5906) sem mudar o formato.
- ⚠️ A regra "maior redução" é decidida na transcrição (só a nota vencedora entra no YAML); se
  surgir um caso em que a vencedora dependa da espessura de forma diferente, o motor precisará
  tratar sobreposição.

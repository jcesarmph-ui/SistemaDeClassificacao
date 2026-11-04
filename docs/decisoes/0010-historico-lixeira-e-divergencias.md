# 0010 — Histórico, lixeira e divergências

- **Status:** aceita
- **Data:** 2026-11-04
- **Complementa:** [0002](0002-sqlite-historico.md), [0009](0009-interface-e-resultado-sem-grau.md)

## Contexto
Até a Fase 5, cada classificação sumia ao fechar o programa. A empresa precisa consultar o que já
foi classificado (por volume, resultado, data…) e registrar quando uma classificação estava errada,
para corrigir o programa. Esse histórico também vai ser a base do machine learning da Fase 8.

O programa fica numa **pasta comum da rede**, sem servidor. Quase sempre uma pessoa usa por vez,
mas às vezes duas ou três usam juntas.

## Decisão — banco SQLite na pasta da rede
- Arquivo `historico.db` na pasta de dados, ao lado das normas.
- **Journal tradicional (`DELETE`), nunca WAL**, porque o WAL não funciona em pasta de rede. Também
  `busy_timeout`, transações curtas e chaves estrangeiras ligadas.
- Versão do esquema em `PRAGMA user_version` (= 1), para migrar no futuro.
- **Backup diário automático** ao abrir o programa, em `backup/`, guardando as últimas 30 cópias.
- Duas tabelas:

| Tabela | Guarda |
|---|---|
| `classificacao` | O "retrato" da classificação como saiu na hora: valores digitados, acabamento, resultado, norma, correlatas, avisos, tolerância, **volume**, data/hora, usuário do Windows, PC e versão do programa. Excluir só preenche `excluido_em` (Lixeira). |
| `divergencia` | Classificação correta + motivo, quem registrou e quando; `resolvida_em` preenchido depois da correção. |

- O banco fica atrás da classe `RepositorioHistorico` (`historico/repositorio.py`), o único lugar
  que lê e grava. A tela não conhece SQL; trocar o banco no futuro muda só esse pacote.
- Gravação recusada vira `ErroDeValidacao` com mensagens para a tela, em vermelho, sem pop-up. Isso
  vale para campo obrigatório vazio e também para banco ocupado por outro computador.

## Decisão — sem trava de edição (exceção ao padrão)
O padrão dos programas da MG tem trava de edição (modo edição/consulta). **Este programa não tem**
(decisão do usuário, 2026-11-03). Cada salvamento é um registro novo, e ninguém edita o registro
de outra pessoa. Por isso duas pessoas podem classificar e salvar ao mesmo tempo sem interferir uma
na outra; o `busy_timeout` e as transações curtas dão conta.

## Decisão — salvar
- Salva **só pelo botão Salvar**, depois de CLASSIFICAR: testes e simulações não entram no
  histórico (que vai ensinar o ML).
- Faixa de botões: `[Nova] [Limpar] [CLASSIFICAR] Volume [__] [Salvar]`. **Volume obrigatório.**
- Digitar algo depois de classificar desliga o Salvar até classificar de novo, para não gravar um
  resultado que não corresponde mais aos valores da tela. Um mesmo resultado não é salvo duas vezes.
- Registro salvo **não é editável**. Se estava errado, registra-se uma divergência.

## Decisão — abas Classificar | Histórico | Divergências | Lixeira
- Histórico e Lixeira usam a mesma peça (`PainelRegistros`): **lista (2/5) | detalhes (3/5)** (era 2/3 | 1/3 até a Fase 8: a coluna do resultado ficava larga demais e os detalhes precisavam de rolagem). Os valores digitados aparecem em duas colunas (espessuras e mecânicas | químicos).
  A lista mostra **Data/hora, Volume e Resultado**; os detalhes mostram o registro completo, com
  cores (tolerância verde/vermelho/amarelo, avisos em amarelo).
- **Pesquisa por texto livre**: cada palavra tem de aparecer em algum campo do registro, sem
  diferenciar maiúsculas nem acentos.
- Histórico: **Excluir** manda para a Lixeira. Lixeira: **Restaurar** e **Excluir
  permanentemente** (apaga junto as divergências do registro).
- **As duas exclusões pedem confirmação**, numa janela no visual do programa
  (`componentes.DialogoConfirmacao`), não na caixa branca do Windows. "Cancelar" já vem
  selecionado, então um Enter sem querer não apaga nada.
- Cores dos botões: Excluir com contorno e letra **vermelhos**, Restaurar e Marcar como resolvida
  com contorno **verde**. O vermelho cheio continua exclusivo do CLASSIFICAR.
- Abrir uma aba relê o banco, porque outra pessoa pode ter salvo algo. O que muda numa aba
  atualiza as outras.
- Sem histórico (banco indisponível), só a aba Classificar fica ativa.
- Com as abas, a janela passou a calcular o tamanho delas antes de aparecer. Sem isso, o
  `showMaximized()` se perdia e a janela abria pequena.

## Decisão — divergências (melhoria contínua e base do ML)
- No Histórico, **Registrar divergência** abre uma janela própria com **classificação correta +
  motivo, os dois obrigatórios**.
- **Só uma divergência pendente por registro** (regra no repositório). Enquanto houver uma, o
  botão fica desligado e os detalhes mostram o aviso em amarelo.
- Aba Divergências: lista | detalhes, **Pendentes / Resolvidas**, uma nota cinza explicando para
  que serve, e **Marcar como resolvida** (com confirmação), que deve ser usado só depois que o
  programa foi corrigido.
- Divergência de registro que está na Lixeira some da lista e volta ao restaurar.
- Ciclo: divergência registrada → correção da norma/regra + **caso de teste** → nova versão →
  marcada como resolvida.
- **Fase 8 (decidido pelo usuário):** as divergências ensinam o ML no modo **"aprender e
  avisar"**. Ao registrar uma divergência, o programa já passa a reconhecer o caso, sem mudar
  código. Numa classificação parecida, mostra um aviso amarelo com a classificação correta do caso
  anterior e o motivo. **O resultado continua sendo o da norma.**

## Consequências
- ✅ Tudo o que foi classificado fica rastreável (quem, quando, em qual PC, com qual versão).
- ✅ Exclusão com volta (Lixeira) e confirmação; o backup diário protege contra perda do arquivo.
- ✅ Erros de classificação viram dados organizados para corrigir o programa e para o ML.
- ⚠️ A pesquisa lê todos os registros e filtra em Python. É simples e serve para o volume
  esperado (5–10 por dia); se ficar lenta com muitos anos de dados, passar o filtro para o SQL.
- ⏭️ Fase 7: executável `.exe`. Fase 8: ML de outliers e avisos a partir das divergências.

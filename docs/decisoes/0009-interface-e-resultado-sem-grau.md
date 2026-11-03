# 0009 — Interface (layout, tema, versão) e resultado sem grau

- **Status:** aceita
- **Data:** 2026-10-28
- **Complementa:** [0001](0001-python-pyside6.md), [0006](0006-motor-de-classificacao.md),
  [0008](0008-tolerancia-de-espessura.md)
- **Altera em parte:** [0006](0006-motor-de-classificacao.md) — o ZC passa a ser resultado de último
  recurso de GI/GA (continua sem sair da tabela da NBR 7008-2)

## Contexto
A Fase 5 levou o motor para uma janela PySide6. O esboço à mão era só referência; o usuário pediu
uma tela sem espaços vazios, simétrica e com cores que tenham sempre o mesmo significado, para
"bater o olho" e saber se deu certo. Ao usar a tela apareceram também casos que o motor não
cobria: GI/GA que não atende nenhum grau e revestido sem camada informada.

## Decisão — camadas da interface
A interface não tem regra de norma. Ela só lê o que foi digitado e mostra o que o motor devolve.

| Módulo | Papel |
|---|---|
| `interface/entrada.py` | Lê os campos (`ler_numero`, `montar_amostra`); erro de digitação → `ErroEntrada` |
| `interface/servico.py` | Carrega os dados e expõe `classificar`, `pesquisar`, autocompletar e `fabricante()` |
| `interface/janela.py` | `JanelaPrincipal`: monta a tela e mostra o resultado |
| `interface/app.py` | Abre o programa maximizado, com ícone e `AppUserModelID` |

A janela é testada automaticamente em modo offscreen (sem aparecer na tela).

## Decisão — layout em faixas
- **Sempre maximizada**, sem espaços vazios.
- Faixas horizontais; dentro de cada faixa, caixas da **mesma altura e larguras iguais**:
  1. Cabeçalho: logo da MG | título em maiúsculas, centralizado | versão.
  2. Entradas: Material + Espessura e tolerância | Mecânicas | Químicas (3 colunas × 5 linhas).
  3. Botões: Nova classificação, Limpar valores, CLASSIFICAR (largo).
  4. Resultado (2/3) | Pesquisa reversa (1/3).
- "Limpar valores" mantém acabamento e camada; "Nova classificação" apaga tudo.
- Números com vírgula ou ponto decimal, "%" opcional, **sem separador de milhar**.
- Erros de digitação aparecem em vermelho na área de avisos, **sem pop-up**.
- **Roda do mouse só rola a tela**: nunca troca a opção de uma lista, como o acabamento
  (`interface/componentes.py`, `FiltroRodaDoMouse`, igual ao do SistemaCalibracao). O mesmo filtro
  põe a mãozinha do mouse em tudo o que é clicável.
- Tooltips: nome por extenso dos elementos químicos e fabricante/emissor das normas correlatas.
- A pesquisa reversa mostra as faixas exigidas em cinza ao lado de cada campo; se a norma
  digitada leva a mais de um grau, aparece uma lista para escolher.

## Decisão — tema escuro e significado das cores
Fundo **preto puro** (o logo da MG tem texto branco), caixas `#0a0a0a`, campos `#161616`,
contornos e títulos **brancos**, fonte Segoe UI 13pt. Sem efeito neon/brilho.

| Cor | Significado (único) |
|---|---|
| 🔴 Vermelho | **Só** o botão CLASSIFICAR e **erros** (digitação, espessura fora da tolerância) |
| 🟡 Amarelo | **Todo aviso**, inclusive tolerância não avaliada (fundo amarelo, letra preta) |
| 🟢 Verde | O que está certo: espessura dentro da tolerância e **contorno do resultado** quando há classificação |
| ⚪ Cinza | Dicas e faixas da pesquisa reversa |

O contorno verde do resultado é ligado pela propriedade Qt `classificado`. Assim a regra fica no
estilo, não espalhada pelo código.

## Decisão — ícone e versão
- Ícone = símbolo do logo da MG, sem letras (`icone_mg.png` / `.ico`, na pasta de dados). No Windows,
  `SetCurrentProcessExplicitAppUserModelID` evita que a barra de tarefas mostre o ícone do Python.
  O `.ico` será usado no PyInstaller (Fase 7).
- **Versionamento semântico** `MAIOR.MENOR.CORREÇÃO`, num lugar só (`__version__`; o
  `pyproject.toml` lê de lá), mostrado no título e no canto superior direito. Durante o
  desenvolvimento, `0.x` com **MENOR = fase do roteiro** (Fase 5 = `0.5.0`). `1.0.0` = primeira
  versão em uso na empresa.

## Decisão — resultado sem grau (regras do usuário)
- **ZC como último recurso de GI/GA:** se nenhum grau da NBR 7008-2 nem da 7008-3 é atendido, o
  resultado é fixo, `ZC - Z___` / `ZC - ZF___`, **sem avaliar a norma** (nem a química do ZC), com
  o aviso "Nenhum grau da NBR 7008-2 nem da NBR 7008-3 atendido" (o material pode ser duro ou mole
  demais). Faz o mesmo papel do `1006/08` nos sem revestimento. Dentro da sequência, o ZC continua
  **sem sair** da tabela da 7008-2.
- Na folha de classificações, o resultado fixo (`SemGrau`) aceita `resultado` e `aviso` juntos.
- **Camada não informada:** revestido (GI, GA, EG) com camada vazia ou zero → resultado sem camada
  e aviso "Camada não informada".
- **Tolerância de resultado sem grau** (ZC de GI/GA, `1006/08 EG`) → **NBR 7013 Tabela 2**, a mesma
  do grau sem LE definido. Isso substitui o "não avalia" do ADR 0008 para esses casos.

## Consequências
- ✅ Regra de negócio continua toda no motor; a janela é fina e testada sem abrir na tela.
- ✅ Cores com significado fixo: vermelho só aparece quando há ação principal ou problema.
- ✅ Todo GI/GA sai com resultado; o aviso deixa claro que é um resultado de último recurso.
- ⚠️ O padrão visual vale para todos os programas do usuário. Mudança aqui deve ser repetida
  nos outros.
- ⏭️ Histórico, lixeira e trava de edição (modo edição/consulta) chegam na Fase 6.

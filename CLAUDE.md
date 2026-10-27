# Classificação Automática

## Idioma
- Toda comunicação, comentários e documentação em português (pt-BR).

## Modo de trabalho
- O usuário está aprendendo: guiar **passo a passo**, explicar o porquê de cada etapa e deixar ele
  executar as partes simples. Uma etapa por vez, esperando confirmação.
- **Perguntar sempre que houver dúvida** sobre regra de norma ou comportamento — nunca supor.

## Estado atual
- Arquitetura **decidida** (2026-10-27). **Fases 0 e 1 concluídas** (branch `fase-1-dominio-yaml`).
  Próxima: **Fase 2 – Motor (TDD)** (ver "Roteiro").
- Fase 1 entregou: `dominio/propriedades.py` (enum `Propriedade`), `dominio/modelos.py` (pydantic),
  `normas/carregador.py` (`carregar_norma`, `ErroNorma`), `normas/conferir.py` (imprime a norma no
  formato das tabelas ABNT) e `dados/normas/nbr-5915-2.yaml` **conferida pelo usuário** (2026-10-27).
  Formato e regras de interpretação: ADR 0005.
- Ambiente: `.venv` criado; rodar sempre `.venv/Scripts/python -m pytest` / `-m ruff check .`.
- Permissões em `.claude/settings.json` (testes, ruff, git status/diff/log/add/commit liberados; push pergunta).
- Pendências restantes na seção "Pendências".

## Objetivo
Programa (MG Centro de Serviço) para **classificar materiais de aço (produtos planos)** a partir das
propriedades mecânicas e químicas digitadas pelo usuário, indicando a classificação (sigla/grau) conforme
as normas ABNT, além de verificar tolerância de espessura e mostrar normas correlatas.

## Material de referência (`normas_claude/`)
- Imagens das tabelas das normas (nome do arquivo = norma-parte-página):

| Norma | Produto | Graus | Conteúdo |
|---|---|---|---|
| NBR 5915-2:2013 | Laminado a frio – estampagem | EM, EP, EEP 1–4 | Química, mecânica, Erichsen (Tab. 3) |
| ~~NBR 5915-3:2013~~ | Frio – alta resistência | IS, IFAR | **Fora do escopo — ignorar** |
| ~~NBR 5915-4:2013~~ | Frio – bake hardening | BH | **Fora do escopo — ignorar** |
| ~~NBR 5915-5:2013~~ | Frio – refosforado | RP | **Fora do escopo — ignorar** |
| ~~NBR 5915-6:2013~~ | Frio – ARBL | ARBL | **Fora do escopo — ignorar** |
| NBR 5906 | Laminado a quente | EM, EP, EPA | Química, mecânica |
| NBR 7008-2:2021 | Zincado imersão – estampagem | ZC, ZE, ZEE 1–4 | Química, mecânica |
| NBR 7008-3:2021 | Zincado imersão – estrutural | ZAR-230 a ZAR-550 | Química, mecânica |
| NBR 11888 | Frio – tolerâncias | — | Tab. 11 (espessura, baixa resistência) |
| NBR 7013 | Zincado – tolerâncias | — | Tab. 1–4 (espessura × largura, por faixa de LE mín) |

- `classificações.pdf`: tabela de siglas de acabamento, indicação de camada e a relação
  **sigla ↔ norma ↔ acabamento ↔ normas correlatas** (EN, GMW, VW, HES, TSG, FG, MS...).
- `Equivalencia de normas de material.xlsx`: planilha de equivalência — fonte das normas correlatas,
  do autocompletar e da pesquisa reversa.
- `esboço da interface.pdf`: esboço à mão da tela (**apenas referência**; pode ser melhorado).

### Acabamentos e camada
- FF (frio), FQ (quente), FQ DO (quente decapado e oleado), GI ZN / GI ZM (zincado imersão, cristais
  normais/minimizados), GA ZF (zinco-ferro, Galvanew), EG (eletrolítico).
- Camada: GI → `Z___` (g/m², duas faces, ex. Z100); GA → `ZF___` (ex. ZF100); EG → `_/_` (g/m² por face, ex. 50/50).
- Formato da saída: sigla + camada, ex. `ZEE G2 - Z275` (GI), `EEP G1 EG 50/50`. Sem camada → só a sigla.

## Requisitos do usuário

### Regras de classificação
- **Grau mais nobre:** se o material atende a vários graus, mostrar **sempre o mais nobre**.
  Regra: **ordem das linhas da tabela da norma — quanto mais para baixo, mais nobre**
  (ex.: NBR 5915-2: EEP 4 > … > EP > EM; NBR 5906: EPA > EP > EM; NBR 7008-2: ZEE 4 > … > ZE > ZC). A ordem fica **explícita na base de normas** (lista por norma, na mesma
  sequência da tabela) e é conferida pelo usuário na transcrição.
- **Sequência de tabelas por acabamento** (passa para a próxima só se não atender nenhum grau da anterior;
  reprovação pode ser **mecânica ou química**):

  | Acabamento | 1ª tabela | 2ª tabela | Se não atender nenhuma |
  |---|---|---|---|
  | FF | NBR 5915-2 | — | `1006/08` |
  | FQ / FQ DO | NBR 5906 | — | `1006/08` |
  | EG | NBR 5915-2 (EM…EEP G3) | — | `1006/08 EG _/_` (teórico) |
  | GI ZN / GI ZM / GA ZF | NBR 7008-2 (ZC…ZEE 4) | NBR 7008-3 (ZAR) | aviso "material mais duro que o último ZAR" (teórico) |
- **EG (eletrolítico)** é classificado pela norma **sem revestimento** (NBR 5915-2, com NBR 16964 para o
  revestimento — **não é preciso transcrever a NBR 16964**), e a saída recebe `EG` + camada por face: ex. `EEP G3 EG 50/50`.
  Graus EG existentes na folha de classificações: EM, EP, EEP G1, EEP G2, EEP G3 (**não há EEP G4 EG**).
  EG que atende EEP G4 → resultado `EEP G3 EG` (mais nobre disponível para EG). EG que não atende nem
  EM → `1006/08 EG _/_` (caso teórico).
- `1010` **não** é usado como resultado.
- NBR 5915-3/-4/-5/-6 (IS, IFAR, BH, RP, ARBL) estão **fora do escopo** e são ignoradas.
- **Os candidatos de cada acabamento vêm da folha de classificações** (`classificações.pdf`): só pode
  ser resultado um grau que exista ali para aquele acabamento (FF, FQ, GI, GA, EG). Exceção: ZAR
  (não está na folha), com saída no formato `ZAR-230 - Z275` / `ZAR-230 - ZF100`.
- **Valores vazios:** classificar mesmo assim, **avisando quais valores estavam faltando**. Vazio é
  tratado como **zero** em todas as comparações (inclusive mínimos — ex.: Al vazio reprova Al mín).
- **Ignorar** propriedades que estão na norma mas não na interface (anisotropia r90/ΔR, encruamento n90,
  BH etc.) e entradas do usuário que a norma não exige (ex.: Lo80 % quando a norma só define Lo50).
- **Aviso de "quase passou" (fase 1, por regra):** se um grau mais nobre falhou por **uma única variável**,
  classificar no grau atendido mas avisar, ex.: "Seria EEP 3, mas o alongamento (32 < 34 mín) rebaixou".
- **Aviso por histórico (fase 2, machine learning):** quando houver registros suficientes, comparar com
  classificações parecidas já salvas e avisar se algum valor está fora do comum (outlier).

### Resultado
- O campo **RESULTADO** mostra **somente** a classificação NBR + camada (ex.: `EEP G2 - Z275`).
- Em campos separados: "De acordo com a norma NBR …", **normas correlatas** (da planilha de
  equivalência), avisos (valores faltando, "quase passou", outlier) e tolerância de espessura.
- Normas correlatas: ao passar o mouse, tooltip com o **fabricante/emissor** (prefixo da norma):

  | Prefixo | Fabricante / emissor | Confiança |
  |---|---|---|
  | HES | Honda (Honda Engineering Standard) | confirmado pelo usuário |
  | TSG | Toyota | confirmado pelo usuário |
  | GMW, GMW EMS ME | General Motors | alta |
  | VW | Volkswagen | alta |
  | MS 50002 | Stellantis (ex-Fiat Chrysler/FCA) | confirmado em pesquisa |
  | FG 528xx | Fiat (Stellantis) | **provável — confirmar** |
  | EN, DIN EN | Norma europeia (CEN/DIN) — não é montadora | alta |
  | JIS | Norma japonesa (JSA) — não é montadora | alta |
  | NBR | ABNT | alta |

### Pesquisa reversa
- Botão de pesquisa reversa: o usuário digita **qualquer norma** (NBR ou correlata, com autocompletar
  pela planilha de equivalência) e recebe os **valores/intervalos exigidos** de cada entrada da tela.

### Interface
- **Sempre em tela cheia**, sem espaços vazios; esboço é só referência.
- **Esquerda:** logo MG, "Classificação de Materiais"; acabamento (FQ DO, FF, GI ZN, GI ZM, EG);
  camada em g/m² (qualquer valor; vazio ou zero = sem revestimento).
- **Centro – mecânicas:** LE (MPa), LR (MPa), alongamento Lo50 % e Lo80 % (aceitar com ou sem "%",
  limpar após Enter), embutimento (mm); espessura nominal e real (mm) + largura (mm) → dentro/fora da
  tolerância (verde/vermelho), mostrando intervalo e norma usada.
- **Direita – químicas (%):** C, Mn, P, S, Al, Ni, Ti, V, Nb, Cr, Si, B, Mo. Ao passar o mouse sobre o
  símbolo, tooltip com o nome por extenso (C → Carbono, Mn → Manganês…).
- Botões: CLASSIFICAR, nova classificação, limpar valores, pesquisa reversa.

### Histórico e lixeira
- Aba de **histórico**: salvar classificações e pesquisar antigas.
- **Excluir** move para a aba **Lixeira** (exclusão lógica). Na lixeira o registro aparece igual ao do
  histórico e pode ser **restaurado** de volta ou **excluído permanentemente**.

### Tolerância de espessura
- **Zincados (EG, GA ZF, GI ZM, GI ZN):** NBR 7013 Tab. 1–4 — uma tabela para cada faixa de LE mín
  do grau; +0,01 mm para revestimento ≥ Z275.
- **Sem revestimento (FF, FQ, FQ DO):** NBR 11888 Tab. 11 (FQ usa a mesma tabela do FF).

## Arquitetura (decidida em 2026-10-27)
- **Python 3.12+**, interface **PySide6** (desktop Windows, `.exe` via PyInstaller), histórico em **SQLite**.
- Camadas independentes: **interface → motor → base de normas**; o motor não conhece a interface.
- **Base de normas em YAML** (dados, não código), validada ao carregar; notas de rodapé viram
  ajustes declarativos; ordem de nobreza explícita por norma.
- Comparações com `Decimal` (sem erro de arredondamento de `float`).
- Histórico atrás de uma classe `RepositorioHistorico` (permite trocar o banco no futuro).
- Estrutura: `src/classificador/{dominio,normas,motor,tolerancia,historico,interface}`, `tests/`,
  `docs/decisoes/` (ADRs), `dados/` (fora do Git).
- **Repositório GitHub é PÚBLICO:** `normas_claude/` e `dados/` (normas transcritas, casos reais) nunca
  são versionados. Testes versionados usam uma **norma fictícia**; testes com normas reais rodam só localmente.
- Sem VS Code: o usuário acompanha pelo terminal (diffs, `git diff`, `type arquivo`).
- **Não abrir `.md` no Bloco de Notas:** o Bloco de Notas do Windows 11 reformata Markdown ao salvar e
  insere escapes (`\_`, `\&`, `\[`, `\---`) que quebram links, badges, YAML e diagramas. Arquivos são
  editados pelo Claude Code; se aparecer alteração externa com esses escapes, conferir com `git diff`
  e restaurar.

## Roteiro (cada fase = branch + PR)
0. Fundação: `.gitignore`, ADRs, `pyproject.toml`, estrutura de pastas, `.claude/settings.json`.
1. Domínio + formato YAML; transcrever NBR 5915-2 (piloto) e conferir com o usuário.
2. Motor (TDD): `classificar()`, ajustes das notas, "quase passou", pesquisa reversa.
3. Demais normas (uma por commit, conferidas pelo usuário).
4. Tolerância (NBR 11888, NBR 7013).
5. Interface PySide6.
6. Histórico SQLite + lixeira + pesquisa.
7. Empacotamento `.exe`.
8. Aviso de outlier por machine learning (quando houver histórico suficiente).

## Regras das normas já identificadas (notas de rodapé)
- LE não definido → usar valor a 0,2 % de deformação.
- NBR 5915-2 nota b: espessura ≤ 0,70 mm e/ou planicidade especial → alongamento pode ser 2 unidades
  abaixo. **Não aplicada:** usuário decidiu usar a maior redução entre b e d (= sempre a nota d).
- NBR 5915-2 nota d: espessura < 0,5 mm → LE máx +40 MPa e alongamento −4; 0,50 ≤ e ≤ 0,70 → LE máx +20 MPa e alongamento −2
  (redução vale para Lo50 e Lo80).
- NBR 5915-2: Nb pode substituir Ti → **Ti+Nb ≤ 0,20 % só em EEP 3/4** (nos demais, Ti/Nb sem limite);
  B máx 0,0005 % se o comprador exigir (**não aplicado**); EEP 4 não substitui EEP 3 sem autorização
  (**aviso informativo** do grau).
- NBR 5915-2: LE do EEP 4 impresso "120 – 160 (5)" → o "(5)" é ignorado. Tab. 3 em 0,90 mm (EEP 3/4)
  transcrita como impressa, embora fuja da progressão.

## Regras de interpretação decididas (ver ADR 0005)
- Notas de rodapé e tabela de embutimento usam a **espessura nominal**.
- Embutimento: linha de espessura **mais próxima** (empate → linha maior); fora da faixa da tabela →
  não avaliado; **embutimento vazio → não avaliado** (com aviso), exceção à regra "vazio = zero".
  EM (5915-2) não tem exigência de embutimento.
- Lo50 e Lo80: se a norma define os dois, **avaliar ambos**; se só um foi preenchido, o outro não é avaliado.
- Notas sobrepostas na mesma propriedade: vale a **maior redução**, sem acumular.
- Testes com valores de normas reais ficam em `dados/testes/` (fora do Git); `tests/` só usa a norma
  fictícia `tests/dados/norma-ficticia.yaml`.
- NBR 5906: e ≤ 2,0 mm → LE/LR máx +20 MPa e alongamento −3; decapado contínuo/laminação de
  acabamento → alongamento −1; EPA com 2,0 < e < 3,0 → LE máx +10 MPa; Lo = 50 mm é o padrão.
- NBR 7008-2/-3: revestimento zinco-ferro (GA) → alongamento −2.
- NBR 7008-2: ZC sem limites mecânicos; NBR 7013 considera para ZC o LE de ZE (260/360 MPa).
- Microligantes (Nb, Ti, V, Zr, Ta, B) — somatório máx 0,25 % (7008-3).
- Tolerância de espessura: +0,01 mm para revestimento ≥ Z275 (NBR 7013); bobinas com solda: dobro da
  tolerância nos 15 m das extremidades (NBR 11888).

## Pendências (decidir com o usuário)
1. Confirmar FG 528xx = Fiat (pesquisa não achou fonte pública).

## Decisões menores já tomadas
- Tolerância de espessura: usar sempre a coluna **normal** (não a restritiva).
- Folha de siglas = `classificações.pdf` (é imagem escaneada → transcrita para `dados/siglas.yaml`).

## Versionamento
- Git com repositório no GitHub (branch `main`), **público**.
- Fazer commits pequenos a cada etapa concluída, com mensagens em português.
- Commits locais e atualização do `README.md` podem ser feitos **sem pedir permissão**.
- **Manter o `README.md` atualizado a cada etapa**, no estilo dos outros repositórios do usuário
  (ex.: `jcesarmph-ui/SistemaCalibracao`): badges shields.io `for-the-badge` centralizados no topo,
  descrição centralizada, seções com emoji, tabela "Tecnologia | Aplicação no projeto", diagramas
  mermaid, `<details>` recolhíveis, roteiro com checkboxes e frase de fechamento em negrito.
- Sempre confirmar com o usuário antes de `git push`.
- Nunca versionar dados sensíveis, senhas, chaves de API, `normas_claude/` ou `dados/`.

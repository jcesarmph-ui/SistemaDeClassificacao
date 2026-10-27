# Classificação Automática

## Idioma
- Toda comunicação, comentários e documentação em português (pt-BR).

## Modo de trabalho
- O usuário está aprendendo: guiar **passo a passo**, explicar o porquê de cada etapa e deixar ele
  executar as partes simples. Uma etapa por vez, esperando confirmação.
- **Perguntar sempre que houver dúvida** sobre regra de norma ou comportamento — nunca supor.

## Estado atual
- Arquitetura **decidida** (2026-10-27). **Fases 0 a 3 concluídas** (Fase 3: branch `fase-3-normas`,
  PR para a `main`). Próxima: **Fase 4 – Tolerância de espessura** (NBR 11888, NBR 7013).
- Fase 3 entregou: NBR 7008-2, 7008-3 e 5906 em `dados/normas/` (**conferidas pelo usuário**);
  notas com `motivo`, `acabamentos` e `remover` (ADR 0007); `dados/correlatas.yaml` (união folha +
  planilha, **conferida pelo usuário**), `Correlatas`, `carregar_correlatas`, correlatas no
  `formatar()` e `pesquisar()` (pesquisa reversa por qualquer norma). O caso real GI → ZAR-250 passa.
- Fase 2 entregou o motor (`src/classificador/motor/`): `limites.py` (`limites_efetivos`),
  `avaliacao.py` (`avaliar_grau`), `classificar.py` (`classificar_na_norma` + recorte de graus
  disponíveis), `sequencia.py` (`classificar` por acabamento), `saida.py` (`formatar`) e `reversa.py`
  (`requisitos`); `dominio/amostra.py` (`Acabamento`, `Amostra`); folha de classificações em
  `dados/folha-classificacoes.yaml` (conferida pelo usuário). Regras: ADR 0006.
- Casos reais em `dados/casos/*.yaml`, rodados por `dados/testes/test_casos_reais.py` (pulam enquanto
  a norma não estiver transcrita). Só 1 caso (GI → ZAR-250 - Z100); usuário não tem mais certificados
  à mão — não pedir de novo.
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
- A camada sai **exatamente como digitada** (113 → `Z113`); o usuário é instruído a usar o nominal
  (100 ou 275), não o medido do certificado. EG: digita um número só (por face) → `50` sai `50/50`.

## Requisitos do usuário

### Regras de classificação
- **Grau mais nobre:** se o material atende a vários graus, mostrar **sempre o mais nobre**.
  Regra: **ordem das linhas da tabela da norma — quanto mais para baixo, mais nobre**
  (ex.: NBR 5915-2: EEP 4 > … > EP > EM; NBR 5906: EPA > EP > EM; NBR 7008-2: ZEE 4 > … > ZE). A ordem fica **explícita na base de normas** (lista por norma, na mesma
  sequência da tabela) e é conferida pelo usuário na transcrição.
  GI/GA: **todos os ZAR (7008-3) são mais nobres que os graus da 7008-2** (ZE < ZEE 1…4 < ZAR-230 … ZAR-550).
- **ZC nunca é resultado** (decisão do usuário, 2026-10-27): se o material não atende pelo menos ZE na
  7008-2, vai direto para a 7008-3.
- **Sequência de tabelas por acabamento** (passa para a próxima só se não atender nenhum grau da anterior;
  reprovação pode ser **mecânica ou química**):

  | Acabamento | 1ª tabela | 2ª tabela | Se não atender nenhuma |
  |---|---|---|---|
  | FF | NBR 5915-2 | — | `1006/08` |
  | FQ / FQ DO | NBR 5906 | — | `1006/08` |
  | EG | NBR 5915-2 (EM…EEP G3) | — | `1006/08 EG _/_` (teórico) |
  | GI ZN / GI ZM / GA ZF | NBR 7008-2 (ZE…ZEE 4) | NBR 7008-3 (ZAR) | aviso "material mais duro que o último ZAR" (teórico) |
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
- **Comparação exata**, sem arredondar o valor digitado às casas da norma (0,0074 > 0,007 → reprova).
- **Valores vazios:** classificar mesmo assim, **avisando quais valores estavam faltando** — só os campos
  que a norma usada **exige** (Ni vazio não gera aviso na 5915-2): os exigidos pelo **grau do resultado**
  + os vazios que, valendo zero, **barraram um grau mais nobre**. Vazio é
  tratado como **zero** em todas as comparações (inclusive mínimos — ex.: Al vazio reprova Al mín).
- **Ignorar** propriedades que estão na norma mas não na interface (anisotropia r90/ΔR, encruamento n90,
  BH etc.) e entradas do usuário que a norma não exige (ex.: Lo80 % quando a norma só define Lo50).
- **Aviso de "quase passou" (fase 1, por regra):** se um grau mais nobre falhou por **uma única variável**,
  classificar no grau atendido mas avisar, ex.: "Seria EEP 3, mas o alongamento (32 < 34 mín) rebaixou".
  Avisa **só o mais nobre** desses graus, **dentro da tabela que deu o resultado**; Lo50 e Lo80 contam
  como **variáveis separadas**; vale também quando o resultado é `1006/08`.
- **Aviso por histórico (machine learning, Fase 8):** quando houver registros suficientes, comparar com
  classificações parecidas já salvas e avisar se algum valor está fora do comum (outlier). **Só alerta —
  nunca muda a classificação**, que é sempre por regra da norma (explicável e determinística).
- **Casos reais** (certificados já classificados pela empresa) ficam em `dados/casos/` e viram testes
  locais (nunca no Git nem em arquivo versionado). 1º caso: certificado GI em `normas_claude/` (PDF
  "CQ …"), classificado pela empresa como ZAR-250 — confirma ZC fora, ZE reprovado por LE e queda
  para a 7008-3. Testável ao fim da Fase 3.

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
- **Registro de divergências** (melhoria contínua): no histórico, o usuário pode marcar "a classificação
  correta era outra" e escrever o motivo. As divergências formam uma lista para revisão — cada uma vira
  correção no YAML/regra + caso de teste.

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
6. Histórico SQLite + lixeira + pesquisa + registro de divergências.
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
- Lo50 e Lo80: se a norma define os dois, **avaliar ambos**; se só um foi preenchido, o outro não é
  avaliado, mas **gera aviso de que faltou** ("Valores não informados (não avaliados)"). Na prática:
  NBR 5915-2 (FF e EG) e sem revestimento exigem Lo50 e Lo80; 7008-2/-3 (GI/GA) só têm Lo50, então
  Lo80 vazio nunca gera aviso. Embutimento vazio entra no mesmo aviso.
- Notas sobrepostas na mesma propriedade: do **mesmo motivo** (ex.: espessura) vale a **maior
  redução**, sem acumular; de **motivos diferentes** (espessura + zinco-ferro) **somam**.
- Testes com valores de normas reais ficam em `dados/testes/` (fora do Git); `tests/` só usa a norma
  fictícia `tests/dados/norma-ficticia.yaml`.
- NBR 5906 (código **sem ano**: `NBR 5906`): nota a e ≤ 2,0 mm → LE/LR máx +20 MPa e alongamento −3;
  nota c EPA com 2,0 < e < 3,0 → LE máx +10 MPa; e ≥ 3,0 mm → Lo50 da 3ª coluna (EM 30, EP 34,
  EPA 35) e **Lo80 ignorado**; nota b (decapado contínuo −1) **não aplicada**; Lo = 50 mm é o padrão.
- NBR 7008-2/-3: nota b e < 0,70 mm → alongamento −2 (planicidade ignorada); nota c GA ZF →
  alongamento −2 (**soma** com a b).
- NBR 7008-2: ZC sem limites mecânicos (e nunca é resultado). LR só máximo.
- NBR 7008-3: microligantes Nb + Ti + V + B ≤ 0,25 % (Zr e Ta da nota não estão na tela). ZAR-550 sem
  alongamento. LE e LR só mínimo.

## Normas correlatas (decididas na Fase 3)
- Fonte: **união** da folha de classificações e da planilha (aba 2, mais completa), sem indicar a
  origem; divergências aparecem as duas (5906: DD11 e DD12, HR0 e HR1, FG 52806 e FG 52807).
- Na tela: lista simples separada por vírgula junto do resultado. EN 10152 só no EG.
- Graus sem revestimento recebem as colunas "sem" + "com ou sem revestimento" da planilha; zincados,
  "com" + "com ou sem". ZAR (7008-3) não têm correlatas. NBR 6656 (LNE) não tem equivalências.
- **Revestimentos nunca se misturam num grupo:** grau sem revestimento e seu equivalente revestido
  (ex.: BH-180 e ZARBH-180) ficam em grupos separados; colunas "com ou sem" entram nos dois.
  Exceção decidida pelo usuário: o **EG** mostra as correlatas do grau FF + EN 10152 (igual à
  caixa da folha de classificações).
- Fora do escopo (IF, BH, ARBL): só equivalências na pesquisa reversa, sem valores exigidos.
- ARBL: a aba 1 tem "LAC420480T" e "LAC550Y620Y" (erros); usada a forma da aba 2.
- Arquivo mantido como YAML (`dados/correlatas.yaml`), gerado uma vez a partir das duas fontes — o
  usuário pediu simplicidade; se quiser que o programa leia o .xlsx direto, rever.
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

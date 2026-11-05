# Sistema de Classificação Automática de Aços Planos

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/PySide6-Qt-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PySide6"/>
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/>
  <img src="https://img.shields.io/badge/YAML-CB171E?style=for-the-badge&logo=yaml&logoColor=white" alt="YAML"/>
  <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic"/>
  <img src="https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white" alt="scikit-learn"/>
  <img src="https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white" alt="NumPy"/>
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest"/>
  <img src="https://img.shields.io/badge/Ruff-D7FF64?style=for-the-badge&logo=ruff&logoColor=black" alt="Ruff"/>
  <img src="https://img.shields.io/badge/PyInstaller-.exe-4B8BBE?style=for-the-badge&logo=python&logoColor=white" alt="PyInstaller"/>
  <img src="https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"/>
  <img src="https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white" alt="Git"/>
  <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"/>
  <img src="https://img.shields.io/badge/Claude_Code-D97757?style=for-the-badge&logo=claude&logoColor=white" alt="Claude Code"/>
</p>
<p align="center">
  <img src="https://img.shields.io/badge/status-em_uso_na_empresa-brightgreen?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/versão-1.0.0-blue?style=flat-square" alt="Versão"/>
  <img src="https://img.shields.io/badge/normas-ABNT-009739?style=flat-square" alt="Normas ABNT"/>
  <img src="https://img.shields.io/badge/idioma-pt--BR-green?style=flat-square" alt="Idioma"/>
</p>

<p align="center">
  Aplicação desktop da <b>MG Centro de Serviços</b> que classifica aços planos — laminados a frio, a quente e
  zincados — a partir das propriedades mecânicas e químicas, indicando o grau conforme as normas ABNT.
  Hoje <b>em uso na empresa</b> (versão 1.0.0), com histórico compartilhado na rede e avisos de
  <b>machine learning</b> aprendidos com o próprio histórico.
</p>

<p align="center">
  <a href="#-visão-geral">Visão Geral</a> •
  <a href="#-em-números">Em números</a> •
  <a href="#-telas">Telas</a> •
  <a href="#-funcionalidades">Funcionalidades</a> •
  <a href="#-como-a-classificação-funciona">Como funciona</a> •
  <a href="#️-arquitetura">Arquitetura</a> •
  <a href="#-modelo-de-dados">Modelo de dados</a> •
  <a href="#️-como-foi-desenvolvido">Desenvolvimento</a> •
  <a href="#-história-das-fases">História</a> •
  <a href="#-estrutura-do-repositório">Estrutura</a>
</p>

---

## 📌 Visão Geral

Classificar uma bobina de aço significa comparar dezenas de valores — limite de escoamento, resistência,
alongamento, carbono, manganês, alumínio… — com as tabelas de várias normas, aplicando notas de rodapé
que mudam os limites conforme a espessura e o revestimento. Feito à mão, o processo é lento e sujeito a erro.

Este sistema automatiza essa comparação: o usuário digita os valores do certificado e recebe a
classificação no formato usado no dia a dia, por exemplo:

| Acabamento | Exemplo de resultado |
|---|---|
| Laminado a frio (FF) | `EEP G2` |
| Zincado por imersão (GI) | `ZEE G2 - Z275` |
| Zinco-ferro (GA) | `ZE - ZF100` |
| Eletrolítico (EG) | `EEP G3 EG 50/50` |

| ❌ Problema | 💡 Solução | ✅ Resultado |
|---|---|---|
| Cada certificado comparado **à mão** com as tabelas de várias normas, com notas de rodapé que mudam os limites pela espessura e pelo revestimento. | **Motor de regras** que testa todos os graus da norma certa para o acabamento e aplica as notas automaticamente. | Classificação em **~0,1 ms**, sempre no **grau mais nobre** atendido, com a norma usada. |
| Um grau perdido por um único valor passava despercebido; campos em branco também. | **Avisos** de "quase passou" e de valores não informados junto do resultado. | Quem classifica vê **por que** o material não subiu de grau e o que faltou digitar. |
| Tolerância de espessura e normas equivalentes (montadoras) consultadas em outras tabelas. | **Tolerância** (NBR 11888 / NBR 7013) e **normas correlatas** na mesma tela, mais a **pesquisa reversa**. | Dentro/fora em verde/vermelho, com o intervalo; qualquer norma vira a lista de valores exigidos. |
| Erro de digitação que a norma aceita (ex.: LR 29 em vez de 290) e erros que já aconteceram antes. | **Histórico** compartilhado + **divergências** + **machine learning** que compara com o que já foi salvo. | Aviso amarelo de valor fora do comum ou de caso parecido com uma divergência — **sem nunca mudar o resultado**. |
| Uso por mais de um computador, sem servidor nem TI. | Programa e banco SQLite numa **pasta comum da rede**, com lançador que copia o programa para cada PC. | Abre em **1–2 s** pela rede; atualizar = trocar uma pasta. |

```mermaid
mindmap
  root((Classificação de Materiais))
    Classificar
      Grau mais nobre
      Notas de rodapé
      Resultado + camada
      Quase passou
      Valores não informados
    Normas
      NBR 5915-2
      NBR 5906
      NBR 7008-2 e 7008-3
      Correlatas de montadoras
      Pesquisa reversa
    Tolerância
      NBR 11888
      NBR 7013
      Dentro ou fora
    Histórico
      Salvar com volume
      Pesquisa por texto livre
      Lixeira
      Divergências
    Machine learning
      Fora do comum
      Caso parecido
      Só avisa
    Rede
      Lançador com cópia local
      Backup diário
      Duas pessoas ao mesmo tempo
```

### 🎯 Objetivos

| | Objetivo |
|---|---|
| ⚙️ | Automatizar a comparação dos certificados com as normas ABNT. |
| 🏅 | Indicar sempre o grau mais nobre atendido, no formato usado no dia a dia. |
| ⚠️ | Explicar o resultado: o que rebaixou o grau, o que faltou e quais limites mudaram. |
| 📏 | Verificar a tolerância de espessura na mesma tela. |
| 🗂️ | Guardar um histórico único e pesquisável para toda a equipe. |
| 🔁 | Transformar cada erro encontrado em correção e caso de teste (melhoria contínua). |
| 🤖 | Usar o histórico para avisar o que parece errado, sem tirar da norma a decisão. |

## 📊 Em números

| | Número | O que significa |
|---|---|---|
| 🧪 | **291 testes automáticos** (+ 37 locais) | Motor, normas, tolerância, histórico, ML e tela testados com uma norma fictícia; os 37 locais usam as normas reais e ficam fora do GitHub. |
| 🐍 | **~4.000 linhas** de código + **~2.800** de testes | Programa em camadas: a regra de negócio não conhece a tela. |
| 🔀 | **10 pull requests** em **9 fases** (0 a 8) | Cada fase numa branch própria, revisada e aprovada antes de juntar. |
| 🏷️ | **1 versão entregue** (`v1.0.0`) | Versionamento semântico, versão visível na tela; `0.x` durante o desenvolvimento. |
| 📝 | **12 decisões de arquitetura** (ADRs) | Do formato das normas em YAML ao machine learning. |
| 📚 | **4 normas de classificação, 22 graus** + **2 de tolerância** | Transcritas em YAML e conferidas linha a linha pelo autor. |
| ⚡ | **~0,1 ms** para classificar · **~60 ms** para carregar as normas | Medido no próprio projeto. |
| 🚀 | **1–2 s** para abrir pela rede | Lançador com cópia local (1ª abertura 1,6 s, seguintes 1,0 s). |
| 🤖 | **0 alarmes falsos** em 340 classificações | Demonstração com histórico fictício: o aviso de "fora do comum" não disparou nas classificações normais. |

## 📸 Telas

> Imagens geradas com um **histórico 100% fictício** (volumes, pessoas, computadores, datas e
> valores inventados), sem nenhuma informação real.

<p align="center">
  <img src="docs/telas/01_classificar.png" alt="Tela Classificar: zincado GI classificado como ZEE G2 - Z275" width="100%"/>
  <br/><em>Classificar: resultado com a camada (contorno verde), norma usada, normas correlatas e
  tolerância dentro (verde). O aviso amarelo vem do machine learning: um caso parecido já teve
  divergência registrada.</em>
</p>

<table>
  <tr>
    <td width="50%" align="center">
      <img src="docs/telas/02_pesquisa_reversa.png" alt="Pesquisa reversa da norma DC04"/>
      <br/><em>Pesquisa reversa: digitada uma correlata (DC04), aparecem o grau NBR equivalente e,
      ao lado de cada campo, a faixa exigida.</em>
    </td>
    <td width="50%" align="center">
      <img src="docs/telas/03_historico.png" alt="Aba Histórico: lista de classificações salvas e detalhes do registro"/>
      <br/><em>Histórico: lista (data/hora, volume, resultado) e, ao lado, o registro completo como
      saiu na hora — com avisos, tolerância e valores digitados.</em>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="docs/telas/04_divergencias.png" alt="Aba Divergências: classificação correta, motivo e o registro original"/>
      <br/><em>Divergências: cada uma mostra a classificação correta, o motivo e o registro
      original, até ser marcada como resolvida.</em>
    </td>
    <td width="50%" align="center">
      <img src="docs/telas/05_ml_fora_do_comum.png" alt="LR 29 digitado no lugar de 290: a norma aceita, o ML avisa que está fora do comum"/>
      <br/><em>Machine learning: digitaram LR 29 em vez de 290. A norma só limita o máximo do LR
      e aceita, mas o ML compara com as classificações salvas do mesmo grau e avisa.</em>
    </td>
  </tr>
</table>

<sub>Vermelho só no botão principal e em erros, amarelo em avisos e verde no que está certo
(tolerância dentro e contorno do resultado).</sub>

## ✨ Funcionalidades

- 🔎 **Classificação automática** — sempre no **grau mais nobre** atendido.
- ⚠️ **Avisos inteligentes** — valores não informados e "quase passou"
  (*"Seria EEP G3, mas o alongamento rebaixou"*).
- 📏 **Tolerância de espessura** — dentro/fora (verde/vermelho), com o intervalo e a norma usada.
- 🔗 **Normas correlatas** — equivalências de montadoras (Honda, Toyota, GM, VW, Stellantis…) com
  identificação do fabricante ao passar o mouse.
- ↩️ **Pesquisa reversa** — digite qualquer norma e veja os intervalos exigidos.
- 🗂️ **Histórico** — cada classificação salva com o volume, quem salvou, em qual PC e com qual
  versão do programa; pesquisa por texto livre em tudo o que foi salvo.
- 🗑️ **Lixeira** — excluir não apaga: o registro pode ser restaurado ou excluído de vez, sempre com
  confirmação.
- 🔁 **Melhoria contínua** — quando uma classificação salva estava errada, registra-se a
  **divergência** (classificação correta + motivo); cada uma vira correção de regra e caso de teste.
- 🛡️ **Uso em rede sem servidor** — banco SQLite numa pasta comum, com backup diário automático;
  duas pessoas podem classificar e salvar ao mesmo tempo.
- 🚀 **Executável para Windows** — não precisa instalar nada; mora na pasta da rede, mas abre em
  1–2 segundos porque cada PC guarda uma cópia local do programa.
- 🤖 **Machine learning** — aprende com o histórico e com as divergências e **avisa** quando um
  valor está fora do comum para o grau (ex.: erro de digitação que a norma aceita) ou quando o
  material é parecido com um caso que já teve divergência. Aprende na hora, sem mudar código; só
  alerta — a classificação continua sempre pela regra da norma.

<details>
<summary><b>📚 Normas cobertas</b> (clique para expandir)</summary>

| Norma | Produto | Graus |
|---|---|---|
| NBR 5915-2 | Laminado a frio — estampagem | EM, EP, EEP G1–G4 |
| NBR 5906 | Laminado a quente | EM, EP, EPA |
| NBR 7008-2 | Zincado por imersão — estampagem | ZE, ZEE G1–G4 (ZC na norma, nunca é resultado) |
| NBR 7008-3 | Zincado por imersão — estrutural | ZAR |
| NBR 11888 | Tolerâncias — sem revestimento | — |
| NBR 7013 | Tolerâncias — zincados | — |

</details>

## 🧠 Como a classificação funciona

```mermaid
flowchart TD
    A[Valores digitados<br/>mecânicos + químicos] --> B{Acabamento}
    B -->|FF| C[NBR 5915-2]
    B -->|FQ / FQ DO| D[NBR 5906]
    B -->|EG| E[NBR 5915-2<br/>EM a EEP G3]
    B -->|GI / GA| F[NBR 7008-2<br/>ZE a ZEE G4]
    F -->|nenhum grau atende| G[NBR 7008-3 · ZAR]
    C & D & E & F & G --> H[Testa todos os graus<br/>e aplica as notas de rodapé]
    H --> I[Escolhe o grau mais nobre<br/>= linha mais abaixo na tabela]
    I --> J[Resultado + camada<br/>ex.: ZEE G2 - Z275]
    C & D & E -->|nenhum grau atende| K[1006/08]
```

<details>
<summary><b>⚠️ Avisos que acompanham o resultado</b></summary>

```text
RESULTADO: ZEE G2 - Z275
De acordo com a norma NBR 7008-2:2021
Normas correlatas: EN 10346 DX54D, EN 10327 DX54D, GMW 2M CR2, FG 52806 FEP02, MS 50002 CR02, …
🟢 Dentro da tolerância: 0,74 a 0,86 mm (± 0,06, com +0,01 do revestimento ≥ 275 g/m²) — NBR 7013, Tabela 1
⚠ Seria ZEE G3, mas o C (0,04 > 0,01 máx) rebaixou
⚠ Valores não informados (não avaliados): alongamento Lo80
⚠ Limites ajustados pela espessura: Tabela 2, nota d
```

| Aviso | Quando aparece |
|---|---|
| **Quase passou** | Um grau mais nobre falhou por uma única variável |
| **Valores não informados** | Campo exigido ficou vazio (vale zero, ou não é avaliado no caso de embutimento/alongamento) |
| **Grau inexistente no acabamento** | Ex.: atende EEP G4, mas não existe EEP G4 EG → sai EEP G3 EG |
| **Limites ajustados** | Uma nota de rodapé mudou os limites (espessura ou zinco-ferro) |
| **Aviso do grau** | Observação da norma, ex.: EEP G4 não substitui EEP G3 sem autorização |

As **normas correlatas** (folha de classificações + planilha de equivalência) aparecem numa
lista simples junto do resultado.

A **pesquisa reversa** faz o caminho inverso: digitada qualquer norma — NBR ou correlata, como
`DC04` ou `GMW 2M CR3` — e, se quiser, a espessura, mostra o que cada campo da tela precisa ter,
usando os mesmos limites do classificador.

</details>

## 🔁 Melhoria contínua

Uma classificação errada nunca passa em silêncio: ela vira dado organizado para corrigir o programa
— e, no futuro, para o machine learning avisar em casos parecidos.

```mermaid
flowchart LR
    A[Classificar<br/>e salvar] --> B[(Histórico)]
    B --> C{Estava<br/>certo?}
    C -->|não| D[Registrar divergência<br/>correta + motivo]
    D --> E[Corrigir norma/regra<br/>+ caso de teste]
    E --> F[Nova versão<br/>marcada como resolvida]
    D -.->|aprende na hora| G[🤖 ML avisa em<br/>casos parecidos]
```

<details>
<summary><b>🤖 Como o machine learning decide avisar</b></summary>

```mermaid
flowchart TD
    A[CLASSIFICAR] --> B[Resultado pela norma<br/>nunca muda]
    A --> H[(Histórico<br/>+ divergências)]
    H --> C{Caso parecido com<br/>uma divergência?}
    H --> D{Valor muito fora<br/>do comum no grau?}
    C -->|mesmo acabamento e grau,<br/>valores dentro das margens| E[⚠ Histórico: em um caso<br/>parecido, a correta foi…]
    D -->|longe da mediana,<br/>a partir de 20 registros| F["⚠ Histórico: LR 29 fora<br/>do comum, normal 270 a 311"]
```

| Aviso | Como funciona |
|---|---|
| **Caso parecido** | Busca de vizinhos mais próximos (`NearestNeighbors`, scikit-learn) entre os casos que tiveram divergência: mesmo acabamento, mesmo grau e cada valor dentro da sua margem (ex.: LE ± 20 MPa, químicos ± 25 %). Mostra o mais próximo, com a classificação correta e o motivo. |
| **Fora do comum** | Estatística robusta por acabamento e grau: mediana e faixa central de cada valor, que não se deixam enganar por um erro antigo salvo. Só avisa o que está muito fora, para não virar ruído. |

Numa demonstração com histórico fictício de 340 classificações, o aviso de "fora do comum" não
deu **nenhum alarme falso** nas classificações normais.

</details>

## 🏛️ Arquitetura

Camadas independentes: a interface **não contém regras** e o motor **não conhece a interface** — por isso
o motor é testado automaticamente, sem abrir nenhuma janela.

```mermaid
flowchart LR
    UI[🖥️ Interface<br/>PySide6] --> M[⚙️ Motor de<br/>classificação]
    M --> N[(📄 Normas<br/>YAML)]
    UI --> R[🗄️ Repositório<br/>do histórico]
    R --> H[(SQLite<br/>+ backup diário)]
```

<details>
<summary><b>🚀 Distribuição na rede (sem servidor)</b></summary>

Na pasta da rede aparece um único arquivo: o **lançador**. Ele copia o programa para o PC uma vez
por versão e abre a cópia local; normas e histórico continuam na rede, iguais para todos.

```mermaid
flowchart LR
    subgraph REDE[📁 Pasta comum da rede]
        L[Lançador<br/>.exe]
        P[programa<br/>oculta]
        D[(dados<br/>normas + histórico)]
    end
    subgraph PC[💻 Cada computador]
        C[Cópia local<br/>do programa]
    end
    L -->|1ª vez de cada versão| P
    P -->|copia| C
    L -->|abre em 1–2 s| C
    C <-->|lê normas,<br/>grava histórico| D
```

- **Atualizar** = trocar a pasta do programa; cada PC copia a versão nova sozinho.
- **Norma corrigida** = trocar o arquivo YAML, sem gerar o programa de novo.
- Cópia segura: uma cópia interrompida nunca é usada e duas aberturas ao mesmo tempo não se
  atrapalham.

</details>

| Tecnologia | Aplicação no projeto |
|---|---|
| Python | Motor de regras, validação e lógica da aplicação. |
| PySide6 (Qt) | Interface desktop em tela cheia, com abas e tooltips. |
| SQLite | Histórico, lixeira e divergências numa pasta de rede (journal tradicional, backup diário). |
| scikit-learn + NumPy | Machine learning: casos parecidos com divergências e valores fora do comum. |
| YAML + Pydantic | Base de normas legível e validada ao carregar. |
| Pytest + Ruff | Testes automáticos e qualidade do código. |
| PyInstaller | Executável para Windows, com lançador que copia o programa para o PC e abre rápido. |
| Git + GitHub | Controle de versão e documentação. |
| Claude Code | Desenvolvimento assistido por IA: regras definidas e cada etapa aprovada pelo autor. |

<details>
<summary><b>📝 Decisões de arquitetura (ADRs)</b></summary>

| ADR | Decisão |
|---|---|
| [0001](docs/decisoes/0001-python-pyside6.md) | Python + PySide6 para o programa desktop |
| [0002](docs/decisoes/0002-sqlite-historico.md) | SQLite para o histórico (com lixeira) |
| [0003](docs/decisoes/0003-repositorio-publico-dados-fora-do-git.md) | Repositório público com dados das normas fora do Git |
| [0004](docs/decisoes/0004-normas-em-yaml.md) | Base de normas em arquivos YAML |
| [0005](docs/decisoes/0005-formato-yaml-normas.md) | Formato detalhado do YAML e regras de interpretação |
| [0006](docs/decisoes/0006-motor-de-classificacao.md) | Motor de classificação: etapas e regras |
| [0007](docs/decisoes/0007-notas-por-motivo-e-correlatas.md) | Notas por motivo/acabamento e normas correlatas |
| [0008](docs/decisoes/0008-tolerancia-de-espessura.md) | Tolerância de espessura (NBR 11888 e NBR 7013) |
| [0009](docs/decisoes/0009-interface-e-resultado-sem-grau.md) | Interface (layout em faixas, cores, versão) e resultado sem grau (ZC de último recurso) |
| [0010](docs/decisoes/0010-historico-lixeira-e-divergencias.md) | Histórico, lixeira e divergências (SQLite em rede, abas, melhoria contínua) |
| [0011](docs/decisoes/0011-executavel-e-entrega-na-rede.md) | Executável e entrega na pasta da rede (lançador com cópia local) |
| [0012](docs/decisoes/0012-machine-learning-avisos-do-historico.md) | Machine learning: avisos aprendidos do histórico (nunca muda o resultado) |

</details>

## 💾 Modelo de dados

Dois tipos de dado: as **normas**, em arquivos YAML (dados, não código), e o **histórico**, num
banco SQLite na pasta da rede.

<details>
<summary><b>🧩 Modelo de dados de uma norma</b></summary>

Cada norma é um arquivo YAML validado ao carregar — exemplo completo em
[`tests/dados/norma-ficticia.yaml`](tests/dados/norma-ficticia.yaml).

```mermaid
classDiagram
    direction LR
    Norma "1" *-- "1..*" Grau : graus (último = mais nobre)
    Norma "1" *-- "0..*" Ajuste : notas de rodapé
    Norma "1" *-- "0..1" TabelaEmbutimento
    Grau "1" *-- "0..*" Limite : por propriedade
    Grau "1" *-- "0..*" Soma : ex. Ti + Nb
    Ajuste "1" *-- "1" FaixaEspessura : quando
    Ajuste "1" *-- "1..*" Variacao : efeito
    class Norma {
        codigo
        titulo
    }
    class Grau {
        sigla
        nome_na_norma
        avisos
    }
    class Limite {
        min
        max
    }
    class Soma {
        elementos
        max
    }
    class FaixaEspessura {
        min
        max
        min_inclusivo
        max_inclusivo
    }
    class Variacao {
        soma ao min
        soma ao max
    }
    class TabelaEmbutimento {
        linhas por espessura
        minimo por grau
    }
```

Erros de transcrição (campo com nome errado, chave repetida, `min > max`, grau inexistente…) são
apontados com **arquivo, linha e campo**:

```text
nbr-exemplo.yaml, linha 8 (graus → 1 → limites → LE): mínimo (280) maior que o máximo (140)
```

</details>

<details>
<summary><b>🗄️ Banco do histórico (SQLite)</b></summary>

```mermaid
erDiagram
    CLASSIFICACAO ||--o{ DIVERGENCIA : "pode ter"
    CLASSIFICACAO {
        int id PK
        text criado_em
        text usuario "usuário do Windows"
        text computador
        text versao_programa
        text volume "obrigatório"
        text acabamento
        json valores "campo da tela → texto digitado"
        text resultado "ex.: ZEE G2 - Z275"
        text norma
        json correlatas
        json avisos
        text tolerancia
        int tolerancia_dentro "1 dentro, 0 fora"
        text excluido_em "preenchido = na Lixeira"
        text excluido_por
    }
    DIVERGENCIA {
        int id PK
        int classificacao_id FK
        text correta
        text motivo
        text criado_em
        text usuario
        text computador
        text resolvida_em "preenchido = já corrigida"
        text resolvida_por
    }
```

- O registro guarda o resultado **como saiu na hora** (com avisos e tolerância) e é só leitura.
- **Exclusão lógica:** excluir só preenche `excluido_em`; a Lixeira restaura ou exclui de vez.
- O machine learning lê esse banco: registros com divergência entram com a **classificação correta**.

</details>

## 🛠️ Como foi desenvolvido

| Prática | Como foi aplicada |
|---|---|
| 🧭 **Fases com entrega** | Roteiro em 9 fases; cada uma numa **branch** com **pull request**, juntada só depois de aprovada. |
| 📋 **Normas conferidas pelo autor** | Cada norma transcrita para YAML foi impressa no formato das tabelas ABNT e conferida linha a linha antes de entrar no programa. |
| 🧪 **Testes primeiro no motor** | Motor de classificação escrito com testes antes do código, usando uma norma fictícia; casos reais rodam só localmente. |
| 📸 **Aprovação por foto** | Cada mudança de tela gerou "fotos" da janela (sem abri-la) para o autor aprovar antes de seguir. |
| 📝 **Decisões registradas** | Escolhas de arquitetura e regras de interpretação das normas em ADRs (`docs/decisoes/`). |
| 🏷️ **Versionamento semântico** | `0.x` durante o desenvolvimento (uma versão por fase), `1.0.0` na entrada em uso, tag Git por versão. |
| 🔒 **Dados protegidos** | Normas transcritas, casos reais e histórico ficam fora do repositório público; testes e fotos usam dados fictícios. |
| 🤖 **IA como ferramenta** | Desenvolvimento com Claude Code: o autor define as regras de negócio, revisa e aprova cada etapa. |

### 🗺️ Roteiro

- [x] **Fase 0** — Fundação: repositório, ADRs, ambiente Python, permissões do Claude Code
- [x] **Fase 1** — Modelo de dados, formato YAML validado e NBR 5915-2 transcrita e conferida
- [x] **Fase 2** — Motor de classificação (com testes primeiro): sequência por acabamento,
  "quase passou", valores faltando, saída formatada e pesquisa reversa
- [x] **Fase 3** — NBR 5906, 7008-2 e 7008-3 transcritas e conferidas; normas correlatas e pesquisa
  reversa por qualquer norma
- [x] **Fase 4** — Tolerância de espessura: NBR 11888 (Tab. 11) e NBR 7013 (Tab. 1–4) transcritas e
  conferidas; dentro/fora com intervalo e norma
- [x] **Fase 5** — Interface PySide6: tela em faixas simétricas, tema escuro com cores de significado
  fixo, classificação, tolerância, correlatas e pesquisa reversa na tela
- [x] **Fase 6** — Histórico em SQLite na rede (backup diário), abas Histórico, Divergências e
  Lixeira, pesquisa por texto livre e registro de divergências (melhoria contínua)
- [x] **Fase 7** — Executável para Windows na pasta da rede: lançador com cópia local (abre em
  1–2 s), dados ao lado do programa e teste com dois PCs salvando ao mesmo tempo
- [x] **Fase 8** — Machine learning: avisos de valores fora do comum e de casos parecidos com
  divergências já registradas (aprende na hora, nunca muda o resultado)
- [x] **Versão `1.0.0`** — primeira versão em uso na empresa (novembro de 2026)

## 📜 História das fases

O programa foi construído do zero, uma fase por vez, cada uma entregue e aprovada antes da
seguinte. Abaixo, o que cada fase trouxe.

<details>
<summary><b>🧱 Fases 0 e 1 — Fundação e formato das normas</b></summary>

- Repositório público com os dados das normas **fora do Git** (direitos autorais), ADRs desde o
  primeiro dia e ambiente Python com testes e verificação de código.
- Formato YAML das normas com validação ao carregar (erro aponta arquivo, linha e campo) e um
  comando que imprime a norma no formato das tabelas ABNT para conferência.
- NBR 5915-2 transcrita como piloto e conferida pelo autor.

</details>

<details>
<summary><b>⚙️ Fase 2 — Motor de classificação</b></summary>

- Sequência de tabelas por acabamento, grau mais nobre pela ordem das linhas da norma e notas de
  rodapé declarativas (espessura, zinco-ferro).
- Avisos de "quase passou" e de valores não informados; resultado sem grau (`1006/08`, ZC) quando
  nenhum grau atende.
- Pesquisa reversa: os mesmos limites do classificador, no caminho inverso.

</details>

<details>
<summary><b>📚 Fases 3 e 4 — Demais normas, correlatas e tolerância</b></summary>

- NBR 5906, 7008-2 e 7008-3 transcritas e conferidas; normas correlatas de montadoras e normas
  europeias unidas de duas fontes.
- Tolerância de espessura pela NBR 11888 (sem revestimento) e NBR 7013 (zincados), com o acréscimo
  do revestimento ≥ Z275.

</details>

<details>
<summary><b>🖥️ Fase 5 — Interface</b></summary>

- Tela em faixas simétricas, sempre maximizada, tema escuro com cores de significado fixo
  (vermelho = ação principal e erro, amarelo = aviso, verde = certo).
- Erros de digitação na área de avisos, sem janelas de alerta; roda do mouse só rola a tela.

</details>

<details>
<summary><b>🗂️ Fase 6 — Histórico, lixeira e divergências</b></summary>

- Banco SQLite preparado para pasta de rede (journal tradicional, espera quando ocupado, backup
  diário com as últimas 30 cópias).
- Abas Histórico, Divergências e Lixeira; pesquisa por texto livre; registro de divergências com
  classificação correta e motivo.

</details>

<details>
<summary><b>🚀 Fase 7 — Executável e entrega na rede</b></summary>

- Executável com PyInstaller e lançador que copia o programa para cada PC uma vez por versão
  (abre em 1–2 s), com normas e histórico na rede.
- Testado com dois computadores salvando ao mesmo tempo.

</details>

<details>
<summary><b>🤖 Fase 8 e versão 1.0.0 — Machine learning e entrada em uso</b></summary>

- Avisos de valor fora do comum (estatística robusta por grau) e de caso parecido com uma
  divergência (vizinhos mais próximos com scikit-learn); aprende na hora e nunca muda o resultado.
- Demonstração com histórico fictício e versão `1.0.0` em uso na empresa.

</details>

## 📁 Estrutura do Repositório

```text
SistemaDeClassificacao/
├── src/classificador/
│   ├── dominio/         # propriedades, amostra, modelos (norma, grau, folha de classificações)
│   ├── normas/          # carregador do YAML e comando de conferência
│   ├── motor/           # limites, avaliação, classificação, sequência, saída, pesquisa reversa
│   ├── tolerancia/      # tolerância de espessura (real × nominal)
│   ├── historico/       # banco SQLite, repositório, lixeira, divergências e backup
│   ├── aprendizado/     # machine learning: casos parecidos e valores fora do comum
│   ├── interface/       # janela PySide6 em abas (só mostra; as regras ficam no motor)
│   └── lancador.py      # lançador da rede: copia o programa para o PC e abre rápido
├── tests/               # testes automáticos
│   └── dados/           # norma, folha, correlatas e tolerância fictícias usadas nos testes
├── docs/decisoes/       # registros de decisões de arquitetura (ADRs)
├── docs/telas/          # fotos da tela (dados fictícios)
├── dados/               # NÃO versionado
│   ├── normas/          # normas transcritas (YAML)
│   ├── tolerancias/     # NBR 11888 e NBR 7013 transcritas (YAML)
│   ├── casos/           # certificados reais com a classificação esperada
│   ├── testes/          # testes com valores das normas reais
│   ├── folha-classificacoes.yaml
│   └── correlatas.yaml
├── pyproject.toml       # dependências e configuração das ferramentas
├── CLAUDE.md            # instruções do projeto para o Claude Code
└── README.md
```

## 🏅 Aplicações e Competências Demonstradas

| | Competência |
|---|---|
| 🐍 | Desenvolvimento de aplicações desktop em Python com PySide6. |
| ⚙️ | Motor de regras de negócio declarativo, com as normas como dados (YAML validado). |
| 🔬 | Interpretação de normas técnicas ABNT de aços planos (mecânica, química, tolerâncias). |
| 🤖 | Machine learning aplicado com responsabilidade: só alerta, explica o porquê e nunca decide. |
| 🗃️ | Persistência em SQLite numa pasta de rede, com exclusão lógica e backup diário. |
| 🚀 | Empacotamento e distribuição sem servidor (executável + lançador com cópia local). |
| 🧪 | Testes automatizados e arquitetura em camadas, com regras independentes da tela. |
| 🔁 | Melhoria contínua: cada erro registrado vira correção e caso de teste. |
| 🤝 | Uso de IA (Claude Code) como ferramenta de desenvolvimento, com o autor no controle das regras. |

## ⚖️ Direitos autorais

O conteúdo das normas ABNT é protegido e **não faz parte deste repositório**. As tabelas transcritas
ficam apenas na pasta local `dados/`, listada no `.gitignore`.

---

<p align="center">
  <b>Projeto de desenvolvimento de software aplicado à qualidade na indústria do aço, com foco em
  automação de processos, rastreabilidade e redução de erros de classificação.</b>
</p>

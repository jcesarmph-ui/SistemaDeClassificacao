# Sistema de Classificação Automática de Aços Planos

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/PySide6-Qt-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PySide6"/>
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/>
  <img src="https://img.shields.io/badge/YAML-CB171E?style=for-the-badge&logo=yaml&logoColor=white" alt="YAML"/>
  <img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic"/>
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
  <img src="https://img.shields.io/badge/status-em_desenvolvimento-yellow?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/fase-5_interface-blue?style=flat-square" alt="Fase"/>
  <img src="https://img.shields.io/badge/normas-ABNT-009739?style=flat-square" alt="Normas ABNT"/>
  <img src="https://img.shields.io/badge/idioma-pt--BR-green?style=flat-square" alt="Idioma"/>
</p>

<p align="center">
  Aplicação desktop da <b>MG Centro de Serviços</b> que classifica aços planos — laminados a frio, a quente e
  zincados — a partir das propriedades mecânicas e químicas, indicando o grau conforme as normas ABNT.
</p>

<p align="center">
  <a href="#-visão-geral">Visão Geral</a> •
  <a href="#-funcionalidades">Funcionalidades</a> •
  <a href="#-como-a-classificação-funciona">Como funciona</a> •
  <a href="#️-arquitetura">Arquitetura</a> •
  <a href="#-como-executar">Como executar</a> •
  <a href="#-roteiro">Roteiro</a>
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

## ✨ Funcionalidades

- 🔎 **Classificação automática** — sempre no **grau mais nobre** atendido.
- ⚠️ **Avisos inteligentes** — valores não informados e "quase passou"
  (*"Seria EEP G3, mas o alongamento rebaixou"*).
- 📏 **Tolerância de espessura** — dentro/fora (verde/vermelho), com o intervalo e a norma usada.
- 🔗 **Normas correlatas** — equivalências de montadoras (Honda, Toyota, GM, VW, Stellantis…) com
  identificação do fabricante ao passar o mouse.
- ↩️ **Pesquisa reversa** — digite qualquer norma e veja os intervalos exigidos.
- 🗂️ **Histórico** — classificações salvas e pesquisáveis, com **lixeira** (restaurar ou excluir de vez).
- 🔁 **Melhoria contínua** *(planejado)* — divergências apontadas pelo usuário viram correções de regra e
  novos casos de teste.
- 🤖 **Detecção de outliers** *(planejado)* — machine learning sobre o histórico para apontar valores
  fora do comum (só alerta; a classificação continua sempre pela regra da norma).

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

## 🏛️ Arquitetura

Camadas independentes: a interface **não contém regras** e o motor **não conhece a interface** — por isso
o motor é testado automaticamente, sem abrir nenhuma janela.

```mermaid
flowchart LR
    UI[🖥️ Interface<br/>PySide6] --> M[⚙️ Motor de<br/>classificação]
    M --> N[(📄 Normas<br/>YAML)]
    UI --> H[(🗄️ Histórico<br/>SQLite)]
```

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

| Tecnologia | Aplicação no projeto |
|---|---|
| Python | Motor de regras, validação e lógica da aplicação. |
| PySide6 (Qt) | Interface desktop em tela cheia, com abas e tooltips. |
| SQLite | Histórico de classificações e lixeira. |
| YAML + Pydantic | Base de normas legível e validada ao carregar. |
| Pytest + Ruff | Testes automáticos e qualidade do código. |
| PyInstaller | Geração do executável `.exe` para Windows. |
| Git + GitHub | Controle de versão e documentação. |
| Claude Code | Desenvolvimento assistido por IA, guiado por `CLAUDE.md` e ADRs. |

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

</details>

## 📁 Estrutura do Repositório

```text
SistemaDeClassificacao/
├── src/classificador/
│   ├── dominio/         # propriedades, amostra, modelos (norma, grau, folha de classificações)
│   ├── normas/          # carregador do YAML e comando de conferência
│   ├── motor/           # limites, avaliação, classificação, sequência, saída, pesquisa reversa
│   └── tolerancia/      # tolerância de espessura (real × nominal)
├── tests/               # testes automáticos
│   └── dados/           # norma, folha, correlatas e tolerância fictícias usadas nos testes
├── docs/decisoes/       # registros de decisões de arquitetura (ADRs)
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

## 🚀 Como executar

Requisitos: **Windows** e **Python 3.12+**. No PowerShell, na pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
```

Para conferir uma norma transcrita contra as imagens da ABNT (imprime no formato das tabelas):

```powershell
.\.venv\Scripts\python.exe -m classificador.normas.conferir tests\dados\norma-ficticia.yaml
```

Para abrir o programa (precisa da pasta local `dados/` com as normas transcritas):

```powershell
.\.venv\Scripts\python.exe -m classificador
```

> Interface em desenvolvimento (Fase 5): classificação, tolerância, correlatas e pesquisa reversa
> já funcionam na tela; histórico e lixeira chegam na Fase 6.

## 🗺️ Roteiro

- [x] **Fase 0** — Fundação: repositório, ADRs, ambiente Python, permissões do Claude Code
- [x] **Fase 1** — Modelo de dados, formato YAML validado e NBR 5915-2 transcrita e conferida
- [x] **Fase 2** — Motor de classificação (com testes primeiro): sequência por acabamento,
  "quase passou", valores faltando, saída formatada e pesquisa reversa
- [x] **Fase 3** — NBR 5906, 7008-2 e 7008-3 transcritas e conferidas; normas correlatas e pesquisa
  reversa por qualquer norma
- [x] **Fase 4** — Tolerância de espessura: NBR 11888 (Tab. 11) e NBR 7013 (Tab. 1–4) transcritas e
  conferidas; dentro/fora com intervalo e norma
- [ ] **Fase 5** — Interface PySide6 *(em andamento: tela principal pronta, faltam ajustes visuais)*
- [ ] **Fase 6** — Histórico, lixeira, pesquisa e registro de divergências (melhoria contínua)
- [ ] **Fase 7** — Executável `.exe`
- [ ] **Fase 8** — Detecção de outliers com machine learning

## ⚖️ Direitos autorais

O conteúdo das normas ABNT é protegido e **não faz parte deste repositório**. As tabelas transcritas
ficam apenas na pasta local `dados/`, listada no `.gitignore`.

---

<p align="center">
  <b>Projeto de desenvolvimento de software aplicado à qualidade na indústria do aço, com foco em
  automação de processos, rastreabilidade e redução de erros de classificação.</b>
</p>

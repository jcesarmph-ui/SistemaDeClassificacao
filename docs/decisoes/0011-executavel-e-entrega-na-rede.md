# 0011 — Executável e entrega na pasta da rede

- **Status:** aceita
- **Data:** 2026-11-04
- **Complementa:** [0001](0001-python-pyside6.md), [0010](0010-historico-lixeira-e-divergencias.md)

## Contexto
O programa precisa rodar nos computadores da empresa **sem instalar Python** e sem servidor nem TI:
tudo fica numa **pasta comum da rede**. As normas transcritas e o histórico também ficam nessa pasta,
para todos verem os mesmos dados.

O primeiro teste mostrou um problema: abrir o `.exe` direto da rede é lento, porque o Windows puxa
o programa inteiro (dezenas de MB, com o Qt) pela rede a cada abertura.

## Decisão — executável com PyInstaller, dados ao lado
- O programa vira um executável Windows com **PyInstaller** (pasta, não arquivo único: abre mais
  rápido). Ficam de fora as partes do Qt que o programa não usa (OpenGL por software, Quick/QML,
  PDF, traduções), o que reduz bastante o tamanho.
- As normas, tolerâncias, folha de classificações, correlatas, logo e ícone **não vão dentro do
  `.exe`**: ficam na pasta `dados/`, ao lado. **Norma corrigida = trocar o YAML**, sem gerar o
  programa de novo.
- Onde o programa procura os dados (`interface/servico.py`, `pasta_dados_padrao`):
  1. variável de ambiente `CLASSIFICADOR_DADOS`, quando existe (é o que o lançador usa);
  2. no executável (`sys.frozen`): `dados/` ao lado do `.exe`;
  3. em desenvolvimento: `dados/` do projeto.
- Cada geração grava um `versao.txt` com a versão + data/hora, que identifica a cópia.

## Decisão — lançador que copia o programa para o PC (igual ao da calibração)
- Quem abre a pasta da rede vê **um único arquivo**: "Classificação de Materiais.exe", o
  **lançador** (`src/classificador/lancador.py`). Ele é pequeno e não usa PySide6, para abrir rápido.
- Na primeira abertura de cada versão, o lançador copia o programa para o próprio PC
  (`%LOCALAPPDATA%\MG Centro de Servicos\Classificacao\<versão>`), com uma janelinha
  "Preparando…". Nas aberturas seguintes, abre direto a cópia local (**~1–2 s**).
- O programa copiado continua lendo as normas e gravando o histórico na pasta `dados/` **da rede**:
  todos usam o mesmo histórico.
- Segurança da cópia: copia para uma pasta temporária e só renomeia no fim, então cópia
  interrompida nunca é usada e duas aberturas ao mesmo tempo não se atrapalham. Versões antigas são
  apagadas do PC. Sem conseguir copiar, abre direto da rede (mais devagar, mas abre).
- O lançador **oculta** as pastas `_internal`, `programa` e `dados`, para ninguém mexer nelas sem
  querer. A entrega já sai com elas ocultas, e o lançador oculta de novo se a marca se perder.
- **Atualizar = trocar a pasta `programa`**, com o programa fechado por todos. Cada PC copia a
  versão nova sozinho na próxima abertura. **Nunca copiar `dados/` por cima**: apagaria o histórico.

## Decisão — pasta de entrega
- A entrega é montada pronta (lançador + `programa/` + `dados/`) e o usuário só a copia para a rede.
- `dados/` vai **só com o necessário** (normas, tolerâncias, folha, correlatas, logo, ícone). O
  **histórico começa vazio**: a montagem recusa a entrega se encontrar um banco `.db`.
- Os scripts que geram o executável e a entrega **ficam fora do repositório público** (estão só no
  repositório privado de configuração), assim como o executável: ele traz as normas da empresa.

## Testes feitos
- Pasta que simula a rede: primeira abertura 1,6 s, segunda 1,0 s, histórico criado na rede.
- Na rede da empresa: programa aberto e **dois PCs salvando ao mesmo tempo**, com os dois registros
  aparecendo no histórico dos dois (confirma a decisão de não ter trava de edição, ADR 0010).
- Caminho mais longo da cópia local ≈ 187 caracteres (limite do Windows: 260).

## Consequências
- ✅ Abre em 1–2 s, mesmo morando numa pasta da rede, e não precisa instalar nada.
- ✅ Um histórico só para todos; atualizar é trocar uma pasta.
- ✅ Norma corrigida não exige gerar o programa de novo.
- ⚠️ A primeira abertura de cada versão em cada PC leva alguns segundos a mais (a cópia).
- ⚠️ Cada PC guarda uma cópia do programa (~80 MB) na pasta do usuário.
- ⏭️ Próximo: versão `1.0.0` (primeira em uso na empresa) e Fase 8 (machine learning).

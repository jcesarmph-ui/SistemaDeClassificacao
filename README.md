# Classificação Automática de Materiais

Programa desktop da **MG Centro de Serviço** para classificar aços planos (laminados a frio, a quente
e zincados) a partir das propriedades mecânicas e químicas, conforme as normas ABNT.

> **Status:** em definição de arquitetura — ainda sem código executável.

## O que o programa faz
- Recebe as propriedades **mecânicas** (LE, LR, alongamento, embutimento) e **químicas** (C, Mn, P, S,
  Al, Ni, Ti, V, Nb, Cr, Si, B) e o **acabamento** (FF, FQ, FQ DO, GI ZN, GI ZM, GA ZF, EG).
- Indica o **grau mais nobre** atendido, com a camada de revestimento (ex.: `ZEE G2 - Z275`,
  `EEP G3 EG 50/50`), a norma usada e as **normas correlatas** (montadoras/normas internacionais).
- Avisa valores não informados e quando um grau mais nobre foi perdido por uma única propriedade.
- Verifica a **tolerância de espessura** (NBR 11888 / NBR 7013).
- **Pesquisa reversa:** a partir de uma norma, mostra os intervalos exigidos.
- **Histórico** de classificações, com lixeira e restauração.

## Normas cobertas
NBR 5915-2 (frio – estampagem), NBR 5906 (quente), NBR 7008-2 e 7008-3 (zincado por imersão),
NBR 11888 e NBR 7013 (tolerâncias).

## Tecnologia
- Python 3.12+ · PySide6 (interface) · SQLite (histórico) · YAML (base de normas)
- pytest (testes) · ruff (qualidade) · PyInstaller (executável `.exe`)

## Estrutura (planejada)
```
src/classificador/   código (domínio, normas, motor, tolerância, histórico, interface)
tests/               testes automáticos (usam uma norma fictícia)
docs/decisoes/       registros de decisões de arquitetura (ADRs)
dados/               normas transcritas e casos reais — NÃO versionado
```

## Direitos autorais
O conteúdo das normas ABNT é protegido e **não faz parte deste repositório**. As tabelas
transcritas ficam apenas na pasta local `dados/`, que está no `.gitignore`.

# Classificação Automática

## Idioma
- Toda comunicação, comentários e documentação em português (pt-BR).

## Estado atual
- **Fase de definição** — ainda NÃO escrever código. Estamos definindo escopo, regras e arquitetura.
- Próximo passo: responder às pendências (seção "Pendências") e fechar as decisões antes de implementar.

## Objetivo
Programa (MG Centro de Serviço) para **classificar materiais de aço (produtos planos)** a partir das
propriedades mecânicas e químicas digitadas pelo usuário, indicando a classificação (sigla/grau) conforme
as normas ABNT, além de verificar tolerância de espessura e mostrar normas correlatas.

## Material de referência (`normas_claude/`)
- Imagens das tabelas das normas (nome do arquivo = norma-parte-página):

| Norma | Produto | Graus | Conteúdo |
|---|---|---|---|
| NBR 5915-2:2013 | Laminado a frio – estampagem | EM, EP, EEP 1–4 | Química, mecânica, Erichsen (Tab. 3) |
| NBR 5915-3:2013 | Frio – alta resistência | IS-220/260/300, IFAR-180/210/240/270 | Química, mecânica |
| NBR 5915-4:2013 | Frio – bake hardening | BH-180 a BH-340 | Química, mecânica (inclui BH mín) |
| NBR 5915-5:2013 | Frio – refosforado | RP-180 a RP-300 | Química, mecânica |
| NBR 5915-6:2013 | Frio – ARBL | ARBL-240 a ARBL-550 | Química, mecânica |
| NBR 5906 | Laminado a quente | EM, EP, EPA | Química, mecânica |
| NBR 7008-2:2021 | Zincado imersão – estampagem | ZC, ZE, ZEE 1–4 | Química, mecânica |
| NBR 7008-3:2021 | Zincado imersão – estrutural | ZAR-230 a ZAR-550 | Química, mecânica |
| NBR 11888 | Frio – tolerâncias | — | Tab. 11 (espessura, baixa resistência) |
| NBR 7013 | Zincado – tolerâncias | — | Tab. 1–4 (espessura × largura, por faixa de LE mín) |

- `classificações.pdf`: tabela de siglas de acabamento, indicação de camada e a relação
  **sigla ↔ norma ↔ acabamento ↔ normas correlatas** (EN, GMW, VW, HES, TSG, FG, MS...).
- `esboço da interface.pdf`: esboço à mão da tela.

### Acabamentos e camada
- FF (frio), FQ (quente), FQ DO (quente decapado e oleado), GI ZN / GI ZM (zincado imersão, cristais
  normais/minimizados), GA ZF (zinco-ferro, Galvanew), EG (eletrolítico).
- Camada: GI → `Z___` (g/m², duas faces, ex. Z100); GA → `ZF___` (ex. ZF100); EG → `_/_` (g/m² por face, ex. 50/50).
- Formato da saída: sigla + camada, ex. `ZEE G2 - Z275` (GI), `EEP G1 EG 50/50`.

## Interface (conforme esboço)
- **Esquerda:** logo MG, "Classificação de Materiais"; acabamento (lista: FQ DO, FF, GI ZN, GI ZM, EG);
  upload da folha de classificações/siglas; camada em g/m² (permitir outros valores além de 100 e 275;
  vazio ou zero = sem revestimento).
- **Centro – propriedades mecânicas:** LE (MPa), LR (MPa), alongamento Lo50 % e Lo80 % (aceitar com ou
  sem "%", limpar após Enter), embutimento (mm); espessura nominal e real (mm) + largura (mm) →
  resposta dentro/fora da tolerância (verde/vermelho), mostrando intervalo e norma usada.
- **Direita – propriedades químicas (%):** C, Mn, P, S, Al, Ni, Ti, V, Nb, Cr, Si, B
  (vazio = não tem, considerar zero na comparação — ver pendência 3).
- Campo para digitar norma correlata com autocompletar pelas primeiras letras (todas as normas da
  planilha de equivalência).
- **Classificação reversa:** escolher o grau e mostrar os intervalos de valores exigidos.
- Botões: CLASSIFICAR (mostra a classificação no campo de resultado), nova classificação, limpar valores.
- **Outra aba:** histórico de classificações — salvar números/valores, pesquisar antigas.

## Arquitetura proposta (a confirmar)
1. **Base de normas (dados, não código):** cada norma em arquivo estruturado (YAML/JSON ou Excel):
   graus, limites mín/máx por propriedade, notas como regras de ajuste, tabelas de tolerância.
   Transcrição feita a partir das imagens e conferida pelo usuário.
2. **Motor de classificação:** testa todos os graus candidatos do acabamento escolhido; retorna
   aprovado/reprovado por grau com o motivo (ex.: "C = 0,09 > 0,08 máx"). Aplica as notas das normas.
   Classificação reversa usa a mesma base.
3. **Verificação de tolerância:** tabela escolhida por norma do acabamento + faixa de LE mín do grau +
   largura; +0,01 mm quando camada ≥ Z275.
4. **Interface + histórico:** desktop Windows; histórico em SQLite.
- Tecnologia sugerida: **Python + PySide6**, empacotado como `.exe` (PyInstaller). Alternativa mais
  simples: Streamlit (web local).
- Testes automáticos com casos reais já classificados (pasta `exemplos/`).

## Regras das normas já identificadas (notas de rodapé)
- LE não definido → usar valor a 0,2 % de deformação.
- Espessura < 0,70 mm e/ou planicidade especial → alongamento pode ser 2 unidades abaixo.
- Espessura ≥ 1,60 mm → r90 −0,2 e n90 −0,02.
- NBR 5915-2 nota d: espessura < 0,5 mm → LE máx +40 MPa e alongamento −4; 0,50 ≤ e ≤ 0,70 → LE máx +20 MPa e alongamento −2.
- NBR 5915-2: Nb pode substituir Ti (Ti+Nb ≤ 0,20 %); B máx 0,0005 % se o comprador exigir; EEP 4 não substitui EEP 3 sem autorização.
- NBR 5906: e ≤ 2,0 mm → LE/LR máx +20 MPa e alongamento −3; decapado contínuo/laminação de
  acabamento → alongamento −1; EPA com 2,0 < e < 3,0 → LE máx +10 MPa; Lo = 50 mm é o padrão.
- NBR 7008-2/-3: revestimento zinco-ferro (GA) → alongamento −2, r90 −0,2, n90 −0,02.
- NBR 7008-2: ZC sem limites mecânicos; NBR 7013 considera para ZC o LE de ZE (260/360 MPa).
- Microligantes (Nb, Ti, V, Zr, Ta, B) — somatório máx 0,22 % (5915-3) / 0,25 % (5915-6, 7008-3).
- Tolerância de espessura: +0,01 mm para revestimento ≥ Z275 (NBR 7013); bobinas com solda: dobro da
  tolerância nos 15 m das extremidades (NBR 11888).

## Pendências (decidir com o usuário)
1. Quando mais de um grau atende (ex.: passa em EEP G2, EP e EM): mostrar o mais nobre, todos, ou ambos?
2. Quando nenhum atende: mostrar "não classificável" + grau mais próximo e o que falhou?
3. Vazio = zero: ok para máximos, mas reprova mínimos (Al mín) e impede checar r90/n90. Proposta:
   distinguir "não informado" de "zero" e sinalizar "não verificado".
4. Dados faltantes: SAE 1006/1008/1010; NBR 16964 (EG); tolerância para FQ; NBR 11888 Tab. 12
   (alta resistência); campos r90, n90 e BH não estão no esboço.
5. Tolerância padrão: normal ou restritiva?
6. A "folha de siglas" do upload é a do `classificações.pdf`? Deve ser substituível sem mexer no programa?
7. Direitos autorais ABNT: se o repositório GitHub for público, NÃO versionar `normas_claude/` nem as
   tabelas transcritas. Repositório é público ou privado?
8. Uso: uma pessoa/um PC ou várias pessoas com histórico compartilhado?
9. Tecnologia: confirmar PySide6 (desktop) × Streamlit.

## Versionamento
- Git com repositório no GitHub (branch `main`).
- Fazer commits pequenos a cada etapa concluída, com mensagens em português.
- Sempre confirmar com o usuário antes de `git push`.
- Nunca versionar dados sensíveis, senhas ou chaves de API.
- Até resolver a pendência 7, não versionar a pasta `normas_claude/`.

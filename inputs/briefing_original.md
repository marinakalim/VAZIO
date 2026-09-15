# Levantamento — 50 maiores associações do Brasil (XIPP)

Você é o orquestrador de uma pesquisa de inteligência de mercado para a XIPP Benefícios. Trabalhe com subagentes em paralelo (Task tool), grave tudo em arquivos e só pare quando a entrega estiver completa no padrão descrito no fim deste prompt. Não me peça confirmação entre as fases: registre as decisões na aba Metodologia e siga.

## Contexto

A XIPP quer visitar as associações com maior número de associados do Brasil para oferecer dois produtos: o **Mais Família** (benefício de saúde da XIPP com a Avus) e o **NutriPass**. A proposta de valor para a associação é ampliar o que ela entrega ao associado pagante, reter associados e atrair novos. A ideia surgiu de uma reunião com a ANABB (Associação Nacional dos Funcionários do Banco do Brasil).

O que vale como critério, conforme o briefing:
- "Principais" = **maior número de associados**.
- Entram **apenas entidades pagas**, ou seja, em que o associado paga uma contribuição periódica: mensalidade, anuidade ou equivalente. A periodicidade não importa. O que importa é existir uma cobrança, porque o produto gera valor dentro do que o associado já paga.
- As fundações vinculadas são uma etapa secundária: fazer só uma passada leve.
- No fim, cruzar as 50 com o pipeline atual da PX (CRM da XIPP). Sempre "a PX", no feminino.

## Arquivos

- `inputs/Pesquisa_Associações-Summary_2984.docx`: briefing original.
- `inputs/pipeline_px.xlsx` (ou `.csv`): export do pipeline da PX. **Se o arquivo não existir, conclua todo o resto, deixe a coluna de pipeline como "export da PX pendente" e avise no resumo final.**
- Trabalho intermediário em `work/` e entrega final em `output/`.

## Escopo: o que entra e o que não entra

**Entra no Top 50:** entidade cujos associados sejam **pessoas físicas** e que cobre contribuição periódica (mensalidade ou anuidade). Na maioria dos casos, a natureza jurídica será **399-9 – Associação Privada**. A exceção é a **OAB**, que entra mesmo sem essa natureza jurídica (categoria 7). As categorias abaixo servem de guia para a busca, não de cota:
1. Associações de funcionários de empresas, estatais e bancos (ex.: ANABB, AFABB, APCEFs, associações de empregados de Petrobras, Correios, Caixa, elétricas etc.)
2. Associações de servidores públicos, militares, policiais e bombeiros (federais, estaduais e municipais)
3. Associações de profissionais (medicina, odontologia, advocacia, engenharia, contabilidade, magistratura, MP etc.), **não** os conselhos
4. Associações de aposentados e pensionistas
5. Clubes sociais e recreativos com quadro associativo pagante
6. Outras associações de pessoas físicas pagas (ex-alunos, consumidores etc.)
7. **OAB.** A unidade de análise é a **seccional** (OAB-SP, OAB-RJ etc.), porque é nela que acontecem a visita e a decisão, como no exemplo da OAB do Rio. Cada seccional é uma linha e disputa o ranking pelo número de inscritos ativos. Na mesma linha, registre a Caixa de Assistência correspondente (CAASP, CAARJ etc.), com CNPJ e site, porque os benefícios costumam ficar nela. O valor a informar é a anuidade vigente da seccional. Registre também o Conselho Federal, com o total nacional, na aba Metodologia como referência.

**Não entra no Top 50, mas vai para a aba "Fora do critério – relevantes"** quando for grande ou estratégico, com o motivo registrado:
- Demais conselhos profissionais (CRM, CREA, COREN, CRC etc.). Eles cobram anuidade, mas são autarquias de fiscalização e raramente oferecem benefícios. Levante esses conselhos com os mesmos campos do Top 50, numa aba própria chamada **"Conselhos profissionais – a decidir"**, para que possam ser promovidos ao ranking sem retrabalho.
- Sindicatos, cooperativas, fundações e entidades fechadas de previdência.
- Associações empresariais e setoriais, cujos associados são empresas.
- Programas de sócio-torcedor.
- Associações de proteção veicular ou mutualismo. Elas são associações que cobram mensalidade, mas têm risco regulatório e reputacional: registre-as com esse alerta e deixe a decisão de inclusão para a XIPP.

**Alerta reputacional (não exclui):** marque as associações citadas nas investigações sobre descontos associativos indevidos em benefícios do INSS, com a fonte.

## Arquitetura

### Fase 1 — Universo (paralelo)
Dispare **um subagente por categoria** (1 a 7; o da categoria 7 levanta as 27 seccionais da OAB e as Caixas de Assistência) e **um subagente transversal**, que procura rankings, reportagens e listas de "maiores associações" e checa entidades citadas pela imprensa. Cada subagente deve entregar **30 a 40 candidatas**, sem teto se houver mais, em `work/universo_<categoria>.jsonl`, com esta linha por entidade:

```json
{"nome": "", "sigla": "", "cnpj": "", "categoria": "", "associados": null, "base_contagem": "titulares ativos | total cadastrado | inclui dependentes | não informado", "fonte_associados": "", "data_fonte": "", "tipo_fonte": "declarado pela entidade | documento oficial | imprensa | estimado", "entidade_paga": "sim | não | a confirmar", "tipo_cobranca": "mensalidade | anuidade | outra", "evidencia_cobranca": "", "observacoes": ""}
```

### Fase 2 — Consolidação e corte (orquestrador)
1. Junte os arquivos, deduplique **por CNPJ** (use nome normalizado quando faltar CNPJ) e grave `work/longlist.csv`.
2. Confirme CNPJ, razão social, natureza jurídica, município e UF da matriz em base pública de CNPJ (ex.: `https://brasilapi.com.br/api/cnpj/v1/{cnpj}`). Tire quem não for 399-9, **exceto as seccionais da OAB e suas Caixas de Assistência**, e mande para a aba "Fora do critério".
3. Ordene por número de associados e **separe as 60 primeiras** que atendem ao critério. As 10 extras são folga para os cortes do fact-check.

### Fase 3 — Enriquecimento (paralelo, lotes de 10)
Divida as 60 em 6 lotes e dispare um subagente por lote. Para cada entidade:
- **Número de associados:** busque primeiro o número declarado pela própria entidade (site, relatório anual, balanço, demonstrações contábeis, estatuto, releases), depois a imprensa. Se só houver receita de contribuições, a estimativa é permitida, mas precisa trazer a premissa escrita.
- **Valor da mensalidade (ou anuidade):** informe o valor como é cobrado, com a periodicidade e o equivalente mensal. Exemplo: "R$ 1.020/ano (≈ R$ 85/mês)". Se houver faixas (por idade, tempo de inscrição, categoria), informe a faixa e o critério. Se não for público, escreva "não público". Não estime valor.
- **Benefícios inclusos na mensalidade ou anuidade:** o que o associado recebe sem pagar à parte.
- **Benefícios de saúde já oferecidos** (coluna extra): plano de saúde, odonto, telemedicina, nutrição, com operadora ou administradora e se o benefício está incluso ou é pago à parte. Esse dado mostra o incumbente e o ângulo de proposta para Mais Família e NutriPass.
- **Fundação vinculada:** registre só quando houver vínculo documentado (mesma empresa instituidora, mesma categoria, parceria formal) e informe o tipo de vínculo, como no exemplo Copel/Fundação Copel. Sem evidência, escreva "não identificada".
- **Site oficial e LinkedIn:** a URL da página da entidade. Confira se a página é da entidade certa e não de homônimo, regional ou afiliada.
- **Cidade e UF da sede:** conforme a matriz no CNPJ.

Grave em `work/enriquecido_lote<N>.jsonl`, com fonte (link) e data **para cada campo**.

### Fase 4 — Fact-check independente (paralelo)
Dispare subagentes **que não participaram da pesquisa**, com lotes de 15. Eles recebem apenas nome e CNPJ, **refazem a busca do zero** para número de associados, existência de cobrança e valor cobrado, e comparam o resultado com o enriquecido. Cada campo recebe um veredito: `confirmado | divergente | não verificável`, com a fonte. Em caso de divergência, a primeira hipótese é diferença de recorte (titulares vs. dependentes, ativos vs. cadastrados, nacional vs. regional); busque a explicação antes de escolher um valor. Quando a divergência não se explica, a fonte mais recente com data explícita prevalece, e a divergência fica registrada.

Depois do fact-check, refaça o ranking e **corte em 50**. Quem cair vai para a aba Longlist, com o motivo.

### Fase 5 — Cruzamento com a PX
Casamento por CNPJ primeiro, depois por nome normalizado ou sigla (com fuzzy match e revisão manual dos casos duvidosos). Colunas: `na_pipeline_px` (sim/não), `estagio_px` e `responsavel_px`, quando existirem no export. Liste também as associações que estão na PX mas ficaram fora do Top 50.

### Fase 6 — Entrega
Monte `output/Top50_Associacoes_XIPP.xlsx` com openpyxl, com cabeçalho formatado, filtros, primeira linha congelada, links clicáveis e larguras ajustadas.

**Aba "Top 50"**: as colunas do briefing primeiro, **nesta ordem exata**:
1. Nome da associação
2. CNPJ (quando houver)
3. Número de associados
4. Valor da mensalidade
5. Benefícios inclusos na mensalidade (quando disponível)
6. Fundação vinculada
7. Cidade
8. UF
9. Site
10. Linkedin

Depois delas, as colunas extras: Ranking · Categoria · Base da contagem · Fonte e data (associados) · Real ou estimado · Tipo de cobrança (mensalidade/anuidade) · Fonte e data (valor cobrado) · Caixa de Assistência (OAB) · Benefícios de saúde já oferecidos / incumbente · Alerta reputacional · Status do fact-check · Na pipeline da PX · Estágio na PX · Observações.

**Demais abas:** Longlist (todas as candidatas, com motivo de corte) · Fora do critério – relevantes · Pipeline PX fora do Top 50 · Metodologia (critério, fontes, decisões tomadas, limitações) · Pendências e hipóteses (o que ficou em aberto e onde buscar) · Fontes (todas as URLs com data de acesso).

Gere também `output/resumo.md` com meia página: como o ranking foi feito, os 10 primeiros, os principais achados comerciais (onde já existe benefício de saúde, quem não tem, quem já está na PX) e as pendências.

## Regras inegociáveis

- **Campo sem fonte fica vazio.** "Não encontrado" é uma resposta válida. Nunca preencha por plausibilidade.
- **Número de associados sempre traz fonte, data e base de contagem.** Associações costumam inflar esse número. Nunca ranqueie números de bases diferentes lado a lado sem sinalizar.
- **Estimativa sempre vem marcada** como "estimado" e traz a premissa na própria célula ou em Observações.
- **Site institucional envelhece:** prefira o dado mais recente com data explícita.
- **Nome fantasia não é razão social:** confira pelo CNPJ.
- **Não levante telefones nem contatos pessoais.** Nesta fase entram só dados institucionais.
- **Fonte preferida:** a própria entidade e documentos oficiais, depois imprensa especializada, depois imprensa geral. Agregadores servem só como pista.

## Checklist AAA (verifique antes de encerrar)

- [ ] 50 linhas no Top 50, todas com natureza jurídica confirmada (399-9, ou OAB) e cobrança periódica comprovada
- [ ] 100% das linhas com número de associados, fonte, data e base de contagem
- [ ] Nenhuma célula preenchida sem fonte; estimativas marcadas e com premissa
- [ ] Fact-check independente concluído, com os status registrados
- [ ] Cruzamento com a PX feito, ou pendência declarada
- [ ] Abas Metodologia, Pendências e Fontes preenchidas
- [ ] Planilha abre sem erro, links funcionam e as 10 colunas do briefing estão na ordem certa
- [ ] resumo.md escrito

Ao terminar, me mostre o caminho dos arquivos, o top 10 e as 3 principais pendências.

# Resumo — Levantamento das maiores associações do Brasil (XIPP)

**Status: entrega parcial, fechada a pedido do usuário após bloqueio de ambiente.** Este não é o padrão AAA definido no briefing original — é a Fase 1 (universo de candidatas) consolidada, ranqueada e cruzada com a PX, sem as Fases 3 (enriquecimento) e 4 (fact-check independente), que não puderam ser executadas nesta sessão. Ver detalhes em "O que ficou pendente" abaixo e na aba Metodologia da planilha.

## Como o ranking foi feito

8 subagentes pesquisaram em paralelo (categorias 1 a 7 do briefing + 1 transversal de imprensa/rankings), levantando 252 candidatas brutas via WebSearch. Após deduplicar por CNPJ/nome (234 entidades únicas), separar as 27 seccionais da OAB, e excluir 9 entidades de natureza sindical/federativa/confederativa ("Fora do critério"), sobrou um pool de 224 candidatas (197 gerais + 27 OAB) que disputaram o Top 50 por número de associados declarado.

**Limitação central:** só 46 das 224 candidatas têm um número de associados com alguma fonte (a cota de 200 buscas WebSearch da sessão, compartilhada entre os 8 subagentes paralelos, esgotou antes de completar a pesquisa; WebFetch e chamadas diretas via `curl` foram bloqueadas por política de rede do ambiente para praticamente todo domínio institucional/imprensa testado). As 4 vagas restantes do Top 50 foram preenchidas com candidatas sem número confirmado, só para completar a estrutura pedida — a posição delas no ranking **não reflete tamanho real**, apenas ordem de exibição (sinalizado na coluna "Real ou estimado").

## Top 10 (por número de associados declarado — não fact-checado)

| # | Associação | Associados | Categoria | Na PX? |
|---|---|---|---|---|
| 1 | Associação dos Aposentados Mutualistas para Benefícios Coletivos (AMBEC) | 650.000 | Aposentados/pensionistas | Sim |
| 2 | PROTESTE — Associação Brasileira de Defesa do Consumidor | 280.000 | Outras | Sim |
| 3 | APVS Brasil — Associação de Proteção Veicular | 280.000 | Outras (alerta regulatório) | Não |
| 4 | OAB — Seccional Minas Gerais | 140.810 | OAB | Não |
| 5 | Clube Curitibano | 131.000 (⚠ baixa confiança, não confirmado) | Clubes sociais | Não |
| 6 | OAB — Seccional Rio Grande do Sul | 92.268 | OAB | Não |
| 7 | Associação Brasileira de Odontologia | 90.000 | Profissionais | Não |
| 8 | Grande Oriente do Brasil | 86.000 | Outras | Não |
| 9 | Minas Tênis Clube | 73.000 (dado de ~2013, desatualizado) | Clubes sociais | Não |
| 10 | Associação dos Advogados de São Paulo (AASP) | 70.000 | Profissionais | Sim |

## Principais achados comerciais

- **AMBEC é a maior candidata numericamente, mas com alerta reputacional grave**: alvo direto da Operação Sem Desconto (PF/CGU, 2025) por descontos indevidos em benefícios do INSS — abordagem comercial exige cautela.
- **8 das 50 candidatas já estão na pipeline da PX** (AMBEC, PROTESTE, AASP e outras 5) — checar estágio/responsável na aba Top 50 e cruzar internamente antes de qualquer contato.
- **Nenhuma linha do Top 50 tem benefício de saúde incumbente mapeado** — a Fase 3 (que levantaria isso) não rodou. Esse é o maior buraco para a proposta comercial do Mais Família/NutriPass: hoje não sabemos quem já tem plano de saúde/odonto/telemedicina para comparar contra a oferta da XIPP.
- **OAB é a categoria mais frágil**: só 2 das 27 seccionais têm número de inscritos confirmado com fonte e data (MG e RS); as outras 25 precisam de nova pesquisa dedicada, fora do orçamento compartilhado desta sessão.
- **2 candidatas do Top 50 têm alerta reputacional/regulatório** (AMBEC — INSS; APVS Brasil — proteção veicular).

## O que ficou pendente (críticos)

1. **Fase 3 (enriquecimento) não rodou**: mensalidade/anuidade, benefícios inclusos, benefícios de saúde incumbentes, fundação vinculada, site, LinkedIn e cidade/UF estão vazios ou genéricos para a maioria das 50 linhas — as 6 colunas centrais do briefing (das 10 pedidas) ficaram incompletas.
2. **Fase 4 (fact-check independente) não rodou**: nenhum número foi confirmado por um segundo agente. Trate todo número como não verificado, incluindo os com "baixa confiança" já sinalizados pelo próprio subagente de origem (Clube Curitibano, Minas Tênis Clube, APM, Grêmio Náutico União, entre outros — ver aba Metodologia/Fontes).
3. **Natureza jurídica não verificada via API pública de CNPJ**: a classificação 399-9 é presumida pela categoria, não confirmada.
4. **OAB**: 25 das 27 seccionais sem inscritos confirmados; conselhos profissionais (CRM, CREA etc.) não foram levantados (aba entregue vazia).
5. **Causa raiz de tudo isso**: WebSearch esgotou a cota da sessão (200/200) e WebFetch/curl foram bloqueados por política de rede do ambiente (testado diretamente contra brasilapi.com.br — 403 por política, não falha transitória). Ambos precisam ser resolvidos (cota maior e/ou liberação de domínios) para completar o briefing como especificado.

Arquivos: `output/Top50_Associacoes_XIPP.xlsx` (8 abas) e este `output/resumo.md`.

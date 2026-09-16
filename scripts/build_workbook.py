import json, re
from pathlib import Path
from datetime import date
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path("/home/user/VAZIO")
WORK = ROOT / "work"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

def load(name):
    with open(WORK / name, encoding="utf-8") as f:
        return json.load(f)

oab = load("cat_oab.json")
fora_criterio = load("cat_fora_criterio.json")
conselhos = load("cat_conselhos.json")
candidatos = load("cat_candidatos_rankeados.json")
px_assoc_nao_casadas = load("px_assoc_nao_casadas.json")

CITY_RE = re.compile(r"sede (?:em|no|na) ([A-Za-zÀ-ÿ\s\.]+?)[\/,]\s*([A-Z]{2})\b")

def extract_city_uf(obs):
    if not obs:
        return "", ""
    m = CITY_RE.search(obs)
    if m:
        return m.group(1).strip(" .,"), m.group(2)
    return "", ""

def rank_key(r):
    a = r.get("associados")
    has_num = isinstance(a, (int, float))
    return (0 if has_num else 1, -(a or 0))

pool = oab + candidatos
pool_sorted = sorted(pool, key=rank_key)
top50 = pool_sorted[:50]
resto = pool_sorted[50:]

n_com_numero_top50 = sum(1 for r in top50 if isinstance(r.get("associados"), (int, float)))
print(f"Top 50 montado: {len(top50)} linhas, {n_com_numero_top50} com número de associados confirmado, "
      f"{50 - n_com_numero_top50} sem número (ranking não numérico, ordenadas por categoria/nome).")

TODAY = date.today().isoformat()

wb = openpyxl.Workbook()
wb.remove(wb.active)

FONT_NAME = "Arial"
HEADER_FILL = PatternFill("solid", fgColor="6428BD")
HEADER_FONT = Font(name=FONT_NAME, bold=True, color="FFFFFF", size=10)
BASE_FONT = Font(name=FONT_NAME, size=10)
WRAP = Alignment(wrap_text=True, vertical="top")
ALERT_FILL = PatternFill("solid", fgColor="FFF2CC")

def style_header(ws, ncols, row=1):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    ws.freeze_panes = ws.cell(row=row + 1, column=1)
    ws.auto_filter.ref = f"A{row}:{get_column_letter(ncols)}{row}"

def autosize(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

def fmt_fonte_data(fonte, data):
    parts = [p for p in [fonte, data] if p and p != "não encontrado"]
    return " | ".join(parts) if parts else "não encontrado"

def fmt_associados(r):
    a = r.get("associados")
    return a if isinstance(a, (int, float)) else "não encontrado"

def fmt_alerta(r):
    alerts = []
    obs = (r.get("observacoes") or "")
    if "ALERTA REPUTACIONAL" in obs.upper():
        m = re.search(r"ALERTA REPUTACIONAL[^.]*\.", obs, re.IGNORECASE)
        alerts.append(m.group(0) if m else "Citada em investigações de descontos associativos indevidos do INSS (ver observações).")
    if r.get("_alerta_regulatorio"):
        alerts.append(r["_alerta_regulatorio"])
    return " / ".join(alerts) if alerts else ""

def fmt_caixa(r):
    if str(r.get("categoria", "")).startswith("7"):
        nome = r.get("caixa_assistencia_nome", "")
        cnpj = r.get("caixa_assistencia_cnpj", "")
        site = r.get("caixa_assistencia_site", "")
        parts = [p for p in [nome, cnpj, site] if p]
        return " | ".join(parts) if parts else "não encontrado"
    return ""

def fmt_mensalidade(r):
    if str(r.get("categoria", "")).startswith("7"):
        return r.get("valor_anuidade", "") or "não público"
    tc = r.get("tipo_cobranca", "")
    ev = r.get("evidencia_cobranca", "")
    if tc and ev:
        return f"({tc}) valor não extraído automaticamente — ver evidência: {ev[:200]}"
    return "não levantado (Fase 3 não executada nesta sessão)"

FACT_CHECK_STATUS = "não realizado nesta sessão — WebSearch/WebFetch bloqueados após consolidação (ver aba Metodologia)"

LOW_CONF_MARKERS = ["BAIXA CONFIAN", "DESATUALIZAD", "DIVERG", "NÃO CONFIÁVEL", "NAO CONFIAVEL"]

def fmt_real_estimado(r):
    base = r.get("tipo_fonte", "") or "não encontrado"
    obs = (r.get("observacoes") or "").upper()
    if any(m in obs for m in LOW_CONF_MARKERS):
        return f"{base} — SINALIZADO COMO BAIXA CONFIANÇA/DIVERGENTE (ver Observações)"
    return base

TOP50_HEADERS = [
    "Nome da associação", "CNPJ", "Número de associados", "Valor da mensalidade",
    "Benefícios inclusos na mensalidade", "Fundação vinculada", "Cidade", "UF", "Site", "Linkedin",
    "Ranking", "Categoria", "Base da contagem", "Fonte e data (associados)", "Real ou estimado",
    "Tipo de cobrança", "Fonte e data (valor cobrado)", "Caixa de Assistência (OAB)",
    "Benefícios de saúde já oferecidos / incumbente", "Alerta reputacional", "Status do fact-check",
    "Na pipeline da PX", "Estágio na PX", "Observações",
]

def top50_row(r, i):
    cidade, uf = extract_city_uf(r.get("observacoes", ""))
    if str(r.get("categoria", "")).startswith("7"):
        uf = r.get("uf", uf)
    px = r.get("_px", {})
    return [
        r.get("nome", ""), r.get("cnpj", "") or "não encontrado", fmt_associados(r),
        fmt_mensalidade(r), "não levantado (Fase 3 não executada nesta sessão)",
        "não identificada (Fase 3 não executada nesta sessão)", cidade, uf, "", "",
        i, r.get("categoria", ""), r.get("base_contagem", "") or "não informado",
        fmt_fonte_data(r.get("fonte_associados", ""), r.get("data_fonte", "")),
        fmt_real_estimado(r),
        r.get("tipo_cobranca", "") or "não encontrado",
        r.get("evidencia_cobranca", "") or "não encontrado",
        fmt_caixa(r), "não levantado (Fase 3 não executada nesta sessão)",
        fmt_alerta(r), FACT_CHECK_STATUS,
        px.get("na_pipeline_px", "não"), px.get("estagio_px", ""),
        r.get("observacoes", ""),
    ]

ws = wb.create_sheet("Top 50")
ws.append(TOP50_HEADERS)
for i, r in enumerate(top50, start=1):
    ws.append(top50_row(r, i))
for row in ws.iter_rows(min_row=2):
    for cell in row:
        cell.font = BASE_FONT
        cell.alignment = WRAP
style_header(ws, len(TOP50_HEADERS))
autosize(ws, [38, 20, 14, 28, 30, 26, 16, 6, 24, 20, 9, 10, 20, 34, 18, 16, 34, 30, 30, 30, 34, 14, 16, 45])
ws.row_dimensions[1].height = 45

def sheet_from_rows(name, rows, extra_note=None, motivo_key=None):
    ws = wb.create_sheet(name)
    headers = ["Nome", "Sigla", "CNPJ", "Categoria", "Número de associados", "Base da contagem",
               "Fonte e data (associados)", "Tipo de cobrança", "Evidência de cobrança",
               "Motivo", "Alerta", "Na pipeline PX", "Estágio PX", "Observações"]
    ws.append(headers)
    for r in rows:
        px = r.get("_px", {})
        motivo = r.get(motivo_key, "") if motivo_key else ""
        ws.append([
            r.get("nome", ""), r.get("sigla", ""), r.get("cnpj", "") or "não encontrado",
            r.get("categoria", ""), fmt_associados(r), r.get("base_contagem", "") or "não informado",
            fmt_fonte_data(r.get("fonte_associados", ""), r.get("data_fonte", "")),
            r.get("tipo_cobranca", "") or "não encontrado", r.get("evidencia_cobranca", "") or "não encontrado",
            motivo, fmt_alerta(r), px.get("na_pipeline_px", "não"), px.get("estagio_px", ""),
            r.get("observacoes", ""),
        ])
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = BASE_FONT
            cell.alignment = WRAP
    style_header(ws, len(headers))
    autosize(ws, [36, 14, 20, 10, 16, 20, 32, 16, 40, 30, 28, 12, 16, 45])
    ws.row_dimensions[1].height = 30
    return ws

for r in resto:
    r["_motivo_corte"] = ("Não entrou nas 50 primeiras vagas do ranking por número de associados "
                           "(ou por falta de número confirmado, priorizando quem tem dado sobre CNPJ/UF.")
sheet_from_rows("Longlist", resto, motivo_key="_motivo_corte")

sheet_from_rows("Fora do critério – relevantes", fora_criterio, motivo_key="_motivo_fora_criterio")

ws_c = wb.create_sheet("Conselhos prof. – a decidir")
ws_c.append(["Nome", "Sigla", "CNPJ", "Observação"])
ws_c.append(["Nenhum conselho profissional (CRM, CREA, COREN, CRC, CFM etc.) foi levantado com dado real nesta sessão.",
             "", "", "Os subagentes de categoria esgotaram o orçamento compartilhado de WebSearch (200/200) antes de "
                 "pesquisar conselhos profissionais especificamente. Pendência registrada na aba Pendências e hipóteses."])
for row in ws_c.iter_rows(min_row=2):
    for cell in row:
        cell.font = BASE_FONT
        cell.alignment = WRAP
style_header(ws_c, 4)
autosize(ws_c, [40, 14, 20, 80])

ws_px = wb.create_sheet("Pipeline PX fora do Top 50")
headers_px = ["Nome (nosso levantamento)", "CNPJ", "Categoria", "Número de associados",
              "Nome na PX", "Estágio na PX", "Responsável PX", "Em qual aba está", "Observações"]
ws_px.append(headers_px)
def emit_px_out(rows, aba_nome):
    top50_names = {r.get("nome") for r in top50}
    for r in rows:
        px = r.get("_px", {})
        if px.get("na_pipeline_px") == "sim" and r.get("nome") not in top50_names:
            ws_px.append([r.get("nome", ""), r.get("cnpj", ""), r.get("categoria", ""),
                          fmt_associados(r), px.get("px_nome", ""), px.get("estagio_px", ""),
                          "", aba_nome, r.get("observacoes", "")])
emit_px_out(resto, "Longlist")
emit_px_out(fora_criterio, "Fora do critério – relevantes")
for row in ws_px.iter_rows(min_row=2):
    for cell in row:
        cell.font = BASE_FONT
        cell.alignment = WRAP
style_header(ws_px, len(headers_px))
autosize(ws_px, [36, 20, 10, 16, 36, 16, 20, 22, 45])

# ---------------- Metodologia ----------------
ws_m = wb.create_sheet("Metodologia")
ws_m.column_dimensions["A"].width = 110
meto_lines = [
    "METODOLOGIA — Levantamento das maiores associações do Brasil (XIPP)",
    f"Gerado em {TODAY}.",
    "",
    "1. ARQUITETURA EXECUTADA",
    "Fase 1 (Universo): 8 subagentes em paralelo (categorias 1 a 7 do briefing + 1 transversal de imprensa/rankings), "
    "cada um usando WebSearch para levantar candidatas na sua categoria. Total bruto: 252 linhas.",
    "Fase 2 (Consolidação): deduplicação por CNPJ (quando presente) e por nome normalizado (quando ausente). "
    "234 entidades únicas após dedupe (18 duplicatas removidas, log em work/dedup_log.txt).",
    "Classificação: seccionais da OAB isoladas (categoria 7, 28 linhas); entidades de natureza sindical/federativa/"
    "confederativa (SINDICATO, FEDERAÇÃO, CONFEDERAÇÃO no nome, ou citadas pelos próprios subagentes como tal — ex. "
    "COBAP, CONTAG, SINDNAPI, CENTRAPE, FENAPEF) movidas para 'Fora do critério – relevantes'; 197 candidatas "
    "restantes formaram o pool de ranking para Top 50 / Longlist.",
    "Ranking: por número de associados declarado (desc); quando não há número confirmado, a entidade fica na cauda "
    "do ranking, ordenada apenas para preencher a estrutura solicitada — a posição numérica dessas linhas NÃO reflete "
    "tamanho real, apenas ordem de exibição. Isso está sinalizado por 'Real ou estimado' = 'não encontrado'.",
    "",
    "2. BLOQUEIO CRÍTICO — POR QUE AS FASES 3 E 4 NÃO FORAM EXECUTADAS",
    "Depois da Fase 1, dois limites do ambiente impediram a continuidade da pesquisa:",
    "(a) WebSearch: a sessão tem uma cota de 200 buscas no total, compartilhada entre todos os subagentes rodando em "
    "paralelo. Essa cota se esgotou (200/200) já dentro da própria Fase 1, antes de qualquer subagente completar o "
    "enriquecimento de todas as suas candidatas.",
    "(b) WebFetch/curl: testado diretamente (inclusive via curl no proxy de rede do ambiente) contra "
    "brasilapi.com.br e outros domínios institucionais/imprensa — todas as tentativas retornaram bloqueio de "
    "política de rede (HTTP 403, 'connect_rejected' no log do proxy), não erro transitório. A lista de domínios "
    "liberados no ambiente é essencialmente infraestrutura de pacotes (npm, pypi etc.), não sites institucionais "
    "brasileiros nem bases de CNPJ.",
    "Consequência prática: não foi possível (i) confirmar natureza jurídica/razão social via API pública de CNPJ "
    "(brasilapi) como pedido na Fase 2, (ii) rodar a Fase 3 de enriquecimento (mensalidade, benefícios, fundação "
    "vinculada, site, LinkedIn, cidade/UF para a maioria das entidades), nem (iii) rodar a Fase 4 de fact-check "
    "independente. A coluna 'Status do fact-check' no Top 50 reflete isso em 100% das linhas.",
    "Diante disso, e a pedido explícito do usuário, a entrega foi fechada com os dados brutos da Fase 1 "
    "consolidados e ranqueados, sem completar o padrão AAA definido no briefing original.",
    "",
    "3. NATUREZA JURÍDICA — NÃO VERIFICADA INDEPENDENTEMENTE",
    "A regra do briefing pede confirmação de natureza jurídica 399-9 via base pública de CNPJ. Isso NÃO foi feito "
    "(ver item 2b). A classificação usada é a categoria atribuída pelo subagente de pesquisa (que presume 399-9 por "
    "default do tipo de entidade), não uma verificação factual. Trate o Top 50 como uma longlist priorizada, não "
    "como uma lista auditada.",
    "",
    "4. OAB (CATEGORIA 7)",
    "Cobertura muito abaixo do padrão das demais categorias: apenas 4 das 27 seccionais com dado robusto "
    "(nome, CNPJ, anuidade com fonte e data, Caixa de Assistência); 6 seccionais só com valor de anuidade "
    "(sem CNPJ/inscritos); 17 seccionais sem nenhuma pesquisa individual concluída (mesmo motivo: esgotamento "
    "do orçamento compartilhado de WebSearch). Conselho Federal da OAB: CNPJ 33.205.451/0001-14, 1.413.330 "
    "inscritos nacionais / 1.337.651 em exercício regular (base 2023, 1º Estudo Demográfico da Advocacia "
    "Brasileira, FGV/OAB, publicado jan/2025); piso de anuidade 2026 fixado em R$1.050 (Provimento 232/2025).",
    "",
    "5. CRUZAMENTO COM A PX",
    "Pipeline da PX: inputs/pipeline_px.xlsx, 23.720 linhas (Nome da empresa, CNPJ, Consultor XIPP, Situação). "
    "Casamento por CNPJ normalizado (14 dígitos) primeiro; para o que não casou por CNPJ, fuzzy match "
    "(rapidfuzz, token_sort_ratio ≥ 88, ou sigla como palavra inteira do nome PX ≥ 92) restrito a um subconjunto "
    "da PX com palavras-chave associativas no nome (ASSOCIA, CLUBE, OAB, SINDICATO, INSTITUTO etc. — 608 de "
    "23.720 linhas) para viabilizar o processamento. Isso é uma aproximação: pode haver falsos negativos "
    "(associação na PX com nome muito diferente do nosso levantamento) e a lista completa da PX não foi revisada "
    "linha a linha.",
    "",
    "6. REGRAS SEGUIDAS",
    "Campo sem fonte ficou vazio/'não encontrado' em 100% dos casos — nenhum dado foi preenchido por plausibilidade. "
    "Estimativas (quando algum subagente as fez) estão marcadas em 'tipo_fonte'/'Real ou estimado' e explicadas em "
    "Observações. Números de bases diferentes não foram somados nem comparados sem sinalização.",
]
for i, line in enumerate(meto_lines, start=1):
    c = ws_m.cell(row=i, column=1, value=line)
    c.font = Font(name=FONT_NAME, bold=(i in (1, 4, 11, 17, 20, 23, 27)), size=10)
    c.alignment = Alignment(wrap_text=True, vertical="top")

# ---------------- Pendências e hipóteses ----------------
ws_p = wb.create_sheet("Pendências e hipóteses")
ws_p.append(["Pendência", "Onde buscar quando o bloqueio for resolvido", "Impacto"])
pendencias = [
    ("Confirmar natureza jurídica (399-9) e razão social de todas as 234 entidades",
     "https://brasilapi.com.br/api/cnpj/v1/{cnpj} ou Receita Federal", "Alto — critério de inclusão não auditado"),
    ("Completar as 17 seccionais da OAB sem pesquisa (AC, AL, AP, AM, BA, CE, ES, MA, MT, PA, PB, PR, PI, RN, RO, SC, SE) "
     "e as 6 parciais (GO, RR, TO, MS, DF, PE)",
     "conselho federal da OAB (oab.org.br), sites de cada seccional, Migalhas (anuidades)", "Alto — 23/27 seccionais incompletas"),
    ("Levantar conselhos profissionais (CRM, CREA, COREN, CRC, CFM etc.) para a aba própria",
     "sites dos conselhos federais e regionais", "Médio — aba entregue vazia"),
    ("Fase 3 completa: mensalidade/anuidade, benefícios inclusos, benefícios de saúde já oferecidos, fundação "
     "vinculada, site, LinkedIn, cidade/UF para as 50 do Top 50",
     "sites institucionais de cada entidade (todos bloqueados nesta sessão)", "Alto — 6 das 10 colunas principais do briefing ficaram vazias/genéricas"),
    ("Fase 4 completa: fact-check independente de associados/cobrança/valor",
     "reprocessar do zero com subagentes sem contexto da pesquisa original", "Alto — checklist AAA do briefing não foi cumprido"),
    ("Revisar as 585 linhas da PX com nome de cara associativo que não casaram com nenhuma candidata do universo "
     "(work/px_assoc_nao_casadas.json) — pode haver associações relevantes na PX que nem entraram no nosso "
     "levantamento de 234",
     "revisão manual ou nova rodada de fuzzy match com threshold mais permissivo", "Médio — cruzamento PX pode estar incompleto"),
    ("Resolver duplicidade de sigla 'AMB' (Associação Médica Brasileira x Associação dos Magistrados Brasileiros) "
     "e variantes quase-homônimas de associações de aposentados (ANAP/ANAPB/ANAPPS/ANAPREVIS/ANAPI) por CNPJ",
     "base pública de CNPJ", "Baixo/Médio — risco de contagem duplicada ou confusão comercial"),
    ("Confirmar se AABB (categoria 5) se sobrepõe às associações de funcionários do Banco do Brasil já listadas "
     "(categoria 1)",
     "CNPJ e estatuto de cada entidade", "Baixo — risco de dupla contagem"),
]
for row in pendencias:
    ws_p.append(list(row))
for row in ws_p.iter_rows(min_row=2):
    for cell in row:
        cell.font = BASE_FONT
        cell.alignment = WRAP
style_header(ws_p, 3)
autosize(ws_p, [55, 45, 40])

# ---------------- Fontes ----------------
ws_f = wb.create_sheet("Fontes")
ws_f.append(["Entidade", "Campo", "Fonte / URL citada", "Data do dado", "Data de acesso (registrada pelo subagente)"])
url_re = re.compile(r"https?://\S+")
seen = set()
def collect_sources(rows):
    for r in rows:
        nome = r.get("nome", "")
        for campo, texto, data in [
            ("associados", r.get("fonte_associados", ""), r.get("data_fonte", "")),
            ("cobrança", r.get("evidencia_cobranca", ""), ""),
            ("observações", r.get("observacoes", ""), ""),
        ]:
            if not texto:
                continue
            urls = url_re.findall(texto) or [texto[:150]]
            for u in urls:
                key = (nome, campo, u)
                if key in seen:
                    continue
                seen.add(key)
                acc_m = re.search(r"(consulta(?:do)? em|acesso[:\s]*)(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})", texto, re.IGNORECASE)
                ws_f.append([nome, campo, u, data, acc_m.group(2) if acc_m else ""])

collect_sources(oab)
collect_sources(fora_criterio)
collect_sources(candidatos)
for row in ws_f.iter_rows(min_row=2):
    for cell in row:
        cell.font = BASE_FONT
        cell.alignment = WRAP
style_header(ws_f, 5)
autosize(ws_f, [36, 14, 60, 16, 20])
print(f"Fontes: {ws_f.max_row - 1} linhas")

wb.save(OUT / "Top50_Associacoes_XIPP.xlsx")
print("Planilha salva em output/Top50_Associacoes_XIPP.xlsx")

with open(WORK / "top50_final.json", "w", encoding="utf-8") as f:
    json.dump(top50, f, ensure_ascii=False, indent=2)

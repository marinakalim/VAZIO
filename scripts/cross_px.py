import json, re, unicodedata
from pathlib import Path
import openpyxl
from rapidfuzz import fuzz

ROOT = Path("/home/user/VAZIO")
WORK = ROOT / "work"

def strip_accents(s):
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def norm_name(s):
    s = strip_accents(s or "").upper()
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def norm_cnpj(s):
    if not s:
        return ""
    digits = re.sub(r"\D", "", s)
    return digits if len(digits) == 14 else ""

print("Carregando pipeline PX...")
wb = openpyxl.load_workbook(ROOT / "inputs" / "pipeline_px.xlsx", data_only=True, read_only=True)
ws = wb["Sheet1"]
px_rows = []
for row in ws.iter_rows(min_row=2, values_only=True):
    nome, cnpj, consultor, situacao = (row + (None,) * 4)[:4]
    if not nome:
        continue
    px_rows.append({
        "nome": nome, "cnpj_norm": norm_cnpj(cnpj), "nome_norm": norm_name(nome),
        "consultor": consultor, "situacao": situacao
    })
print(f"PX: {len(px_rows)} linhas carregadas")

px_by_cnpj = {r["cnpj_norm"]: r for r in px_rows if r["cnpj_norm"]}

ASSOC_KEYWORDS = ["ASSOCIA", "CLUBE", "ORDEM DOS ADVOGADOS", "OAB", "SINDICATO", "CAIXA DE ASSISTENCIA",
                   "INSTITUTO", "UNIAO", "FEDERACAO", "CONFEDERACAO", "GREMIO", "IATE", "TENIS", "CIRCULO"]
px_assoc_subset = [r for r in px_rows if any(k in r["nome_norm"] for k in ASSOC_KEYWORDS)]
print(f"PX subconjunto com palavras-chave associativas (para fuzzy match): {len(px_assoc_subset)}")

def match_px(entity_cnpj, entity_nome, entity_sigla=""):
    ck = norm_cnpj(entity_cnpj)
    if ck and ck in px_by_cnpj:
        m = px_by_cnpj[ck]
        return {"na_pipeline_px": "sim", "estagio_px": m["situacao"], "responsavel_px": m["consultor"],
                "match_tipo": "CNPJ", "match_score": 100, "px_nome": m["nome"]}
    nn = norm_name(entity_nome)
    sn = norm_name(entity_sigla)
    best = None
    best_score = 0
    for r in px_assoc_subset:
        score = fuzz.token_sort_ratio(nn, r["nome_norm"])
        if sn and len(sn) >= 3 and sn in r["nome_norm"].split():
            score = max(score, 92)
        if score > best_score:
            best_score = score
            best = r
    if best and best_score >= 88:
        return {"na_pipeline_px": "sim", "estagio_px": best["situacao"], "responsavel_px": best["consultor"],
                "match_tipo": "fuzzy_nome", "match_score": best_score, "px_nome": best["nome"]}
    return {"na_pipeline_px": "não", "estagio_px": "", "responsavel_px": "", "match_tipo": "", "match_score": 0, "px_nome": ""}

def process_file(path):
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    for r in rows:
        m = match_px(r.get("cnpj", ""), r.get("nome", ""), r.get("sigla", ""))
        r["_px"] = m
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    return rows

all_matched = []
for fname in ["cat_oab.json", "cat_fora_criterio.json", "cat_candidatos_rankeados.json"]:
    rows = process_file(WORK / fname)
    all_matched.extend(rows)
    n_match = sum(1 for r in rows if r["_px"]["na_pipeline_px"] == "sim")
    print(f"{fname}: {len(rows)} linhas, {n_match} casadas na PX")

# PX entries that are associations (per keyword) not matched to anything in our universe at all
matched_px_names = set()
for r in all_matched:
    if r["_px"]["na_pipeline_px"] == "sim":
        matched_px_names.add(r["_px"]["px_nome"])

px_assoc_unmatched = [r for r in px_assoc_subset if r["nome"] not in matched_px_names]
with open(WORK / "px_assoc_nao_casadas.json", "w", encoding="utf-8") as f:
    json.dump(px_assoc_unmatched, f, ensure_ascii=False, indent=2, default=str)
print(f"\nPX com cara de associação mas não casada com nenhuma candidata do universo: {len(px_assoc_unmatched)}")

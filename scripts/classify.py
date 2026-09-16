import json, re
from pathlib import Path

ROOT = Path("/home/user/VAZIO")
WORK = ROOT / "work"

with open(WORK / "consolidado.json", encoding="utf-8") as f:
    rows = json.load(f)

def has_word(text, words):
    text = (text or "").upper()
    return any(re.search(r"\b" + w + r"\b", text) for w in words)

EXCLUDE_LEGAL_FORM = ["SINDICATO", "FEDERACAO", "FEDERAÇÃO", "CONFEDERACAO", "CONFEDERAÇÃO",
                       "COOPERATIVA"]
EXCLUDE_NAME_HINTS = ["SINDNAPI", "CONTAG", "COBAP", "CENTRAPE", "FENAPEF"]

CONSELHO_HINTS = ["CONSELHO REGIONAL", "CONSELHO FEDERAL", "CRM", "CREA", "COREN", "CRC ", "CRO ",
                   "CFM", "CFC", "CREF"]

PROTECAO_VEICULAR_HINTS = ["PROTECAO VEICULAR", "PROTEÇÃO VEICULAR", "MUTUALISMO", "MUTUALISTA"]

oab = []
fora_criterio = []
conselhos = []
candidatos = []  # pool for Top 50 / Longlist ranking

for r in rows:
    nome = r.get("nome", "") or ""
    sigla = r.get("sigla", "") or ""
    categoria = str(r.get("categoria", ""))
    obs = r.get("observacoes", "") or ""
    combined = f"{nome} {sigla}"

    if categoria == "7-federal":
        # Conselho Federal da OAB e um total nacional de referencia, nao uma
        # seccional que disputa o ranking - fica documentado so na Metodologia.
        continue
    if categoria.startswith("7"):
        oab.append(r)
        continue

    # explicit sindical/federative/confederative legal form -> excluded
    is_excluded_form = has_word(combined, EXCLUDE_LEGAL_FORM) or any(h in sigla.upper() or h in nome.upper() for h in EXCLUDE_NAME_HINTS)
    if is_excluded_form:
        r["_motivo_fora_criterio"] = "Natureza sindical/federativa/confederativa (2º grau), não associação direta de pessoas físicas 399-9 — conforme regra do briefing."
        fora_criterio.append(r)
        continue

    if has_word(combined, CONSELHO_HINTS) or "conselho profissional" in obs.lower():
        r["_motivo_conselho"] = "Conselho profissional (autarquia de fiscalização) — aba própria para decisão da XIPP."
        conselhos.append(r)
        continue

    if has_word(combined, PROTECAO_VEICULAR_HINTS) or any(h.lower() in obs.lower() for h in PROTECAO_VEICULAR_HINTS):
        r["_alerta_regulatorio"] = "Associação de proteção veicular/mutualismo — risco regulatório e reputacional (art. briefing). Decisão de inclusão cabe à XIPP."

    candidatos.append(r)

print(f"OAB (categoria 7): {len(oab)}")
print(f"Fora do critério (sindical/federativo): {len(fora_criterio)}")
print(f"Conselhos profissionais: {len(conselhos)}")
print(f"Pool de candidatas (Top50/Longlist): {len(candidatos)}")

def rank_key(r):
    a = r.get("associados")
    has_num = isinstance(a, (int, float)) and a is not None
    return (0 if has_num else 1, -(a or 0))

candidatos_sorted = sorted(candidatos, key=rank_key)
oab_sorted = sorted(oab, key=rank_key)

with open(WORK / "cat_oab.json", "w", encoding="utf-8") as f:
    json.dump(oab_sorted, f, ensure_ascii=False, indent=2)
with open(WORK / "cat_fora_criterio.json", "w", encoding="utf-8") as f:
    json.dump(fora_criterio, f, ensure_ascii=False, indent=2)
with open(WORK / "cat_conselhos.json", "w", encoding="utf-8") as f:
    json.dump(conselhos, f, ensure_ascii=False, indent=2)
with open(WORK / "cat_candidatos_rankeados.json", "w", encoding="utf-8") as f:
    json.dump(candidatos_sorted, f, ensure_ascii=False, indent=2)

com_numero = [r for r in candidatos_sorted if isinstance(r.get("associados"), (int, float))]
print(f"\nCandidatas gerais com numero de associados confirmado (fonte+data, nao-OAB): {len(com_numero)}")
com_numero_oab = [r for r in oab_sorted if isinstance(r.get("associados"), (int, float))]
print(f"Seccionais OAB com numero de inscritos confirmado: {len(com_numero_oab)}")

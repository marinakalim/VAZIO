import json, re, unicodedata, glob
from pathlib import Path

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
    if len(digits) != 14:
        return ""
    return digits

FILES = sorted(glob.glob(str(WORK / "universo_*.jsonl")))

rows = []
for fp in FILES:
    src = Path(fp).name
    with open(fp, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"SKIP malformed line {src}:{i}: {e}")
                continue
            d["_source_file"] = src
            rows.append(d)

print(f"Total linhas brutas carregadas: {len(rows)}")

# dedup by CNPJ first, then by normalized name
by_cnpj = {}
by_name = {}
deduped = []
dup_log = []

for r in rows:
    cnpj_key = norm_cnpj(r.get("cnpj", ""))
    name_key = norm_name(r.get("nome", ""))
    key = ("cnpj", cnpj_key) if cnpj_key else ("name", name_key)
    existing_idx = by_cnpj.get(cnpj_key) if cnpj_key else by_name.get(name_key)
    if existing_idx is not None:
        existing = deduped[existing_idx]
        # merge: keep the row with more non-empty fields; log the merge
        def fill_score(d):
            return sum(1 for k, v in d.items() if v not in (None, "", "não encontrado") and not k.startswith("_"))
        if fill_score(r) > fill_score(existing):
            r["_merged_from"] = existing.get("_source_file")
            deduped[existing_idx] = r
        else:
            existing.setdefault("_also_seen_in", []).append(r.get("_source_file"))
        dup_log.append((r.get("nome"), r.get("_source_file"), existing.get("_source_file")))
        continue
    idx = len(deduped)
    deduped.append(r)
    if cnpj_key:
        by_cnpj[cnpj_key] = idx
    if name_key:
        by_name[name_key] = idx

print(f"Após dedupe: {len(deduped)} entidades únicas ({len(dup_log)} duplicatas removidas)")

with open(WORK / "consolidado.json", "w", encoding="utf-8") as f:
    json.dump(deduped, f, ensure_ascii=False, indent=2)

with open(WORK / "dedup_log.txt", "w", encoding="utf-8") as f:
    for nome, src, kept_src in dup_log:
        f.write(f"{nome} | visto em {src}, mantido de {kept_src}\n")

print("Gravado work/consolidado.json e work/dedup_log.txt")

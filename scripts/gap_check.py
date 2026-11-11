"""Phase 1 gap check: collect metadata (Crossref) and abstracts (saved search results)
for existing review articles, as input for Table T1.
Output: data/gap_check/reviews_meta.csv and data/gap_check/crossref/<doi>.json"""
import csv, json, glob, time, re
from pathlib import Path
import requests
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "gap_check"; (OUT / "crossref").mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "NTL-systematic-review/0.1 (academic research script)"}
DOIS = [l.strip().lower() for l in open(ROOT / "data" / "gap_check" / "review_dois.txt") if l.strip() and not l.startswith("#")]

abstracts = {}
for f in glob.glob(str(ROOT / "data" / "raw_api" / "search" / "*.json")) + glob.glob(str(ROOT / "data" / "raw_api" / "phase1_pilot" / "*.json")):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    for r in d.get("records", []):
        if r.get("doi") and len(r.get("abstract") or "") > len(abstracts.get(r["doi"], "")):
            abstracts[r["doi"]] = r["abstract"]

rows = []
for doi in DOIS:
    fp = OUT / "crossref" / (re.sub(r"[^a-z0-9]+", "_", doi) + ".json")
    if fp.exists():
        m = json.load(open(fp, encoding="utf-8"))
    else:
        r = requests.get(f"https://api.crossref.org/works/{doi}", headers=UA, timeout=40)
        m = r.json()["message"] if r.ok else {}
        json.dump(m, open(fp, "w", encoding="utf-8"))
        time.sleep(0.5)
    if not m:
        rows.append({"doi": doi, "status": "NOT IN CROSSREF"}); continue
    yr = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
    a = m.get("author") or [{}]
    ab = abstracts.get(doi) or re.sub(r"<[^>]+>", " ", m.get("abstract", "") or "")
    rows.append({"doi": doi, "status": "ok", "year": yr, "first_author": a[0].get("family", ""),
                 "n_authors": len(m.get("author") or []), "title": " ".join((m.get("title") or [""])[0].split()),
                 "venue": (m.get("container-title") or [""])[0], "type": m.get("type"),
                 "reference_count": m.get("reference-count") or m.get("references-count"),
                 "abstract": " ".join(ab.split())})
with open(OUT / "reviews_meta.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["doi", "status", "year", "first_author", "n_authors", "title", "venue", "type", "reference_count", "abstract"])
    w.writeheader(); w.writerows(rows)
print(len(rows), "rows")

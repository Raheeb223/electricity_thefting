"""Search-coverage (recall) test against an external reference set.

Known-relevant set: references cited by the 14 background reviews (Crossref reference
lists, from the cached Crossref records) that (a) have a DOI, (b) were published
2010 or later, and (c) have a title about electricity theft / NTL (theft, pilferage,
fraud, non-technical, tamper + electric/energy/power/meter context). Titles are taken
from the reference entry or, if absent, from one Crossref lookup per DOI (cached).
Recall = share of this set present among all records retrieved by our search
(data/records_all.csv, before any filtering), matched by DOI or fuzzy title (>= 92).
Output: data/coverage_test.csv and a printed summary.
"""
import json
import re
import time
from pathlib import Path

import pandas as pd
import requests
from rapidfuzz import fuzz, process

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "refs" / "crossref_cache"
UA = {"User-Agent": "NTL-systematic-review/0.2 (coverage test)"}
REVIEW_KEYS = ["glauner2017challenge", "papadimitriou2017non", "saeed2020detection", "gupta2020detection",
               "desouzasavian2021non", "yan2022performance", "xia2022detection", "badr2023review",
               "stracqualursi2023systematic", "kgaphola2024electricity", "kim2024data", "sibiya2024electricity",
               "apata2026machine", "labate2026comprehensive"]
TOPIC = re.compile(r"(theft|pilfer|fraud|non[- ]?technical|nontechnical|tamper|\bntls?\b|illegal (connection|consumption)|"
                   r"energy (stealing|thieves)|electricity thie)", re.I)


def cached(doi):
    fp = CACHE / (re.sub(r"[^a-z0-9]+", "_", doi.lower()) + ".json")
    if fp.exists():
        return json.load(open(fp, encoding="utf-8"))
    try:
        r = requests.get(f"https://api.crossref.org/works/{doi}", headers=UA, timeout=40)
        msg = r.json()["message"] if r.ok else {}
    except Exception:
        msg = {}
    json.dump(msg, open(fp, "w", encoding="utf-8"))
    time.sleep(0.3)
    return msg


def norm(t):
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", (t or "").lower()).split())


def main():
    km = pd.read_csv(ROOT / "refs" / "key_map.csv")
    rev = km[km.key.isin(REVIEW_KEYS)]
    refs = []
    for _, r in rev.iterrows():
        msg = cached(r.doi)
        for ref in msg.get("reference") or []:
            d = (ref.get("DOI") or "").lower().strip()
            if d:
                refs.append({"review": r.key, "doi": d, "title": ref.get("article-title") or "",
                             "year": ref.get("year") or ""})
    df = pd.DataFrame(refs).drop_duplicates("doi")
    print("references with DOI in review lists:", len(df))
    need = df[(df.title == "") | (df.year == "")]
    for i, row in need.iterrows():  # one cached lookup per DOI lacking title/year
        m = cached(row.doi)
        if m:
            df.at[i, "title"] = df.at[i, "title"] or " ".join(m.get("title") or [""])
            df.at[i, "year"] = df.at[i, "year"] or str(((m.get("issued") or {}).get("date-parts") or [[""]])[0][0])
    df["year_n"] = pd.to_numeric(df.year.astype(str).str[:4], errors="coerce")
    known = df[(df.year_n >= 2010) & df.title.str.contains(TOPIC)].copy()
    allr = pd.read_csv(ROOT / "data" / "records_all.csv", dtype=str).fillna("")
    dois = set(allr.doi.str.lower().str.strip())
    titles = [norm(t) for t in allr.title]
    tset = sorted(set(titles))
    found = []
    for _, k in known.iterrows():
        if k.doi in dois:
            found.append("doi"); continue
        best = process.extractOne(norm(k.title), tset, scorer=fuzz.token_sort_ratio)
        found.append("title" if best and best[1] >= 92 else "")
    known["found_by"] = found
    known.to_csv(ROOT / "data" / "coverage_test.csv", index=False)
    n, f = len(known), (known.found_by != "").sum()
    print(f"known-relevant references (2010+, theft/NTL title): {n}; retrieved by our search: {f} ({100 * f / max(n, 1):.1f}%)")
    print("not retrieved (first 15):")
    for t in known[known.found_by == ""].title.head(15):
        print(" -", t[:110])


if __name__ == "__main__":
    main()

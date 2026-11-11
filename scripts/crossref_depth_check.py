"""R2 (M4): was the Crossref search truncated?

Each of the 25 Crossref phrase queries was run for the top 200 relevance-ranked results
(25 x 200 = 5,000; a design cap, because Crossref's query.bibliographic matches any term
and returns millions of loosely relevant works). This script fetches ranks 201-1,000
for every query, applies the same local Boolean re-check (queries.match_strings) and
counts records that pass it and are NOT already among the 12,041 retrieved records.
Any such records are saved for screening. Output: data/raw_api/crossref_depth/*.json,
data/crossref_depth_summary.csv, data/crossref_depth_new_records.csv.
"""
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from queries import CROSSREF as CROSSREF_QUERIES, match_strings  # noqa: E402

OUT = ROOT / "data" / "raw_api" / "crossref_depth"
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "NTL-systematic-review/0.2 (depth check)"}


def main():
    have = set(pd.read_csv(ROOT / "data" / "records_all.csv", dtype=str).fillna("").doi.str.lower())
    summ, new = [], []
    for i, q in enumerate(CROSSREF_QUERIES):
        fp = OUT / f"q{i:02d}.json"
        if fp.exists():
            items = json.load(open(fp, encoding="utf-8"))
        else:
            items = []
            for offset in range(200, 1000, 100):
                for attempt in range(3):
                    try:
                        r = requests.get("https://api.crossref.org/works", headers=UA, timeout=60, params={
                            "query.bibliographic": q, "rows": 100, "offset": offset,
                            "filter": "from-pub-date:2010-01-01,until-pub-date:2026-12-31",
                            "select": "DOI,title,issued,container-title,type,abstract"})
                        if r.ok:
                            items += [{"rank": offset + k + 1, **it} for k, it in enumerate(r.json()["message"]["items"])]
                            break
                    except requests.RequestException:
                        pass
                    time.sleep(5)
                time.sleep(1.2)
            json.dump(items, open(fp, "w", encoding="utf-8"))
        bands = {"201-400": [0, 0], "401-600": [0, 0], "601-1000": [0, 0]}
        for it in items:
            title = " ".join((it.get("title") or [""])[0].split())
            ab = " ".join(re.sub(r"<[^>]+>", " ", it.get("abstract") or "").split())
            ok = bool(match_strings(title, ab))
            doi = (it.get("DOI") or "").lower()
            b = "201-400" if it["rank"] <= 400 else ("401-600" if it["rank"] <= 600 else "601-1000")
            if ok:
                bands[b][0] += 1
                if doi not in have:
                    bands[b][1] += 1
                    new.append({"query": q, "rank": it["rank"], "doi": doi, "title": title, "abstract": ab,
                                "year": ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0],
                                "venue": (it.get("container-title") or [""])[0], "type": it.get("type")})
        summ.append({"query": q, "fetched": len(items), **{f"pass_{k}": v[0] for k, v in bands.items()},
                     **{f"new_{k}": v[1] for k, v in bands.items()}})
        print(i, q[:40], summ[-1])
    pd.DataFrame(summ).to_csv(ROOT / "data" / "crossref_depth_summary.csv", index=False)
    nd = pd.DataFrame(new).drop_duplicates("doi") if new else pd.DataFrame()
    nd.to_csv(ROOT / "data" / "crossref_depth_new_records.csv", index=False)
    print("new Boolean-passing records beyond rank 200:", len(nd))


if __name__ == "__main__":
    main()

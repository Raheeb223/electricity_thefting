"""Extra open-access retrieval for synthesis studies still without a PDF.

Sources: Semantic Scholar Graph API (openAccessPdf, arXiv id) and arXiv. Publisher hosts
listed in data/fulltext_stopped_hosts.txt are never contacted (retrieval rules).
One request at a time; 5-10 s before any download, 3 s between API calls.
Log: data/fulltext_oa_extra_log.csv
"""
import csv
import random
import time
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "fulltext"
UA = {"User-Agent": "NTL-systematic-review/0.2 (academic research; one request at a time)"}
STOPPED = set((ROOT / "data" / "fulltext_stopped_hosts.txt").read_text().split())


def main():
    s = pd.read_csv(ROOT / "data" / "synthesis_set.csv", keep_default_na=False)
    rec = pd.read_csv(ROOT / "data" / "records_dedup.csv", keep_default_na=False, usecols=["record_id", "doi"])
    s = s.merge(rec, on="record_id", how="left")
    todo = [r for r in s.itertuples() if not (OUT / f"{r.record_id}.pdf").exists() and r.doi]
    log = []
    for r in todo:
        time.sleep(3)
        try:
            j = requests.get(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{r.doi}",
                             params={"fields": "openAccessPdf,externalIds"}, headers=UA, timeout=40)
        except requests.RequestException as e:
            log.append((r.record_id, "api error", str(e)[:80])); continue
        if j.status_code == 429:
            time.sleep(30); log.append((r.record_id, "api 429", "")); continue
        if not j.ok:
            log.append((r.record_id, f"api {j.status_code}", "")); continue
        d = j.json()
        urls = []
        if (d.get("openAccessPdf") or {}).get("url"):
            urls.append(d["openAccessPdf"]["url"])
        ax = (d.get("externalIds") or {}).get("ArXiv")
        if ax:
            urls.append(f"https://arxiv.org/pdf/{ax}")
        got = False
        for u in urls:
            host = urlparse(u).netloc
            if host in STOPPED or any(h in host for h in ("mdpi.com", "sciencedirect", "wiley", "acm.org", "emerald")):
                log.append((r.record_id, "skipped stopped host", u)); continue
            time.sleep(random.uniform(5, 10))
            try:
                p = requests.get(u, headers=UA, timeout=90)
            except requests.RequestException:
                continue
            if p.status_code in (403, 429):
                STOPPED.add(host)
                with open(ROOT / "data" / "fulltext_stopped_hosts.txt", "a") as f:
                    f.write(host + "\n")
                log.append((r.record_id, f"STOP {host} {p.status_code}", u)); continue
            if p.ok and p.content[:5] == b"%PDF-" and len(p.content) > 20000:
                (OUT / f"{r.record_id}.pdf").write_bytes(p.content)
                log.append((r.record_id, "downloaded", u)); got = True
                print(r.record_id, "saved", host); break
        if not got and not urls:
            log.append((r.record_id, "no OA copy listed", ""))
    with open(ROOT / "data" / "fulltext_oa_extra_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["record_id", "status", "url"]); w.writerows(log)
    print("saved:", sum(1 for x in log if x[1] == "downloaded"), "of", len(todo))


if __name__ == "__main__":
    main()

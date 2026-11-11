"""Download open-access full texts for the full-text targets, politely.

Retrieval rules:
- only records that passed screening (data/fulltext_targets.csv);
- one request at a time, 6-9 s between requests;
- open-access locations only (OpenAlex best OA location). Subscription publisher
  pages are NOT scraped: systematic downloading usually breaks library licence terms.
  Those papers go to data/missing_fulltext.csv for the author to download by hand;
- a 403, 429 or CAPTCHA/"unusual activity" page from a host stops all further requests
  to that host and is reported (stop condition);
- PDFs are saved as data/fulltext/<record_id>.pdf; existing files are skipped, so the
  script is safe to re-run.
"""
import csv
import random
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "fulltext"
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "NTL-systematic-review/0.1 (academic research; single polite requests)"}
BLOCK_PAT = re.compile(r"captcha|unusual (traffic|activity)|are you a robot|access denied", re.I)


def main():
    rows = list(csv.DictReader(open(ROOT / "data" / "fulltext_targets.csv", encoding="utf-8")))
    blocked, log, missing = set(), [], []
    for r in rows:
        rid, url = r["record_id"], (r.get("oa_url") or "").strip()
        dest = OUT / f"{rid}.pdf"
        if dest.exists() and dest.stat().st_size > 10_000:
            log.append((rid, "exists", url)); continue
        if not url:
            missing.append((rid, r["doi"], r["title"], "no open-access copy found")); continue
        host = urlparse(url).netloc
        if host in blocked:
            missing.append((rid, r["doi"], r["title"], f"host {host} blocked earlier")); continue
        try:
            resp = requests.get(url, headers=UA, timeout=60, allow_redirects=True)
        except requests.RequestException as e:
            missing.append((rid, r["doi"], r["title"], f"network error: {e}")); time.sleep(6); continue
        body_start = resp.content[:4]
        text_head = resp.text[:3000] if b"%PDF" not in body_start else ""
        if resp.status_code in (403, 429) or BLOCK_PAT.search(text_head):
            blocked.add(host)
            missing.append((rid, r["doi"], r["title"], f"STOP: host {host} returned {resp.status_code}/block page"))
            print(f"STOP CONDITION: {host} returned {resp.status_code}; no further requests to it")
        elif resp.ok and body_start == b"%PDF":
            dest.write_bytes(resp.content); log.append((rid, "downloaded", url))
        else:
            missing.append((rid, r["doi"], r["title"], f"not a PDF (HTTP {resp.status_code}); landing page only"))
        print(rid, resp.status_code, host)
        time.sleep(random.uniform(6, 9))
    with open(ROOT / "data" / "missing_fulltext.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["record_id", "doi", "title", "reason"]); w.writerows(missing)
    with open(ROOT / "data" / "fulltext_download_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["record_id", "status", "url"]); w.writerows(log)
    print(f"downloaded/existing: {len(log)}  missing: {len(missing)}  blocked hosts: {sorted(blocked)}")
    return 2 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())

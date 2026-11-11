"""Second open-access retrieval pass for records still missing a full text.

Looks up ALL open-access locations (OpenAlex 'locations', Semantic Scholar
'openAccessPdf') rather than only the best one, and prefers repository copies.
Retrieval rules kept from fetch_fulltext.py:
- hosts that refused access earlier are never contacted (BLOCKED below);
- DOI links are resolved WITHOUT following the redirect (one HEAD to doi.org) and are
  skipped if they lead to a blocked host;
- one request at a time, 6-9 s apart; any new 403/429/CAPTCHA blocks that host too.
Writes data/fulltext/<record_id>.pdf and data/fulltext_alt_log.csv.
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
UA = {"User-Agent": "NTL-systematic-review/0.2 (academic research; single polite requests)"}
BLOCK_PAT = re.compile(r"captcha|unusual (traffic|activity)|are you a robot|access denied", re.I)
BLOCKED = {"www.mdpi.com", "mdpi.com", "mdpi-res.com", "www.sciencedirect.com", "sciencedirect.com",
           "linkinghub.elsevier.com", "onlinelibrary.wiley.com", "www.colibri.udelar.edu.uy",
           "pdf.sciencedirectassets.com"}


def pause():
    time.sleep(random.uniform(6, 9))


def blocked(host):
    return any(host == b or host.endswith("." + b) for b in BLOCKED)


def candidates(doi):
    urls = []
    try:
        r = requests.get(f"https://api.openalex.org/works/doi:{doi}", headers=UA, timeout=40)
        if r.ok:
            for loc in r.json().get("locations") or []:
                if loc.get("pdf_url"):
                    src = (loc.get("source") or {}).get("type") or ""
                    urls.append((0 if src == "repository" else 1, loc["pdf_url"]))
    except requests.RequestException:
        pass
    pause()
    try:
        r = requests.get(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}",
                         params={"fields": "openAccessPdf"}, headers=UA, timeout=40)
        if r.ok and (r.json().get("openAccessPdf") or {}).get("url"):
            urls.append((1, r.json()["openAccessPdf"]["url"]))
    except requests.RequestException:
        pass
    pause()
    seen, out = set(), []
    for _, u in sorted(urls):
        if u not in seen:
            seen.add(u); out.append(u)
    return out


def resolve_doi_host(url):
    """For doi.org links, read the redirect target without contacting the publisher."""
    if "doi.org" not in urlparse(url).netloc:
        return url
    try:
        r = requests.head(url, headers=UA, timeout=30, allow_redirects=False)
        return r.headers.get("Location", url)
    except requests.RequestException:
        return url


def main():
    missing = list(csv.DictReader(open(ROOT / "data" / "missing_fulltext.csv", encoding="utf-8")))
    log = []
    for m in missing:
        rid, doi = m["record_id"], m["doi"]
        dest = OUT / f"{rid}.pdf"
        if dest.exists() and dest.stat().st_size > 10_000:
            log.append((rid, "exists", "")); continue
        got = False
        for url in candidates(doi):
            target = resolve_doi_host(url)
            host = urlparse(target).netloc.lower()
            if blocked(host):
                log.append((rid, f"skipped blocked host {host}", url)); continue
            try:
                resp = requests.get(target, headers=UA, timeout=60, allow_redirects=True)
            except requests.RequestException as e:
                log.append((rid, f"network error {e.__class__.__name__}", target)); pause(); continue
            final_host = urlparse(resp.url).netloc.lower()
            head = resp.content[:4]
            text_head = resp.text[:3000] if head != b"%PDF" else ""
            if resp.status_code in (403, 429) or BLOCK_PAT.search(text_head):
                BLOCKED.add(final_host)
                log.append((rid, f"STOP host {final_host} HTTP {resp.status_code}; host now blocked", target))
                print("STOP CONDITION for host", final_host)
            elif resp.ok and head == b"%PDF":
                dest.write_bytes(resp.content); got = True
                log.append((rid, "downloaded", target)); print(rid, "downloaded from", final_host)
            else:
                log.append((rid, f"not a PDF (HTTP {resp.status_code})", target))
            pause()
            if got:
                break
        if not got:
            log.append((rid, "no usable open-access copy", ""))
    with open(ROOT / "data" / "fulltext_alt_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["record_id", "status", "url"]); w.writerows(log)
    n = sum(1 for _, s, _ in log if s == "downloaded")
    print(f"new PDFs: {n}; blocked hosts now: {sorted(BLOCKED)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

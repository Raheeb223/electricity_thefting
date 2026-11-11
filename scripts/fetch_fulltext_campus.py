"""Round-2 full-text retrieval for the priority synthesis (R3/R6).

Targets: priority studies under the chosen scope variant (data/priority_synthesis_B.csv)
plus every row of human_tasks/fulltext_todo.csv. All passed title/abstract screening.

Rules followed:
- one request at a time, 5-10 s random wait before every request, no parallelism;
- open-access copy first (OpenAlex best/other OA PDF locations), then the publisher
  page through campus access (citation_pdf_url meta tag or known PDF path);
- an HTTP 403/429 or a CAPTCHA / "unusual activity" / "access denied" page from a host
  stops ALL further requests to that host for the rest of the run (no retry, no
  workaround);
- if five publisher hosts in a row return non-PDF responses, the run stops (possible
  loss of campus access);
- honest User-Agent, no browser spoofing, no cookies beyond the session;
- PDFs saved to data/fulltext/<record_id>.pdf (private use only, git-ignored).
Log: data/fulltext_campus_log.csv; still missing: data/missing_fulltext_round2.csv.
"""
import csv
import random
import re
import sys
import time
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlparse, quote

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "fulltext"
UA = {"User-Agent": "NTL-systematic-review/0.2 (academic research; one request at a time)"}
BLOCK = re.compile(r"captcha|unusual (traffic|activity)|are you a robot|access denied|"
                   r"verify you are human|cf-chl|just a moment\.\.\.", re.I)
S = requests.Session()
S.headers.update(UA)
STOPPED = ROOT / "data" / "fulltext_stopped_hosts.txt"   # persists across runs: never retried
blocked = set(STOPPED.read_text(encoding="utf-8").split()) if STOPPED.exists() else set()
last = [0.0]
RESOLVERS = {"doi.org", "dx.doi.org", "api.openalex.org"}  # redirectors are never blocked themselves


def wait(host=""):
    # 5-10 s before every publisher request (retrieval rules); the metadata API and
    # the DOI resolver are not publisher sites, so a 1 s pause is used for them.
    lo, hi = (1, 1.5) if host in RESOLVERS else (5, 10)
    gap = random.uniform(lo, hi) - (time.time() - last[0])
    if gap > 0:
        time.sleep(gap)
    last[0] = time.time()


def get(url):
    host = urlparse(url).netloc
    if host in blocked:
        return None, f"host {host} stopped earlier"
    r = None
    for _ in range(8):  # follow redirects by hand so a stopped host is never contacted
        if urlparse(url).netloc in blocked:
            return None, f"redirect to stopped host {urlparse(url).netloc}"
        wait(urlparse(url).netloc)
        try:
            r = S.get(url, timeout=60, allow_redirects=False)
        except requests.RequestException as e:
            return None, f"network error {type(e).__name__}"
        if r.is_redirect or r.status_code in (301, 302, 303, 307, 308):
            nxt = r.headers.get("Location")
            if not nxt:
                break
            url = urljoin(url, nxt)
            continue
        break
    fhost = urlparse(r.url).netloc
    head = r.content[:5]
    if r.status_code in (403, 429) or (head != b"%PDF-" and BLOCK.search(r.text[:20000] if r.content else "")):
        stop = {fhost} | ({host} if host not in RESOLVERS else set())
        blocked.update(stop - RESOLVERS)
        with open(STOPPED, "a", encoding="utf-8") as fh:
            for h in sorted(stop - RESOLVERS):
                fh.write(h + chr(10))
        print(f"  STOP CONDITION: {fhost} returned {r.status_code}/block page; no further requests to it")
        return None, f"STOP {fhost} {r.status_code}"
    return r, ""


def is_pdf(r):
    return r is not None and r.ok and r.content[:5] == b"%PDF-" and len(r.content) > 20_000


def openalex_pdfs(doi):
    r, _ = get(f"https://api.openalex.org/works/https://doi.org/{quote(doi)}")
    if r is None or not r.ok:
        return []
    try:
        w = r.json()
    except ValueError:
        return []
    urls = []
    for loc in [w.get("best_oa_location")] + (w.get("locations") or []):
        if loc and loc.get("is_oa") and loc.get("pdf_url"):
            urls.append(loc["pdf_url"])
    return list(dict.fromkeys(urls))


def publisher_pdf_candidates(doi, landing):
    cands = []
    m = re.search(r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)', landing.text, re.I) \
        or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_pdf_url', landing.text, re.I)
    if m:
        cands.append(urljoin(landing.url, unescape(m.group(1))))
    host = urlparse(landing.url).netloc
    if "ieeexplore" in host:
        a = re.search(r"/document/(\d+)", landing.url)
        if a:
            cands.append(f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={a.group(1)}&ref=")
    elif "link.springer.com" in host:
        cands.append(f"https://link.springer.com/content/pdf/{doi}.pdf")
    elif "onlinelibrary.wiley.com" in host or "ietresearch" in host:
        cands.append(f"https://{host}/doi/pdfdirect/{doi}")
    elif "tandfonline" in host:
        cands.append(f"https://www.tandfonline.com/doi/pdf/{doi}")
    elif "mdpi.com" in host:
        cands.append(landing.url.rstrip("/") + "/pdf")
    return list(dict.fromkeys(cands))


def targets():
    pri = pd.read_csv(ROOT / "data" / "priority_synthesis_B.csv", keep_default_na=False)
    todo = pd.read_csv(ROOT / "human_tasks" / "fulltext_todo.csv", keep_default_na=False)
    rec = pd.read_csv(ROOT / "data" / "records_dedup.csv", keep_default_na=False,
                      usecols=["record_id", "doi", "title", "oa_url"])
    ids = list(dict.fromkeys(list(pri.record_id) + list(todo.record_id)))
    t = rec.set_index("record_id").reindex(ids).reset_index()
    t["group"] = ["priority" if i in set(pri.record_id) else "todo_list" for i in ids]
    return t


def main():
    t = targets()
    log, missing, consecutive_fail = [], [], 0
    for _, row in t.iterrows():
        rid, doi = row.record_id, str(row.doi or "").strip().lower()
        dest = OUT / f"{rid}.pdf"
        if dest.exists() and dest.stat().st_size > 20_000:
            log.append((rid, row.group, "exists", "", "")); continue
        if not doi:
            missing.append((rid, row.group, "", row.title, "no DOI")); continue
        print(rid, doi)
        got, how, why = None, "", []
        # 1) open-access copies
        oa = ([row.oa_url] if str(row.oa_url).startswith("http") else []) + openalex_pdfs(doi)
        for u in list(dict.fromkeys(oa))[:3]:
            r, e = get(u)
            if is_pdf(r):
                got, how = r, "open access"; break
            why.append(e or f"OA not PDF ({getattr(r, 'status_code', '-')})")
        # 2) publisher through campus access
        pub_tried = False
        if got is None:
            land, e = get(f"https://doi.org/{doi}")
            if land is not None and land.ok:
                if is_pdf(land):
                    got, how = land, "publisher (direct)"
                else:
                    for u in publisher_pdf_candidates(doi, land)[:2]:
                        pub_tried = True
                        r, e2 = get(u)
                        if is_pdf(r):
                            got, how = r, f"publisher {urlparse(u).netloc}"; break
                        why.append(e2 or f"publisher not PDF ({getattr(r, 'status_code', '-')}) {urlparse(u).netloc}")
                    if not pub_tried:
                        why.append(f"no PDF link on {urlparse(land.url).netloc}")
            else:
                why.append(e or f"landing HTTP {getattr(land, 'status_code', '-')}")
        if got is not None:
            dest.write_bytes(got.content)
            log.append((rid, row.group, "downloaded", how, got.url)); consecutive_fail = 0
            print("  saved via", how)
        else:
            missing.append((rid, row.group, doi, row.title, "; ".join(why)[:300]))
            consecutive_fail = consecutive_fail + 1 if pub_tried else consecutive_fail
            print("  missing:", "; ".join(why)[:160])
        if consecutive_fail >= 8:
            print("STOP CONDITION: eight publisher attempts in a row failed (campus access lost?)")
            break
    with open(ROOT / "data" / "fulltext_campus_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["record_id", "group", "status", "route", "url"]); w.writerows(log)
    with open(ROOT / "data" / "missing_fulltext_round2.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["record_id", "group", "doi", "title", "reason"]); w.writerows(missing)
    print(f"have: {len(log)}  missing: {len(missing)}  stopped hosts: {sorted(blocked)}")


if __name__ == "__main__":
    sys.exit(main())

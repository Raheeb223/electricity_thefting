"""Round-3 full-text retrieval for the in-depth synthesis studies still without a PDF
(human_tasks/fulltext_todo_round2.csv). Same rules as fetch_fulltext_campus.py, whose
request functions are reused:
- one request at a time, 5-10 s before every publisher request, honest User-Agent;
- open-access copies first (all OpenAlex OA locations, then Semantic Scholar
  openAccessPdf), then the publisher through campus access;
- hosts that refused automated access in earlier rounds are never contacted again, and
  this includes the content-delivery hosts of the same publishers (MDPI, Elsevier, Wiley,
  ACM, Emerald), so a refusal is not worked around through another host of that publisher;
- a 403/429 or block page stops all requests to that host (persisted);
- if the first three IEEE attempts fail, IEEE is not tried further (campus access
  probably unavailable).
Output: data/fulltext/<record_id>.pdf (git-ignored), log data/fulltext_round3_log.csv.
"""
import csv
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_fulltext_campus as fc  # noqa: E402

ROOT = fc.ROOT
TODO = ROOT / "human_tasks" / "fulltext_todo_round2.csv"
PUBLISHER_OWNED = {"mdpi.com", "mdpi-res.com", "sciencedirect.com", "sciencedirectassets.com",
                   "elsevier.com", "wiley.com", "acm.org", "emerald.com", "techrxiv.org"}


def refused_publisher(url):
    h = urlparse(url).netloc.lower()
    return any(h == d or h.endswith("." + d) for d in PUBLISHER_OWNED)


def s2_pdf(doi):
    r, _ = fc.get(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{quote(doi)}?fields=openAccessPdf")
    if r is None or not r.ok:
        return []
    try:
        u = (r.json().get("openAccessPdf") or {}).get("url")
    except ValueError:
        return []
    return [u] if u else []


def main():
    fc.RESOLVERS.add("api.semanticscholar.org")
    rows = list(csv.DictReader(open(TODO, encoding="utf-8-sig")))
    log, ieee_fail, ieee_ok, ieee_off = [], 0, 0, False
    for row in rows:
        rid = row["record_id"]
        dest = fc.OUT / f"{rid}.pdf"
        if dest.exists() and dest.stat().st_size > 20_000:
            log.append((rid, "exists", "", "")); continue
        doi = row["doi_link"].replace("https://doi.org/", "").strip().lower()
        print(rid, doi, row["publisher"])
        got, how, why = None, "", []
        oa = [u for u in fc.openalex_pdfs(doi) + s2_pdf(doi) if u]
        for u in list(dict.fromkeys(oa))[:4]:
            if refused_publisher(u):
                why.append(f"OA copy on refused publisher host {urlparse(u).netloc} (not contacted)"); continue
            r, e = fc.get(u)
            if fc.is_pdf(r):
                got, how = r, f"open access {urlparse(u).netloc}"; break
            why.append(e or f"OA not PDF ({getattr(r, 'status_code', '-')}) {urlparse(u).netloc}")
        is_ieee = "IEEE" in row["publisher"]
        if got is None and not (is_ieee and ieee_off) and not any(
                p in row["publisher"] for p in ("MDPI", "ScienceDirect", "IET", "Wiley", "Emerald", "ACM")):
            land, e = fc.get(f"https://doi.org/{doi}")
            if land is not None and land.ok and not refused_publisher(land.url):
                if fc.is_pdf(land):
                    got, how = land, "publisher (direct)"
                else:
                    for u in fc.publisher_pdf_candidates(doi, land)[:2]:
                        if refused_publisher(u):
                            continue
                        r, e2 = fc.get(u)
                        if fc.is_pdf(r):
                            got, how = r, f"publisher {urlparse(u).netloc}"; break
                        why.append(e2 or f"publisher not PDF ({getattr(r, 'status_code', '-')}) {urlparse(u).netloc}")
            else:
                why.append(e or f"landing {getattr(land, 'status_code', '-')} {urlparse(getattr(land, 'url', '') or '').netloc}")
            if is_ieee:
                if got is not None:
                    ieee_ok += 1
                else:
                    ieee_fail += 1
                    if ieee_ok == 0 and ieee_fail >= 3:
                        ieee_off = True
                        print("  IEEE: first three attempts failed; campus access probably unavailable, IEEE stopped")
        elif got is None:
            why.append("publisher refused automated access earlier (not contacted)")
        if got is not None:
            dest.write_bytes(got.content)
            log.append((rid, "downloaded", how, got.url)); print("  saved via", how)
        else:
            log.append((rid, "missing", "; ".join(why)[:300], "")); print("  missing:", "; ".join(why)[:150])
    with open(ROOT / "data" / "fulltext_round3_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["record_id", "status", "route_or_reason", "url"]); w.writerows(log)
    print("downloaded:", sum(1 for l in log if l[1] == "downloaded"), "missing:", sum(1 for l in log if l[1] == "missing"),
          "stopped hosts:", sorted(fc.blocked))


if __name__ == "__main__":
    t0 = time.time(); main(); print(f"{(time.time() - t0) / 60:.1f} min")

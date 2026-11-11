"""Phase 2 (and Phase 1 gap check): run search strings S1-S4 on OpenAlex, Semantic
Scholar, arXiv and Crossref.

Safe to re-run: every (source, string) result is saved once to data/raw_api/search/ and
skipped next time if the file exists. Delete a file to force that query to run again.

Output per query: JSON with {"source","string_id","query","search_date","records":[...]}.
Records are normalised to: source, source_id, doi, title, abstract, year, venue,
venue_type, authors, cited_by, type, oa_url, keywords.

Run from project root:  .venv/Scripts/python scripts/search_main.py
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import queries as Q  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw_api" / "search"
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "NTL-systematic-review/0.1 (academic research script)"}
TODAY = dt.date.today().isoformat()


def get(url, params, tries=3, wait=8):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=60)
            if r.status_code == 429:
                print(f"    429 rate limit, waiting {wait * (i + 1)} s")
                time.sleep(wait * (i + 1))
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            print(f"    error: {e}")
            time.sleep(wait)
    return None


def save(name, source, sid, query, records, extra=None):
    payload = {"source": source, "string_id": sid, "query": query, "search_date": TODAY,
               "n_records": len(records), **(extra or {}), "records": records}
    (OUT / name).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"  saved {name}: {len(records)} records")


def oa_abstract(inv):
    if not inv:
        return ""
    pos = {i: w for w, idxs in inv.items() for i in idxs}
    return " ".join(pos[i] for i in sorted(pos))


def openalex(sid, query):
    name = f"openalex_{sid}.json"
    if (OUT / name).exists():
        print(f"  skip {name} (exists)")
        return
    # Page-number paging: cursor paging needs an API key since 2026.
    recs, page = [], 1
    sel = ("id,doi,display_name,publication_year,type,primary_location,authorships,"
           "abstract_inverted_index,cited_by_count,open_access,keywords,best_oa_location")
    while True:
        r = get("https://api.openalex.org/works", {
            "filter": f"title_and_abstract.search:{query},publication_year:2010-2026",
            "per-page": 200, "page": page, "select": sel})
        if r is None:
            print("  OpenAlex failed; partial results NOT saved, re-run later")
            return
        d = r.json()
        for w in d["results"]:
            src = ((w.get("primary_location") or {}).get("source") or {})
            recs.append({
                "source": "openalex", "source_id": w["id"],
                "doi": (w.get("doi") or "").replace("https://doi.org/", "").lower(),
                "title": w.get("display_name") or "",
                "abstract": oa_abstract(w.get("abstract_inverted_index")),
                "year": w.get("publication_year"), "venue": src.get("display_name") or "",
                "venue_type": src.get("type") or "", "issn": src.get("issn_l") or "",
                "authors": [a["author"]["display_name"] for a in w.get("authorships", [])],
                "cited_by": w.get("cited_by_count"), "type": w.get("type"),
                "oa_url": ((w.get("best_oa_location") or {}).get("pdf_url")
                           or (w.get("open_access") or {}).get("oa_url") or ""),
                "keywords": [k.get("display_name") for k in w.get("keywords") or []],
            })
        if len(d["results"]) < 200 or len(recs) >= d["meta"]["count"]:
            break
        page += 1
        time.sleep(0.3)
    save(name, "openalex", sid, query, recs, {"api_count": len(recs)})


def s2(sid, query):
    name = f"semanticscholar_{sid}.json"
    if (OUT / name).exists():
        print(f"  skip {name} (exists)")
        return
    recs, token = [], None
    fields = "title,abstract,year,venue,publicationVenue,externalIds,authors,citationCount,publicationTypes,openAccessPdf"
    while True:
        p = {"query": query, "year": "2010-2026", "fields": fields}
        if token:
            p["token"] = token
        r = get("https://api.semanticscholar.org/graph/v1/paper/search/bulk", p, tries=5, wait=15)
        if r is None:
            print("  Semantic Scholar failed; partial results NOT saved, re-run later")
            return
        d = r.json()
        for x in d.get("data") or []:
            recs.append({
                "source": "semanticscholar", "source_id": x.get("paperId"),
                "doi": ((x.get("externalIds") or {}).get("DOI") or "").lower(),
                "title": x.get("title") or "", "abstract": x.get("abstract") or "",
                "year": x.get("year"), "venue": x.get("venue") or "",
                "venue_type": ((x.get("publicationVenue") or {}).get("type") or ""), "issn": "",
                "authors": [a.get("name") for a in x.get("authors") or []],
                "cited_by": x.get("citationCount"),
                "type": ";".join(x.get("publicationTypes") or []),
                "oa_url": ((x.get("openAccessPdf") or {}).get("url") or ""), "keywords": [],
            })
        token = d.get("token")
        if not token or len(recs) >= 5000:
            break
        time.sleep(3)
    save(name, "semanticscholar", sid, query, recs, {"api_total": d.get("total")})


def arxiv(sid, query):
    name = f"arxiv_{sid}.json"
    if (OUT / name).exists():
        print(f"  skip {name} (exists)")
        return
    ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
    recs, start = [], 0
    while True:
        r = get("http://export.arxiv.org/api/query",
                {"search_query": query, "start": start, "max_results": 200})
        if r is None:
            return
        entries = ET.fromstring(r.text).findall("a:entry", ns)
        for e in entries:
            doi = e.find("x:doi", ns)
            jr = e.find("x:journal_ref", ns)
            recs.append({
                "source": "arxiv", "source_id": e.findtext("a:id", "", ns),
                "doi": (doi.text if doi is not None else "").lower(),
                "title": " ".join(e.findtext("a:title", "", ns).split()),
                "abstract": " ".join(e.findtext("a:summary", "", ns).split()),
                "year": int(e.findtext("a:published", "0000", ns)[:4]),
                "venue": jr.text if jr is not None else "arXiv", "venue_type": "repository",
                "issn": "", "authors": [a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)],
                "cited_by": None, "type": "preprint",
                "oa_url": e.findtext("a:id", "", ns).replace("/abs/", "/pdf/"), "keywords": [],
            })
        if len(entries) < 200:
            break
        start += 200
        time.sleep(3)
    recs = [x for x in recs if x["year"] >= 2010]
    save(name, "arxiv", sid, query, recs)


def crossref(i, query):
    name = f"crossref_q{i:02d}_{re.sub(r'[^a-z0-9]+', '_', query.lower())[:40]}.json"
    if (OUT / name).exists():
        print(f"  skip {name} (exists)")
        return
    recs = []
    for offset in (0, 100):
        r = get("https://api.crossref.org/works", {
            "query.bibliographic": query, "rows": 100, "offset": offset,
            "filter": "from-pub-date:2010-01-01,until-pub-date:2026-12-31",
            "select": "DOI,title,author,issued,container-title,type,is-referenced-by-count,abstract,ISSN,subject"})
        if r is None:
            return
        for it in r.json()["message"]["items"]:
            yr = ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0]
            recs.append({
                "source": "crossref", "source_id": it.get("DOI"), "doi": (it.get("DOI") or "").lower(),
                "title": " ".join((it.get("title") or [""])[0].split()),
                "abstract": " ".join(re.sub(r"<[^>]+>", " ", it.get("abstract") or "").split()),
                "year": yr, "venue": (it.get("container-title") or [""])[0], "venue_type": it.get("type"),
                "issn": ";".join(it.get("ISSN") or []),
                "authors": [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in it.get("author", [])],
                "cited_by": it.get("is-referenced-by-count"), "type": it.get("type"), "oa_url": "",
                "keywords": it.get("subject") or [],
            })
        time.sleep(1)
    save(name, "crossref", "CR", query, recs)


def main():
    print(f"Search date {TODAY}; output {OUT}")
    for sid, q in Q.OPENALEX.items():
        print(f"OpenAlex {sid}")
        openalex(sid, q)
    for sid, q in Q.ARXIV.items():
        print(f"arXiv {sid}")
        arxiv(sid, q)
    for i, q in enumerate(Q.CROSSREF):
        print(f"Crossref {i}: {q}")
        crossref(i, q)
    for sid, q in Q.S2.items():
        print(f"Semantic Scholar {sid}")
        s2(sid, q)
        time.sleep(5)


if __name__ == "__main__":
    main()

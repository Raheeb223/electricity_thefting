"""Phase 1 gap check: find existing review/survey articles on electricity theft / NTL.

Queries four free APIs (OpenAlex, Semantic Scholar, Crossref, arXiv), saves every raw
response as JSON/XML under data/raw_api/phase1_reviews/<timestamp>/, and writes a
merged, de-duplicated candidate list of likely review articles to
data/raw_api/phase1_reviews/<timestamp>/candidates.csv.

Run from the project root:
    .venv/Scripts/python scripts/search_reviews.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
STAMP = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
OUT = ROOT / "data" / "raw_api" / "phase1_reviews" / STAMP
OUT.mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "NTL-systematic-review/0.1 (academic research script)"}

# Topic phrases x review phrases. Kept short because the free APIs do not all support
# full Boolean syntax; the full Boolean strings for Scopus/WoS/IEEE are in protocol.md.
TOPICS = [
    "electricity theft",
    "energy theft",
    "power theft",
    "non-technical losses",
    "non-technical loss detection",
    "electricity theft detection",
    "meter tampering",
    "illegal electricity connections",
]
REVIEW_TERMS = ["review", "survey", "systematic review", "state of the art"]
REGIONAL = [
    "electricity theft Bangladesh",
    "system loss Bangladesh electricity distribution",
    "non-technical losses developing countries",
    "electricity theft India",
    "electricity theft Pakistan",
    "electricity theft South Asia",
    "electricity theft Africa",
    "non-technical losses Brazil",
    "electricity theft governance corruption",
]

REVIEW_RE = re.compile(
    r"\b(review|survey|overview|state[- ]of[- ]the[- ]art|systematic|bibliometric|"
    r"meta-analysis|taxonomy|literature|comprehensive|perspective|challenges)\b",
    re.I,
)


def save(name: str, payload) -> None:
    path = OUT / name
    if isinstance(payload, (dict, list)):
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        path.write_text(payload, encoding="utf-8")


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:60]


def get(url, params=None, tries=4):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=40)
            if r.status_code == 429:
                time.sleep(5 * (i + 1))
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:  # network hiccup: back off and retry
            if i == tries - 1:
                print(f"  FAILED {url} {params}: {e}")
                return None
            time.sleep(3 * (i + 1))
    return None


records: list[dict] = []


def add(source, query, title, doi, year, venue, authors, abstract, cites, url, typ):
    records.append(
        {
            "source": source,
            "query": query,
            "title": (title or "").strip(),
            "doi": (doi or "").lower().replace("https://doi.org/", "").strip(),
            "year": year or "",
            "venue": venue or "",
            "first_author": authors[0] if authors else "",
            "n_authors": len(authors),
            "type": typ or "",
            "cited_by": cites if cites is not None else "",
            "url": url or "",
            "abstract": (abstract or "").replace("\n", " ").strip(),
        }
    )


def openalex_abstract(inv):
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def run_openalex(q, review_only):
    flt = "publication_year:2010-2026"
    if review_only:
        flt += ",type:review"
    params = {"search": q, "filter": flt, "per-page": 50, "sort": "relevance_score:desc"}
    r = get("https://api.openalex.org/works", params)
    if not r:
        return
    data = r.json()
    save(f"openalex_{'rev_' if review_only else ''}{slug(q)}.json", data)
    for w in data.get("results", []):
        add(
            "openalex", q, w.get("title"), w.get("doi"), w.get("publication_year"),
            ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
            [a["author"]["display_name"] for a in w.get("authorships", [])],
            openalex_abstract(w.get("abstract_inverted_index")), w.get("cited_by_count"),
            w.get("id"), w.get("type"),
        )


def run_s2(q):
    params = {
        "query": q, "limit": 50, "year": "2010-2026",
        "fields": "title,year,venue,authors,externalIds,abstract,citationCount,publicationTypes,url",
    }
    r = get("https://api.semanticscholar.org/graph/v1/paper/search", params)
    time.sleep(1.5)  # unauthenticated rate limit
    if not r:
        return
    data = r.json()
    save(f"s2_{slug(q)}.json", data)
    for p in data.get("data", []) or []:
        add(
            "semanticscholar", q, p.get("title"), (p.get("externalIds") or {}).get("DOI"),
            p.get("year"), p.get("venue"), [a.get("name") for a in p.get("authors") or []],
            p.get("abstract"), p.get("citationCount"), p.get("url"),
            ";".join(p.get("publicationTypes") or []),
        )


def run_crossref(q):
    params = {
        "query.bibliographic": q, "rows": 50,
        "filter": "from-pub-date:2010-01-01,until-pub-date:2026-12-31",
        "select": "DOI,title,author,issued,container-title,type,is-referenced-by-count,abstract,URL",
    }
    r = get("https://api.crossref.org/works", params)
    if not r:
        return
    data = r.json()
    save(f"crossref_{slug(q)}.json", data)
    for it in data.get("message", {}).get("items", []):
        yr = ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0]
        authors = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in it.get("author", [])]
        abstract = re.sub(r"<[^>]+>", " ", it.get("abstract", "") or "")
        add(
            "crossref", q, (it.get("title") or [""])[0], it.get("DOI"), yr,
            (it.get("container-title") or [""])[0], authors, abstract,
            it.get("is-referenced-by-count"), it.get("URL"), it.get("type"),
        )


def run_arxiv(q):
    terms = " AND ".join(f'all:"{t}"' if " " in t else f"all:{t}" for t in q.split(" | "))
    params = {"search_query": terms, "start": 0, "max_results": 50}
    r = get("http://export.arxiv.org/api/query", params)
    time.sleep(3)  # arXiv asks for 3 s between calls
    if not r:
        return
    save(f"arxiv_{slug(q)}.xml", r.text)
    ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    root = ET.fromstring(r.text)
    for e in root.findall("a:entry", ns):
        doi_el = e.find("arxiv:doi", ns)
        add(
            "arxiv", q, " ".join((e.findtext("a:title", "", ns)).split()),
            doi_el.text if doi_el is not None else "", (e.findtext("a:published", "", ns))[:4],
            "arXiv", [a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)],
            e.findtext("a:summary", "", ns), None, e.findtext("a:id", "", ns), "preprint",
        )


def main():
    review_queries = [f"{t} {r}" for t in TOPICS for r in REVIEW_TERMS[:2]] + [
        f"{t} systematic review" for t in TOPICS[:4]
    ]
    print(f"Saving raw results to {OUT}")
    for q in review_queries:
        print("OpenAlex/S2/Crossref:", q)
        run_openalex(q, review_only=False)
        run_s2(q)
        run_crossref(q)
    for t in TOPICS:
        print("OpenAlex type=review:", t)
        run_openalex(t, review_only=True)
    for q in REGIONAL:
        print("Regional:", q)
        run_openalex(q, review_only=False)
        run_s2(q)
        run_crossref(q)
    for q in ["electricity theft | review", "electricity theft | survey",
              "non-technical losses | review", "energy theft | survey"]:
        print("arXiv:", q)
        run_arxiv(q)

    # Merge: one row per DOI (or normalised title when DOI is missing).
    def norm(t):
        return re.sub(r"[^a-z0-9]", "", t.lower())

    merged: dict[str, dict] = {}
    for rec in records:
        if not rec["title"]:
            continue
        key = rec["doi"] or norm(rec["title"])
        if key in merged:
            m = merged[key]
            m["sources"].add(rec["source"])
            m["queries"].add(rec["query"])
            for f in ("abstract", "venue", "doi", "cited_by", "year"):
                if not m[f] and rec[f]:
                    m[f] = rec[f]
        else:
            merged[key] = {**rec, "sources": {rec["source"]}, "queries": {rec["query"]}}

    topic_re = re.compile(
        r"(theft|non[- ]?technical|ntl\b|tamper|pilfer|illegal connection|fraud|system loss)", re.I
    )
    fields = ["doi", "title", "year", "venue", "first_author", "n_authors", "type",
              "cited_by", "is_review_like", "is_topic", "sources", "queries", "url", "abstract"]
    rows = []
    for m in merged.values():
        text = f"{m['title']} {m['type']}"
        m["is_review_like"] = bool(REVIEW_RE.search(text)) or "review" in m["type"].lower()
        m["is_topic"] = bool(topic_re.search(m["title"] + " " + m["abstract"][:600]))
        m["sources"] = ";".join(sorted(m["sources"]))
        m["queries"] = " || ".join(sorted(m["queries"]))
        rows.append(m)
    rows.sort(key=lambda r: (not (r["is_review_like"] and r["is_topic"]), -int(r["cited_by"] or 0)))
    with open(OUT / "candidates.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    n_rt = sum(r["is_review_like"] and r["is_topic"] for r in rows)
    summary = {"timestamp": STAMP, "raw_records": len(records), "unique_records": len(rows),
               "review_like_and_on_topic": n_rt}
    save("summary.json", summary)
    print(summary)


if __name__ == "__main__":
    main()

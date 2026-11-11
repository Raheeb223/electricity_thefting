"""Merge all saved search results, apply the protocol's Boolean logic locally,
deduplicate, and record PRISMA identification counts.

Inputs : data/raw_api/search/*.json, optional data/raw_exports/*.csv|*.ris|*.bib
Outputs: data/records_all.csv       (every retrieved record, one row per hit)
         data/records_dedup.csv     (unique records that enter screening)
         data/prisma_counts.json    (identification-stage numbers)

Dedup rules (protocol 4.4): (1) same lower-cased DOI; (2) normalised title fuzzy
ratio >= 95 and year within 1. Metadata are merged, preferring OpenAlex, then the
longest abstract.
"""
from __future__ import annotations

import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).parent))
import queries as Q  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PREF = {"openalex": 0, "crossref": 1, "semanticscholar": 2, "arxiv": 3, "export": 4}
EXCLUDED_TYPES = {"dataset", "peer-review", "component", "grant", "erratum", "retraction",
                  "paratext", "editorial", "letter", "standard", "posted-content-x"}


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def load_exports() -> list[dict]:
    """Scopus/WoS exports added by the author (CSV with Title/DOI/Year/Abstract columns, or RIS)."""
    recs = []
    for f in glob.glob(str(ROOT / "data" / "raw_exports" / "*")):
        p = Path(f)
        try:
            if p.suffix.lower() == ".csv":
                df = pd.read_csv(p, dtype=str).fillna("")
                cols = {c.lower(): c for c in df.columns}
                g = lambda row, *names: next((row[cols[n]] for n in names if n in cols), "")
                for _, row in df.iterrows():
                    recs.append({"source": "export", "source_id": p.name, "doi": g(row, "doi", "di").lower(),
                                 "title": g(row, "title", "ti", "article title"), "abstract": g(row, "abstract", "ab"),
                                 "year": g(row, "year", "py", "publication year"),
                                 "venue": g(row, "source title", "so", "journal"), "venue_type": "", "issn": "",
                                 "authors": g(row, "authors", "au").split(";"), "cited_by": g(row, "cited by", "tc"),
                                 "type": g(row, "document type", "dt"), "oa_url": "", "keywords": []})
            elif p.suffix.lower() == ".ris":
                import rispy
                for e in rispy.load(open(p, encoding="utf-8", errors="ignore")):
                    recs.append({"source": "export", "source_id": p.name, "doi": (e.get("doi") or "").lower(),
                                 "title": e.get("title") or e.get("primary_title") or "",
                                 "abstract": e.get("abstract") or "", "year": e.get("year") or "",
                                 "venue": e.get("secondary_title") or e.get("journal_name") or "",
                                 "venue_type": "", "issn": "", "authors": e.get("authors") or [],
                                 "cited_by": "", "type": e.get("type_of_reference") or "", "oa_url": "",
                                 "keywords": e.get("keywords") or []})
        except Exception as ex:  # keep going; report the bad file
            print(f"could not read export {p.name}: {ex}")
    return recs


def main():
    hits = []
    per_file = {}
    for f in sorted(glob.glob(str(ROOT / "data" / "raw_api" / "search" / "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        per_file[Path(f).name] = d["n_records"]
        for r in d["records"]:
            r["string_id_query"] = d["string_id"]
            r["search_date"] = d["search_date"]
            hits.append(r)
    exports = load_exports()
    for r in exports:
        r["string_id_query"], r["search_date"] = "export", ""
    hits += exports

    by_source = Counter(h["source"] for h in hits)
    df = pd.DataFrame(hits)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["authors"] = df["authors"].apply(lambda a: "; ".join(x for x in (a or []) if x))
    df["keywords"] = df["keywords"].apply(lambda a: "; ".join(x for x in (a or []) if x) if isinstance(a, list) else a)
    df["abstract"] = df["abstract"].fillna("")
    df["title"] = df["title"].fillna("").str.strip()
    df["doi"] = df["doi"].fillna("").str.strip().str.lower()
    df.to_csv(ROOT / "data" / "records_all.csv", index=False)

    # --- automation-tool removals (before dedup, reported in PRISMA "removed before screening")
    n0 = len(df)
    no_title = df["title"].eq("")
    df = df[~no_title]
    bad_year = ~df["year"].between(2010, 2026)
    df = df[~bad_year]
    bad_type = df["type"].fillna("").str.lower().isin(EXCLUDED_TYPES)
    df = df[~bad_type]
    df["strings_matched"] = [";".join(Q.match_strings(t, a)) for t, a in zip(df["title"], df["abstract"])]
    nomatch = df["strings_matched"].eq("")
    removed_logic = int(nomatch.sum())
    removed_logic_by_source = df[nomatch]["source"].value_counts().to_dict()
    df = df[~nomatch].copy()

    # --- deduplication
    df["pref"] = df["source"].map(PREF)
    df["abs_len"] = df["abstract"].str.len()
    df["ntitle"] = df["title"].map(norm_title)
    df = df.sort_values(["pref", "abs_len"], ascending=[True, False]).reset_index(drop=True)

    groups: list[list[int]] = []
    doi_idx: dict[str, int] = {}
    title_idx: dict[str, int] = {}
    by_year: dict[int, list[int]] = {}
    for i, row in df.iterrows():
        g = None
        if row["doi"] and row["doi"] in doi_idx:
            g = doi_idx[row["doi"]]
        elif row["ntitle"] in title_idx:
            g = title_idx[row["ntitle"]]
        else:
            y = int(row["year"])
            for yy in (y - 1, y, y + 1):
                for gi in by_year.get(yy, []):
                    rep = df.loc[groups[gi][0]]
                    if abs(len(rep["ntitle"]) - len(row["ntitle"])) < 15 and \
                            fuzz.ratio(rep["ntitle"], row["ntitle"]) >= 95:
                        # different non-empty DOIs = different works (e.g. conf vs journal): keep apart
                        if rep["doi"] and row["doi"] and rep["doi"] != row["doi"]:
                            continue
                        g = gi
                        break
                if g is not None:
                    break
        if g is None:
            groups.append([i])
            g = len(groups) - 1
            by_year.setdefault(int(row["year"]), []).append(g)
        else:
            groups[g].append(i)
        if row["doi"]:
            doi_idx.setdefault(row["doi"], g)
        title_idx.setdefault(row["ntitle"], g)

    out = []
    for n, idxs in enumerate(groups, 1):
        sub = df.loc[idxs]
        best = sub.iloc[0].to_dict()
        for f in ("doi", "abstract", "venue", "issn", "oa_url", "keywords", "authors"):
            if not best.get(f) or (isinstance(best.get(f), float)):
                vals = [v for v in sub[f] if isinstance(v, str) and v]
                best[f] = max(vals, key=len) if vals else ""
        if len(best.get("abstract") or "") < max(sub["abs_len"]):
            best["abstract"] = sub.loc[sub["abs_len"].idxmax(), "abstract"]
        oa = [v for v in sub["oa_url"] if isinstance(v, str) and v]
        best["oa_url"] = oa[0] if oa else ""
        best["sources"] = ";".join(sorted(set(sub["source"])))
        best["strings_matched"] = ";".join(sorted(set(";".join(sub["strings_matched"]).split(";")) - {""}))
        best["n_hits"] = len(sub)
        best["record_id"] = f"R{n:05d}"
        best["is_review_like"] = bool(Q.RE_REVIEW.search(best["title"])) or "review" in str(best["type"]).lower()
        out.append(best)

    cols = ["record_id", "doi", "title", "year", "venue", "venue_type", "issn", "type", "authors",
            "cited_by", "sources", "strings_matched", "n_hits", "is_review_like", "oa_url", "keywords", "abstract"]
    dd = pd.DataFrame(out)[cols].sort_values("record_id")
    dd.to_csv(ROOT / "data" / "records_dedup.csv", index=False)

    counts = {
        "identified_total_hits": n0,
        "identified_by_source": dict(by_source),
        "identified_by_file": per_file,
        "removed_no_title": int(no_title.sum()),
        "removed_outside_2010_2026": int(bad_year.sum()),
        "removed_ineligible_record_type": int(bad_type.sum()),
        "removed_by_automation_search_logic": removed_logic,
        "removed_by_automation_search_logic_by_source": removed_logic_by_source,
        "duplicates_removed": int(len(df) - len(dd)),
        "records_screened": int(len(dd)),
        "records_by_string": {s: int(dd["strings_matched"].str.contains(s).sum()) for s in ("S1", "S2", "S3", "S4")},
        "records_review_like": int(dd["is_review_like"].sum()),
    }
    json.dump(counts, open(ROOT / "data" / "prisma_counts.json", "w"), indent=1)
    print(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main()

"""Verify every entry of a BibTeX file against the Crossref API.

For each entry with a DOI, the script fetches https://api.crossref.org/works/{DOI} and
checks four fields against the .bib entry:
  * title        fuzzy match (token-set ratio >= 90 after normalisation)
  * first author family name matches (accent- and case-insensitive)
  * year         exact match, or within 1 year (online-first vs issue year) -> WARN
  * venue        fuzzy match of journal/booktitle vs Crossref container-title (>= 80),
                 also accepting Crossref short-container-title
Entries marked @misc/@techreport/@online with `note = {grey literature}` or a
`keywords` field containing `grey` are treated as grey literature: their URL is checked
for reachability instead (HTTP status < 400) and they need `urldate`.

Outputs refs/verification_report.md (default) and returns exit code 1 if any entry FAILs.

Usage:
    .venv/Scripts/python scripts/verify_refs.py [path/to/file.bib] [--report path.md]
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import time
import unicodedata
from pathlib import Path

import bibtexparser
import requests
from rapidfuzz import fuzz

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "NTL-systematic-review/0.1 (reference verification script)"}


def norm(s: str) -> str:
    # German sharp s: LaTeX {\ss}, Unicode ß, and Crossref's mis-encoded Greek beta all mean "ss"
    s = (s or "").replace(chr(92) + "ss", "ss").replace("ß", "ss").replace("β", "ss")
    s = re.sub(chr(92) + chr(92) + "[\"'`^~]", "", s)  # drop LaTeX accent commands such as \"o
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[{}\\$]", "", s)          # strip LaTeX braces and commands
    s = re.sub(r"<[^>]+>", " ", s)          # strip HTML/MathML from Crossref titles
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return " ".join(s.split())


def bib_first_author_family(author_field: str) -> str:
    first = re.split(r"\s+and\s+", author_field or "", flags=re.I)[0].strip()
    if "," in first:
        return norm(first.split(",")[0])
    return norm(first.split()[-1]) if first else ""


def crossref(doi: str):
    url = f"https://api.crossref.org/works/{requests.utils.quote(doi, safe='/')}"
    for i in range(4):
        try:
            r = requests.get(url, headers=UA, timeout=30)
            if r.status_code == 404:
                return None, "DOI not found in Crossref (404)"
            if r.status_code == 429:
                time.sleep(5 * (i + 1))
                continue
            r.raise_for_status()
            return r.json()["message"], ""
        except requests.RequestException as e:
            err = str(e)
            time.sleep(3 * (i + 1))
    return None, f"request failed: {err}"


def check_grey(e: dict) -> tuple[str, list[str]]:
    notes = []
    url = e.get("url", "").replace(chr(92) + "%", "%")  # undo LaTeX escaping of percent-encoding
    if not url:
        return "FAIL", ["grey literature entry has no url"]
    if not e.get("urldate"):
        notes.append("missing urldate (access date)")
    try:
        r = requests.get(url, headers=UA, timeout=30, allow_redirects=True, stream=True)
        if r.status_code == 403:  # bot protection, not a dead link; never worked around
            return "WARN", notes + ["HTTP 403 (site blocks automated clients): confirm the link by hand"]
        if r.status_code >= 400:
            return "FAIL", notes + [f"URL returned HTTP {r.status_code}"]
    except requests.RequestException as ex:
        return "FAIL", notes + [f"URL unreachable: {ex}"]
    return ("WARN" if notes else "PASS"), notes or ["URL reachable"]


def check_entry(e: dict) -> tuple[str, list[str]]:
    kw = (e.get("keywords", "") + " " + e.get("note", "")).lower()
    if "grey" in kw or "gray" in kw:
        return check_grey(e)
    doi = e.get("doi", "").strip().replace("https://doi.org/", "")
    if not doi:
        return "FAIL", ["no DOI (academic entries must have a DOI; grey literature must be tagged)"]
    msg, err = crossref(doi)
    if msg is None:
        return "FAIL", [err]

    status, notes = "PASS", []

    cr_title = " ".join(msg.get("title") or [])
    t_score = fuzz.token_set_ratio(norm(e.get("title", "")), norm(cr_title))
    if t_score < 90:
        status = "FAIL"
        notes.append(f"title mismatch ({t_score:.0f}): Crossref has '{cr_title}'")

    cr_authors = msg.get("author") or []
    cr_fam = norm(cr_authors[0].get("family", cr_authors[0].get("name", ""))) if cr_authors else ""
    bib_fam = bib_first_author_family(e.get("author", ""))
    if not cr_fam:
        notes.append("Crossref has no author list; first author not checked")
        status = "WARN" if status == "PASS" else status
    elif bib_fam != cr_fam and fuzz.ratio(bib_fam, cr_fam) < 85:
        status = "FAIL"
        notes.append(f"first author mismatch: bib '{bib_fam}' vs Crossref '{cr_fam}'")

    years = set()
    for k in ("published-print", "published-online", "issued", "published"):
        dp = (msg.get(k) or {}).get("date-parts") or [[None]]
        if dp[0] and dp[0][0]:
            years.add(int(dp[0][0]))
    try:
        by = int(e.get("year", "0"))
    except ValueError:
        by = 0
    if by not in years:
        if years and min(abs(by - y) for y in years) == 1:
            status = "WARN" if status == "PASS" else status
            notes.append(f"year {by} differs by 1 from Crossref {sorted(years)}")
        else:
            status = "FAIL"
            notes.append(f"year mismatch: bib {by} vs Crossref {sorted(years)}")

    bib_venue = e.get("journal") or e.get("booktitle") or ""
    cr_venues = (msg.get("container-title") or []) + (msg.get("short-container-title") or [])
    if bib_venue:
        v_score = max((fuzz.token_set_ratio(norm(bib_venue), norm(v)) for v in cr_venues), default=0)
        if v_score < 80:
            status = "FAIL"
            notes.append(f"venue mismatch ({v_score:.0f}): Crossref has {cr_venues[:1]}")
    else:
        notes.append("no journal/booktitle in bib entry")
        status = "WARN" if status == "PASS" else status

    if not notes:
        notes.append("title, first author, year, venue match")
    return status, notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bib", nargs="?", default=str(ROOT / "refs" / "references.bib"))
    ap.add_argument("--report", default=str(ROOT / "refs" / "verification_report.md"))
    a = ap.parse_args()

    parser = bibtexparser.bparser.BibTexParser(common_strings=True)
    with open(a.bib, encoding="utf-8") as f:
        db = bibtexparser.load(f, parser=parser)

    results = []
    for e in db.entries:
        st, notes = check_entry(e)
        results.append((e["ID"], e.get("doi", ""), st, notes))
        print(f"{st:5} {e['ID']}: {'; '.join(notes)}")
        time.sleep(0.2)

    counts = {s: sum(r[2] == s for r in results) for s in ("PASS", "WARN", "FAIL")}
    lines = [
        "# Reference verification report",
        "",
        f"- File: `{Path(a.bib).name}`",
        f"- Run: {dt.datetime.now():%Y-%m-%d %H:%M}",
        f"- Entries: {len(results)} | PASS {counts['PASS']} | WARN {counts['WARN']} | FAIL {counts['FAIL']}",
        "",
        "FAIL entries must be fixed or moved to `refs/unverified.md` and not cited.",
        "WARN entries need a manual look (usually online-first vs print year).",
        "",
        "| Key | DOI | Status | Notes |",
        "|---|---|---|---|",
    ]
    for key, doi, st, notes in sorted(results, key=lambda r: ("FAIL", "WARN", "PASS").index(r[2])):
        lines.append(f"| {key} | {doi} | {st} | {'; '.join(notes).replace('|', '/')} |")
    Path(a.report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nReport written to {a.report}: {counts}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())

"""R8: venue audit of academic references against the public Scopus title list.

Source list: Elsevier public "Scopus Source Title List", November 2024 edition
(data/venue_audit/scopus_title_list_2024-11.xlsx, downloaded 2026-11-11 from
https://www.elsevier.com/resources/scopus-titlelists). Sheets used:
  - "Scopus Active (30294)": active serials (ISSN / EISSN / title, discontinued flag);
  - "Serial Conf. Proc. with Profile": serial conference proceedings;
  - "All Conf. Proceedings Jun. 2024": individual proceedings volumes to June 2024.
Web of Science Master Journal List could not be checked (needs a login).

Status per reference:
  V-J   journal ISSN/EISSN (or exact normalised title) in the active list
  V-S   serial conference proceedings / book series in the list (e.g. LNNS, LNEE, AIP Conf Proc)
  V-C   this conference volume (title and year) is in the proceedings list
  P-C   later than June 2024 and earlier editions of the same conference series are in the
        list (probably indexed; not verifiable with this list)
  D     source flagged "discontinued due to quality issues"
  N     not found: E5 candidate, needs a manual check in Scopus or the MJL
Output: data/venue_audit/venue_audit.csv and a summary.
"""
import re
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
X = ROOT / "data" / "venue_audit" / "scopus_title_list_2024-11.xlsx"


def norm(s):
    s = str(s or "").lower().replace("&", "and")
    s = re.sub(r"\b(19|20)\d{2}\b", " ", s)
    s = re.sub(r"\b\d+(st|nd|rd|th)\b", " ", s)
    s = re.sub(r"\b(the|of|on|in|and|for|ieee|international|conference|proceedings|annual|"
               r"journal|transactions|a|an)\b", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(s.split())


def issns(s):
    return {x.replace("-", "").upper() for x in re.findall(r"\d{4}-?\d{3}[\dXx]", str(s or ""))}


def load():
    wb = openpyxl.load_workbook(X, read_only=True)
    act = list(wb["Scopus Active (30294)"].iter_rows(values_only=True))[1:]
    j_issn, j_title, disc = {}, {}, set()
    for r in act:
        title, issn, eissn, discont = r[1], r[2], r[3], r[6]
        for i in issns(f"{issn} {eissn}"):
            j_issn[i] = ("V-J", title)
        j_title[norm(title)] = ("V-J", title)
        if discont:
            disc.add(norm(title))
    for r in list(wb["Serial Conf. Proc. with Profile"].iter_rows(values_only=True))[1:]:
        if not r[1]:
            continue
        for i in issns(f"{r[2]} {r[3]}"):
            j_issn.setdefault(i, ("V-S", r[1]))
        if r[4]:
            disc.add(norm(r[1]))
    conf = list(wb["All Conf. Proceedings Jun. 2024"].iter_rows(values_only=True))[1:]
    series_count, c_idx = {}, {}
    for r in conf:
        title, year, src = r[0], r[1], r[2]
        if not title:
            continue
        for name in {title, src}:
            if name:
                c_idx.setdefault(norm(name), set()).add(year)
        if src:
            series_count[norm(src)] = series_count.get(norm(src), 0) + 1
    # a proceedings "source title" used by many different volumes is a book series (LNNS etc.)
    series = {k for k, n in series_count.items() if n >= 20}
    return j_issn, j_title, series, c_idx, disc


JOURNALISH = re.compile(r"journal|jurnal|review|transactions|letters|magazine|revista|dergisi|"
                        r"jou|research and development|energies|sustainability|electronics", re.I)


def classify(venue, issn, year, kb, rtype=""):
    j_issn, j_title, series, c_idx, disc = kb
    nv = norm(venue)
    if not nv and not issns(issn):
        return "N", "no venue recorded"
    if nv in disc:
        return "D", "discontinued for quality"
    for i in issns(issn):
        if i in j_issn:
            st, t = j_issn[i]
            return st, f"ISSN {i}: {t}"
    if nv in j_title:
        return "V-J", f"title: {j_title[nv][1]}"
    if nv in series:
        return "V-S", f"book series with >=20 indexed volumes: {venue}"
    is_conf = "conference" in str(rtype).lower() or re.search(r"conference|symposium|workshop|meeting|congress|forum", str(venue), re.I)
    if JOURNALISH.search(str(venue)) and not is_conf:
        return "N", "journal-type venue not in the active list"
    tv = set(nv.split())
    best, score, yrs = None, 0.0, set()
    if len(tv) >= 2:
        for k, ys in c_idx.items():
            tk = set(k.split())
            if not tk:
                continue
            jac = len(tv & tk) / len(tv | tk)
            if jac > score:
                best, score, yrs = k, jac, ys
    try:
        y = int(year)
    except (TypeError, ValueError):
        y = None
    if best and score >= 0.75:
        if y in yrs:
            return "V-C", f"proceedings in list for {y}: {best}"
        return "P-C", f"other editions in list {sorted(x for x in yrs if x)[-3:]}: {best}"
    return "N", f"not found (best match {score:.2f}: {best})"


def main():
    pri = pd.read_csv(ROOT / "data" / "priority_synthesis_B.csv", keep_default_na=False)
    ext = pd.read_csv(ROOT / "data" / "extraction.csv", keep_default_na=False)
    rec = pd.read_csv(ROOT / "data" / "records_dedup.csv", keep_default_na=False,
                      usecols=["record_id", "doi", "venue", "issn", "year", "type", "title"])
    ids = list(pri.record_id) + [i for i in ext[ext.role == "background review"].id if i not in set(pri.record_id)]
    t = rec.set_index("record_id").reindex(ids).reset_index()
    t["group"] = ["priority study" if i in set(pri.record_id) else "background review" for i in ids]
    kb = load()
    res = [classify(v, s, y, kb, ty) for v, s, y, ty in zip(t.venue, t.issn, t.year, t.type)]
    t["scopus_status"] = [r[0] for r in res]
    t["evidence"] = [r[1] for r in res]
    # second pass for unmatched venues: ISSN and venue name from OpenAlex (cached)
    import json
    import time
    import requests
    cache_fp = ROOT / "data" / "venue_audit" / "openalex_issn_recheck.json"
    cache = json.load(open(cache_fp)) if cache_fp.exists() else {}
    for i in t.index[t.scopus_status == "N"]:
        rid, doi = t.at[i, "record_id"], t.at[i, "doi"]
        if rid not in cache and doi:
            try:
                w = requests.get(f"https://api.openalex.org/works/https://doi.org/{doi}", timeout=40,
                                 headers={"User-Agent": "NTL-systematic-review/0.2"}).json()
                src = ((w.get("primary_location") or {}).get("source") or {})
                cache[rid] = [src.get("display_name"), " ".join(src.get("issn") or [])]
            except Exception:
                cache[rid] = [None, ""]
            time.sleep(1.2)
        if rid in cache:
            name, iss = cache[rid][0], cache[rid][1]
            st, ev = classify(name or t.at[i, "venue"], iss, t.at[i, "year"], kb, t.at[i, "type"])
            if st != "N":
                t.loc[i, ["scopus_status", "evidence"]] = [st, ev + " (ISSN from OpenAlex)"]
            if name and not t.at[i, "venue"]:
                t.at[i, "venue"] = name
    json.dump(cache, open(cache_fp, "w"), indent=1)
    special = {"R00330": "E4: Zenodo upload, not peer reviewed",
               "R02212": "grey literature (KDI archive report): moved to grey table",
               "R00034": "no venue recorded: E5 pending author check"}

    def dec(r):
        if r.record_id in special:
            return special[r.record_id]
        if r.scopus_status in ("V-J", "V-S", "V-C"):
            return "indexed (Scopus list)"
        if r.scopus_status == "P-C":
            return "probably indexed (conference series indexed; edition after list date): keep, flag"
        return "E5 provisional: not in Scopus list Nov 2024; WoS MJL check by author pending"
    t["decision"] = t.apply(dec, axis=1)
    out = ROOT / "data" / "venue_audit" / "venue_audit.csv"
    t.to_csv(out, index=False)
    print(t.scopus_status.value_counts().to_dict())
    print(pd.crosstab(t.group, t.scopus_status))
    return t


if __name__ == "__main__":
    main()

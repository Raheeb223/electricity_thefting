"""Build refs/references.bib from Crossref metadata (never from memory).

Inputs : data/fulltext_targets.csv (record_id, doi) and refs/extra_dois.txt (method refs
         found by Crossref search; one DOI per line, '#' comments allowed).
Output : refs/references.bib, refs/key_map.csv (record_id/doi -> citation key).
Cached Crossref JSON in refs/crossref_cache/ so re-runs make no new requests.
"""
import csv
import json
import re
import time
import unicodedata
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "refs" / "crossref_cache"
CACHE.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "NTL-systematic-review/0.1 (reference builder)"}
STOP = {"a", "an", "the", "of", "on", "in", "for", "and", "to", "with", "using", "based", "via", "by"}


def fetch(doi):
    fp = CACHE / (re.sub(r"[^a-z0-9]+", "_", doi.lower()) + ".json")
    if fp.exists():
        return json.load(open(fp, encoding="utf-8"))
    r = requests.get(f"https://api.crossref.org/works/{doi}", headers=UA, timeout=40)
    msg = r.json()["message"] if r.ok else {}
    json.dump(msg, open(fp, "w", encoding="utf-8"))
    time.sleep(0.4)
    return msg


def ascii_(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def tex(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    s = s.replace("&amp;", "&").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")
    return " ".join(s.split())


def key_for(msg, used):
    a = (msg.get("author") or [{}])[0]
    fam = ascii_(a.get("family") or a.get("name") or "anon").lower()
    fam = re.sub(r"[^a-z]", "", fam) or "anon"
    yr = str(((msg.get("issued") or {}).get("date-parts") or [[0]])[0][0])
    words = [w for w in re.findall(r"[a-z]+", ascii_(" ".join(msg.get("title") or [""])).lower()) if w not in STOP]
    k = f"{fam}{yr}{words[0] if words else ''}"
    base, i = k, 1
    while k in used:
        i += 1
        k = f"{base}{chr(96 + i)}"
    used.add(k)
    return k


ACC = {"́": "'", "̀": "`", "̂": "^", "̃": "~", "̈": '"', "̧": "c ",
       "̌": "v ", "̄": "=", "̆": "u ", "̊": "r ", "̨": "k ", "̇": "."}
SPECIAL = {"ß": "{\\ss}", "β": "{\\ss}", "ø": "{\\o}", "Ø": "{\\O}", "ł": "{\\l}",
           "Ł": "{\\L}", "æ": "{\\ae}", "ı": "{\\i}", "đ": "{\\dj}"}


def texname(s):
    """Author names with LaTeX accent macros, so BibTeX can abbreviate initials safely."""
    out = []
    for ch in tex(s):
        if ord(ch) < 128:
            out.append(ch); continue
        if ch in SPECIAL:
            out.append(SPECIAL[ch]); continue
        d = unicodedata.normalize("NFD", ch)
        base, marks = d[0], d[1:]
        if ord(base) < 128 and marks and all(m in ACC for m in marks):
            r = base
            for m in marks:
                r = "\\" + ACC[m] + r if ACC[m].endswith(" ") is False else "\\" + ACC[m] + r
            out.append("{" + r + "}")
        else:
            out.append(ascii_(ch) or "")
    return "".join(out)


def entry(msg, key):
    typ = msg.get("type", "")
    btype = {"journal-article": "article", "proceedings-article": "inproceedings",
             "book-chapter": "incollection", "posted-content": "misc"}.get(typ, "article")
    authors = " and ".join(
        f"{texname(a.get('family', ''))}, {texname(a.get('given', ''))}".strip(", ") if a.get("family") else texname(a.get("name", ""))
        for a in msg.get("author") or [])
    yr = ((msg.get("issued") or {}).get("date-parts") or [[None]])[0][0]
    venue = tex((msg.get("container-title") or [""])[0])
    f = {"author": authors, "title": "{" + tex(" ".join(msg.get("title") or [""])) + "}", "year": str(yr or ""),
         "doi": msg.get("DOI", "")}
    if btype == "article":
        f["journal"] = venue
        for k_, c in (("volume", "volume"), ("number", "issue"), ("pages", "page")):
            if msg.get(c):
                f[k_] = str(msg[c]).replace("-", "--")
        if not msg.get("page") and msg.get("article-number"):
            f["pages"] = str(msg["article-number"])
    else:
        f["booktitle"] = venue
        if msg.get("page"):
            f["pages"] = str(msg["page"]).replace("-", "--")
    if msg.get("publisher"):
        f["publisher"] = tex(msg["publisher"])
    body = ",\n".join(f"  {k} = {{{v}}}" if k != "title" else f"  {k} = {{{v}}}" for k, v in f.items() if v)
    return f"@{btype}{{{key},\n{body}\n}}\n"


OA_AUTH = {r["record_id"]: r["authors"] for r in csv.DictReader(open(ROOT / "data" / "records_dedup.csv", encoding="utf-8"))}


def main():
    targets = list(csv.DictReader(open(ROOT / "data" / "fulltext_targets.csv", encoding="utf-8")))
    extra = []
    ef = ROOT / "refs" / "extra_dois.txt"
    if ef.exists():
        extra = [l.split("#")[0].strip() for l in open(ef, encoding="utf-8") if l.split("#")[0].strip()]
    used, out, km, failed = set(), [], [], []
    for rid, doi in [(t["record_id"], t["doi"]) for t in targets] + [("method", d) for d in extra]:
        msg = fetch(doi)
        if not msg:
            failed.append((rid, doi)); continue
        # R8: Crossref author lists that are missing or contain affiliations are replaced by
        # the OpenAlex author names stored with the record (records_dedup.csv), not by memory.
        auths = msg.get("author") or []
        bad = (not auths) or any(len((a.get("family") or a.get("name") or "")) > 60 or
                                 re.search(r"laborato|universit|faculty|school|[0-9]{4,}", (a.get("family") or a.get("name") or ""), re.I)
                                 for a in auths)
        if bad and rid in OA_AUTH and OA_AUTH[rid]:
            names = [n.strip() for n in OA_AUTH[rid].split(";")
                     if n.strip() and not re.search(r"laborato|universit|faculty|school|[0-9]{4,}", n, re.I)]
            msg = dict(msg, author=[{"given": " ".join(n.split()[:-1]), "family": n.split()[-1]} for n in names])
        k = key_for(msg, used)
        out.append(entry(msg, k)); km.append((rid, doi, k))
    text = "\n".join(out).replace("\\&amp;", "\\&").replace("&amp;", "\\&")  # R8: no HTML entities
    # R8: character artefacts in Crossref metadata (beta for German sharp s; lost quote marks)
    text = text.replace("Schlöβer", "Schlö{\\ss}er").replace("�counter conduct�", "`counter conduct'")
    text = text.replace("�", "")
    (ROOT / "refs" / "references.bib").write_text(text, encoding="utf-8")
    with open(ROOT / "refs" / "key_map.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["record_id", "doi", "key"]); w.writerows(km)
    print(f"{len(out)} entries; failed: {failed}")


if __name__ == "__main__":
    main()

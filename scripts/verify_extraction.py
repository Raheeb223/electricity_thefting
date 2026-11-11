"""Mechanical verification of the page-referenced full-text extraction
(data/extraction_ft.csv) against the PDF text.

For every extracted item it checks:
  1. quote_on_page: the supporting quote occurs on the cited PDF page (after normalising
     case, whitespace, hyphenation and punctuation; a fuzzy match >= 0.90 of the quote's
     characters in one aligned block is accepted, to tolerate PDF ligatures);
  2. quote_elsewhere: if not on the cited page, whether it occurs on another page
     (page number wrong but value supported);
  3. numbers_supported: every number in the extracted value occurs in the quote, or on the
     cited page (values may be paraphrased, e.g. "about 3 times" from 15.3% vs 72.0%; such
     rows are listed for manual reading).
This checks that values are traceable to the source text. It does not check that the
reading of the text is correct.
Output: data/extraction_ft_verification.csv and a printed summary.
Usage: python scripts/verify_extraction.py
"""
import csv
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ft_view import pages  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NUMRE = re.compile(r"\d+(?:[.,]\d+)*")


def norm(s):
    s = s.lower().replace("ﬁ", "fi").replace("ﬂ", "fl").replace("–", "-").replace("—", "-")
    s = re.sub(r"-\s+", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def found(q, text):
    parts = [x for x in q.split("...") if norm(x)]
    if len(parts) > 1:  # elided quote: every part must occur
        return all(found(x, text) for x in parts)
    q, t = norm(q), norm(text)
    if not q:
        return False
    if q in t:
        return True
    # tolerate small extraction differences: slide a window of the quote's length
    best, L = 0.0, len(q)
    anchor = q[:12]
    starts = [m.start() for m in re.finditer(re.escape(anchor), t)] or range(0, max(1, len(t) - L), max(1, L // 4))
    for st in starts:
        seg = t[max(0, st - 20): st + L + 20]
        m = SequenceMatcher(None, q, seg, autojunk=False)
        best = max(best, sum(b.size for b in m.get_matching_blocks()) / L)
        if best >= 0.9:
            return True
    return best >= 0.9


def nums(s):
    return {n.replace(",", "") for n in NUMRE.findall(s)}


# unit or format conversions read and confirmed by hand (value -> quote)
CONVERSIONS = {
    ("R00722", "setting and data"): "820K in the quote = 820,000",
    ("R02232", "field test"): "quote gives 50,000 and 100,000; value writes them with spaces",
    ("R00472", "result"): "quote gives 90% and 78%; value writes 0.90 and 0.78",
}


def main():
    rows = list(csv.DictReader(open(ROOT / "data" / "extraction_ft.csv", encoding="utf-8")))
    out = []
    for r in rows:
        pdf = ROOT / "data" / "fulltext" / f"{r['record_id']}.pdf"
        if not pdf.exists():
            out.append({**r, "quote_on_page": "no pdf", "quote_elsewhere": "", "numbers_supported": "", "unsupported_numbers": ""})
            continue
        pg = pages(r["record_id"])
        try:
            p = int(r["page"])
        except ValueError:
            p = 0
        on_page = 1 <= p <= len(pg) and found(r["quote"], pg[p - 1])
        elsewhere = ""
        if not on_page:
            hits = [i + 1 for i, t in enumerate(pg) if found(r["quote"], t)]
            elsewhere = ";".join(map(str, hits)) or "not found"
        page_text = pg[p - 1] if 1 <= p <= len(pg) else ""
        support = nums(r["quote"]) | nums(page_text.replace(",", ""))
        missing = sorted(n for n in nums(r["value"]) if n not in support)
        out.append({**r, "quote_on_page": "yes" if on_page else "no", "quote_elsewhere": elsewhere,
                    "numbers_supported": "yes" if not missing else
                    ("yes (conversion)" if (r["record_id"], r["item"]) in CONVERSIONS else "no"),
                    "unsupported_numbers": " ".join(missing)})
    f = ROOT / "data" / "extraction_ft_verification.csv"
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    checked = [o for o in out if o["quote_on_page"] != "no pdf"]
    print("items:", len(out), "with pdf:", len(checked))
    print("quote on cited page:", sum(o["quote_on_page"] == "yes" for o in checked))
    print("quote on another page:", sum(o["quote_elsewhere"] not in ("", "not found") for o in checked))
    print("quote not found:", sum(o["quote_elsewhere"] == "not found" for o in checked))
    print("numbers supported:", sum(o["numbers_supported"].startswith("yes") for o in checked),
          "of which unit conversions confirmed by hand:", sum(o["numbers_supported"] == "yes (conversion)" for o in checked))
    for o in checked:
        if o["quote_on_page"] != "yes" or not o["numbers_supported"].startswith("yes"):
            print(" -", o["record_id"], o["item"], "| page", o["page"], "| on page:", o["quote_on_page"],
                  o["quote_elsewhere"], "| unsupported:", o["unsupported_numbers"])


if __name__ == "__main__":
    main()

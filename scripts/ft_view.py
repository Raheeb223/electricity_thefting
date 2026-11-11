"""Compact, page-referenced full-text view for R6 extraction.

Usage: python scripts/ft_view.py R00480 [R01285 ...] [--n 22]
Prints the first ~900 characters of the paper and up to N key sentences (data, labels,
validation, field results, metrics, costs, limitations), each tagged with its PDF page.
Page texts are cached in data/fulltext_pages/<record_id>.json.
"""
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "fulltext_pages"
CACHE.mkdir(exist_ok=True)
KEY = re.compile(
    r"(dataset|data set|consumers|customers|households|smart meter|monthly|daily|hourly|"
    r"\b\d+[- ]?min|label|inspect|field|deploy|pilot|in operation|utility|company|"
    r"precision|recall|f1|auc|accuracy|detection rate|hit rate|false positive|"
    r"recover|kwh|revenue|cost|usd|\$|tk\b|taka|limitation|bangladesh|survey|respondent|"
    r"difference-in-difference|regression|panel|reduc)", re.I)
NUM = re.compile(r"\d")


def pages(rid):
    fp = CACHE / f"{rid}.json"
    if fp.exists():
        return json.load(open(fp, encoding="utf-8"))
    pdf = ROOT / "data" / "fulltext" / f"{rid}.pdf"
    out = []
    for p in PdfReader(str(pdf)).pages:
        try:
            out.append(" ".join((p.extract_text() or "").split()))
        except Exception:
            out.append("")
    json.dump(out, open(fp, "w", encoding="utf-8"))
    return out


def view(rid, n=22):
    pg = pages(rid)
    print(f"########## {rid}  ({len(pg)} pages)")
    print("HEAD:", (" ".join(pg[:2]))[:900])
    seen, k = set(), 0
    for i, t in enumerate(pg, 1):
        for s in re.split(r"(?<=[.!?])\s+", t):
            if 50 < len(s) < 420 and KEY.search(s) and NUM.search(s) and s not in seen:
                seen.add(s)
                print(f"  [p{i}] {s}")
                k += 1
                if k >= n:
                    return


if __name__ == "__main__":
    args = sys.argv[1:]
    n = 22
    if "--n" in args:
        i = args.index("--n"); n = int(args[i + 1]); args = args[:i] + args[i + 2:]
    for rid in args:
        try:
            view(rid, n)
        except Exception as e:
            print(rid, "ERROR", e)

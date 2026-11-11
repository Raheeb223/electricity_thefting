"""Merge title/abstract screening decisions into data/screening.csv.

Each data/screening_batches/dec_*.csv covers a line range of one batch_NN.txt file
(stated in its first comment line: '# batch_NN lines A-B'). Records listed explicitly get
that decision; every other record in the covered line range gets the file's DEFAULT row.

Decision codes
  INC + I5a  documents forms/scale/drivers of theft      INC + I5b  detection method with evaluation
  INC + I5c  prevention/governance intervention           INC + I4   electric three-wheeler charging theme
  INC + RV   existing review (Table T1 / background)      INC + GREY grey literature case
  EXC + E1..E7 exclusion reasons as in protocol section 2

Outputs: data/screening.csv, data/screening_ta_summary.json
"""
import csv
import glob
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "data" / "screening_batches"


def batch_lines(n):
    ids = {}
    for i, line in enumerate((B / f"batch_{n:02d}.txt").read_text(encoding="utf-8").split("\n"), 1):
        m = re.match(r"(R\d{5})\|", line)
        if m:
            ids[i] = m.group(1)
    return ids


def main():
    recs = pd.read_csv(ROOT / "data" / "records_dedup.csv", dtype=str).fillna("")
    decisions = {}
    covered_by = {}
    for f in sorted(glob.glob(str(B / "dec_*.csv"))):
        lines = open(f, encoding="utf-8").read().splitlines()
        m = re.match(r"#\s*batch_(\d+)\s+lines\s+(\d+)-(\d+)", lines[0])
        if not m:
            raise SystemExit(f"{f}: first line must state '# batch_NN lines A-B'")
        bn, a, b = map(int, m.groups())
        ids = batch_lines(bn)
        covered = [rid for ln, rid in ids.items() if a <= ln <= b]
        default = None
        explicit = {}
        for row in csv.reader(lines[1:]):
            if not row or row[0].startswith("#"):
                continue
            row = (row + [""] * 5)[:5]
            rid, dec, code, fam, note = [x.strip() for x in row[:4]] + [",".join(row[4:]).strip()]
            if rid == "DEFAULT":
                default = (dec, code, fam, note)
            else:
                explicit[rid] = (dec, code, fam, note)
        for rid in covered:
            covered_by[rid] = Path(f).name
            if rid in explicit:
                decisions[rid] = explicit[rid] + ("explicit",)
            elif default:
                decisions[rid] = default + ("default",)
        stray = set(explicit) - set(covered)
        if stray:
            print(f"WARNING {Path(f).name}: IDs not in its line range: {sorted(stray)}")
            for rid in stray:  # still record them; they were read in an adjacent block
                decisions[rid] = explicit[rid] + ("explicit",)
                covered_by[rid] = Path(f).name

    out = []
    missing = []
    for _, r in recs.iterrows():
        d = decisions.get(r["record_id"])
        if not d:
            missing.append(r["record_id"])
            d = ("", "", "", "", "")
        out.append({
            "record_id": r["record_id"], "doi": r["doi"], "year": r["year"], "title": r["title"],
            "venue": r["venue"], "type": r["type"], "strings_matched": r["strings_matched"],
            "ta_decision": d[0], "ta_code": d[1], "family": d[2], "ta_note": d[3],
            "ta_basis": d[4], "decision_file": covered_by.get(r["record_id"], ""),
            "screener": "AI assistant under author supervision",
        })
    df = pd.DataFrame(out)
    df.to_csv(ROOT / "data" / "screening.csv", index=False)
    summ = {
        "records": len(df),
        "missing_decision": missing,
        "ta_decision": dict(Counter(df["ta_decision"])),
        "ta_code": dict(Counter(df["ta_code"])),
        "included_by_family": dict(Counter(df[df["ta_decision"] == "INC"]["family"])),
    }
    json.dump(summ, open(ROOT / "data" / "screening_ta_summary.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in summ.items() if k != "missing_decision"}, indent=1))
    print("missing:", len(missing), missing[:20])


if __name__ == "__main__":
    main()

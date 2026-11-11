"""R3: merge the manual evidence-map codes and apply the Option B scope rule.

Inputs : data/evidence_map_batches/code_NN.txt (one line per record, coded by reading
         each title and abstract; format record_id|CTY|GR|LB|VL|E3W|GOVM|note)
         data/evidence_map_batches/map_index.csv (record_id, ta_code)
Outputs: data/evidence_map_coded_manual.csv, data/priority_synthesis_B.csv,
         data/priority_synthesis_B_summary.json; summary printed.

Rule (reviews/evidence_map_codebook.md, author decision 2026-11-10). A non-review
record is a priority study if ANY of:
  C1 CTY contains BGD; C2 E3W = 1; C3 VL = F; C4 ta_code I5b/I5c with GR = M and LB = R;
  C5 GOVM = 1 and CTY is a low- or middle-income economy (World Bank income groups).
Only scope and evidence type are used. Venue, citations and results are never used.

A criterion met only through a code marked "?" (probable, needs full-text check) is
counted as PROBABLE; a criterion met through unmarked codes is FIRM.
"""
import glob
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "data" / "evidence_map_batches"

# World Bank income groups, current table (FY2027) on the Data Help Desk page
# https://datahelpdesk.worldbank.org/knowledgebase/articles/906519 (read 2026-11-11).
# Only economies that occur in the codes are listed. HIC = high income.
HIC = {"USA", "GBR", "IRL", "ESP", "ITA", "PRT", "FRA", "DEU", "NLD", "BEL", "AUS", "CAN",
       "KOR", "JPN", "GRC", "URY", "CHL", "GUY", "ROU", "SAU", "ARE", "QAT", "KWT", "OMN",
       "BHR", "ISR", "SGP", "NZL", "POL", "CHE", "AUT", "SWE", "NOR", "DNK", "FIN", "HUN",
       "CZE", "SVN", "HRV", "EST", "LTU", "LVA", "CYP", "MLT", "TWN", "HKG", "PAN", "TTO"}
LMIC = {"BGD", "PAK", "IND", "NGA", "GHA", "MMR", "BOL", "KEN", "CMR", "EGY", "MAR", "TUN",
        "LBN", "NPL", "HND", "ZWE", "TZA", "TGO", "VEN", "ETH", "UGA", "TCD", "SDN",
        "BRA", "IDN", "ZAF", "TUR", "IRN", "ARG", "IRQ", "PER", "COL", "ECU", "PRY", "SUR",
        "THA", "PHL", "MEX", "JAM", "DZA", "JOR", "LKA", "MYS", "VNM", "CHN", "ALB", "SRB",
        "RUS", "COD", "HTI", "LBR", "DOM", "CUB", "NAM", "UKR"}
# COD, HTI, LBR, DOM, CUB, NAM, UKR verified on the same page on 2026-11-11.
# RUS: listed as upper middle income in the same table. MULTI is handled separately.

DUPLICATES = {"X06": "R03100"}           # confirmed duplicates (E6)
PROBABLE_DUP = {"R02442": "R02406", "R02483": "R02437", "R01516": "R01478"}


def load_codes():
    rows = []
    for f in sorted(glob.glob(str(B / "code_*.txt"))):
        for line in open(f, encoding="utf-8"):
            if line.strip():
                p = line.rstrip("\n").split("|", 7)
                p += [""] * (8 - len(p))
                rows.append(p + [Path(f).name])
    df = pd.DataFrame(rows, columns=["record_id", "CTY", "GR", "LB", "VL", "E3W", "GOVM",
                                     "note", "code_file"])
    return df


def flag(val, target):
    """Return 'F' (firm), 'P' (probable) or '' for a code value against a target letter."""
    v = str(val)
    if not v.startswith(target):
        return ""
    return "P" if "?" in v else "F"


def countries(cty):
    return [c for c in re.split(r"\+", str(cty).replace("?", "")) if c and c != "-"]


def lmic_flag(cty):
    cs = countries(cty)
    if not cs:
        return ""
    if any(c in LMIC for c in cs):
        return "P" if "?" in str(cty) else "F"
    if "MULTI" in cs:
        return "P"
    return ""


VARIANTS = {"K": (False, False), "N1": (True, False), "N2": (True, True), "N3": (False, True)}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="N1", choices=sorted(VARIANTS),
                    help="K = Option B as written; N1 = C4 only in LMIC settings; "
                         "N2 = C3 and C4 only in LMIC; N3 = C3 only in LMIC")
    ap.add_argument("--c6", action="store_true", help="add criterion C6 (empirical driver studies in LMICs)")
    args = ap.parse_args()
    c4_lmic, c3_lmic = VARIANTS[args.variant]
    df = load_codes()
    # R6: codes confirmed or corrected from the full text replace abstract-level codes
    ov_path = ROOT / "data" / "fulltext_overrides.csv"
    df["code_source"] = "abstract"
    if ov_path.exists():
        ov = pd.read_csv(ov_path, keep_default_na=False, dtype=str).set_index("record_id")
        for rid, o in ov.iterrows():
            i = df.index[df.record_id == rid]
            if len(i) == 0:
                continue
            for c in ["CTY", "GR", "LB", "VL", "E3W", "GOVM"]:
                if o.get(c, ""):
                    df.loc[i, c] = o[c]
            df.loc[i, "code_source"] = "full text"
    idx = pd.read_csv(B / "map_index.csv")
    df = df.merge(idx, on="record_id", how="left", validate="one_to_one")
    assert df.ta_code.notna().all(), "record without ta_code"
    assert len(df) == len(idx) == df.record_id.nunique(), "coverage mismatch"

    df["excluded_duplicate"] = df.record_id.map(DUPLICATES)
    df["probable_duplicate_of"] = df.record_id.map(PROBABLE_DUP)
    df["is_review"] = df.ta_code.eq("RV") | df.CTY.eq("DUP")

    crit = pd.DataFrame(index=df.index)
    crit["C1_BGD"] = ["P" if "BGD?" in str(c) else ("F" if "BGD" in str(c) else "")
                      for c in df.CTY]
    crit["C2_E3W"] = [flag(v, "1") for v in df.E3W]
    def lmic_gate(f, cty, on):
        if not f or not on:
            return f
        g = lmic_flag(cty)
        return "" if not g else ("F" if f == g == "F" else "P")
    crit["C3_FIELD"] = [lmic_gate(flag(v, "F"), c, c3_lmic) for v, c in zip(df.VL, df.CTY)]
    c4 = []
    for t, g, l in zip(df.ta_code, df.GR, df.LB):
        if t not in ("I5b", "I5c"):
            c4.append("")
            continue
        fg, fl = flag(g, "M"), flag(l, "R")
        c4.append("" if not (fg and fl) else ("F" if fg == fl == "F" else "P"))
    crit["C4_MON_REAL"] = [lmic_gate(f, c, c4_lmic) for f, c in zip(c4, df.CTY)]
    c5 = []
    for gv, cty in zip(df.GOVM, df.CTY):
        fg, fc = flag(gv, "1"), lmic_flag(cty)
        c5.append("" if not (fg and fc) else ("F" if fg == fc == "F" else "P"))
    crit["C5_GOV_LMIC"] = c5
    # C6 (added 2026-11-11, author delegated): empirical study of the causes or social
    # context of theft (ta_code I5a, VL = Q) set in a low- or middle-income country
    c6 = []
    for t, v, cty in zip(df.ta_code, df.VL, df.CTY):
        fv, fc = (flag(v, "Q") if t == "I5a" else ""), lmic_flag(cty)
        c6.append("" if not (args.c6 and fv and fc) else ("F" if fv == fc == "F" else "P"))
    crit["C6_DRIVERS_LMIC"] = c6
    df = pd.concat([df, crit], axis=1)

    ok = ~df.is_review & df.excluded_duplicate.isna()
    any_f = crit.eq("F").any(axis=1)
    any_p = crit.eq("P").any(axis=1)
    df["priority"] = ""
    df.loc[ok & any_f, "priority"] = "firm"
    df.loc[ok & ~any_f & any_p, "priority"] = "probable"
    # a probable duplicate is never counted as firm
    df.loc[df.priority.eq("firm") & df.probable_duplicate_of.notna(), "priority"] = "probable"
    df["needs_fulltext_check"] = df.priority.eq("probable") | (
        df.priority.eq("firm") & df.note.str.contains(r"\?", regex=True))

    out = ROOT / "data"
    df.to_csv(out / "evidence_map_coded_manual.csv", index=False)
    pri = df[df.priority.ne("")].copy()
    pri.to_csv(out / "priority_synthesis_B.csv", index=False)

    # current synthesis set (round-2 baseline) for comparison
    prev = pd.read_csv(out / "extraction.csv")
    prev_dois = set(prev.doi.dropna().str.lower())
    rec = pd.read_csv(out / "records_dedup.csv", usecols=["record_id", "doi"])
    doi = dict(zip(rec.record_id, rec.doi.astype(str).str.lower()))
    pri["in_current_synthesis"] = pri.record_id.map(lambda r: doi.get(r, "") in prev_dois)

    summ = {
        "variant": args.variant,
        "records_coded": int(len(df)),
        "reviews_mapped": int(df.ta_code.eq("RV").sum()),
        "confirmed_duplicates_excluded": int(df.excluded_duplicate.notna().sum()),
        "priority_firm": int(df.priority.eq("firm").sum()),
        "priority_probable": int(df.priority.eq("probable").sum()),
        "priority_total_upper": int(df.priority.ne("").sum()),
        "priority_already_in_current_synthesis": int(pri.in_current_synthesis.sum()),
        "probable_duplicates_in_priority": int(pri.probable_duplicate_of.notna().sum()),
        "by_criterion_firm": {c: int(crit.loc[ok, c].eq("F").sum()) for c in crit},
        "by_criterion_any": {c: int(crit.loc[ok, c].ne("").sum()) for c in crit},
        "only_one_criterion_firm": {},
        "firm_needing_fulltext_check": int((df.priority.eq("firm") & df.needs_fulltext_check).sum()),
    }
    firm = df[df.priority.eq("firm")]
    for c in crit:
        others = [o for o in crit if o != c]
        summ["only_one_criterion_firm"][c] = int(
            (firm[c].ne("") & firm[others].eq("").all(axis=1)).sum())
    summ["priority_by_ta_code"] = pri.ta_code.value_counts().to_dict()
    json.dump(summ, open(out / "priority_synthesis_B_summary.json", "w"), indent=2)
    print(json.dumps(summ, indent=2))


if __name__ == "__main__":
    main()

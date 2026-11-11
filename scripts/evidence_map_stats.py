"""R3: descriptive statistics of the systematic evidence map (all eligible records,
abstract-level manual codes; '?' codes counted at their stated value; confirmed
duplicates removed). Output: data/evidence_map_stats.json."""
import glob
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from apply_scope_b import lmic_flag, load_codes, DUPLICATES  # noqa: E402


def main():
    # abstract-level codes straight from the coding files (no full-text overrides)
    m = load_codes().merge(pd.read_csv(ROOT / "data/evidence_map_batches/map_index.csv"), on="record_id")
    m = m[~m.record_id.isin(DUPLICATES)]
    yr = {}
    for f in glob.glob(str(ROOT / "data/evidence_map_batches/map_*.txt")):
        for line in open(f, encoding="utf-8"):
            p = line.split("|")
            yr[p[0]] = p[2]
    m["year"] = m.record_id.map(yr).astype(int)
    for c in ("GR", "LB", "VL"):
        m[c + "1"] = m[c].str[0]
    det = m[m.ta_code == "I5b"]
    dd = det[det.GR1.isin(["S", "M", "U"])]
    has = lambda c, k: k in c.replace("?", "").split("+")  # noqa: E731
    out = dict(n=len(m), by_code=m.ta_code.value_counts().to_dict(), det_n=len(det),
               det_GR=det.GR1.value_counts().to_dict(), det_LB=det.LB1.value_counts().to_dict(),
               det_VL=det.VL1.value_counts().to_dict(), dd_n=len(dd),
               dd_LB=dd.LB1.value_counts().to_dict(), dd_VL=dd.VL1.value_counts().to_dict(),
               dd_SGCC=int(dd.CTY.map(lambda c: has(c, "CHN")).sum()),
               dd_cty_stated=int((~dd.CTY.isin(["-", "-?"])).sum()),
               det_lmic=int(det.CTY.map(lambda c: lmic_flag(c) != "").sum()),
               all_BGD=int(m.CTY.str.contains("BGD").sum()),
               field_all=int(m.VL1.eq("F").sum()), field_det=int(det.VL1.eq("F").sum()),
               det_M=int(det.GR1.eq("M").sum()), det_M_R=int((det.GR1.eq("M") & det.LB1.eq("R")).sum()))
    bins = [2009, 2015, 2020, 2023, 2026]
    out["year_bins"] = {str(k): int(v) for k, v in m.groupby(pd.cut(m.year, bins), observed=False).size().items()}
    out["det_by_period_field"] = {str(k): int((g.VL1 == "F").sum()) for k, g in det.groupby(pd.cut(det.year, bins), observed=False)}
    gov = m[m.ta_code == "I5c"]
    out["gov_n"] = len(gov)
    out["gov_GOVM1"] = int(gov.GOVM.str.startswith("1").sum())
    out["no_abstract"] = int(m.note.str.contains("no abstract", case=False).sum())
    ctys = {}
    for c in m.CTY:
        for k in c.replace("?", "").split("+"):
            if k not in ("-", "", "DUP"):
                ctys[k] = ctys.get(k, 0) + 1
    out["top_countries"] = dict(sorted(ctys.items(), key=lambda x: -x[1])[:15])
    json.dump(out, open(ROOT / "data/evidence_map_stats.json", "w"), indent=1)
    print(json.dumps(out)[:400])


if __name__ == "__main__":
    main()

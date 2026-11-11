"""Apply the reference-budget tightening rule (protocol v1.1, section 2.1) to the
title/abstract-included records. Selection lists are explicit and versioned here.
Output: data/tightening_selection.csv, appends counts to data/prisma_counts.json"""
import json
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
SELECT = {
 "P1_bangladesh_e3w": ["R00874","R01422","R02285","R02485","R00590","R02400","R02453","R01790",
                       "R01924","R00953","R02446","R00633","R00347","R02859","R01968","R00240"],
 "P2_governance_lmic": ["R02736","R02801","R03052","R02682","R02852","R02824","R00686","R03062",
                        "R00626","R02987","R01631","R00226","R02851","R00994","R03050","R01764",
                        "R01295","R01144","R02339"],
 "P3_datadriven": ["R01017","R01804","R01449","R01701","R02911",
                   "R01632","R00365","R00430","R00431","R00678","R01224","R01198","R01414",
                   "R00176","R01647","R00480","R02093",
                   "R01066","R01660","R01254","R00311","R01022"],
 "P4_network": ["R01562","R03009","R02728","R01569","R01432","R00337","R02632"],
 "P5_hardware": ["R02234","R00854","R02645","R00875","R02473","R01109"],
 "P6_hybrid_cost": ["R01285","R02006","R02649","R02931","R02370"],
}
BACKGROUND_REVIEWS = ["R02624","R02139","R02619","R02666","R00212","R00638","R02488","R01524",
                      "R00667","R00093","R01690","R00682","R02734","R02266","R02409","R02557",
                      "R01918","R00691","R02663"]
s = pd.read_csv(ROOT/"data/screening.csv", dtype=str).fillna("")
f = pd.read_csv(ROOT/"data/tightening_flags.csv", dtype=str).fillna("")
inc = s[s.ta_decision=="INC"].merge(f[["record_id","lmic","lowres","real","journal_tier"]], on="record_id", how="left")
pool_of = {rid: p for p, ids in SELECT.items() for rid in ids}
rows = []
for r in inc.itertuples():
    if r.record_id in pool_of:
        dec, code, why = "RETRIEVE", pool_of[r.record_id], "Selected for full-text assessment"
    elif r.record_id in BACKGROUND_REVIEWS:
        dec, code, why = "BACKGROUND", "BG_review", "Existing review: Table T1 / background, not an included primary study"
    elif r.family == "RV":
        dec, code, why = "EXC_T", "T4", "Review not needed beyond the T1 set (narrower or lower-tier)"
    elif r.family == "DD" and not (r.lowres == "True" or (r.lmic == "True" and r.real == "True")):
        dec, code, why = "EXC_T", "T1", "Data-driven study on generic smart-meter/benchmark data without a Bangladesh-constraint contribution"
    else:
        dec, code, why = "EXC_T", "T2", "Eligible but ranked below the pool cut-off (venue tier, citation rate, redundancy with selected studies)"
    rows.append({"record_id": r.record_id, "title": r.title, "year": r.year, "venue": r.venue,
                 "family": r.family, "t_decision": dec, "t_code": code, "t_reason": why})
out = pd.DataFrame(rows)
missing = set(pool_of) - set(out.record_id)
assert not missing, f"selected IDs not in T/A includes: {missing}"
out.to_csv(ROOT/"data/tightening_selection.csv", index=False)
c = json.load(open(ROOT/"data/prisma_counts.json"))
c["ta_included"] = int(len(inc)); c["ta_excluded"] = int((s.ta_decision=="EXC").sum())
c["tightening"] = out.groupby(["t_decision","t_code"]).size().rename("n").reset_index().to_dict("records")
c["sought_for_retrieval"] = int((out.t_decision=="RETRIEVE").sum())
c["background_reviews"] = int((out.t_decision=="BACKGROUND").sum())
json.dump(c, open(ROOT/"data/prisma_counts.json","w"), indent=1)
print(out.groupby(["t_decision","t_code"]).size())

"""Build human-verification kits requested by peer review (verification/):

1. human_screening_sheet.csv  BLIND title/abstract re-screen (no AI decision shown):
   all 83 records retained for synthesis (69 studies + 14 reviews) and a stratified random
   sample of exclusions: 10% of each exclusion code (minimum 5) and 5% of each
   prioritisation code (minimum 10). Fixed seed.
2. human_extraction_sheet.csv  independent extraction of key fields for every study
   that supports a central claim (FT-CHECK sentences, Table 11) plus a random 20% of the
   remaining included studies. Blank fields, AI values hidden.
3. drm_expert_form.csv  blank C1-C7 scores (0-3) per family for each external expert,
   with the anchor definitions in drm_expert_instructions.md.
Answer keys (AI decisions/values) stay in data/ and are joined by verification_stats.py.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "verification"
V.mkdir(exist_ok=True)
rng = np.random.default_rng(20261110)

CENTRAL = ["haramaini2026hybrid", "barros2022maximizing", "otchereappiah2021impact", "rabbani2020does",
           "taruna2025electricity", "norouzi2025novel", "orozcoceron2026comparing", "soleimaninasab2022effect",
           "liao2024sample", "menezes2026geospatial", "razavi2019socio", "hossain2026measuring", "arafat2022prospects",
           "altamimi2025how", "odje2021aggregated", "biswas2020electricity", "yang2022detection", "jokar2016electricity",
           "jamil2014empirical", "mirza2023impact", "kankonde2025bridging", "wong2021perceptions", "massaferro2020fraud",
           "akand2019analytical", "chowdhury2026operational", "schloer2022how", "khan2020e", "ariasmarin2025methodological",
           "saeed2019ensemble", "buzau2019detection"]


def main():
    recs = pd.read_csv(ROOT / "data" / "records_dedup.csv", dtype=str).fillna("")
    scr = pd.read_csv(ROOT / "data" / "screening.csv", dtype=str).fillna("")
    tig = pd.read_csv(ROOT / "data" / "tightening_selection.csv", dtype=str).fillna("")
    ex = pd.read_csv(ROOT / "data" / "extraction.csv", dtype=str).fillna("")
    retained = set(ex[ex.role.isin(["included study", "background review"])].id)

    sample = set(retained)
    for code, g in scr[scr.ta_decision == "EXC"].groupby("ta_code"):
        k = min(len(g), max(5, int(np.ceil(0.10 * len(g)))))
        sample |= set(rng.choice(g.record_id.values, k, replace=False))
    for code, g in tig[tig.t_decision == "EXC_T"].groupby("t_code"):
        k = min(len(g), max(10, int(np.ceil(0.05 * len(g)))))
        sample |= set(rng.choice(g.record_id.values, k, replace=False))
    s = recs[recs.record_id.isin(sample)][["record_id", "title", "year", "venue", "abstract"]].copy()
    s = s.sample(frac=1, random_state=7)  # shuffle so retained records are not grouped
    for c in ["human_decision (INC/EXC)", "human_reason_code", "human_notes", "screener_initials"]:
        s[c] = ""
    s.to_csv(V / "human_screening_sheet.csv", index=False)

    inc = ex[ex.role == "included study"]
    central = inc[inc.citation_key.isin(CENTRAL)]
    rest = inc[~inc.citation_key.isin(CENTRAL)]
    extra = rest.sample(n=int(np.ceil(0.2 * len(rest))), random_state=11)
    e = pd.concat([central, extra])[["id", "citation_key", "doi", "year"]].copy()
    fields = ["country_region", "study_type", "data_granularity", "labelled_data", "class_imbalance_handling",
              "metrics_reported", "real_world_deployment", "headline_numbers_as_printed", "full_text_read (Y/N)",
              "extractor_initials", "notes"]
    for c in fields:
        e[c] = ""
    e.to_csv(V / "human_extraction_sheet.csv", index=False)

    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from drm import DRM, CONSTRAINTS
    rows = []
    for name, *_ in DRM:
        rows.append({"family": name, **{c.split()[0]: "" for c in CONSTRAINTS}, "comments": ""})
    pd.DataFrame(rows).to_csv(V / "drm_expert_form.csv", index=False)
    print(f"screening sheet: {len(s)} records ({len(retained)} retained + {len(s) - len(retained)} sampled exclusions)")
    print(f"extraction sheet: {len(e)} studies ({len(central)} central + {len(extra)} random)")
    print(f"DRM form: {len(rows)} families")


if __name__ == "__main__":
    main()

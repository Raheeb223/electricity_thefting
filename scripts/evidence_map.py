"""Evidence map of ALL 1,644 eligible records and a selection-sensitivity check.

Question (peer review): would the key descriptive findings change if the 1,550
eligible-but-not-selected records had been synthesised?  We cannot extract 1,644 studies,
but we can apply the same transparent text indicators to the title+abstract of every
eligible record and compare selected vs not-selected records.

Indicators (regular expressions on title + abstract, case-insensitive):
  field      field test/trial/validation/inspection, on-site inspection, deployed, pilot,
             in operation, real-world deployment
  monthly    monthly, billing data, conventional/traditional/electromechanical meter,
             non-smart, low sampling
  smart      smart meter, AMI, advanced metering, SGCC, half-hourly/15-min, high-resolution
  synthetic  synthetic, simulated attack, injected, attack model, theft case(s) generated
  lmic       Bangladesh, India, Pakistan, Nepal, Sri Lanka, Brazil, Africa, Indonesia, Iran,
             developing countr*, emerging econom*
Indicators are keyword flags, not judgements; they are reported as an approximate
sensitivity check. Outputs: data/evidence_map.csv (per record), data/evidence_map_summary.csv,
data/pool_cutoffs.csv, figures/figS1_evidence_map.(pdf|png).
"""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IND = {
    "field": r"field (?:test|trial|validation|validated|experiment|deployment)|pilot (?:project|study|deployment)|(?:was|were|has been) (?:deployed|implemented|put into operation) (?:in|at|by) (?:the |a )?(?:utility|company|distribution)|real[- ]world deployment|new (?:field )?inspections|inspections? (?:were|was) (?:carried out|conducted|performed) to (?:validate|verify|confirm)",
    "monthly": r"monthly|billing data|bill(ing)? records|conventional meter|traditional meter|electromechanical|non-smart|low[- ]sampling|postpaid",
    "smart": r"smart meter|\bami\b|advanced metering|sgcc|state grid|half[- ]hourly|15[- ]min|high[- ]resolution|fine[- ]grained",
    "synthetic": r"synthetic|simulated attack|inject|attack model|false data|theft (cases|attacks) (were )?generated",
    "lmic": r"bangladesh|india|pakistan|nepal|sri lanka|brazil|africa|indonesia|iran|developing countr|emerging econom|nigeria|ghana|kenya",
}
FAM = {"DD": "Data-driven", "NW": "Network", "HW": "Hardware/metering", "HY": "Hybrid", "GV": "Governance",
       "E3W": "E3W/Bangladesh", "BD": "E3W/Bangladesh", "RV": "Review"}


def main():
    recs = pd.read_csv(ROOT / "data" / "records_dedup.csv", dtype=str).fillna("")
    scr = pd.read_csv(ROOT / "data" / "screening.csv", dtype=str).fillna("")
    tig = pd.read_csv(ROOT / "data" / "tightening_selection.csv", dtype=str).fillna("")
    elig = scr[scr.ta_decision == "INC"][["record_id", "ta_code", "family", "year"]]
    elig = elig.merge(recs[["record_id", "title", "abstract"]], on="record_id").merge(
        tig[["record_id", "t_decision", "t_code"]], on="record_id", how="left")
    elig["selected"] = np.where(elig.t_decision == "RETRIEVE", "selected",
                                np.where(elig.t_decision == "BACKGROUND", "background review", "not selected"))
    text = (elig.title + " " + elig.abstract).str.lower()
    for k, rx in IND.items():
        elig[k] = text.str.contains(rx, regex=True)
    elig["has_abstract"] = elig.abstract.str.len() > 50
    elig["group"] = elig.family.map(FAM).fillna("Other")
    elig.drop(columns=["abstract"]).to_csv(ROOT / "data" / "evidence_map.csv", index=False)

    det = elig[(elig.ta_code == "I5b") & elig.has_abstract]
    rows = []
    for lab, sub in [("Selected detection studies", det[det.selected == "selected"]),
                     ("Not-selected detection studies", det[det.selected == "not selected"]),
                     ("All eligible detection studies", det)]:
        rows.append({"set": lab, "n": len(sub), **{f"% {k}": round(100 * sub[k].mean(), 1) for k in IND}})
    summ = pd.DataFrame(rows)
    summ.to_csv(ROOT / "data" / "evidence_map_summary.csv", index=False)
    print(summ.to_string(index=False))

    # pool cut-offs: eligible per family vs selected per pool
    pc = elig.groupby("group").agg(eligible=("record_id", "size"),
                                   selected=("selected", lambda s: (s == "selected").sum()),
                                   background=("selected", lambda s: (s == "background review").sum())).reset_index()
    pc.to_csv(ROOT / "data" / "pool_cutoffs.csv", index=False)
    print(pc.to_string(index=False))

    # evidence-map figure: eligible records by year and family, selected overlaid
    yrs = list(range(2010, 2027))
    groups = ["Data-driven", "Network", "Hardware/metering", "Hybrid", "Governance", "E3W/Bangladesh", "Review"]
    cols = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]
    elig["yr"] = pd.to_numeric(elig.year, errors="coerce")
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.8), gridspec_kw={"width_ratios": [2.2, 1]})
    bottom = np.zeros(len(yrs))
    for g, c in zip(groups, cols):
        v = np.array([((elig.group == g) & (elig.yr == y)).sum() for y in yrs])
        axs[0].bar(yrs, v, bottom=bottom, color=c, width=0.75, label=g, edgecolor="white", linewidth=0.6)
        bottom += v
    sel = np.array([((elig.selected == "selected") & (elig.yr == y)).sum() for y in yrs])
    axs[0].plot(yrs, sel, color="#0b0b0b", marker="o", ms=3, lw=1.2, label="Selected for synthesis")
    axs[0].set_ylabel("Eligible records", fontsize=8); axs[0].tick_params(labelsize=7)
    axs[0].set_xticks(yrs[::2]); axs[0].spines[["top", "right"]].set_visible(False)
    axs[0].legend(fontsize=6, frameon=False, ncol=2, loc="upper left")
    labs = ["field", "monthly", "smart", "synthetic", "lmic"]
    names = ["Field\nvalidation", "Monthly /\nbilling", "Smart-meter\ndata", "Synthetic\ntheft", "LMIC\nsetting"]
    x = np.arange(len(labs))
    s1 = summ.set_index("set")
    axs[1].bar(x - 0.2, [s1.loc["Selected detection studies", f"% {k}"] for k in labs], 0.4, color="#2a78d6", label="Selected")
    axs[1].bar(x + 0.2, [s1.loc["Not-selected detection studies", f"% {k}"] for k in labs], 0.4, color="#b7d3f6", label="Not selected")
    axs[1].set_xticks(x); axs[1].set_xticklabels(names, fontsize=6)
    axs[1].set_ylabel("% of detection studies (keyword flag)", fontsize=7); axs[1].tick_params(labelsize=7)
    axs[1].legend(fontsize=6, frameon=False); axs[1].spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    for ext, kw in (("pdf", {}), ("png", {"dpi": 300})):
        fig.savefig(ROOT / "figures" / f"figS1_evidence_map.{ext}", bbox_inches="tight", **kw)
    print("saved figS1")


if __name__ == "__main__":
    main()

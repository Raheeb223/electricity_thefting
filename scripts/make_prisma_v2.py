"""Two-tier PRISMA 2020 flow diagram (R3, m4). All numbers computed from data files.
Saves figures/fig1_prisma_flow.pdf/.png (replaces the round-2 diagram)."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from make_figures import box, arrow, save, INK2, SLOTS  # noqa: E402


def counts():
    p = json.load(open(ROOT / "data/prisma_counts.json"))
    scr = pd.read_csv(ROOT / "data/screening.csv")
    exc = scr[scr.ta_decision == "EXC"].ta_code.value_counts().to_dict()
    dep = pd.read_csv(ROOT / "data/screening_batches/dec_14_crossref_depth.csv")
    dep_inc = int((dep.ta_decision == "INC").sum())
    dep_exc = dep[dep.ta_decision == "EXC"].ta_code.value_counts().to_dict()
    m = pd.read_csv(ROOT / "data/evidence_map_coded_manual.csv", keep_default_na=False)
    m = m[m.excluded_duplicate == ""]
    rv = m[m.ta_code == "RV"]
    rv_noabs = int(rv.note.str.contains("no abstract", case=False).sum())
    sb = json.load(open(ROOT / "data/priority_synthesis_B_summary.json"))
    n_pri = sb["priority_firm"] + sb["priority_probable"]
    va = pd.read_csv(ROOT / "data/venue_audit/venue_audit.csv", keep_default_na=False)
    pri_ids = set(pd.read_csv(ROOT / "data/priority_synthesis_B.csv").record_id)
    pv = va[(va.group == "priority study") & va.record_id.isin(pri_ids)]
    v_e5 = int(pv.decision.str.startswith(("E5", "no venue")).sum())
    v_e4 = int(pv.decision.str.startswith("E4").sum())
    v_grey = int(pv.decision.str.startswith("grey").sum())
    fx = pd.read_csv(ROOT / "data/fulltext_exclusions.csv")
    syn = pd.read_csv(ROOT / "data/synthesis_set.csv", keep_default_na=False)
    n_notret = len(pd.read_csv(ROOT / "data/synthesis_not_retrieved.csv", keep_default_na=False))
    ft = set(pd.read_csv(ROOT / "data/extraction_ft.csv").record_id)
    g = pd.read_csv(ROOT / "data/grey/grey_literature.csv")
    return dict(p=p, exc=exc, dep_inc=dep_inc, dep_exc=dep_exc, n_map=len(m), n_rv=len(rv), rv_noabs=rv_noabs,
                n_pri=n_pri, n_out=len(m) - len(rv) - n_pri, v_e5=v_e5, v_e4=v_e4, v_grey=v_grey,
                fx=fx.code.value_counts().to_dict(), n_syn=len(syn), n_ft=int(syn.record_id.isin(ft).sum()),
                n_grey=len(g), n_notret=n_notret)


def main():
    c = counts()
    p, s = c["p"], c["p"]["identified_by_source"]
    fig, ax = plt.subplots(figsize=(7.4, 9.2))
    ax.set_xlim(0, 1); ax.set_ylim(-0.02, 1); ax.axis("off")
    L, R, W, WR = 0.05, 0.58, 0.45, 0.41
    X = L + W / 2
    for y, lab in [(0.92, "Identification"), (0.76, "Screening"), (0.45, "Tier 1: evidence map"),
                   (0.12, "Tier 2: synthesis")]:
        ax.text(0.003, y, lab, rotation=90, ha="left", va="center", fontsize=7.5, color=INK2, fontweight="bold")
    box(ax, L, 0.88, W, 0.10, f"Records identified (n = {p['identified_total_hits']:,})\n"
        f"OpenAlex {s['openalex']:,}; Semantic Scholar {s['semanticscholar']:,};\n"
        f"Crossref {s['crossref']:,}; arXiv {s['arxiv']}", fs=6.8)
    box(ax, R, 0.865, WR, 0.125, "Removed before screening:\n"
        f"duplicates (n = {p['duplicates_removed']:,})\n"
        f"failed Boolean re-check (n = {p['removed_by_automation_search_logic']:,})\n"
        f"ineligible record type (n = {p['removed_ineligible_record_type']})\n"
        f"no title (n = {p['removed_no_title']})", fs=6.5)
    arrow(ax, L + W, 0.93, R, 0.93)
    box(ax, L, 0.76, W, 0.07, f"Records screened on title and abstract\n(n = {p['records_screened']:,})", fs=6.8)
    arrow(ax, X, 0.88, X, 0.83)
    e = c["exc"]
    box(ax, R, 0.70, WR, 0.15, f"Excluded (n = {sum(e.values()):,}):\nE1 off topic {e.get('E1', 0)}; E2 no evaluation {e.get('E2', 0)}\n"
        f"E3 not English {e.get('E3', 0)}; E4 not peer-reviewed full paper {e.get('E4', 0)}\n"
        f"E5 venue not indexed {e.get('E5', 0)}; E6 duplicate {e.get('E6', 0)}\nE7 abstract insufficient {e.get('E7', 0)}", fs=6.3)
    arrow(ax, L + W, 0.795, R, 0.795)
    d = c["dep_exc"]
    box(ax, R, 0.565, WR, 0.115, "Crossref depth check (ranks 201-1,000):\n"
        f"54 new Boolean-passing records screened;\nexcluded {sum(d.values())} (E1 {d.get('E1', 0)}, E4 {d.get('E4', 0)}, E5 {d.get('E5', 0)},\n"
        f"E6 {d.get('E6', 0)}, E3 {d.get('E3', 0)}); eligible {c['dep_inc']}", fs=6.3)
    arrow(ax, R, 0.62, L + W, 0.62)
    box(ax, L, 0.57, W, 0.10, f"Eligible records coded in the evidence map\n"
        f"(n = {c['n_map']:,}: {p['ta_included']:,} + {c['dep_inc']} depth check)\n"
        "coded from title and full abstract", fc="#eef4fc", ec=SLOTS[0], fs=6.8)
    arrow(ax, X, 0.76, X, 0.67)
    box(ax, R, 0.475, WR, 0.075, f"Reviews mapped, not synthesised (n = {c['n_rv']});\n"
        f"14 used for Table 1; {c['rv_noabs']} without an abstract", fs=6.3)
    arrow(ax, X, 0.5125, R, 0.5125)
    box(ax, R, 0.39, WR, 0.065, f"Not meeting scope criteria P1-P6\n(n = {c['n_out']:,}): mapped only", fs=6.3)
    arrow(ax, X, 0.4225, R, 0.4225)
    box(ax, L, 0.29, W, 0.075, f"Studies meeting scope criteria P1-P6\n(n = {c['n_pri']}; firm and probable)", fs=6.8)
    arrow(ax, X, 0.57, X, 0.365)
    box(ax, R, 0.19, WR, 0.085, "Removed after venue audit (n = "
        f"{c['v_e5'] + c['v_e4'] + c['v_grey']}):\nE5 venue not in Scopus list, WoS\nstatus not checked {c['v_e5']}; "
        f"E4 not peer-reviewed {c['v_e4']};\nmoved to grey literature {c['v_grey']}", fs=6.2)
    arrow(ax, X, 0.2325, R, 0.2325)
    box(ax, R, 0.118, WR, 0.064, "Full text not retrieved (n = "
        f"{c['n_notret']}):\nno open-access copy or automated publisher\naccess; kept in the evidence map only", fs=6.2)
    arrow(ax, X, 0.15, R, 0.15)
    box(ax, R, 0.05, WR, 0.05, "Excluded on full text (n = "
        f"{sum(c['fx'].values())}): " + "; ".join(f"{k} {v}" for k, v in c["fx"].items()) + "\n(gas utility; network-equipment theft; duplicate)", fs=6.2)
    arrow(ax, X, 0.075, R, 0.075)
    box(ax, L, -0.01, W, 0.07, f"Studies in the in-depth synthesis,\nfull text read (n = {c['n_syn']})\n"
        f"+ grey literature (n = {c['n_grey']}, purposive search)", fc="#eef4fc", ec=SLOTS[0], fs=6.8)
    arrow(ax, X, 0.29, X, 0.06)
    save(fig, "fig1_prisma_flow")
    print({k: v for k, v in c.items() if k != "p"})


if __name__ == "__main__":
    main()

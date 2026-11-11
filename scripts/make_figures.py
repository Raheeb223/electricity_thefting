"""Phase 5: all figures, saved as vector PDF + 300 dpi PNG in figures/.

Palette: validated categorical slots 1-6 (light mode, adjacent pairs pass CVD and
normal-vision floors; contrast WARN relieved by legends/direct labels and by the
supplementary CSV tables). Sequential: single blue ramp.
"""
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from drm import DRM, CONSTRAINTS  # noqa: E402

FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#fcfcfb"
SEQ = ["#f0efec", "#b7d3f6", "#6da7ec", "#256abf", "#0d366b"]
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": False, "pdf.fonttype": 42, "savefig.facecolor": "white",
})

GROUP = {"E3W": "Bangladesh context & E3W", "BD-SYS": "Bangladesh context & E3W",
         "GOV-DRV": "Governance & socio-economic", "GOV-INST": "Governance & socio-economic",
         "GOV-REG": "Governance & socio-economic", "DD-ML": "Data-driven", "DD-DL": "Data-driven",
         "DD-LAB": "Data-driven", "DD-ECON": "Data-driven", "DD-GEO": "Data-driven",
         "NW-BAL": "Network-based", "NW-SE": "Network-based", "HW-MON": "Hardware & metering",
         "HW-SM": "Hardware & metering", "HW-PREV": "Hardware & metering", "HY": "Hybrid"}
ORDER = ["Data-driven", "Network-based", "Hardware & metering", "Hybrid",
         "Governance & socio-economic", "Bangladesh context & E3W"]


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def load():
    ex = pd.read_csv(ROOT / "data" / "extraction.csv", dtype=str).fillna("")
    inc = ex[ex.role == "included study"].copy()
    inc["group"] = inc.approach_family.map(GROUP)
    inc["year"] = inc.year.astype(int)
    return ex, inc


def box(ax, x, y, w, h, text, fc="white", ec=MUTED, fs=7, bold=False, color=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.004,rounding_size=0.012",
                                fc=fc, ec=ec, lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=color,
            fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=INK2, lw=0.8, shrinkA=0, shrinkB=0))


def fig_prisma(inc):
    p = json.load(open(ROOT / "data" / "prisma_counts.json"))
    s = p["identified_by_source"]
    n_ft = 8
    fig, ax = plt.subplots(figsize=(7.2, 7.6))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    L, R, W, WR = 0.04, 0.58, 0.44, 0.40
    for y, lab in [(0.93, "Identification"), (0.62, "Screening"), (0.13, "Included")]:
        ax.text(0.005, y, lab, rotation=90, ha="left", va="center", fontsize=8, color=INK2, fontweight="bold")
    box(ax, L, 0.86, W, 0.12, f"Records identified (n = {p['identified_total_hits']:,})\n"
        f"OpenAlex {s['openalex']:,}; Semantic Scholar {s['semanticscholar']:,};\n"
        f"Crossref {s['crossref']:,}; arXiv {s['arxiv']}\nSearch dates: see Supplementary S4")
    box(ax, R, 0.84, WR, 0.16, "Removed before screening:\n"
        f"duplicates (n = {p['duplicates_removed']:,})\n"
        f"failed Boolean re-check (n = {p['removed_by_automation_search_logic']:,})\n"
        f"ineligible record type (n = {p['removed_ineligible_record_type']})\n"
        f"no title (n = {p['removed_no_title']})")
    arrow(ax, L + W, 0.92, R, 0.92)
    box(ax, L, 0.70, W, 0.08, f"Records screened on title/abstract\n(n = {p['records_screened']:,})")
    arrow(ax, L + W / 2, 0.86, L + W / 2, 0.78)
    box(ax, R, 0.655, WR, 0.17, f"Records excluded (n = {p['ta_excluded']:,})\nE1 off topic 784"
        "\nE5 venue not indexed 366\nE4 not a peer-reviewed full paper 344\n"
        "E6 duplicate 24; E2 no evaluation 13;\nE7 abstract insufficient 2")
    arrow(ax, L + W, 0.74, R, 0.74)
    box(ax, L, 0.53, W, 0.09, f"Records eligible after screening\n(n = {p['ta_included']:,})")
    arrow(ax, L + W / 2, 0.70, L + W / 2, 0.62)
    box(ax, R, 0.47, WR, 0.15, "Not selected under pre-specified\nprioritisation rule (n = 1,550):\n"
        "T1 generic smart-meter or benchmark\ndetection study 867\nT2 below pool cut-off 640\n"
        "T4 review beyond Table 1 set 43")
    arrow(ax, L + W, 0.575, R, 0.575)
    box(ax, L, 0.36, W, 0.09, f"Reports sought for retrieval (n = {p['sought_for_retrieval']})\n"
        f"Background reviews set aside for Table 1 (n = {p['background_reviews']})")
    arrow(ax, L + W / 2, 0.53, L + W / 2, 0.45)
    box(ax, R, 0.33, WR, 0.12, "Reports with neither full text nor\nabstract available (n = 6):\n"
        "withheld, not cited\n(reviews without abstract: 5)")
    arrow(ax, L + W, 0.405, R, 0.405)
    box(ax, L, 0.21, W, 0.10, f"Reports assessed for eligibility (n = {len(inc)})\n"
        f"full text n = {n_ft}; abstract + metadata n = {len(inc) - n_ft}")
    arrow(ax, L + W / 2, 0.36, L + W / 2, 0.31)
    box(ax, L, 0.04, W, 0.12, f"Studies included in synthesis (n = {len(inc)})\n"
        f"+ background reviews (n = 14)\n+ grey literature (n = 13, separate search)", fc="#eef4fc", ec=SLOTS[0])
    arrow(ax, L + W / 2, 0.21, L + W / 2, 0.16)
    box(ax, R, 0.06, WR, 0.10, "Grey literature: utility statements,\nregulatory and multilateral reports,\n"
        "national newspapers (Bangladesh)")
    arrow(ax, R, 0.11, L + W, 0.11)
    save(fig, "fig1_prisma_flow")


def fig_years(inc):
    yrs = list(range(2010, 2027))
    ct = inc.groupby(["year", "group"]).size().unstack(fill_value=0).reindex(yrs, fill_value=0)
    fig, ax = plt.subplots(figsize=(7.0, 2.9))
    bottom = np.zeros(len(yrs))
    for i, g in enumerate(ORDER):
        v = ct[g].values if g in ct else np.zeros(len(yrs))
        ax.bar(yrs, v, bottom=bottom, color=SLOTS[i], width=0.72, label=g, edgecolor="white", linewidth=1.0)
        bottom += v
    for x, t in zip(yrs, bottom):
        if t:
            ax.text(x, t + 0.2, int(t), ha="center", va="bottom", fontsize=7, color=INK2)
    ax.set_xticks(yrs); ax.set_xticklabels([str(y) for y in yrs], fontsize=6.5, rotation=45)
    ax.set_ylabel("Included studies"); ax.yaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.legend(ncol=3, frameon=False, fontsize=7, loc="upper left", bbox_to_anchor=(0, 1.22))
    ax.text(1.0, -0.2, "2026 covers January to November", transform=ax.transAxes, ha="right", fontsize=6.5, color=MUTED)
    save(fig, "fig2_publications_by_year")


COUNTRY = [("Bangladesh", "Bangladesh"), ("Pakistan", "Pakistan"), ("India", "India"), ("Indonesia", "Indonesia"),
           ("Brazil", "Brazil"), ("Iran", "Iran"), ("China", "China"), ("Uganda", "Uganda"), ("Ghana", "Ghana"),
           ("Uruguay", "Uruguay"), ("Nigeria", "Nigeria"), ("South Africa", "South Africa"), ("Ecuador", "Ecuador"),
           ("Congo", "DR Congo"), ("Spain", "Spain"), ("Taiwan", "Taiwan"), ("Korea", "South Korea"),
           ("Saudi", "Saudi Arabia"), ("Africa", "Multi-country Africa"), ("Latin America", "Latin America (region)")]


def country_of(s):
    for k, v in COUNTRY:
        if k in s:
            return v
    return "Not stated / benchmark"


def fig_countries(inc):
    c = Counter(inc.country_region.map(country_of))
    items = sorted(c.items(), key=lambda kv: (kv[0] == "Not stated / benchmark", -kv[1], kv[0]))[::-1]
    fig, ax = plt.subplots(figsize=(3.6, 4.2))
    labels, vals = zip(*items)
    colors = [SLOTS[1] if l == "Bangladesh" else SLOTS[0] for l in labels]
    ax.barh(labels, vals, color=colors, height=0.66)
    for i, v in enumerate(vals):
        ax.text(v + 0.2, i, str(v), va="center", fontsize=7, color=INK2)
    ax.set_xlabel("Included studies"); ax.tick_params(axis="y", length=0, labelsize=7)
    ax.xaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    save(fig, "fig3_countries")
    return c


def fig_datasets(inc):
    meth = inc[inc.approach_family.str[:2].isin(["DD", "NW", "HW", "HY"]) & ~inc.study_type.str.contains("quasi|regression|data analysis|survey|analytical", regex=True)]
    g = meth.data_granularity.str.lower()
    cat = np.select([g.str.startswith("monthly"), g.str.startswith("mixed"), g.str.startswith("daily"),
                     g.str.contains("hourly"), g.str.startswith("imagery")],
                    ["Monthly billing", "Mixed monthly + interval", "Daily", "Hourly / sub-hourly", "Satellite imagery"],
                    "Not applicable (hardware, simulation)")
    lab = meth.labelled_data.str.upper()
    lcat = np.select([lab.str.startswith("Y"), lab.str.startswith("PARTIAL")], ["Real inspection labels", "Partial / injected"],
                     "None or synthetic only")
    rw = meth.real_world_deployment.str.upper()
    dcat = np.select([rw.str.startswith("Y"), rw.str.startswith("PARTIAL")], ["Field-validated or deployed", "Partial (real data, no yield)"],
                     "Offline / simulation only")
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.2), sharex=True)
    for ax, (title, arr) in zip(axs, [("Input data granularity", cat), ("Theft labels", lcat), ("Validation setting", dcat)]):
        cc = Counter(arr); items = sorted(cc.items(), key=lambda kv: kv[1])
        ax.barh([k for k, _ in items], [v for _, v in items], color=SLOTS[0], height=0.6)
        for i, (_, v) in enumerate(items):
            ax.text(v + 0.3, i, str(v), va="center", fontsize=7, color=INK2)
        ax.set_title(title, fontsize=8, color=INK, loc="left"); ax.tick_params(axis="y", length=0, labelsize=6.8)
        ax.xaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    axs[1].set_xlabel(f"Method studies (n = {len(meth)})")
    fig.tight_layout(w_pad=1.2)
    save(fig, "fig4_data_and_validation")
    return len(meth), Counter(cat), Counter(lcat), Counter(dcat)


PERF = [  # study label, setting, metric, value  (values from abstracts/full texts; see Table 4)
    ("Arias-Marin 2025", "Non-AMI billing data,\nreal labels, offline", "Accuracy", 0.897),
    ("Arias-Marin 2025", "Non-AMI billing data,\nreal labels, offline", "F1", 0.894),
    ("Taruna 2025", "Non-AMI billing data,\nreal labels, offline", "Accuracy", 0.89),
    ("Taruna 2025", "Non-AMI billing data,\nreal labels, offline", "F1", 0.90),
    ("Taruna 2025", "Non-AMI billing data,\nreal labels, offline", "AUC / PR-AUC", 0.89),
    ("Norouzi 2025", "Non-AMI billing data,\nreal labels, offline", "Accuracy", 0.997),
    ("Saeed 2019", "Non-AMI billing data,\nreal labels, offline", "Accuracy", 0.931),
    ("Saqib 2024", "Non-AMI billing data,\nreal labels, offline", "F1", 0.91),
    ("Orozco-Ceron 2026", "Non-AMI billing data,\nreal labels, offline", "Accuracy", 0.685),
    ("Orozco-Ceron 2026", "Non-AMI billing data,\nreal labels, offline", "F1", 0.677),
    ("Orozco-Ceron 2026", "Non-AMI billing data,\nreal labels, offline", "AUC / PR-AUC", 0.748),
    ("Haramaini 2026", "Non-AMI billing data,\nreal labels, offline", "AUC / PR-AUC", 0.776),
    ("Haramaini 2026", "Field-validated", "Field detection rate", 0.72),
    ("Rule baseline (Haramaini 2026)", "Field-validated", "Field detection rate", 0.153),
    ("Menezes 2026", "Field-validated", "Accuracy", 0.8305),
    ("Kim 2019", "Simulation or laboratory", "Accuracy", 0.95),
    ("Aryanezhad 2019", "Simulation or laboratory", "Accuracy", 0.99),
]


LABELS = {("Rule baseline (Haramaini 2026)", "Field detection rate"): (0, 9, "center"),
          ("Haramaini 2026", "Field detection rate"): (-8, 0, "right"),
          ("Menezes 2026", "Accuracy"): (-8, 0, "right"),
          ("Norouzi 2025", "Accuracy"): (0, 10, "center"),
          ("Orozco-Ceron 2026", "AUC / PR-AUC"): (0, -10, "center"),
          ("Kim 2019", "Accuracy"): (-8, 0, "right"),
          ("Aryanezhad 2019", "Accuracy"): (-8, 0, "right")}


def fig_performance():
    df = pd.DataFrame(PERF, columns=["study", "setting", "metric", "value"])
    settings = ["Simulation or laboratory", "Non-AMI billing data,\nreal labels, offline", "Field-validated"]
    mk = {"Accuracy": ("o", SLOTS[0]), "F1": ("s", SLOTS[1]), "AUC / PR-AUC": ("^", SLOTS[2]),
          "Field detection rate": ("D", INK2)}
    fig, ax = plt.subplots(figsize=(7.0, 2.9))
    pos = {}
    for i, s in enumerate(settings):
        sub = df[df.setting == s]
        jit = np.linspace(-0.22, 0.22, len(sub)) if len(sub) > 1 else [0]
        for (j, r), dy in zip(sub.iterrows(), jit):
            m, c = mk[r.metric]
            ax.scatter(r.value, i + dy, marker=m, s=34, color=c, edgecolor="white", linewidth=0.8, zorder=3)
            pos[(r.study, r.metric)] = (r.value, i + dy)
        ax.axhspan(i - 0.36, i + 0.36, color="#f6f5f2", zorder=0)
    for (st, mt), (dx, dy, ha) in LABELS.items():
        if (st, mt) in pos:
            x, y = pos[(st, mt)]
            ax.annotate(st, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", fontsize=6.5, color=INK2)
    ax.set_yticks(range(3)); ax.set_yticklabels(settings, fontsize=7); ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, 1.03); ax.set_xlabel("Reported headline value (0-1)")
    ax.xaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    for k, (m, c) in mk.items():
        ax.scatter([], [], marker=m, color=c, s=30, label=k)
    ax.legend(ncol=4, frameon=False, fontsize=7, loc="upper left", bbox_to_anchor=(0, 1.16))
    save(fig, "fig5_reported_performance")


def fig_drm():
    names = [d[0] for d in DRM]
    M = np.array([d[1] for d in DRM], dtype=float)
    E = np.array([d[2] for d in DRM], dtype=float)
    ready = M.mean(axis=1)
    # Order by readiness only (evidence breaks ties); reference row last.
    key = -(ready * 10 + E)
    key[[i for i, n in enumerate(names) if n.startswith("Rule-based")]] = 999
    order = np.argsort(key, kind="stable")
    M, E, ready, names = M[order], E[order], ready[order], [names[i] for i in order]
    from matplotlib.colors import ListedColormap, BoundaryNorm
    cmap = ListedColormap(SEQ[1:]); norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], 4)
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    full = np.column_stack([M, ready, E])
    for j in range(full.shape[1]):
        for i in range(full.shape[0]):
            v = full[i, j]
            col = cmap(norm(round(v)))
            x0 = j + (0.35 if j >= 7 else 0) + (0.2 if j == 8 else 0)
            ax.add_patch(plt.Rectangle((x0, i), 0.94, 0.9, color=col, lw=0))
            txt = f"{v:.1f}" if j == 7 else f"{int(v)}"
            ax.text(x0 + 0.47, i + 0.45, txt, ha="center", va="center", fontsize=7,
                    color="white" if round(v) >= 2 else INK, fontweight="bold" if j == 7 else "normal")
    xt = [j + 0.47 for j in range(7)] + [7.35 + 0.47, 8.55 + 0.47]
    ax.set_xticks(xt)
    short = ["C1\nData\ngranularity", "C2\nMeter type\n/ AMI", "C3\nCost per\nconsumer", "C4\nLabelled\ndata",
             "C5\nPrivacy", "C6\nStaff\ncapacity", "C7\nCollusion\nrobustness"]
    ax.set_xticklabels(short + ["Readiness\n(mean\nC1-C7)", "Evidence\nstrength\n(0-3)"], fontsize=6.6)
    ax.xaxis.tick_top(); ax.tick_params(length=0)
    def mark(n):
        if n.startswith("Active prevention"):
            return n + " †"
        if n.startswith("Rule-based"):
            return n + " [reference]"
        if n.startswith("Energy balance"):
            return n + " ‡"
        return n
    disp = [mark(n) for n in names]
    ax.set_yticks([i + 0.45 for i in range(len(names))]); ax.set_yticklabels(disp, fontsize=7)
    # tier dividers: tier 1 readiness >= 2.0, tier 2 1.4-1.6, tier 3 < 1.0
    for i in range(1, len(names)):
        if names[i].startswith("Rule-based") or (ready[i - 1] >= 2.0 > ready[i]) or (ready[i - 1] >= 1.0 > ready[i]):
            ax.axhline(i - 0.05, color=INK2, lw=0.8, xmax=0.97)
    ax.set_xlim(-0.05, 9.6); ax.set_ylim(len(names), -0.1)
    for s in ax.spines.values():
        s.set_visible(False)
    for k, lab in enumerate(["0 not feasible", "1 substantial need", "2 minor need", "3 fits now"]):
        ax.add_patch(plt.Rectangle((k * 2.4, len(names) + 0.5), 0.35, 0.5, color=cmap(k), clip_on=False))
        ax.text(k * 2.4 + 0.45, len(names) + 0.75, lab, va="center", fontsize=6.8, color=INK2, clip_on=False)
    ax.text(0, len(names) + 1.55, "Evidence strength: 0 concept, 1 simulation/laboratory, 2 real data offline, 3 field-validated.\n"
            "† not recommended (safety, legality).  ‡ transformer-metering baseline in Bangladesh unknown.  Lines separate tiers.",
            fontsize=6.5, color=MUTED, clip_on=False, va="top")
    save(fig, "fig6_deployability_matrix")
    return list(zip(names, ready, E))


def fig_taxonomy():
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    thefts = ["Direct hooking / tapping of\nLV lines and poles", "Meter bypass (wiring\nupstream of the meter)",
              "Meter tampering\n(mechanical, electronic)", "Collusive meter reading\nand billing fraud",
              "Illegal commercial use of\nconnections by\nauto-rickshaw garages", "Non-payment and arrears\n(collection loss, not theft)"]
    ax.text(0.14, 0.97, "Theft modality", ha="center", fontsize=8, fontweight="bold", color=INK)
    ax.text(0.73, 0.97, "Countermeasure layer (family)", ha="center", fontsize=8, fontweight="bold", color=INK)
    ty = np.linspace(0.84, 0.10, len(thefts))
    for y, t in zip(ty, thefts):
        box(ax, 0.01, y - 0.055, 0.26, 0.11, t, fs=6.8)
    layers = [("Data-driven", "supervised ML on bills; cost-sensitive targeting;\ndeep / label-efficient learning; geospatial", SLOTS[0]),
              ("Network-based", "transformer energy balance and correlation;\nstate estimation, load flow", SLOTS[1]),
              ("Hardware & metering", "smart prepaid meters; monitoring meters and\nsensors; active prevention", SLOTS[2]),
              ("Governance & socio-economic", "tariff and service quality; anti-collusion\nincentives; regulation; community schemes", SLOTS[3]),
              ("Auto-rickshaw (E3W) charging", "licensed hubs and tariff; smart garage chargers;\nregistration and enforcement", SLOTS[4])]
    ly = np.linspace(0.82, 0.14, len(layers))
    for y, (n, d, c) in zip(ly, layers):
        ax.add_patch(FancyBboxPatch((0.50, y - 0.065), 0.49, 0.13, boxstyle="round,pad=0.004,rounding_size=0.012",
                                    fc="white", ec=c, lw=1.6))
        ax.text(0.515, y + 0.03, n, fontsize=7.5, fontweight="bold", color=INK, va="center")
        ax.text(0.515, y - 0.022, d, fontsize=6.4, color=INK2, va="center")
    links = {0: [0, 1, 2, 3], 1: [0, 1, 2], 2: [0, 2], 3: [3, 1], 4: [0, 4, 3], 5: [2, 3]}
    for ti, ls in links.items():
        for li in ls:
            ax.plot([0.27, 0.50], [ty[ti], ly[li]], color=layers[li][2], lw=0.7, alpha=0.75, zorder=0)
    ax.text(0.5, 0.0, "Lines show which countermeasure layers can address each modality (conceptual mapping; see text).",
            ha="center", fontsize=6.5, color=MUTED)
    save(fig, "fig7_taxonomy")


def fig_graphical_abstract(drm_rank):
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    widths = {0.01: 0.29, 0.325: 0.29, 0.64: 0.355}
    cols = [(0.01, "Problem: Bangladesh", SLOTS[1],
             "System loss 10.13% (FY2024-25);\ntheft share unknown\n5-7% customer-level NTL (utility\nstatements, no method)\n"
             "48,136 illegal E3W charging\npoints in Dhaka (police, via\nnewspaper, 2025)\nMonthly manual reads; prepaid\nmeters at scale; little AMI"),
             (0.325, "Evidence: scoping review", SLOTS[0],
              "12,041 records, 3,177 screened\n69 included studies + 14 reviews\n+ 13 grey sources\n"
              "Only 6 of 38 method studies\nfield-validated; certainty for\nBangladesh low to very low"),
             (0.64, "Deployability for Bangladesh", SLOTS[2], "")]
    for x, t, c, body in cols:
        ax.add_patch(FancyBboxPatch((x, 0.04), widths[x], 0.90, boxstyle="round,pad=0.005,rounding_size=0.02", fc="white", ec=c, lw=1.8))
        ax.text(x + widths[x] / 2, 0.88, t, ha="center", fontsize=8.5, fontweight="bold", color=INK)
        if body:
            ax.text(x + 0.02, 0.80, body, ha="left", va="top", fontsize=6.6, color=INK2, linespacing=1.5)
    pick = ["Supervised ML on monthly billing data", "Cost-sensitive inspection targeting", "Smart prepaid metering",
            "Energy balance and correlation at transformer/master meters", "Geospatial and remote-sensing screening"]
    top = [r for p_ in pick for r in drm_rank if r[0] == p_]
    ax.text(0.66, 0.81, "Candidates for field piloting (tier 1):", fontsize=6.8, color=INK2)
    for k, (n, r, e) in enumerate(top):
        y = 0.70 - k * 0.125
        ax.add_patch(plt.Rectangle((0.66, y), 0.08 * r / 3, 0.035, color=SLOTS[2]))
        ax.add_patch(plt.Rectangle((0.66, y - 0.045), 0.08 * e / 3, 0.035, color=SLOTS[0]))
        short = n.split(" (")[0].replace("Supervised ML on monthly billing data", "ML on monthly bills").replace(
            " and remote-sensing", "").replace("Cost-sensitive inspection targeting", "Cost-sensitive targeting").replace(
            "Energy balance and correlation at transformer/master meters", "Transformer energy balance")
        ax.text(0.75, y - 0.005, short, fontsize=6.3, color=INK, va="center", wrap=True)
    ax.text(0.66, 0.07, "green = readiness, blue = evidence (0-3)", fontsize=6.2, color=MUTED)
    for x in (0.30, 0.615):
        arrow(ax, x, 0.5, x + 0.025, 0.5)
    save(fig, "graphical_abstract")


def main():
    ex, inc = load()
    fig_prisma(inc)
    fig_years(inc)
    c = fig_countries(inc)
    n, gc, lc, dc = fig_datasets(inc)
    fig_performance()
    rank = fig_drm()
    fig_taxonomy()
    fig_graphical_abstract(rank)
    stats = {"countries": dict(c), "method_studies": n, "granularity": dict(gc), "labels": dict(lc), "validation": dict(dc),
             "drm": [(a, round(float(b), 2), int(e)) for a, b, e in rank],
             "by_group": inc.group.value_counts().to_dict(), "years_2021_2026_included": int((inc.year >= 2021).sum())}
    json.dump(stats, open(ROOT / "data" / "synthesis_stats.json", "w"), indent=1)
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()

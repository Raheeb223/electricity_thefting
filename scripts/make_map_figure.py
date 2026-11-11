"""Evidence-map figure (R3/R11): abstract-level manual codes of all eligible records.
(a) detection studies: data granularity x validation level (counts; one blue ramp);
(b) data-driven detection studies: source of theft labels by publication period
    (shares; categorical slots in fixed order, direct labels).
Saves figures/fig_map.pdf/.png and data/fig_map_data.csv (table view)."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from apply_scope_b import load_codes, DUPLICATES  # noqa: E402
from make_figures import SLOTS, INK, INK2, MUTED, SEQ, save  # noqa: E402

GR = [("S", "Smart-meter / interval"), ("M", "Monthly / conventional meter"), ("N", "Network measurements"),
      ("H", "Hardware prototype"), ("U", "Unclear"), ("X", "None (conceptual)")]
VL = [("F", "Field"), ("O", "Offline,\nreal data"), ("S", "Simu-\nlation"), ("L", "Labor-\natory"),
      ("C", "Concept"), ("U", "Unclear")]
LB = [("R", "Real labels"), ("Y", "Synthetic theft"), ("N", "Unlabelled"), ("U", "Unclear")]


def main():
    m = load_codes().merge(pd.read_csv(ROOT / "data/evidence_map_batches/map_index.csv"), on="record_id")
    m = m[~m.record_id.isin(DUPLICATES)]
    yr = {}
    for f in (ROOT / "data/evidence_map_batches").glob("map_*.txt"):
        for line in open(f, encoding="utf-8"):
            p = line.split("|")
            yr[p[0]] = int(p[2])
    m["year"] = m.record_id.map(yr)
    for c in ("GR", "LB", "VL"):
        m[c + "1"] = m[c].str[0]
    det = m[m.ta_code == "I5b"].copy()
    dd = det[det.GR1.isin(["S", "M", "U"])].copy()   # same definition as evidence_map_stats.py
    det.loc[~det.GR1.isin([g for g, _ in GR]), "GR1"] = "U"
    det.loc[~det.VL1.isin([v for v, _ in VL]), "VL1"] = "U"
    H = np.array([[((det.GR1 == g) & (det.VL1 == v)).sum() for v, _ in VL] for g, _ in GR])

    dd.loc[~dd.LB1.isin([l for l, _ in LB]), "LB1"] = "U"
    periods = [(2010, 2015), (2016, 2020), (2021, 2023), (2024, 2026)]
    P = np.array([[((dd.year.between(a, b)) & (dd.LB1 == l)).sum() for l, _ in LB] for a, b in periods], float)
    n_per = P.sum(1)
    S = P / n_per[:, None]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 3.2), gridspec_kw={"width_ratios": [1.25, 1]})
    vmax = H.max()
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("seq", SEQ)
    a1.imshow(H, cmap=cmap, vmin=0, vmax=vmax, aspect="auto")
    for i in range(H.shape[0]):
        for j in range(H.shape[1]):
            v = H[i, j]
            a1.text(j, i, f"{v}", ha="center", va="center", fontsize=7,
                    color="white" if v > 0.55 * vmax else INK)
    a1.set_xticks(range(len(VL)), [v for _, v in VL], fontsize=6.5)
    a1.set_yticks(range(len(GR)), [g for _, g in GR], fontsize=6.5)
    a1.tick_params(length=0)
    for s in a1.spines.values():
        s.set_visible(False)
    a1.set_title(f"(a) Detection studies (n = {len(det):,}):\ndata used and how the method was validated",
                 fontsize=7.5, loc="left", color=INK)
    a1.set_xticks(np.arange(-.5, len(VL), 1), minor=True)
    a1.set_yticks(np.arange(-.5, len(GR), 1), minor=True)
    a1.grid(which="minor", color="white", linewidth=2)
    a1.tick_params(which="minor", length=0)

    left = np.zeros(len(periods))
    labels = [f"{a}-{str(b)[2:]}\n(n = {int(n)})" for (a, b), n in zip(periods, n_per)]
    y = np.arange(len(periods))
    for k, (l, name) in enumerate(LB):
        a2.barh(y, S[:, k], left=left, color=SLOTS[k], edgecolor="white", linewidth=2, height=0.62, label=name)
        for i in range(len(periods)):
            if S[i, k] >= 0.09:
                a2.text(left[i] + S[i, k] / 2, y[i], f"{100*S[i,k]:.0f}%", ha="center", va="center",
                        fontsize=6.5, color="white" if k in (0, 1) else INK)
        left += S[:, k]
    a2.set_yticks(y, labels, fontsize=6.5)
    a2.invert_yaxis()
    a2.set_xlim(0, 1)
    a2.set_xticks([0, .25, .5, .75, 1], ["0", "25", "50", "75", "100%"], fontsize=6.5)
    a2.spines["left"].set_visible(False)
    a2.tick_params(axis="y", length=0)
    a2.set_title(f"(b) Data-driven detection studies (n = {len(dd):,}):\nsource of theft labels",
                 fontsize=7.5, loc="left", color=INK)
    a2.legend(ncol=2, fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    fig.tight_layout()
    save(fig, "fig_map")
    rows = [dict(panel="a", granularity=g, validation=v.replace("\n", " "), n=int(H[i, j]))
            for i, (_, g) in enumerate(GR) for j, (_, v) in enumerate(VL)]
    rows += [dict(panel="b", period=f"{a}-{b}", labels=name, n=int(P[i, k]), share=round(S[i, k], 3))
             for i, (a, b) in enumerate(periods) for k, (_, name) in enumerate(LB)]
    pd.DataFrame(rows).to_csv(ROOT / "data/fig_map_data.csv", index=False)
    print(H)
    print(pd.DataFrame(S, index=labels, columns=[n for _, n in LB]).round(3))


if __name__ == "__main__":
    main()

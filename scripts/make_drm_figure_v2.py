"""DRM v2 figure (R9): C1-C8, gate, readiness for passing families, split evidence.
Saves figures/fig6_deployability_matrix.pdf/.png and data/fig6_drm_data.csv."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap, BoundaryNorm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from drm import DRM  # noqa: E402
from make_figures import SEQ, INK, INK2, MUTED, save  # noqa: E402


def main():
    ev = pd.read_csv(ROOT / "data/drm_v2.csv").set_index("family")
    un = pd.read_csv(ROOT / "data/drm_uncertainty_v2.csv").set_index("family")
    names = [d[0] for d in DRM]
    M = np.array([d[1] for d in DRM], float)
    ok = ~(M == 0).any(1)
    ready = M.mean(1)
    key = np.where(ok, -ready, 10 - ready)
    key[[i for i, n in enumerate(names) if n.startswith("Rule-based")]] = 99
    order = np.argsort(key, kind="stable")
    cmap = ListedColormap(SEQ[1:]); norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], 4)
    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    rows = []
    for r, i in enumerate(order):
        n = names[i]
        vals = list(M[i]) + [ready[i], ev.at[n, "E_any"], ev.at[n, "E_bd"]]
        for j, v in enumerate(vals):
            x0 = j + (0.35 if j >= 8 else 0) + (0.2 if j >= 9 else 0)
            if j == 8:
                col = cmap(norm(round(v))) if ok[i] else "#ffffff"
                ax.add_patch(plt.Rectangle((x0, r), 0.94, 0.9, facecolor=col, edgecolor=MUTED if not ok[i] else col, lw=0.6))
                txt = f"{v:.2f}" if ok[i] else "fails\ngate"
                ax.text(x0 + 0.47, r + 0.45, txt, ha="center", va="center", fontsize=6.3 if not ok[i] else 7,
                        color=("white" if round(v) >= 2 else INK) if ok[i] else INK2, fontweight="bold" if ok[i] else "normal")
                continue
            if j > 8 and v < 0:  # no study of the family read in full
                ax.add_patch(plt.Rectangle((x0, r), 0.94, 0.9, facecolor="#ffffff", edgecolor=MUTED, lw=0.6))
                ax.text(x0 + 0.47, r + 0.45, "–", ha="center", va="center", fontsize=7, color=INK2)
                continue
            col = cmap(norm(round(v)))
            zero = (j < 8 and v == 0)
            ax.add_patch(plt.Rectangle((x0, r), 0.94, 0.9, facecolor=col, edgecolor=INK if zero else col, lw=1.4 if zero else 0))
            ax.text(x0 + 0.47, r + 0.45, f"{int(v)}", ha="center", va="center", fontsize=7,
                    color="white" if round(v) >= 2 else INK)
        rows.append(dict(family=n, **{f"C{j+1}": int(M[i, j]) for j in range(8)}, passes_gate=bool(ok[i]),
                         readiness=round(ready[i], 2), E_any=int(ev.at[n, "E_any"]), E_bd=int(ev.at[n, "E_bd"]),
                         p_pass_gate=un.at[n, "p_pass_gate"]))
    xt = [j + 0.47 for j in range(8)] + [8.35 + 0.47, 9.55 + 0.47, 10.55 + 0.47]
    short = ["C1\nData\ngranul.", "C2\nMeter /\nAMI", "C3\nCost per\nconsumer", "C4\nLabelled\ndata",
             "C5\nPrivacy", "C6\nStaff\ncapacity", "C7\nCollusion\nrobust.", "C8\nSafety,\nlegality"]
    ax.set_xticks(xt)
    ax.set_xticklabels(short + ["Readiness\n(mean,\npassing)", "Evidence\nanywhere", "Evidence\nBD/compar."], fontsize=6.3)
    ax.xaxis.tick_top(); ax.tick_params(length=0)
    disp = [names[i] + (" [reference]" if names[i].startswith("Rule-based") else "") for i in order]
    ax.set_yticks([i + 0.45 for i in range(len(order))]); ax.set_yticklabels(disp, fontsize=6.8)
    npass = int(ok.sum()) - 0
    first_fail = next(r for r, i in enumerate(order) if not ok[i] and not names[i].startswith("Rule-based"))
    ax.axhline(first_fail - 0.05, color=INK2, lw=0.8, xmax=0.97)
    ax.axhline(len(order) - 1 - 0.05, color=INK2, lw=0.8, xmax=0.97)
    ax.set_xlim(-0.05, 11.6); ax.set_ylim(len(order), -0.1)
    for s in ax.spines.values():
        s.set_visible(False)
    for k, lab in enumerate(["0 not feasible / unsafe", "1 substantial need", "2 minor need", "3 fits now"]):
        ax.add_patch(plt.Rectangle((k * 2.8, len(order) + 0.5), 0.35, 0.5, color=cmap(k), clip_on=False))
        ax.text(k * 2.8 + 0.45, len(order) + 0.75, lab, va="center", fontsize=6.6, color=INK2, clip_on=False)
    ax.text(0, len(order) + 1.5, "Outlined cells score 0: a family with any 0 fails the gate (not deployable without structural change).\n"
            "Evidence: 0 concept, 1 simulation/laboratory, 2 offline real data, 3 field or programme evaluation;\n"
            "BD/compar. = Bangladesh or another LMIC without smart-meter data; – = no study of the family read in full.", fontsize=6.3, color=MUTED, clip_on=False, va="top")
    save(fig, "fig6_deployability_matrix")
    pd.DataFrame(rows).to_csv(ROOT / "data/fig6_drm_data.csv", index=False)
    print(pd.DataFrame(rows)[["family", "passes_gate", "readiness", "E_any", "E_bd", "p_pass_gate"]].to_string(index=False))


if __name__ == "__main__":
    main()

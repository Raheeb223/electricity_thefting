"""Compute validation statistics once humans have filled the verification kits.

Screening  : verification/human_screening_sheet.csv (filled) vs AI title/abstract
             decisions in data/screening.csv -> agreement, Cohen's kappa, AI sensitivity
             and specificity against the human reference, disagreement list.
Extraction : verification/human_extraction_sheet.csv (filled) vs data/extraction.csv ->
             agreement on categorical fields and a side-by-side sheet for adjudication.
DRM        : verification/drm_expert_*.csv (one filled form per expert, file names
             drm_expert_<initials>.csv) -> ICC(2,1) across experts, quadratic-weighted
             kappa of each expert vs the authors' scores, mean expert scores per cell.
Writes verification/verification_report.md. Sections whose inputs are still blank are skipped.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "verification"
sys.path.insert(0, str(ROOT / "scripts"))


def cohen_kappa(a, b):
    a, b = np.asarray(a), np.asarray(b)
    cats = sorted(set(a) | set(b))
    po = np.mean(a == b)
    pe = sum(np.mean(a == c) * np.mean(b == c) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def weighted_kappa(a, b, k=4):
    """Quadratic-weighted kappa for ordinal 0..k-1 scores."""
    a, b = np.asarray(a, int), np.asarray(b, int)
    O = np.zeros((k, k))
    for x, y in zip(a, b):
        O[x, y] += 1
    W = np.array([[(i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)])
    E = np.outer(O.sum(1), O.sum(0)) / O.sum()
    return 1 - (W * O).sum() / (W * E).sum()


def icc21(X):
    """ICC(2,1): two-way random effects, absolute agreement, single rater. X: targets x raters."""
    n, k = X.shape
    m = X.mean()
    msr = k * ((X.mean(1) - m) ** 2).sum() / (n - 1)
    msc = n * ((X.mean(0) - m) ** 2).sum() / (k - 1)
    sse = ((X - X.mean(1, keepdims=True) - X.mean(0, keepdims=True) + m) ** 2).sum()
    mse = sse / ((n - 1) * (k - 1))
    return (msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n)


def screening(lines):
    f = V / "human_screening_sheet.csv"
    h = pd.read_csv(f, dtype=str).fillna("")
    col = "human_decision (INC/EXC)"
    h = h[h[col].str.strip().str.upper().isin(["INC", "EXC"])]
    if h.empty:
        lines.append("## Screening\nNot yet filled in.\n"); return
    ai = pd.read_csv(ROOT / "data" / "screening.csv", dtype=str)[["record_id", "ta_decision", "ta_code"]]
    d = h.merge(ai, on="record_id")
    hu, a = d[col].str.strip().str.upper(), d.ta_decision
    tp = ((hu == "INC") & (a == "INC")).sum(); fn = ((hu == "INC") & (a == "EXC")).sum()
    tn = ((hu == "EXC") & (a == "EXC")).sum(); fp = ((hu == "EXC") & (a == "INC")).sum()
    lines += ["## Screening (human reference vs AI)", f"- Records compared: {len(d)}",
              f"- Agreement: {np.mean(hu == a):.3f}; Cohen's kappa: {cohen_kappa(hu, a):.3f}",
              f"- AI sensitivity (human INC kept by AI): {tp / max(tp + fn, 1):.3f}; specificity: {tn / max(tn + fp, 1):.3f}",
              f"- Disagreements to adjudicate: {fn + fp} (list in screening_disagreements.csv)", ""]
    d[hu != a].to_csv(V / "screening_disagreements.csv", index=False)


def extraction(lines):
    h = pd.read_csv(V / "human_extraction_sheet.csv", dtype=str).fillna("")
    h = h[h["extractor_initials"].str.strip() != ""]
    if h.empty:
        lines.append("## Extraction\nNot yet filled in.\n"); return
    ex = pd.read_csv(ROOT / "data" / "extraction.csv", dtype=str).fillna("")
    d = h.merge(ex, on="id", suffixes=("_human", "_ai"))
    lines.append("## Extraction (human vs AI)")
    for c in ["data_granularity", "labelled_data", "real_world_deployment"]:
        hh = d[f"{c}_human"].str.lower().str[:3]; aa = d[f"{c}_ai"].str.lower().str[:3]
        ok = hh != ""
        lines.append(f"- {c}: agreement {np.mean(hh[ok] == aa[ok]):.3f} (n = {ok.sum()})")
    side = d[["id", "citation_key_human"] + [x for x in d.columns if x.endswith("_human") or x.endswith("_ai")]]
    side.to_csv(V / "extraction_side_by_side.csv", index=False)
    lines += ["- Side-by-side sheet for adjudication: extraction_side_by_side.csv", ""]


def drm(lines):
    from drm import DRM
    forms = sorted(V.glob("drm_expert_*.csv"))
    forms = [f for f in forms if f.name != "drm_expert_form.csv"]
    if not forms:
        lines.append("## DRM expert validation\nNo filled expert forms yet (save as drm_expert_<initials>.csv).\n"); return
    cs = ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
    authors = np.array([d[1] for d in DRM], float).ravel()
    experts = []
    for f in forms:
        x = pd.read_csv(f).set_index("family").loc[[d[0] for d in DRM], cs].astype(float).values.ravel()
        experts.append(x)
    X = np.column_stack(experts)
    lines += ["## DRM expert validation", f"- Experts: {len(forms)}"]
    if X.shape[1] >= 2:
        lines.append(f"- ICC(2,1) among experts: {icc21(X):.3f}")
    lines.append(f"- ICC(2,1) experts + authors: {icc21(np.column_stack([X, authors])):.3f}")
    for f, x in zip(forms, experts):
        lines.append(f"- {f.stem}: quadratic-weighted kappa vs authors {weighted_kappa(x, authors):.3f}")
    mean = X.mean(1).reshape(len(DRM), 7)
    out = pd.DataFrame(mean, columns=cs, index=[d[0] for d in DRM]).round(2)
    out["readiness_experts"] = out[cs].mean(1).round(2)
    out["readiness_authors"] = np.array([d[1] for d in DRM]).mean(1).round(2)
    out.to_csv(V / "drm_expert_mean_scores.csv")
    lines += ["- Mean expert scores and readiness: drm_expert_mean_scores.csv", ""]


def main():
    lines = ["# Verification report", ""]
    screening(lines)
    extraction(lines)
    drm(lines)
    (V / "verification_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

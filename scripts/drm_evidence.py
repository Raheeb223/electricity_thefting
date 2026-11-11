"""R9: gate rule, split evidence strength and score uncertainty for the DRM (C1-C8).

Evidence strength is computed, not judged: for each family, the cited studies are looked
up in the manual evidence-map codes (data/evidence_map_coded_manual.csv) and given a level
  3 = field validation (VL = F) or programme evaluation with measured outcomes (GOVM = 1)
  2 = offline evaluation on real data (VL = O)
  1 = simulation or laboratory (VL = S or L)
  0 = conceptual, descriptive or unclear.
E_any = highest level among cited studies; E_bd = highest level among cited studies set
in Bangladesh or another low- or middle-income country whose data are not smart-meter
(AMI) data (GR != S). Codes marked "?" count at their stated level and are flagged.
Only studies whose full text was retrieved and read count (amendment of 2026-11-11);
a family with no such study gets E = -1, shown as "-" (no study read in full).

Gate: a family with any constraint scored 0 is "not deployable without structural change";
its readiness (mean of C1-C8) is shown in brackets for information only.

Score uncertainty: each of the 14 x 8 cells is shifted by -1, 0 or +1 (p = 0.15, 0.70,
0.15; clipped to 0-3); 10,000 draws; ranks of gate-passing families with 90% intervals;
share of draws in which each family passes the gate.
Outputs: data/drm_v2.csv, data/drm_uncertainty_v2.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from drm import DRM, CONSTRAINTS  # noqa: E402
from apply_scope_b import lmic_flag  # noqa: E402


def level(r):
    vl, gov = str(r.VL), str(r.GOVM)
    if vl.startswith("F") or gov.startswith("1"):
        return 3
    if vl.startswith("O"):
        return 2
    if vl[:1] in ("S", "L"):
        return 1
    return 0


def evidence():
    km = pd.read_csv(ROOT / "refs" / "key_map.csv", keep_default_na=False)
    k2id = dict(zip(km.key, km.record_id))
    m = pd.read_csv(ROOT / "data" / "evidence_map_coded_manual.csv", keep_default_na=False).set_index("record_id")
    rows = []
    for fam, sc, e_old, keys, _ in DRM:
        lv_any, lv_bd, best_any, best_bd, flag, n_ft = 0, 0, "", "", False, 0
        for k in keys.split(";"):
            rid = k2id.get(k)
            if rid not in m.index or not (ROOT / "data" / "fulltext" / f"{rid}.pdf").exists():
                continue
            n_ft += 1
            r = m.loc[rid]
            lv = level(r)
            if lv > lv_any:
                lv_any, best_any = lv, k
            comparable = lmic_flag(r.CTY) != "" and not str(r.GR).startswith("S")
            if comparable and lv > lv_bd:
                lv_bd, best_bd = lv, k
                flag = "?" in f"{r.CTY}{r.GR}{r.VL}{r.GOVM}"
        if n_ft == 0:
            lv_any = lv_bd = -1
        rows.append(dict(family=fam, E_judged_v1=e_old, n_fulltext=n_ft, E_any=lv_any, E_any_from=best_any,
                         E_bd=lv_bd, E_bd_from=best_bd, E_bd_probable=flag))
    return pd.DataFrame(rows)


def main():
    names = [d[0] for d in DRM]
    M = np.array([d[1] for d in DRM], float)
    ev = evidence()
    gate = (M == 0).any(1)
    df = ev.copy()
    for j, c in enumerate(CONSTRAINTS):
        df[c.split()[0]] = M[:, j].astype(int)
    df["passes_gate"] = ~gate
    df["readiness"] = M.mean(1).round(2)
    df["failing_constraints"] = [", ".join(CONSTRAINTS[j].split()[0] for j in np.where(M[i] == 0)[0]) for i in range(len(M))]
    df.to_csv(ROOT / "data" / "drm_v2.csv", index=False)

    rng = np.random.default_rng(20261111)
    N = 10_000
    ranks = np.full((N, len(names)), np.nan)
    passes = np.zeros((N, len(names)), bool)
    for i in range(N):
        X = np.clip(M + rng.choice([-1, 0, 1], size=M.shape, p=[0.15, 0.70, 0.15]), 0, 3)
        ok = ~(X == 0).any(1)
        passes[i] = ok
        r = X.mean(1)
        idx = np.where(ok)[0]
        order = idx[np.lexsort((rng.random(len(idx)), -r[idx]))]
        ranks[i, order] = np.arange(1, len(order) + 1)
    out = pd.DataFrame({
        "family": names, "passes_gate_base": ~gate, "readiness": M.mean(1).round(2),
        "p_pass_gate": passes.mean(0).round(3),
        "rank_median": np.nanmedian(ranks, 0), "rank_p05": np.nanpercentile(ranks, 5, 0),
        "rank_p95": np.nanpercentile(ranks, 95, 0),
        "p_top5": np.nanmean(np.where(np.isnan(ranks), 0, ranks <= 5), 0).round(3)})
    out = out.sort_values(["passes_gate_base", "rank_median"], ascending=[False, True])
    out.to_csv(ROOT / "data" / "drm_uncertainty_v2.csv", index=False)
    pd.set_option("display.width", 220)
    print(df[["family", "E_judged_v1", "E_any", "E_bd", "E_bd_from", "passes_gate", "readiness", "failing_constraints"]].to_string(index=False))
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()

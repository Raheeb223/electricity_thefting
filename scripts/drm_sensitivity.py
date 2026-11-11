"""Sensitivity of the DRM readiness ranking to constraint weights (R9; C1-C8).
Schemes: equal; each constraint doubled in turn; each constraint removed in turn.
Ranking is over families that pass the gate (no constraint scored 0); weights do not
affect the gate. Output: data/drm_sensitivity.csv and the minimum Spearman rho."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from drm import DRM  # noqa: E402

names = [d[0] for d in DRM]
M = np.array([d[1] for d in DRM], float)
ok = ~(M == 0).any(1)
M, names = M[ok], [n for n, o in zip(names, ok) if o]
k = M.shape[1]
schemes = {"equal": np.ones(k)}
for j in range(k):
    w = np.ones(k); w[j] = 2; schemes[f"C{j+1} doubled"] = w
    w = np.ones(k); w[j] = 0; schemes[f"C{j+1} removed"] = w
res = pd.DataFrame({s: (M * w).sum(1) / w.sum() for s, w in schemes.items()}, index=names)
rho = res.rank(ascending=False).corr(method="spearman")["equal"].drop("equal")
res.round(3).to_csv(ROOT / "data" / "drm_sensitivity.csv")
print(rho.round(3).sort_values().to_string())
print("minimum Spearman rho vs equal weights:", round(rho.min(), 3), "(", rho.idxmin(), ")")

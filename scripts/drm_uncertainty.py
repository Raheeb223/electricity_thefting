"""Score-uncertainty analysis for the DRM (addresses: 'sensitivity varies weights, not
scores'). Each of the 98 cells is independently perturbed by -1, 0 or +1 with
probabilities 0.15/0.70/0.15 (clipped to 0-3), 10,000 draws, fixed seed. Reports the
median rank and 90% rank interval of each family's readiness, and the probability of
being in the top third. Output: data/drm_uncertainty.csv."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from drm import DRM
rng = np.random.default_rng(20261110)
names = [d[0] for d in DRM]
M = np.array([d[1] for d in DRM], float)
N = 10_000
ranks = np.empty((N, len(names)))
for i in range(N):
    eps = rng.choice([-1, 0, 1], size=M.shape, p=[0.15, 0.70, 0.15])
    r = np.clip(M + eps, 0, 3).mean(1)
    # rank 1 = highest readiness; ties broken at random
    order = np.lexsort((rng.random(len(r)), -r))
    rk = np.empty(len(r)); rk[order] = np.arange(1, len(r) + 1)
    ranks[i] = rk
base = M.mean(1)
out = pd.DataFrame({"family": names, "readiness": base.round(2),
                    "rank_median": np.median(ranks, 0), "rank_p05": np.percentile(ranks, 5, 0),
                    "rank_p95": np.percentile(ranks, 95, 0),
                    "p_top_third": (ranks <= 5).mean(0).round(3)}).sort_values("rank_median")
out.to_csv(ROOT / "data" / "drm_uncertainty.csv", index=False)
print(out.to_string(index=False))

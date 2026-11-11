"""Final in-depth synthesis set = Option B (variant N1) priority studies whose venue is
indexed or probably indexed (scripts/venue_audit.py decisions), after full-text code
overrides, restricted to studies whose full text was retrieved and read (amendment of
2026-11-11: studies without a retrievable full text are reported as "reports not
retrieved" and stay in the evidence map only).
Outputs: data/synthesis_eligible.csv (all eligible, with has_pdf), data/synthesis_set.csv
(retrieved and read), data/synthesis_not_retrieved.csv, and a summary line."""
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
pri = pd.read_csv(ROOT / "data" / "priority_synthesis_B.csv", keep_default_na=False)
va = pd.read_csv(ROOT / "data" / "venue_audit" / "venue_audit.csv", keep_default_na=False)
dec = dict(zip(va.record_id, va.decision))
pri["venue_decision"] = pri.record_id.map(dec).fillna("not audited")
keep = pri.venue_decision.str.startswith(("indexed", "probably"))
fx = ROOT / "data" / "fulltext_exclusions.csv"
if fx.exists():
    ex = pd.read_csv(fx, keep_default_na=False)
    keep &= ~pri.record_id.isin(ex.record_id)
    print("excluded at full text:", dict(zip(ex.record_id, ex.code)))
out = pri[keep].copy()
fl = ROOT / "data" / "fulltext"
out["has_pdf"] = [(fl / f"{r}.pdf").exists() for r in out.record_id]
out.to_csv(ROOT / "data" / "synthesis_eligible.csv", index=False)
out[~out.has_pdf].to_csv(ROOT / "data" / "synthesis_not_retrieved.csv", index=False)
syn = out[out.has_pdf]
syn.to_csv(ROOT / "data" / "synthesis_set.csv", index=False)
print(f"eligible for synthesis {len(out)}; retrieved and read {len(syn)} (firm {int((syn.priority=='firm').sum())}, "
      f"probable {int((syn.priority=='probable').sum())}); not retrieved {int((~out.has_pdf).sum())}; "
      f"not audited {int((pri.venue_decision=='not audited').sum())}")

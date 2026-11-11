"""Write compact text batches of records for title/abstract screening.
Order: S4, S3, S2 records first (Bangladesh/LMIC/rickshaw), then S1-only, each by year.
Output: data/screening_batches/batch_NN.txt (250 records each) and batch_index.csv"""
import pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
d = pd.read_csv(ROOT / "data" / "records_dedup.csv", dtype=str).fillna("")
pri = d["strings_matched"].map(lambda s: 0 if "S4" in s else 1 if "S3" in s else 2 if "S2" in s else 3)
d = d.assign(pri=pri, y=pd.to_numeric(d["year"], errors="coerce")).sort_values(["pri", "y", "record_id"])
out = ROOT / "data" / "screening_batches"; out.mkdir(exist_ok=True)
idx = []
for b, start in enumerate(range(0, len(d), 250), 1):
    sub = d.iloc[start:start + 250]
    lines = []
    for _, r in sub.iterrows():
        ab = " ".join(r["abstract"].split())[:280]
        lines.append(f"{r['record_id']}|{r['year'][:4]}|{r['strings_matched']}|{r['type'][:12]}|{r['venue'][:45]}|T: {r['title'][:170]}|A: {ab}")
        idx.append({"record_id": r["record_id"], "batch": b})
    (out / f"batch_{b:02d}.txt").write_text("\n".join(lines), encoding="utf-8")
pd.DataFrame(idx).to_csv(out / "batch_index.csv", index=False)
print(len(d), "records in", b, "batches")

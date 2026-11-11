"""R3: write eligible records (full abstracts) into reading batches for manual
evidence-map coding. Abstracts are kept whole up to 320 words (longer ones are cut and
marked [...]); whitespace and HTML tags are removed."""
import re, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
s = pd.read_csv(ROOT / "data/screening.csv")
d = pd.read_csv(ROOT / "data/records_dedup.csv")
inc = s[s.ta_decision == "INC"][["record_id", "ta_code"]].merge(
    d[["record_id", "year", "venue", "title", "abstract", "keywords"]], on="record_id")
x = pd.read_csv(ROOT / "data/crossref_depth_new_records.csv")
xd = pd.read_csv(ROOT / "data/screening_batches/dec_14_crossref_depth.csv")
x = x.join(xd.set_index("idx"))
x = x[x.ta_decision == "INC"].copy()
x["record_id"] = ["X%02d" % i for i in x.index]
inc = pd.concat([inc, x[["record_id", "ta_code", "year", "venue", "title", "abstract"]]])
def clean(t, n=320):
    t = re.sub(r"<[^>]+>", " ", str(t) if pd.notna(t) else "")
    t = re.sub(r"\s+", " ", t).strip()
    w = t.split()
    return " ".join(w[:n]) + (" [...]" if len(w) > n else "")
inc = inc.sort_values(["ta_code", "year", "record_id"]).reset_index(drop=True)
out = ROOT / "data/evidence_map_batches"
B = 50
for b in range(0, len(inc), B):
    lines = []
    for _, r in inc.iloc[b:b + B].iterrows():
        lines.append(f"{r.record_id}|{r.ta_code}|{r.year}|{clean(r.venue,12)}|T: {clean(r.title)}|A: {clean(r.abstract) or 'NONE'}")
    (out / f"map_{b // B + 1:02d}.txt").write_text("\n".join(lines), encoding="utf-8")
inc[["record_id", "ta_code"]].to_csv(out / "map_index.csv", index=False)
print(len(inc), "records in", (len(inc) + B - 1) // B, "batches")

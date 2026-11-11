"""Flag included records for the reference-budget tightening rule (protocol v1.1, s.2).
Output: data/tightening_flags.csv"""
import re
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
s = pd.read_csv(ROOT/"data/screening.csv", dtype=str).fillna("")
r = pd.read_csv(ROOT/"data/records_dedup.csv", dtype=str).fillna("")
d = s[s.ta_decision=="INC"].merge(r[["record_id","abstract","cited_by","authors","venue_type"]], on="record_id", how="left")
txt = (d.title+" "+d.abstract).str.lower()
F = {
 "bd": r"bangladesh|dhaka|chittagong|chattogram|bpdb|\bdesco\b|\bdpdc\b|wzpdcl|\bnesco\b|\bbreb\b|easy[- ]?bike",
 "lmic": r"bangladesh|india|pakistan|nepal|sri lanka|nigeria|ghana|kenya|uganda|tanzania|south africa|zambia|cameroon|congo|ethiopia|brazil|colombia|ecuador|peru|uruguay|mexico|jamaica|honduras|cuba|indonesia|philippines|thailand|malaysia|vietnam|egypt|iran|turkey|turkiye|lebanon|jordan|kosovo|albania|namibia|zimbabwe|mozambique|chad|burundi|myanmar|developing countr|developing nation|emerging econom|emerging market|low-income|middle-income|global south|sub-saharan|africa|latin america",
 "lowres": r"monthly|billing|\bbill\b|bills|low[- ]resolution|low[- ]sampling|traditional meter|conventional meter|mechanical meter|electromechanical|non[- ]smart|without (advanced metering|ami)|lacking advanced metering|analog meter|manual (meter )?reading|\bamr\b|daily meter|low-frequency",
 "real": r"real[- ]world|real data|real utility|inspection|field (validation|trial|test|data|work|study)|deploy|case study|utility data|distribution compan|\bdisco|endesa|naturgy|enel|cpfl|eletropaulo|\bpln\b|\bpea\b|kepco|meralco|\bute\b|eneo|tnb|apspdcl|mepco|k-electric|eskom|hedno|light s\.a",
 "cost": r"\bcost|economic|payback|financial return|budget|revenue",
 "validity": r"leakage|bias|synthetic attack|label|inspection label|covariate shift|benchmark accuracy|row-level",
 "unsup": r"unsupervised|semi-supervised|unlabel|few-shot|active learning|transfer learning|one-class|clustering",
}
for k, p in F.items():
    d[k] = txt.str.contains(p, regex=True)
pub = r"ieee transactions|ieee access|ieee journal|ieee systems|ieee internet of things|ieee open|proceedings of the ieee|iet |energy policy|energy research & social|energy for sustainable|utilities policy|world development|renewable and sustainable|applied energy|^energy$|energy reports|energies|sustainability|sensors|applied sciences|electronics|international journal of electrical power|electric power systems research|sustainable energy grids|expert systems|knowledge-based|engineering applications of artificial|scientific reports|results in engineering|heliyon|measurement|technologies|frontiers|journal of international development|energy economics|journal of energy in southern|nigerian journal of technology|south african journal|international journal of energy economics and policy|utilities|cogent|journal of electrical systems and information|electricity|big data|machine learning"
d["journal_tier"] = d.venue.str.lower().str.contains(pub, regex=True)
d["is_journal"] = d.type.str.lower().str.contains("article|journal|review")
d["cites"] = pd.to_numeric(d.cited_by, errors="coerce").fillna(0)
d["age"] = 2027 - pd.to_numeric(d.year, errors="coerce").fillna(2026)
d["cites_per_year"] = d.cites / d.age
d.drop(columns=["abstract"]).to_csv(ROOT/"data/tightening_flags.csv", index=False)
g = d.groupby("family")
print(g.size())
for k in ["bd","lmic","lowres","real","cost","validity","journal_tier"]:
    print(k, int(d[k].sum()))
dd = d[d.family=="DD"]
print("DD with lowres:", int(dd.lowres.sum()), "| lowres&journal:", int((dd.lowres & dd.journal_tier).sum()),
      "| lmic&real&journal:", int((dd.lmic & dd.real & dd.journal_tier).sum()))

"""Write human_tasks/fulltext_todo_round2.csv: synthesis studies without a PDF in
data/fulltext/, with DOI link, publisher, save-as name and why automatic retrieval failed.
Existing 'status' and 'notes' entries typed by the author are preserved."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PUB = [("10.1109", "IEEE Xplore"), ("10.1016", "ScienceDirect (Elsevier)"), ("10.3390", "MDPI (free)"),
       ("10.1049", "IET / Wiley"), ("10.1002", "Wiley"), ("10.1111", "Wiley"), ("10.1007", "Springer"),
       ("10.1080", "Taylor & Francis"), ("10.1038", "Nature (free)"), ("10.1108", "Emerald"),
       ("10.1145", "ACM"), ("10.3389", "Frontiers (free)"), ("10.1186", "BMC / Springer (free)"),
       ("10.1177", "SAGE"), ("10.1093", "Oxford University Press")]


def main():
    s = pd.read_csv(ROOT / "data/synthesis_set.csv", keep_default_na=False, dtype=str)
    rec = pd.read_csv(ROOT / "data/records_dedup.csv", keep_default_na=False, dtype=str,
                      usecols=["record_id", "doi", "title", "year"])
    km = pd.read_csv(ROOT / "refs/key_map.csv", keep_default_na=False)
    key = dict(zip(km.record_id, km.key))
    why = {}
    for f in ("missing_fulltext_round2.csv", "fulltext_oa_extra_log.csv"):
        fp = ROOT / "data" / f
        if fp.exists():
            d = pd.read_csv(fp, keep_default_na=False, dtype=str)
            col = "reason" if "reason" in d else "status"
            for r, w in zip(d.record_id, d[col]):
                why.setdefault(r, w)
    t = s[[not (ROOT / "data/fulltext" / f"{r}.pdf").exists() for r in s.record_id]].merge(rec, on="record_id", how="left")

    def pub(d):
        return next((n for p, n in PUB if d.lower().startswith(p)), "other (see link)")

    def prio(r):
        if "BGD" in r.CTY or r.E3W.startswith("1"):
            return "1 (Bangladesh or E3W)"
        if r.C3_FIELD or r.C5_GOV_LMIC:
            return "2 (field or governance evidence)"
        if r.C6_DRIVERS_LMIC:
            return "3 (drivers of theft)"
        return "4 (monthly-data detection)"
    out = pd.DataFrame({"priority": t.apply(prio, axis=1), "record_id": t.record_id, "citation_key": t.record_id.map(key),
                        "title": t.title, "year": t.year,
                        "doi_link": ["https://doi.org/" + d if d else "(no DOI: search the title)" for d in t.doi],
                        "publisher": [pub(d) for d in t.doi], "save_as": t.record_id + ".pdf",
                        "why_not_automatic": t.record_id.map(why).fillna("not attempted").str.slice(0, 90),
                        "status (downloaded / no access)": "", "notes": ""})
    old_fp = ROOT / "human_tasks/fulltext_todo_round2.csv"
    if old_fp.exists():
        old = pd.read_csv(old_fp, keep_default_na=False, dtype=str).set_index("record_id")
        for c in ("status (downloaded / no access)", "notes"):
            out[c] = [old.at[r, c] if r in old.index and c in old else "" for r in out.record_id]
    out = out.sort_values(["priority", "publisher", "record_id"])
    out.to_csv(old_fp, index=False, encoding="utf-8-sig")
    print(len(out), out.priority.value_counts().to_dict())
    print(out.publisher.value_counts().to_dict())


if __name__ == "__main__":
    main()

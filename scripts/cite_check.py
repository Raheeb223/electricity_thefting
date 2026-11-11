"""Check every citation key used in manuscript/sections/*.tex:
- present in refs/references.bib or refs/grey.bib;
- status of the cited record: in the synthesis set (SYN), excluded at full text,
  venue-excluded (E5 provisional), mapped only (outside scope), or grey/method source.
Usage: python scripts/cite_check.py [--all]   (--all also lists SYN keys)"""
import glob
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    km = pd.read_csv(ROOT / "refs/key_map.csv", keep_default_na=False)
    k2r = dict(zip(km.key, km.record_id))
    va = pd.read_csv(ROOT / "data/venue_audit/venue_audit.csv", keep_default_na=False)
    dec = dict(zip(va.record_id, va.decision))
    m = pd.read_csv(ROOT / "data/evidence_map_coded_manual.csv", keep_default_na=False)
    mp = dict(zip(m.record_id, m.ta_code))
    syn = set(pd.read_csv(ROOT / "data/synthesis_set.csv").record_id)
    fx = set(pd.read_csv(ROOT / "data/fulltext_exclusions.csv").record_id)
    keys = {}
    for f in sorted(glob.glob(str(ROOT / "manuscript/sections/*.tex"))) + sorted(glob.glob(str(ROOT / "manuscript/tables/*.tex"))):
        txt = open(f, encoding="utf-8").read()
        for g in re.findall(r"\\cite[a-z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}", txt):
            for k in g.split(","):
                keys.setdefault(k.strip(), set()).add(Path(f).name)
    bib = open(ROOT / "refs/references.bib", encoding="utf-8").read() + open(ROOT / "refs/grey.bib", encoding="utf-8").read()
    rows = []
    for key in sorted(keys):
        r = k2r.get(key)
        if r is None:
            st = "grey/method"
        elif r in syn:
            st = "SYN"
        elif r in fx:
            st = "EXCLUDED-FULLTEXT"
        elif r in dec and not dec[r].startswith(("indexed", "probably")):
            st = "VENUE: " + dec[r][:40]
        elif mp.get(r) == "RV":
            st = "review (map)"
        elif r in mp:
            st = "map only (outside scope)"
        else:
            st = "not in map"
        inbib = re.search(r"@\w+\{" + re.escape(key) + r",", bib) is not None
        rows.append((key, r or "", st, "ok" if inbib else "MISSING-BIB", ";".join(sorted(keys[key]))))
    df = pd.DataFrame(rows, columns=["key", "record", "status", "bib", "files"])
    show = df if "--all" in sys.argv else df[(df.status != "SYN") | (df.bib != "ok")]
    pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 60)
    print(show.to_string(index=False))
    print(df.status.value_counts().to_dict())


if __name__ == "__main__":
    main()

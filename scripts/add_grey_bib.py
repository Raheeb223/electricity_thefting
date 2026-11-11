"""Write refs/grey.bib from data/grey/grey_literature.csv (every field from the sheet,
which was filled from the sources themselves). Entries are tagged keywords={grey} so
verify_refs.py checks URL reachability and urldate instead of Crossref."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GREY_KEYS = {
    "G01": "islam2025banglatesla", "G02": "tbs2026illegal", "G03": "bhuiyan2026solar",
    "G04": "bonikbarta2026battery", "G05": "sakib2024banglateslas", "G06": "hossain2024transmission",
    "G07": "bonikbarta2025power", "G08": "mahmud2025integrating", "G09": "bss2025dpdc",
    "G10": "bss2025pdb", "G11": "alam2024fixing", "G12": "lovei2000costs", "G13": "adb2003cost",
}
# Author field: persons as 'Family, Given'; organisations wrapped in braces.
AUTHORS = {
    "G01": "Islam, Md Jahidul", "G02": "{The Business Standard}", "G03": "Bhuiyan, Shafiq R.",
    "G04": "{Bonik Barta}", "G05": "Sakib, S. M. Najmus", "G06": "Hossain, Emran", "G07": "{Bonik Barta}",
    "G08": "Mahmud, Md. Khalid and Moazzem, Khondaker Golam", "G09": "{Bangladesh Sangbad Sangstha}",
    "G10": "{Bangladesh Sangbad Sangstha}", "G11": "Alam, Shafiqul", "G12": "Lovei, Laszlo and McKechnie, Alastair",
    "G13": "{Asian Development Bank}",
}
HOW = {
    "G01": "News report", "G02": "News report", "G03": "Opinion article", "G04": "News report", "G05": "News report",
    "G06": "News report", "G07": "News report", "G08": "Policy dialogue presentation", "G09": "News report",
    "G10": "News report", "G11": "Institute report", "G12": "Viewpoint note", "G13": "Special evaluation study",
}


def esc(s):
    return str(s).replace("&", r"\&").replace("%", r"\%").replace("#", r"\#").replace("_", r"\_")


def main():
    g = pd.read_csv(ROOT / "data" / "grey" / "grey_literature.csv", dtype=str).fillna("")
    out = []
    for _, r in g.iterrows():
        gid = r["grey_id"]
        title = esc(r["title"]).replace("'", "'")
        url = r["url"].replace("%", r"\%")
        out.append(
            f"@misc{{{GREY_KEYS[gid]},\n  author = {{{AUTHORS[gid]}}},\n  title = {{{{{title}}}}},\n"
            f"  howpublished = {{{HOW[gid]}, {esc(r['outlet'])}}},\n  year = {{{r['date'][:4]}}},\n"
            f"  url = {{{url}}},\n  urldate = {{{r['access_date']}}},\n"
            f"  note = {{Grey literature. Accessed {r['access_date']}}},\n  keywords = {{grey}}\n}}\n")
    (ROOT / "refs" / "grey.bib").write_text("\n".join(out), encoding="utf-8")
    print(len(out), "grey entries written")


if __name__ == "__main__":
    main()

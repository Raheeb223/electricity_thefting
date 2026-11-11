"""Idempotent corrections to refs/references.bib found in the final reference audit
(2026-11-11). Every value comes from a real metadata source, noted per fix:
Crossref / OpenAlex record of the DOI, or the DOI string itself. All-capital titles are
converted to sentence case without changing their words.
Usage: python scripts/fix_bib.py"""
import re
from pathlib import Path

BIB = Path(__file__).resolve().parents[1] / "refs" / "references.bib"

# key -> {field: value}; value None deletes the field
FIXES = {
    # OpenAlex biblio: volume 372
    "page2021prisma": {"volume": "372"},
    # DOI 10.30541/v53i3pp.239-254 encodes volume 53, issue 3
    "jamil2014empirical": {"volume": "53", "number": "3"},
    # Nature news item; Crossref and OpenAlex give no volume or pages
    "singhchawla2022massive": {"note": "News article"},
    # Published online 2026-09-25 (Crossref); no volume assigned yet
    "panda2026collectivismindividualism": {"pages": None, "note": "In press, article jid.70120"},
    # Crossref container-title: Computer and Automation Engineering, in the FAIA series
    "marquez2026development": {"booktitle": "Computer and Automation Engineering",
                               "series": "Frontiers in Artificial Intelligence and Applications"},
    # all-capital titles, words unchanged
    "briseno2020factors": {"title": "{Factors associated with electricity losses: a panel data perspective}"},
    "briseno2021factors": {"title": "{Factors associated with electricity losses in {Colombia}}"},
    # HTML entity for an em dash left in the Crossref title
    "babu2013detecting": {"title": "{Detecting unusual customer consumption profiles in power distribution systems --- {APSPDCL}}"},
    "junior2021ntl": {"title": "{{NTL} detection: a intelligent system using a non-supervised clustering of consumption profiles}"},
}


def main():
    s = BIB.read_text(encoding="utf-8")
    for key, fields in FIXES.items():
        m = re.search(r"@\w+\{" + re.escape(key) + r",.*?\n\}", s, re.S)
        assert m, key
        e = m.group(0)
        body, end = e[:-2], e[-2:]
        for f, v in fields.items():
            body = re.sub(r"\n  " + f + r" = \{.*?\},?(?=\n|$)", "", body)
            if v is not None:
                body = body.rstrip(",") + ",\n  " + f + " = {" + v + "}"
        s = s.replace(e, body + end)
    # OpenAlex author record: Alicia O'Cathain (apostrophe lost in the Crossref record)
    s = s.replace("OCathain, Alicia", "O'Cathain, Alicia")
    BIB.write_text(s, encoding="utf-8")
    print("fixed", len(FIXES), "entries")


if __name__ == "__main__":
    main()

"""Phase 8 checks on the manuscript:
- every \\cite key exists in the merged .bib, and every .bib entry is cited;
- reference count (target 90-115) and share from 2021-2026 (target >= 40%);
- grey-literature share (<= 15%);
- banned filler phrases; word count of the main text (abstract to conclusion);
- abstract length (<= 250 words).
Writes reviews/qa_report.md and exits 1 if a hard check fails."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MS = ROOT / "manuscript"
BANNED = ["delve", "in the realm of", "landscape", "plays a pivotal role", "it is worth noting", "tapestry",
          "navigat", "multifaceted", "underscore", "paramount", "crucial role", "game-changer", "leverag"]


def tex_files():
    files = [MS / "main.tex"] + sorted((MS / "tables").glob("*.tex")) + sorted((MS / "sections").glob("*.tex"))
    return [f for f in files if f.exists()]


def strip_comments(s):
    return re.sub(r"(?<!\\)%.*", "", s)


def main():
    src = {f: strip_comments(f.read_text(encoding="utf-8")) for f in tex_files()}
    cited = []
    for s in src.values():
        for m in re.finditer(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}", s):
            cited += [k.strip() for k in m.group(1).split(",") if k.strip()]
    bib = (MS / "references.bib").read_text(encoding="utf-8")
    entries = {m.group(2): m.group(1).lower() for m in re.finditer(r"@(\w+)\{([^,]+),", bib)}
    years = {}
    for m in re.finditer(r"@\w+\{([^,]+),(.*?)\n\}", bib, re.S):
        y = re.search(r"year\s*=\s*\{(\d{4})", m.group(2))
        years[m.group(1)] = int(y.group(1)) if y else None
    grey = {k for k in entries if re.search(r"@\w+\{" + re.escape(k) + r",(?:(?!\n\}).)*keywords = \{grey\}", bib, re.S)}
    cs = set(cited)
    missing = sorted(cs - set(entries))
    uncited = sorted(set(entries) - cs)
    n = len(cs & set(entries))
    recent = sum(1 for k in cs if years.get(k) and years[k] >= 2021)
    g = len(cs & grey)
    body = src[MS / "main.tex"]
    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", body, re.S)
    abs_words = len(re.sub(r"\\[a-zA-Z]+|[{}]", " ", abstract.group(1)).split()) if abstract else 0
    main_txt = body[body.find(r"\section{Introduction}"):body.find(r"\section*{CRediT")]
    for f, s in src.items():
        if f.parent.name == "sections":
            main_txt += s
    plain = re.sub(r"\\begin\{table\*?\}.*?\\end\{table\*?\}|\\begin\{figure\*?\}.*?\\end\{figure\*?\}", " ", main_txt, flags=re.S)
    plain = re.sub(r"\\cite[a-z]*\{[^}]*\}|\\ref\{[^}]*\}|\\label\{[^}]*\}|\\input\{[^}]*\}", " ", plain)
    plain = re.sub(r"\\[a-zA-Z]+\*?|[{}$\\]", " ", plain)
    words = len(plain.split())
    banned_hits = []
    for f, s in src.items():
        low = s.lower()
        for b in BANNED:
            if b in low:
                banned_hits.append(f"{f.name}: '{b}'")
    lines = ["# QA report (Phase 8)", "",
             f"- Cited keys: {len(cs)}; bib entries: {len(entries)}",
             f"- Missing from bib: {missing or 'none'}",
             f"- In bib but not cited: {uncited or 'none'}",
             f"- Reference count (cited and in bib): {n} (target 90-115) -> {'PASS' if 90 <= n <= 115 else 'FAIL'}",
             f"- From 2021-2026: {recent} ({100 * recent / max(n, 1):.1f}%) (target >= 40%) -> {'PASS' if recent / max(n, 1) >= 0.40 else 'FAIL'}",
             f"- Grey literature: {g} ({100 * g / max(n, 1):.1f}%) (limit 15%) -> {'PASS' if g / max(n, 1) <= 0.15 else 'FAIL'}",
             f"- Abstract words: {abs_words} (limit 250) -> {'PASS' if abs_words <= 250 else 'FAIL'}",
             f"- Main-text words (Introduction to Conclusion, excluding tables/figures/citations): {words}",
             f"- Banned phrases: {banned_hits or 'none'}"]
    (ROOT / "reviews").mkdir(exist_ok=True)
    (ROOT / "reviews" / "qa_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    hard = missing or uncited or not (90 <= n <= 115) or recent / max(n, 1) < 0.40 or g / max(n, 1) > 0.15 or abs_words > 250 or banned_hits
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())

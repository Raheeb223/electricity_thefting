"""Style safety checks for rewritten manuscript sections (no lost citations or numbers; sentence length; banned words).

Usage:
  python scripts/style_check.py OLD.tex NEW.tex [--log LOG.md]   compare one section
  python scripts/style_check.py --all manuscript/main.tex         whole-manuscript report

For each section (split at \\section) it reports:
 1. citation keys in OLD missing from NEW (each must be logged with a reason);
 2. numbers in OLD missing from NEW (each must be logged with a reason);
 3. banned words / patterns still present;
 4. average sentence length, share of sentences over 30 words, Flesch Reading Ease
    (textstat if installed; otherwise a built-in syllable estimate, flagged as such).
Writes or appends reviews/style_report.md.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reviews" / "style_report.md"

BANNED = ["delve", "realm", "tapestry", "pivotal", "paramount", "multifaceted", "holistic",
          "seamless", "synergy", "groundbreaking", "cutting-edge", "game-changer", "unlock",
          "harness", "underscore", "a testament to", "shed light on", "pave the way",
          "plays a vital role", "plays a crucial role", "plays a pivotal role",
          "it is worth noting", "it is important to note", "in today's world",
          "in the ever-evolving", "needless to say", "last but not least", "in a nutshell",
          "utilise", "utilize", "facilitate", "elucidate", "commence", "endeavour",
          "in order to", "due to the fact that", "prior to", "with regard to", "leverage"]
BANNED_RX = [(r"\bnot only\b[^.]*\bbut also\b", "not only ... but also"),
             (r"\blandscape\b", "landscape (check literal use)"),
             (r"\bnavigat\w*", "navigate (check literal use)"),
             (r"^\s*(Furthermore|Moreover|Additionally)\b", "sentence opener Furthermore/Moreover/Additionally"),
             (r"\?\s", "question mark in body text (rhetorical question?)"),
             (r"---", "em dash")]
SPARING = ["crucial", "notably", "comprehensive", "robust", "significant"]


def strip_tex(t):
    t = re.sub(r"(?m)(?<!\\)%.*$", "", t)
    t = t.replace("\\%", " percent")
    t = re.sub(r"\\begin\{(figure|table|xltabular|tabular|equation)\*?\}.*?\\end\{\1\*?\}", " ", t, flags=re.S)
    t = re.sub(r"\\(cite[pt]?|citealp|citeauthor|ref|label|eqref|input|includegraphics)\*?(\[[^\]]*\])*\{[^}]*\}", " X ", t)
    t = re.sub(r"\\(section|subsection|paragraph|subsubsection)\*?\{([^}]*)\}", r"\2. ", t)
    t = re.sub(r"\\item\s*", " ", t)
    t = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?\{([^}]*)\}", r"\2", t)
    t = re.sub(r"\\[a-zA-Z]+\*?", " ", t)
    t = re.sub(r"[{}$~\\]", " ", t)
    t = t.replace("e.g.", "eg").replace("i.e.", "ie").replace("et al.", "et al").replace("vs.", "vs").replace("Fig.", "Fig").replace("No.", "No")
    return re.sub(r"\s+", " ", t).strip()


def cites(t):
    keys = set()
    for g in re.findall(r"\\cite[a-z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}", t):
        keys |= {k.strip() for k in g.split(",") if k.strip()}
    return keys


def numbers(t):
    t = re.sub(r"\\(cite[a-z]*|ref|label|input|includegraphics)\*?(\[[^\]]*\])*\{[^}]*\}", " ", t)
    return {x.rstrip(",") for x in re.findall(r"(?<![\w.])\d[\d,]*(?:\.\d+)?", t)}


def sentences(plain):
    s = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", plain)
    return [x for x in s if len(x.split()) >= 3]


def syllables(w):
    w = w.lower()
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups) - (1 if w.endswith("e") and len(groups) > 1 else 0)
    return max(1, n)


def readability(plain):
    try:
        import textstat
        return textstat.flesch_reading_ease(plain), "textstat"
    except Exception:
        words = re.findall(r"[A-Za-z]+", plain)
        sents = max(1, len(sentences(plain)))
        if not words:
            return 0.0, "estimate"
        syl = sum(syllables(w) for w in words)
        return 206.835 - 1.015 * len(words) / sents - 84.6 * syl / len(words), "estimate"


def section_stats(tex):
    plain = strip_tex(tex)
    ss = sentences(plain)
    lens = [len(s.split()) for s in ss]
    avg = sum(lens) / len(lens) if lens else 0
    over = sum(1 for n in lens if n > 30) / len(lens) if lens else 0
    fre, how = readability(plain)
    hits = []
    low = plain.lower()
    for b in BANNED:
        if re.search(r"\b" + re.escape(b) + r"\b", low):
            hits.append(b)
    for s in ss:
        for rx, lab in BANNED_RX:
            if re.search(rx, s, re.I if "Further" not in rx else 0):
                hits.append(lab)
    spar = {w: len(re.findall(r"\b" + w + r"\b", low)) for w in SPARING}
    long_s = [s for s in ss if len(s.split()) > 30]
    return dict(n=len(ss), avg=avg, over=over, fre=fre, fre_how=how, hits=sorted(set(hits)),
                hit_counts={h: hits.count(h) for h in set(hits)}, sparing=spar, long=long_s)


def split_sections(tex):
    parts = re.split(r"(?=\\section\*?\{)", tex)
    out = []
    for p in parts:
        m = re.match(r"\\section\*?\{([^}]*)\}", p)
        out.append((m.group(1) if m else "Front matter", p))
    return out


def compare(old, new):
    lost_c = sorted(cites(old) - cites(new))
    lost_n = sorted(numbers(old) - numbers(new), key=lambda x: float(x.replace(",", "")))
    return lost_c, lost_n


def main():
    a = sys.argv[1:]
    lines = []
    if a and a[0] == "--all":
        tex = Path(a[1]).read_text(encoding="utf-8")
        body = tex.split("\\begin{document}", 1)[-1]
        lines.append(f"# Style report: {a[1]}\n")
        lines.append("| Section | Sentences | Avg words | >30 words | Flesch | Banned / pattern hits |")
        lines.append("|---|---|---|---|---|---|")
        worst = []
        for name, part in split_sections(body):
            st = section_stats(part)
            if st["n"] == 0:
                continue
            lines.append(f"| {name[:60]} | {st['n']} | {st['avg']:.1f} | {100*st['over']:.0f}% | {st['fre']:.0f} | "
                         f"{'; '.join(f'{k} x{v}' for k, v in st['hit_counts'].items()) or '-'} |")
            worst += [(name, s) for s in st["long"]]
        allst = section_stats(body)
        lines.append(f"\nWhole text: {allst['n']} sentences, mean {allst['avg']:.1f} words, "
                     f"{100*allst['over']:.1f}% over 30 words, Flesch {allst['fre']:.0f} ({allst['fre_how']}).")
        lines.append(f"Sparing words: {allst['sparing']}")
        lines.append("\n## Sentences over 30 words\n")
        lines += [f"- [{n[:30]}] {s}" for n, s in worst]
        REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines[:40]))
        return
    old, new = Path(a[0]).read_text(encoding="utf-8"), Path(a[1]).read_text(encoding="utf-8")
    lost_c, lost_n = compare(old, new)
    st = section_stats(new)
    lines.append(f"## {Path(a[1]).name}")
    lines.append(f"- citation keys missing from new: {lost_c or 'none'}")
    lines.append(f"- numbers missing from new: {lost_n or 'none'}")
    lines.append(f"- banned/pattern hits: {st['hit_counts'] or 'none'}")
    lines.append(f"- sentences {st['n']}, mean {st['avg']:.1f} words, {100*st['over']:.0f}% over 30, Flesch {st['fre']:.0f} ({st['fre_how']})")
    for s in st["long"]:
        lines.append(f"  - long: {s}")
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

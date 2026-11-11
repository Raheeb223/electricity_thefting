"""Extract text from data/fulltext/*.pdf into data/fulltext_text/<record_id>.txt (skips existing).
Then write data/fulltext_excerpts/<record_id>.txt with the sections needed for extraction:
abstract, data/dataset paragraphs, sentences with metrics, limitations, conclusion."""
import re, sys
from pathlib import Path
from pypdf import PdfReader
ROOT = Path(__file__).resolve().parents[1]
SRC, TXT, EXC = ROOT/"data/fulltext", ROOT/"data/fulltext_text", ROOT/"data/fulltext_excerpts"
TXT.mkdir(exist_ok=True); EXC.mkdir(exist_ok=True)
PAT = re.compile(r"(dataset|data set|consumers|customers|households|meters?\b|monthly|daily|hourly|minute|resolution|"
                 r"label|inspect|imbalanc|smote|precision|recall|f1|f-score|auc|accuracy|detection rate|false positive|"
                 r"deploy|field|pilot|cost|usd|\$|tk|taka|rupee|limitation|future work|bangladesh|survey|respondent|"
                 r"interview|sample|regression|panel|loss(es)? (fell|reduced|decrease)|reduction)", re.I)
for pdf in sorted(SRC.glob("*.pdf")):
    rid = pdf.stem
    t = TXT/f"{rid}.txt"
    if not t.exists():
        try:
            text = "\n".join((p.extract_text() or "") for p in PdfReader(str(pdf)).pages)
        except Exception as e:
            print(rid, "FAILED", e); continue
        t.write_text(text, encoding="utf-8")
    text = t.read_text(encoding="utf-8")
    flat = " ".join(text.split())
    sents = re.split(r"(?<=[.!?])\s+", flat)
    keep = [s for s in sents if PAT.search(s) and 40 < len(s) < 600]
    head = flat[:2500]
    concl = flat[max(0, flat.lower().rfind("conclusion")):][:2500]
    ex = f"## HEAD\n{head}\n\n## KEY SENTENCES ({len(keep)})\n" + "\n".join(keep[:120]) + f"\n\n## CONCLUSION\n{concl}\n"
    (EXC/f"{rid}.txt").write_text(ex, encoding="utf-8")
    print(rid, len(text), len(keep))

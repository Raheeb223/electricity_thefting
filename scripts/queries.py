"""Search strings S1-S4 (protocol section 4) in API syntax, plus the regular expressions
that re-apply the full Boolean logic locally to every retrieved record."""
import re

# ---- Block phrases ---------------------------------------------------------------
A_PHRASES = [
    "electricity theft", "energy theft", "power theft", "electricity pilferage",
    "power pilferage", "non-technical loss", "non-technical losses", "nontechnical losses",
    "non technical losses", "meter tampering", "meter bypass", "illegal connections",
    "illegal electricity connections", "electricity fraud", "energy fraud",
    "electricity stealing", "theft of electricity",
]
B_PHRASES = [
    "detection", "prevention", "machine learning", "deep learning", "classification",
    "anomaly detection", "smart meter", "advanced metering", "state estimation", "observer",
    "prepaid meter", "prepayment", "governance", "policy", "regulation", "corruption",
    "enforcement", "inspection",
]
C_PHRASES = [
    "Bangladesh", "South Asia", "India", "Pakistan", "Nepal", "Sri Lanka", "Brazil",
    "Africa", "developing countries", "developing country", "low-income", "middle-income",
    "emerging economies",
]
D_UTIL = [
    "system loss", "distribution loss", "prepaid meter", "smart meter", "BPDB", "BREB",
    "DPDC", "DESCO", "WZPDCL", "NESCO", "BERC", "rural electrification",
]
E_PHRASES = [
    "easy bike", "easy-bike", "battery rickshaw", "battery-run rickshaw",
    "battery-operated rickshaw", "battery-powered rickshaw", "electric rickshaw",
    "e-rickshaw", "electric three-wheeler", "electric auto-rickshaw", "auto-rickshaw",
    "battery-driven rickshaw", "light electric vehicle",
]
E_CONTEXT = ["charging", "electricity", "grid", "power consumption", "theft", "illegal connection"]
E_REGION = ["Bangladesh", "India", "Nepal", "South Asia", "developing countries"]


def _or(phrases, q='"', sep=" OR "):
    return "(" + sep.join(f"{q}{p}{q}" for p in phrases) + ")"


# OpenAlex: Boolean AND/OR/NOT with quotes and parentheses, applied to title+abstract.
OPENALEX = {
    "S1": f"{_or(A_PHRASES)} AND {_or(B_PHRASES)}",
    "S2": f"{_or(A_PHRASES)} AND {_or(C_PHRASES)}",
    "S3": f'"Bangladesh" AND ("electricity" OR "power") AND {_or(D_UTIL)}',
    "S4": f"{_or(E_PHRASES)} AND {_or(E_CONTEXT)} AND {_or(E_REGION)}",
}
# Semantic Scholar bulk search: | = OR, + = AND, quotes for phrases.
S2 = {
    "S1": f"{_or(A_PHRASES, sep=' | ')} + {_or(B_PHRASES, sep=' | ')}",
    "S2": f"{_or(A_PHRASES, sep=' | ')} + {_or(C_PHRASES, sep=' | ')}",
    "S3": f'"Bangladesh" + ("electricity" | "power") + {_or(D_UTIL, sep=" | ")}',
    "S4": f"{_or(E_PHRASES, sep=' | ')} + {_or(E_CONTEXT, sep=' | ')} + {_or(E_REGION, sep=' | ')}",
}
# arXiv: field prefixes; abs: searches abstract. Only S1 is meaningful on arXiv.
ARXIV = {
    "S1": "(" + " OR ".join(f'abs:"{p}"' for p in A_PHRASES[:9]) + ")",
}
# Crossref has no Boolean support: one query per theft phrase (+ rickshaw/Bangladesh),
# relevance-ranked, top 200. Local regex filtering removes the noise.
CROSSREF = (
    [f"{p} detection" for p in A_PHRASES[:10]]
    + [f"{p} policy" for p in A_PHRASES[:4]]
    + [f"electricity theft {c}" for c in ["Bangladesh", "India", "Pakistan", "Africa", "Brazil", "Nepal"]]
    + ["system loss electricity distribution Bangladesh", "prepaid meter Bangladesh",
       "easy bike charging Bangladesh electricity", "battery rickshaw charging electricity",
       "e-rickshaw charging grid India"]
)

# ---- Local regular expressions (title + abstract) -----------------------------------
ELEC = r"(electric|electricity|power|energy|grid|meter|utilit|consum|distribution)"
RE_A = re.compile(
    r"(electric(ity|al)?\s+(energy\s+|power\s+)?theft|energy\s+theft|power\s+theft"
    r"|theft\s+of\s+(electric|power|energy)|pilfer|non[- ]?technical\s+loss|\bNTLs?\b"
    r"|meter\s+(tamper|bypass)|tamper\w*\s+(of\s+)?(energy\s+|smart\s+|electric\w*\s+)?meter"
    r"|illegal\s+(electric\w*\s+|power\s+)?(connection|hook)|electricity\s+fraud|energy\s+fraud"
    r"|stealing\s+(electricity|power|energy)|(electricity|energy|power)\s+stealing"
    r"|theft\s+detection|fraud\s+detection)", re.I)
RE_ELEC = re.compile(ELEC, re.I)
RE_B = re.compile(
    r"(detect|prevent|machine\s+learning|deep\s+learning|classif|anomal|smart\s+meter"
    r"|advanced\s+metering|\bAMI\b|state\s+estimat|observer|prepaid|prepayment|governance"
    r"|polic|regulat|corrupt|enforce|inspect|neural|learning|tamper|cluster)", re.I)
RE_C = re.compile(
    r"(bangladesh|south\s+asia|india|pakistan|nepal|sri\s+lanka|brazil|africa|developing\s+countr"
    r"|low[- ]income|middle[- ]income|emerging\s+econom)", re.I)
RE_D = re.compile(
    r"(system\s+loss|distribution\s+loss|prepaid\s+meter|smart\s+meter|\bBPDB\b|\bBREB\b|\bDPDC\b"
    r"|\bDESCO\b|\bWZPDCL\b|\bNESCO\b|\bBERC\b|rural\s+electrification|palli\s+bidyut)", re.I)
RE_E = re.compile(
    r"(easy[- ]?bike|(battery|electric)[- \w]{0,12}rickshaw|e[- ]rickshaw|electric\s+three[- ]wheeler"
    r"|auto[- ]rickshaw|light\s+electric\s+vehicle)", re.I)
RE_E_CTX = re.compile(r"(charg|electricity|grid|power\s+consumption|theft|illegal)", re.I)
RE_E_REG = re.compile(r"(bangladesh|india|nepal|south\s+asia|developing)", re.I)
RE_REVIEW = re.compile(
    r"\b(review|survey|overview|state[- ]of[- ]the[- ]art|systematic|bibliometric|meta-analysis"
    r"|taxonomy|literature)\b", re.I)


def match_strings(title: str, abstract: str) -> list[str]:
    """Return which of S1-S4 a record satisfies under the protocol's Boolean logic."""
    t = f"{title or ''} {abstract or ''}"
    out = []
    a = bool(RE_A.search(t)) and bool(RE_ELEC.search(t))
    if a and RE_B.search(t):
        out.append("S1")
    if a and RE_C.search(t):
        out.append("S2")
    if re.search(r"bangladesh", t, re.I) and re.search(r"electric|power", t, re.I) and RE_D.search(t):
        out.append("S3")
    if RE_E.search(t) and RE_E_CTX.search(t) and RE_E_REG.search(t):
        out.append("S4")
    return out

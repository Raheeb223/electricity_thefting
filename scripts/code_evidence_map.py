"""R3 tier 1: systematic evidence map of ALL eligible records, coded from title + abstract.

Coding is rule-based (transparent regular expressions, listed below) so it is
reproducible; its accuracy is measured against the hand-coded extraction of the 69
synthesis studies (data/extraction.csv) and reported in data/evidence_map_validation.csv.
A human check of a coded sample follows in R4.

Fields: approach family (from screening), country, LMIC flag (World Bank income groups,
FY2026: low, lower-middle and upper-middle income), data granularity, label source,
real utility data (named utility or utility-supplied data, excluding public benchmarks),
validation setting, year.
Then applies the R3 priority-synthesis criteria (scope only, no venue/citation criteria):
  P-BD   Bangladesh setting or data
  P-LMIC LMIC setting with real utility data
  P-MON  monthly or conventional-meter data
  P-FLD  field deployment or validation reported
  P-GOV  governance or E3W evidence with reported outcomes (I5a/I5c/I4 records)
Output: data/evidence_map_coded.csv, data/priority_synthesis.csv, summary printed.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

COUNTRIES = {  # name pattern -> (country, LMIC?)  LMIC = World Bank low/lower-middle/upper-middle income
    r"bangladesh|dhaka|chittagong|khulna|rajshahi|desco|dpdc|bpdb|wzpdcl|nesco|breb|palli bidyut": ("Bangladesh", True),
    r"\bindia\b|indian|uttar pradesh|delhi|maharashtra|mumbai|kerala|karnataka|tamil nadu|gujarat|rajasthan|punjab state": ("India", True),
    r"pakistan|lahore|karachi|islamabad|lesco|mepco|iesco|pesco|fesco|hesco|wapda": ("Pakistan", True),
    r"\bnepal": ("Nepal", True), r"sri lanka": ("Sri Lanka", True),
    r"indonesia|\bpln\b|java|sumatra": ("Indonesia", True), r"malaysia|tenaga": ("Malaysia", True),
    r"philippines": ("Philippines", True), r"vietnam|viet nam": ("Vietnam", True), r"thailand": ("Thailand", True),
    r"\bchina\b|chinese|state grid|sgcc": ("China", True), r"\biran|tehran|mashhad": ("Iran", True),
    r"turkey|t[uü]rkiye": ("Turkey", True), r"brazil|brazilian|s[aã]o paulo|rio de janeiro|par[aá]\b|aneel": ("Brazil", True),
    r"colombia": ("Colombia", True), r"ecuador": ("Ecuador", True), r"peru\b": ("Peru", True), r"mexico": ("Mexico", True),
    r"argentin": ("Argentina", True), r"jamaica": ("Jamaica", True), r"uruguay|\bute\b": ("Uruguay", False),
    r"south africa|eskom|gauteng|soweto": ("South Africa", True), r"nigeria|lagos|abuja": ("Nigeria", True),
    r"ghana|accra|kumasi": ("Ghana", True), r"kenya|nairobi": ("Kenya", True), r"uganda|kampala": ("Uganda", True),
    r"tanzania": ("Tanzania", True), r"cameroon": ("Cameroon", True), r"ethiopia": ("Ethiopia", True),
    r"congo|kinshasa": ("DR Congo", True), r"zimbabwe": ("Zimbabwe", True), r"zambia": ("Zambia", True),
    r"egypt": ("Egypt", True), r"morocco": ("Morocco", True), r"algeria": ("Algeria", True), r"tunisia": ("Tunisia", True),
    r"jordan": ("Jordan", True), r"lebanon": ("Lebanon", True), r"iraq": ("Iraq", True),
    r"saudi": ("Saudi Arabia", False), r"spain|spanish|endesa": ("Spain", False), r"portugal": ("Portugal", False),
    r"ireland|irish": ("Ireland", False), r"\buk\b|united kingdom|london": ("United Kingdom", False),
    r"greece|greek": ("Greece", False), r"italy|italian": ("Italy", False), r"korea": ("South Korea", False),
    r"taiwan": ("Taiwan", False), r"usa\b|united states": ("United States", False), r"canada": ("Canada", False),
    r"australia": ("Australia", False), r"luxembourg": ("Luxembourg", False),
}
GRAN = [("Monthly / billing", r"monthly|billing (data|records|history)|bill(s)? |conventional meter|traditional meter|electromechanical|non[- ]smart|postpaid|meter reading(s)? (taken )?every|low[- ]sampling"),
        ("Imagery", r"satellite|sentinel|remote sensing|aerial|imagery"),
        ("Sub-daily / smart meter", r"half[- ]hourly|hourly|15[- ]min|30[- ]min|smart meter|\bami\b|advanced metering|load profile|high[- ]resolution|fine[- ]grained|sgcc|state grid"),
        ("Daily", r"\bdaily\b")]
LAB_REAL = r"inspect|confirmed (fraud|theft)|real (fraud|theft)|fraud(ulent)? (cases|customers) (identified|confirmed|detected by)|ground truth|labell?ed (by|from) (the )?utilit|historical (fraud|inspection)|irregularit(y|ies) confirmed"
LAB_SYN = r"synthetic|inject|attack model|simulated (theft|attack|fraud)|false data|generated (theft|attack)|theft (cases|types|attacks) (are|were) (generated|simulated)"
REAL_UTIL = r"utilit(y|ies)['’]? (data|database)|data (from|provided by|of) (a |the )?(utilit|distribution compan|power compan|electric(ity)? compan|disco)|real[- ](world|life) (data|dataset)|customers? of (a |the )?(utility|company)|distribution company|power distribution compan|discos?\b|endesa|\bpln\b|\bute\b|cpfl|eletropaulo|lesco|mepco|iesco|pesco|tenaga|eskom"
BENCH = r"sgcc|state grid corporation of china|irish|commission for energy regulation|\bcer\b|london smart meter|public (dataset|data set)|benchmark dataset|kaggle|pecan street"
FIELD = r"field (?:test|trial|validation|validated|experiment|deployment)|pilot (?:project|study|deployment)|(?:was|were|has been) (?:deployed|implemented|put into operation) (?:in|at|by) (?:the |a )?(?:utility|company|distribution)|real[- ]world deployment|new (?:field )?inspections|inspections? (?:were|was) (?:carried out|conducted|performed) to (?:validate|verify|confirm)|in (?:operational )?use (?:at|by)"
SIM = r"simulat|simulink|matlab|prototype|laboratory|lab[- ]scale|hardware[- ]in[- ]the[- ]loop|proteus|arduino|test (bench|system|feeder)|ieee \d+[- ]bus"


def code(row):
    t = f"{row.title} {row.abstract}".lower()
    country, lmic = "Not stated", np.nan
    for rx, (c, l) in COUNTRIES.items():
        if re.search(rx, t):
            country, lmic = c, l
            break
    gran = "Unclear"
    for g, rx in GRAN:
        if re.search(rx, t):
            gran = g
            break
    real, syn = bool(re.search(LAB_REAL, t)), bool(re.search(LAB_SYN, t))
    labels = "Real + synthetic" if real and syn else "Real" if real else "Synthetic" if syn else "Unclear"
    util = bool(re.search(REAL_UTIL, t)) and not (bool(re.search(BENCH, t)) and not re.search(r"utilit(y|ies)['’]? data|provided by", t))
    if re.search(FIELD, t):
        val = "Field"
    elif util or real:
        val = "Offline, real data"
    elif re.search(SIM, t) or syn:
        val = "Simulation / lab"
    else:
        val = "Unclear"
    return pd.Series({"country": country, "lmic": lmic, "granularity": gran, "labels": labels,
                      "real_utility_data": util, "validation": val})


def main():
    recs = pd.read_csv(ROOT / "data" / "records_dedup.csv", dtype=str).fillna("")
    scr = pd.read_csv(ROOT / "data" / "screening.csv", dtype=str).fillna("")
    e = scr[scr.ta_decision == "INC"][["record_id", "ta_code", "family", "year", "venue"]].merge(
        recs[["record_id", "title", "abstract", "doi"]], on="record_id")
    e = pd.concat([e, e.apply(code, axis=1)], axis=1)
    e["is_review"] = e.ta_code.eq("RV")
    e["P_BD"] = e.country.eq("Bangladesh")
    e["P_LMIC"] = e.lmic.eq(True) & e.real_utility_data
    e["P_MON"] = e.granularity.eq("Monthly / billing")
    e["P_FLD"] = e.validation.eq("Field")
    e["P_GOV"] = e.ta_code.isin(["I5a", "I5c", "I4"]) | e.family.isin(["GV", "E3W", "BD"])
    pcols = ["P_BD", "P_LMIC", "P_MON", "P_FLD", "P_GOV"]
    e["priority"] = e[pcols].any(axis=1) & ~e.is_review & ~e.ta_code.eq("GREY")
    e.drop(columns=["abstract"]).to_csv(ROOT / "data" / "evidence_map_coded.csv", index=False)

    # validation against hand coding of the 69 synthesis studies
    ex = pd.read_csv(ROOT / "data" / "extraction.csv", dtype=str).fillna("")
    ex = ex[ex.role == "included study"]
    v = ex[["id", "data_granularity", "labelled_data", "real_world_deployment", "country_region"]].merge(
        e, left_on="id", right_on="record_id", how="left")
    def g_hand(s):
        s = s.lower()
        return ("Monthly / billing" if s.startswith("monthly") or "billing" in s or "40-60" in s else
                "Imagery" if "imagery" in s else "Sub-daily / smart meter" if ("hour" in s or "smart" in s or "interval" in s or "sub" in s)
                else "Daily" if s.startswith("daily") else "Unclear/NA")
    v["g_hand"] = v.data_granularity.map(g_hand)
    v["f_hand"] = v.real_world_deployment.str.upper().str.startswith("Y")
    v["c_hand"] = v.country_region.str.split(r"[ (]", regex=True).str[0]
    meth = v[v.data_granularity.ne("NA")]
    res = {
        "granularity agreement (method studies, excl. unclear)": np.mean(meth.g_hand[meth.g_hand != "Unclear/NA"] == meth.granularity[meth.g_hand != "Unclear/NA"]),
        "field validation: sensitivity": (v.f_hand & v.validation.eq("Field")).sum() / max(v.f_hand.sum(), 1),
        "field validation: specificity": (~v.f_hand & ~v.validation.eq("Field")).sum() / max((~v.f_hand).sum(), 1),
        "country agreement": np.mean([str(a).lower().startswith(str(b).lower()[:5]) for a, b in zip(v.country, v.c_hand)]),
    }
    pd.Series(res).round(3).to_csv(ROOT / "data" / "evidence_map_validation.csv", header=["value"])
    print("validation vs hand coding (n = 69):", {k: round(x, 3) for k, x in res.items()})

    det = e[e.ta_code.eq("I5b")]
    print(f"eligible: {len(e)}; detection studies: {len(det)}")
    for c in ["granularity", "labels", "validation"]:
        print(c, (det[c].value_counts(normalize=True) * 100).round(1).to_dict())
    print("LMIC share (country stated):", round(100 * det.lmic.eq(True).sum() / max(det.country.ne('Not stated').sum(), 1), 1))
    pr = e[e.priority]
    print("priority synthesis set:", len(pr), {c: int(pr[c].sum()) for c in pcols})
    print("already in the 69:", pr.record_id.isin(ex.id).sum(), "| new:", (~pr.record_id.isin(ex.id)).sum())
    pr.drop(columns=["abstract"], errors="ignore").to_csv(ROOT / "data" / "priority_synthesis.csv", index=False)


if __name__ == "__main__":
    main()

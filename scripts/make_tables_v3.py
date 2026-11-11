"""Revision tables built from the two-tier synthesis (R6/R11).
T4 field-validated detection studies; T7 governance and intervention studies with
measured outcomes; S5 (supplement) all synthesis studies with codes.
Rows are written from the page-referenced full-text extraction (data/extraction_ft.csv)
where a full text was read ("FT") and from the abstract otherwise ("Abs."); abstract
values are as reported by the authors and are listed for full-text confirmation.
Uses the table writer of make_tables.py."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from make_tables import write  # noqa: E402

FT = set(pd.read_csv(ROOT / "data/extraction_ft.csv").record_id)
KM = pd.read_csv(ROOT / "refs/key_map.csv", keep_default_na=False)
R2K = dict(zip(KM.record_id, KM.key))
K2R = {v: k for k, v in R2K.items()}


def rl(key):
    return "FT" if K2R.get(key) in FT else "Abs."


T4 = [  # key, country, data and labels, field design, reported field result
    ("haramaini2026hybrid", "Indonesia (PLN West Java)", "Monthly bills and token purchases, 2.36M consumers; inspection labels", "12,407 inspections by utility officers", "Confirmed theft 72.0% vs 15.3% under rules"),
    ("guerrero2018non", "Spain (Endesa)", "Monthly consumption, inspection history", "Inspection campaigns", "Inspection success about 3 times the ~5% baseline"),
    ("gusmao2020customer", "Brazil (CPFL)", "Customer interaction and inspection records", "Field test, then adopted in operations", "Inspection success 2.2 times higher"),
    ("coelho2023hymotree", "Brazil (CPFL)", "Monthly data; inspection labels", "Model-guided field inspections", "76% accuracy on inspected cases"),
    ("comapuig2016fraud", "Spain (Gas Natural Fenosa)", "Monthly readings (half smart meters); fraud history", "Campaigns in three towns of 50,000--100,000, same size as baseline", "Precision notably better than baseline campaigns"),
    ("alharbi2021electricity", "Not stated (utility serving >30M people)", "Low-resolution (monthly) consumption; cost-driven ranking", "Initial testing by the utility", "About 75% precision on new NTL cases"),
    ("barros2022maximizing", "Brazil", "261,489 consumers; inspection labels", "338 new inspections of unlabelled consumers", "Financial return up to 11.5 times higher"),
    ("cevallosvaldiviezo2022non", "Ecuador (Guayaquil)", "Utility consumption data", "Later inspections of new flags", "New flags confirmed; no figure in abstract"),
    ("vieira2023detection", "Brazil (irrigation consumers)", "Monthly data", "Pilot area", "63% accuracy; search area cut by 78%"),
    ("bettiol2023detection", "Brazil", "Monthly bills; Isolation Forest", "Preliminary field tests", "91.7% of inspected flags confirmed"),
    ("kosut2015abnormal", "Uruguay (UTE)", "Monthly data; inspection labels", "Field tests", "Improved hit rate; no figure in abstract"),
    ("acevedo2025ntl", "Uruguay (UTE)", "Low- and high-resolution data", "Comparison with deployed model, field inspections", "Outperformed the deployed model"),
    ("nagi2010ntl", "Malaysia (TNB)", "Consumption of large consumers; inspection labels", "Pilot on-site inspections", "55% hit rate"),
    ("nagi2011improving", "Malaysia (TNB)", "Consumption; inspection labels", "Inspections", "Hit rate from 60% to 72%"),
    ("hu2020understanding", "China (State Grid, Hangzhou)", "Multi-source data; 4,501 inspection-confirmed labels", "Monthly on-site investigation, Aug 2019", "Precision 15% vs 0% for earlier models"),
    ("kang2022research", "China", "Smart-meter and line-loss data", "16 suspects inspected", "10 confirmed (bitcoin mining)"),
    ("jing2021research", "China (Qinghai)", "Photovoltaic generation curves", "Door-to-door inspection", "22 cases confirmed"),
    ("ma2023electricity", "China", "Smart-meter data in high-loss zones", "Field inspection", "Suspects confirmed; no figure in abstract"),
    ("haruna2025temporal", "Brazil (Sao Paulo)", "Interval data, limited labels", "2023 pilot", "NTL down 19% in six months"),
    ("menezes2026geospatial", "Brazil (Para)", "Satellite imagery and GIS; no meter data", ">10,000 inspected sites", "83.05% average accuracy"),
    ("gresoi2025advanced", "Not stated", "Distribution data incl. non-smart meters", "Implementation", "Losses reduced by EUR 45,200"),
    ("toledoorozco2021innovative", "Ecuador", "Customer, network (GIS) and socio-economic data", "Utility project", "Meter errors found; no figure in abstract"),
    ("kippkesalomon2025self", "Spain", "Power-line-carrier AMI with self-diagnosis", "Deployed in a low-voltage network segment", "Qualitative; no figure in abstract"),
    ("ali2023prevention", "Pakistan (PESCO)", "Low-cost smart meters with cloud analytics", "Deployment over 15 km2", "Theft outcomes not reported in abstract"),
    ("calamaro2021energy", "Not stated", "Smart-meter data; knowledge-based rules", "Real-life scenarios", "No figure in abstract"),
    ("abdulhamza2023electricity", "Not stated", "Smart-meter data; cloud CNN", "Tests under real-life conditions", "No figure in abstract"),
]

T7 = [  # key, setting, intervention, design, outcome
    ("otchereappiah2021impact", "Ghana", "Replacement of tampered postpaid meters with smart prepaid meters (2019)", "Difference-in-differences, customer billing panel", "Reported consumption +13.2%; no effect in lowest quartile"),
    ("odje2021aggregated", "Nigeria (11 Discos)", "Scale-up of metering", "Regulatory panel 2015-2020", "Each 1% more metered customers: 0.8% lower ATC&C loss"),
    ("rabbani2020does", "Bangladesh (Dhaka)", "Postpaid to prepaid switch", "Payment records over three years", "Fewer missed payments; 46% recharge monthly"),
    ("akand2019analytical", "Bangladesh", "Prepaid metering", "Analytical study of utility data", "Higher collection, lower system loss reported"),
    ("ahmad2024performance", "India (Jammu and Kashmir)", "Aerial bundled cables and smart meters (RDSS)", "Before-after on one feeder", "AT&C loss from ~60% to ~15%"),
    ("khazaee2017distribution", "Iran (Mashhad)", "AMI pilots, residential and commercial", "Field measurements and simulation", "Distribution loss reduced"),
    ("castro2026photovoltaic", "Brazil (Rio de Janeiro)", "PV with storage and smart metering in a low-income community", "Pilot with two study groups", "Bills -70% and -50%; NTL recovery"),
    ("ballal2020online", "India (Nagpur)", "Power-line-carrier theft detection and prevention", "Smart-city pilot", "Implemented by the utility"),
    ("jamil2014empirical", "Pakistan (9 companies)", "Prices, income, detection and fines", "Panel 1988-2010", "Fines reduce theft; detection probability does not"),
    ("mimmi2010econometric", "Brazil (Belo Horizonte favelas)", "Consumption subsidies", "Econometric household study", "Subsidies helped with equipment upgrades and metering"),
    ("leite2020stochastic", "Brazil (41 utilities)", "Regulatory NTL targets", "Stochastic frontier panel, 10 years", "Targets did not produce a general decline"),
    ("correia2023definition", "Brazil (62 utilities)", "Regulatory NTL targets", "Panel model selection 2007-2017", "Proposes targets matched to utility capacity"),
    ("deoliveiraventura2020new", "South America", "National NTL programmes", "Cross-country indicator", "Indicator tracks supply quality"),
    ("ndaba2020implementation", "South Africa (Eskom)", "Smart prepaid split meters", "Survey of 334 respondents", "Reported benefits for utility and customers"),
]


def main():
    H = ["Study", "Country (utility)", "Data and labels", "Field design", "Reported field result"]
    R = [[k, c, d, f, r] for k, c, d, f, r in T4 if rl(k) == "FT"]
    write("T4_field_detection",
          "Detection studies with field validation or deployment, read in full for the in-depth synthesis. Results are as reported by the authors and were extracted with page references; designs are single campaigns or before-after comparisons without a control group, and baselines differ.",
          "tab:t4", H, R, r"p{2.4cm}p{2.5cm}X p{2.8cm}p{3.2cm}", 0)
    print("T4 rows (full text):", len(R), "of", len(T4))
    missing = [k for k, *_ in T4 + T7 if k not in K2R]
    print("keys not in key map:", missing)
    t8v2()
    t9v2()
    t11v2()
    t12v2()


def ev_s(v):
    return "--" if int(v) < 0 else str(int(v))


def t8v2():
    """DRM with C8, gate and split evidence (R9)."""
    import re
    from drm import DRM, EQUITY, CAVEATS, C8_RATIONALE, DEFAULT_C8
    ev = pd.read_csv(ROOT / "data/drm_v2.csv").set_index("family")
    H = ["Method family", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "Gate", "Ready", "E-any", "E-BD", "Distributional risk"]
    R = []
    for name, c, _e, keys, _w in DRM:
        ok = 0 not in c
        ready = sum(c) / len(c)
        R.append([name] + [str(x) for x in c] + ["pass" if ok else "fail",
                  f"{ready:.2f}" if ok else f"({ready:.2f})", ev_s(ev.at[name, "E_any"]), ev_s(ev.at[name, "E_bd"]), EQUITY[name][0]])
    R.sort(key=lambda r: (r[0].startswith("Rule-based"), r[9] != "pass", -float(r[10].strip("()"))))
    write("T8_drm", "Deployability Readiness Matrix for Bangladesh: a structured heuristic, not a validated ranking. Each cell scores fit with current Bangladeshi conditions: 3 fits now; 2 minor requirement; 1 substantial requirement; 0 not feasible without structural change, or unsafe. C1 data granularity; C2 meter type and AMI coverage; C3 cost per consumer; C4 labelled-data need; C5 privacy; C6 staff capacity; C7 robustness to collusion and institutional drivers; C8 safety and legal compliance. Gate: a family with any 0 fails and is not deployable without structural change; its mean is shown in brackets for information only. Ready is the unweighted mean of C1-C8. E-any and E-BD are evidence strength computed from the cited studies (0 concept, 1 simulation or laboratory, 2 offline on real data, 3 field validation or programme evaluation), anywhere and in Bangladesh or another LMIC without smart-meter data, from studies read in full only; -- means that no study of the family was retrieved in full. Rationale for every row is in Table~\\ref{tab:t10}; score uncertainty in Section~\\ref{sec:drm}.",
          "tab:t8", H, R, r"p{3.9cm}*{8}{>{\centering\arraybackslash}p{0.3cm}}>{\centering\arraybackslash}p{0.6cm}>{\centering\arraybackslash}p{0.75cm}>{\centering\arraybackslash}p{0.55cm}>{\centering\arraybackslash}p{0.55cm}>{\centering\arraybackslash}p{1.3cm}", -1, size=r"\scriptsize")
    rows = []
    for name, c, e, keys, why in DRM:
        rows.append([name, why + " C8: " + C8_RATIONALE.get(name, DEFAULT_C8), CAVEATS.get(name, ""),
                     re.sub(r" \(([a-z]+\d{4}[a-z]*)\)", "", EQUITY[name][1]),
                     ";".join(dict.fromkeys([k for k in keys.split(";") if k] + re.findall(r"\(([a-z]+\d{4}[a-z]*)\)", EQUITY[name][1])))])
    write("T10_drm_rationale", "Rationale, caveats and evidence for each row of the Deployability Readiness Matrix (Table~\\ref{tab:t8}).",
          "tab:t10", ["Method family", "Rationale for the scores", "Caveat", "Distributional note", "Evidence"],
          rows, r"p{2.6cm}X p{2.6cm}p{2.8cm}p{2.6cm}", 4, size=r"\scriptsize")


def t9v2():
    H = ["Gap", "Why it matters for Bangladesh", "Concrete direction", "Evidence"]
    R = [
        ["No public labelled theft dataset from Bangladesh", "Models cannot be trained or compared locally", "Utility-academic data trust; anonymised monthly bills with inspection outcomes", "ahammad2023electricity;glauner2017challenge"],
        ["Few controlled field evaluations of detectors in non-AMI grids", "Offline accuracy does not show inspection yield; field designs lack controls", "Randomised or stepped-wedge inspection pilots that report confirmed share and recovered energy", "haramaini2026hybrid;guerrero2018non;gusmao2020customer"],
        ["Validation on synthetic theft", "Synthetic theft overstates performance", "Validate on inspection-confirmed cases; publish negative results", "this;haramaini2026hybrid"],
        ["Label bias from inspection targeting and collusion", "Models learn where inspectors went; bribed inspectors mislabel thieves", "Random audit inspections; bias-aware learning", "glauner2017is;glauner2017challenge;lovei2000costs"],
        ["Prepaid vend data rarely used for detection", "Millions of prepaid meters produce recharge streams", "Detection on recharge frequency and amount; tamper alarms", "ahammad2023electricity;bss2025pdb;bss2025dpdc"],
        ["No measured E3W charging energy", "Theft and demand estimates vary widely", "Metered sampling of garages; charger efficiency standards", "islam2025banglatesla;mahmud2025integrating"],
        ["E3W charging outside the regulatory frame", "The 2022 charging guideline covers only BRTA-authorised vehicles", "Legal definition, licensed hubs, charging tariff, smart chargers", "powerdivision2022ev;awal2019bangladesh"],
        ["No Bangladeshi evidence on theft drivers", "Interventions cannot target causes", "District panel and household surveys on price, supply quality, trust", "jamil2014empirical;kasumba2025electricity;monstadt2025power"],
        ["Loss reporting mixes technical and non-technical loss", "NTL share is unknown", "Transformer metering and energy audits per feeder", "powercell2025systemloss"],
        ["Treatment of system loss in tariffs not publicly documented", "Decides whether utilities or consumers pay for theft", "Publish loss targets and their use in revenue requirements", "tbs2026berc;cpd2024tariff"],
    ]
    write("T9_gaps", "Research gaps mapped to concrete future directions.", "tab:t9", H, R,
          r"p{3.4cm}p{3.6cm}X p{3.6cm}", 3)


def t11v2():
    H = ["Finding", "Evidence base", "Directness", "Certainty", "Main reasons", "Sources"]
    R = [
        ["The volume of electricity theft in Bangladesh is unknown; no source separates theft from technical loss", "Official total-loss series; utility statements (5-7% customer-level NTL)", "Bangladesh", "Very low", "Statements without published method", "powercell2025systemloss;bss2025pdb;bss2025dpdc"],
        ["Reported T&D loss fell from >40% (FY1991) to 10.06% (FY2023-24)", "Official series; multilateral evaluation", "Bangladesh", "Moderate (descriptive)", "Consistent official data; definitions change over time", "powercell2025systemloss;adb2003cost;alam2024fixing"],
        ["Detection studies are rarely evaluated on monthly data with real labels or in the field", "Evidence map of 1,419 detection studies", "Not country-specific", "Moderate", "Complete coding of eligible records; abstract-level codes", "this"],
        ["Illegal charging of E3Ws is widespread in Dhaka", "Police count via newspaper, utility and ministerial statements, think-tank slides, field surveys", "Bangladesh", "Low", "Sources agree on occurrence; most are not independent", "islam2025banglatesla;bonikbarta2026battery;mahmud2025integrating"],
        ["The energy or revenue lost to E3W charging theft", "Newspaper estimate repeated in parliament", "Bangladesh", "Very low", "No metered data", "islam2025banglatesla;tbs2026illegal"],
        ["ML on monthly billing data raises inspection yield over rules", "Field validations in Indonesia, Spain, Brazil and China; 8 LMIC monthly-data studies read in full", "Indirect", "Low", "No controls; publication bias likely; no Bangladeshi study", "haramaini2026hybrid;guerrero2018non;gusmao2020customer"],
        ["Cost-sensitive targeting raises the yield of inspections", "1 utility test (initial results)", "Indirect (country not stated)", "Very low", "Indirect; single study", "alharbi2021electricity"],
        ["Offline and synthetic-attack evaluations overstate field performance", "Evidence map; field studies with modest metrics; critique of accuracy under imbalance", "Not country-specific", "Moderate", "Consistent across sources; mechanism understood", "this;haramaini2026hybrid"],
        ["Wider metering is associated with lower losses", "1 regulatory panel", "Indirect (Nigeria)", "Very low", "Observational; indirect; single study", "odje2021aggregated"],
        ["Transformer energy balance locates theft without labels", "Mechanism; no field study retrieved in full", "Indirect", "Very low", "No field evidence read; Bangladeshi metering baseline unknown", "this"],
        ["Theft rises with price and falls with income and credible penalties; collusion and rationed access sustain it", "9 empirical studies in LMICs read in full (panels, surveys, field studies)", "Indirect", "Very low", "Observational; indirect; total losses rather than theft in two panels", "jamil2014empirical;briseno2020factors;kasumba2025electricity;monstadt2025power"],
        ["Institutional reform can cut losses (cooperatives, enforcement)", "Programme evaluation and case evidence", "Bangladesh (historical), Pakistan", "Low", "Old, uncontrolled evidence", "adb2003cost;lovei2000costs"],
        ["Regularising E3W charging reduces illegal charging", "No evaluation; design proposals only", "Bangladesh", "Very low", "No empirical study", "awal2019bangladesh;powerdivision2022ev"],
        ["Active prevention hardware is safe and effective", "Concepts and simulation", "Indirect", "Very low", "No field evidence; safety risks", "sayem2020reducing"],
    ]
    write("T11_certainty", "Summary of findings with certainty of evidence for Bangladesh (approach adapted from GRADE; rules in Section~\\ref{sec:synth}). Certainty describes confidence that the finding holds for Bangladesh, not the quality of individual studies.",
          "tab:t11", H, R, r"p{3.6cm}p{3.0cm}p{2.2cm}p{1.8cm}X p{2.8cm}", 5, size=r"\scriptsize")


def t12v2():
    import make_tables as mt
    from add_grey_bib import GREY_KEYS
    keys = dict(GREY_KEYS, G14="powercell2025systemloss", G15="powerdivision2022ev", G16="cpd2024tariff", G17="tbs2026berc")
    g = pd.read_csv(ROOT / "data/grey/grey_literature.csv", dtype=str).fillna("")
    q = pd.read_csv(ROOT / "data/quality_appraisal.csv", dtype=str).set_index("id")
    status = {"G01": "Police count via newspaper; journalist estimate (Tk 4,000 crore)", "G02": "Ministerial statement in parliament",
              "G03": "Opinion (cited only as opinion)", "G04": "Utility and ministerial statements via newspaper",
              "G05": "Official estimate via newspaper", "G06": "Official data via newspaper (superseded by G14)", "G07": "Official data via newspaper",
              "G08": "Think-tank analysis; partly secondary", "G09": "Utility press statement", "G10": "Utility press statement",
              "G11": "Think-tank analysis of official data", "G12": "Multilateral note (historical)", "G13": "Multilateral evaluation (historical)",
              "G14": "Official statistics (primary)", "G15": "Government guideline (primary)", "G16": "Think-tank analysis",
              "G17": "Regulator committee figure via newspaper"}
    corro = {"G01": "Police count repeated by CPD and the Home Minister, who cite the same source; Tk figure not independently estimated",
             "G02": "Not independent of G01", "G03": "Not used for figures", "G04": "No metered data; CPD 750 MW cites a newspaper",
             "G05": "Official notes that accurate figures cannot be obtained", "G06": "Agrees with G14",
             "G07": "Agrees with G14 for FY2023-24; FY2024-25 figure has no primary source", "G08": "Several figures cite newspapers",
             "G09": "No published method for 5-7% NTL", "G10": "No published method for 5-7% NTL",
             "G11": "Consistent with official series", "G12": "Single estimate; old", "G13": "Consistent with long-run decline",
             "G14": "Agrees with G06, G07 and G11", "G15": "Primary text read", "G16": "Slides cite BERC gazettes and BPDB reports",
             "G17": "Final BERC order not seen"}
    H = ["Source", "Date", "Status of the claim", "Main claims used", "Corroboration", "AACODS score", "Ref."]
    R = []
    for _, r in g.iterrows():
        gid = r["grey_id"]
        R.append([f"{r['outlet']} ({gid})", r["date"], status[gid], r["key_facts"][:230] + ("..." if len(r["key_facts"]) > 230 else ""),
                  corro[gid], f"{float(q.loc[gid, 'score']):.2f}", keys[gid]])
    write("T12_grey", "Grey-literature sources: status of each claim, corroboration and AACODS appraisal (authority, accuracy, coverage, objectivity, date, significance; item scores in Supplementary S2). Primary government sources (G14, G15) replace newspaper reports where they exist.",
          "tab:t12", H, R, r"p{2.3cm}p{1.3cm}p{2.4cm}X p{3.0cm}p{1.5cm}p{1.6cm}", 6, size=r"\scriptsize")


if __name__ == "__main__":
    main()

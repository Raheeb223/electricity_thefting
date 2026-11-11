"""Phase 6: comparison tables T1-T9 as CSV (tables/*.csv) and LaTeX (tables/*.tex).
Every row carries at least one citation key. Content comes from data/extraction.csv,
data/grey/grey_literature.csv and scripts/drm.py (all traceable to sources read)."""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from drm import DRM  # noqa: E402

OUT = ROOT / "tables"
OUT.mkdir(exist_ok=True)


def esc(s):
    s = str(s)
    for a, b in (("$", r"\$"), ("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_"), ("~", r"$\sim$"), (">=", r"$\geq$"),
                 ("<", r"$<$"), (">", r"$>$")):
        s = s.replace(a, b)
    return s


X_WIDTH_CM = 3.4  # nominal width given to a bare X column when computing proportions


def proportional(spec):
    """Turn a spec of p{..cm}/X columns into tabularx X columns whose widths keep the
    same proportions but always sum to \\textwidth (so no table can overflow).
    Centred columns stay centred; all others are ragged-right."""
    spec = re.sub(r"\*\{(\d+)\}\{((?:[^{}]|\{[^{}]*\})*)\}", lambda m: m.group(2) * int(m.group(1)), spec)
    cols = []
    for m in re.finditer(r"(>\{[^}]*\})?p\{([\d.]+)cm\}|X", spec):
        if m.group(0) == "X":
            cols.append((X_WIDTH_CM, False))
        else:
            cols.append((float(m.group(2)), "centering" in (m.group(1) or "")))
    n, tot = len(cols), sum(w for w, _ in cols)
    out = []
    for w, centred in cols:
        align = r"\centering" if centred else r"\raggedright"
        out.append(r">{%s\arraybackslash\hsize=%.3f\hsize}X" % (align, n * w / tot))
    return "".join(out)


def write(name, caption, label, header, rows, spec, cite_col, size=r"\footnotesize", star=True, note=""):
    with open(OUT / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    # xltabular = tabularx that can break across pages (long tables in a single-column preprint).
    spec = proportional(spec)
    head = " & ".join(rf"\textbf{{{esc(h)}}}" for h in header) + r" \\"
    lines = [r"\begingroup", size, r"\renewcommand{\arraystretch}{1.12}", r"\setlength{\tabcolsep}{3pt}",
             rf"\begin{{xltabular}}{{\textwidth}}{{{spec}}}",
             rf"\caption{{{caption}}}\label{{{label}}} \\", r"\toprule", head, r"\midrule", r"\endfirsthead",
             rf"\multicolumn{{{len(header)}}}{{l}}{{\emph{{Table \ref{{{label}}} (continued)}}}} \\", r"\toprule",
             head, r"\midrule", r"\endhead", r"\bottomrule", r"\endlastfoot"]
    for r in rows:
        cells = []
        for i, c in enumerate(r):
            if i == cite_col:
                keys = [k.strip() for k in str(c).split(";") if k.strip()]
                cmd = r"\citet" if cite_col == 0 else r"\citealp"
                cells.append(cmd + "{" + ",".join(keys) + "}" if keys and keys[0] != "this" else "This review")
            else:
                cells.append(esc(c))
        lines.append(" & ".join(cells) + r" \\")
    lines += [r"\end{xltabular}"]
    if note:
        lines.append(rf"{{\scriptsize {esc(note)}\par}}")
    lines.append(r"\endgroup")
    (OUT / f"{name}.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(name, len(rows), "rows")


def t1():
    H = ["Review", "Type", "Scope", "LMIC or Bangladesh focus", "Governance", "Deployment analysis", "Studies reviewed", "Refs"]
    R = [
        ["glauner2017challenge", "Survey", "AI-based NTL detection; features, datasets, challenges", "Partial (emerging markets)", "No (label bias noted)", "No", "NS", "62"],
        ["papadimitriou2017non", "Overview + questionnaire", "Detection methods and regulation", "No (10 EE countries)", "Yes (regulatory)", "No", "NS", "11"],
        ["saeed2020detection", "Systematic", "AI-based NTL detection methods", "No", "No", "No", "NS", "123"],
        ["gupta2020detection", "Narrative", "LV power theft detection", "India", "Partial (factors, staff collusion)", "No", "NS", "124"],
        ["desouzasavian2021non", "Bibliometric", "NTL conference literature 1987-2019", "Partial", "No", "No", "392", "NA"],
        ["yan2022performance", "Survey", "Theft-detection performance, metrics", "No", "No", "No", "NS", "220"],
        ["xia2022detection", "Survey", "Smart-meter theft detection", "No", "Partial (socio-economic factors)", "No", "NS", "176"],
        ["badr2023review", "Narrative", "Data-driven fraud detection, privacy, robustness", "No", "No", "No", "NS", "107"],
        ["stracqualursi2023systematic", "Systematic", "Theft practices and AI detection", "No", "No", "Partial (utility integration)", "NS", "131"],
        ["kgaphola2024electricity", "Systematic", "Technology-based detection and prevention", "Partial (flags non-AMI gap)", "No", "No", "11", "66"],
        ["kim2024data", "Narrative", "Data-driven detection, datasets, generative AI", "No", "No", "No", "NS", "87"],
        ["sibiya2024electricity", "Narrative", "Theft impacts in Sub-Saharan Africa", "Sub-Saharan Africa", "Partial", "No", "NS", "42"],
        ["apata2026machine", "Systematic", "ML detection in smart grids", "No", "Partial (regulatory defensibility)", "Generic lifecycle framework", "90", "90"],
        ["labate2026comprehensive", "Tertiary (PRISMA)", "Reviews of energy theft detection", "No", "No", "No", "NS", "83"],
        ["this", "Systematic scoping review", "Detection, prevention, governance; E3W case study", "Bangladesh, with LMIC comparators", "Yes", "Structured heuristic (C1-C7) with evidence strength and certainty", "69 + 13 grey", "105"],
    ]
    write("T1_reviews", "Comparison of this review with existing reviews of electricity theft and NTL. Studies reviewed: as stated by the review (NS: not stated in the abstract or text read). Refs: reference-list length from Crossref metadata, or counted in the full text (Glauner et al.); NA: not available.",
          "tab:t1", H, R, r"p{2.6cm}p{2.2cm}X p{2.2cm}p{2.4cm}p{2.6cm}p{1.3cm}p{0.9cm}", 0, size=r"\scriptsize")


def t2():
    H = ["Year", "Entity", "Indicator", "Reported value", "Source"]
    R = [
        ["FY1991", "Bangladesh (national)", "Total system loss", ">40%", "adb2003cost"],
        ["FY1994", "Bangladesh (national)", "Total system loss", "37%", "adb2003cost"],
        ["2000", "Rural cooperatives (PBSs)", "System loss; bill collection", "13.9%; ~97%", "adb2003cost"],
        ["2000", "BPDB and DESA", "Losses; revenue collected for generated power", ">US$100 million/yr; 55% of generation", "lovei2000costs"],
        ["2001", "BPDB", "T&D loss", "24.9%", "adb2003cost"],
        ["2001", "DESA (Dhaka)", "T&D loss", "36.6%", "adb2003cost"],
        ["2001-02", "National (official series)", "Distribution; transmission; T&D loss", "23.92%; 4.05%; 27.97%", "powercell2025systemloss"],
        ["2009-10", "National (official series)", "Distribution; transmission; T&D loss", "13.49%; 3.08%; 15.73%", "powercell2025systemloss"],
        ["2015-16", "National (official series)", "Distribution; transmission; T&D loss", "10.96%; 2.63%; 13.10%", "powercell2025systemloss"],
        ["2019-20", "National (official series)", "Distribution; transmission; T&D loss", "8.73%; 2.91%; 11.23%", "powercell2025systemloss"],
        ["2022-23", "National (official series)", "Distribution; transmission; T&D loss", "7.65%; 3.07%; 10.33%", "powercell2025systemloss"],
        ["June 2023", "Bangladesh (national)", "T&D loss", "10.33% (33.57% in 1990)", "alam2024fixing"],
        ["2023-24", "National (official series)", "Distribution; transmission; T&D loss", "7.25%; 3.13%; 10.06%", "powercell2025systemloss"],
        ["2023-24", "Utilities (official series)", "Distribution loss", "DESCO 5.57%; DPDC 6.04%; BPDB 7.23%; WZPDCO 7.38%; REB 8.01%; NESCO 8.58%", "powercell2025systemloss"],
        ["2024-25", "National (BPDB data via newspaper; no primary source found)", "System loss", "10.13%", "bonikbarta2025power"],
        ["2025", "DESCO and DPDC (Dhaka)", "Distribution loss (officials)", "~5.5%", "islam2025banglatesla"],
        ["FY2027 (projection)", "National", "Distribution loss assumed by BERC technical committee (newspaper report)", "7.37% (7.38% in FY2025)", "tbs2026berc"],
        ["2025", "BPDB; DPDC", "Customer-level NTL (utility statements)", "5-7%", "bss2025pdb;bss2025dpdc"],
        ["Oct 2025", "BPDB", "Smart prepaid meters / consumers", "3,298,103 / ~4.2 million", "bss2025pdb"],
        ["Oct 2025", "DPDC", "Smart prepaid meters / consumers", "1,066,005 / 1,909,004", "bss2025dpdc"],
        ["2025", "DESCO Tongi 33/11 kV (simulation)", "Base-case substation loss", "12.12%", "alam2025optimizing"],
    ]
    write("T2_bd_losses", "Bangladesh utilities and reported loss figures over time. Definitions differ between sources (total system, T\\&D, distribution, customer-level NTL) and are not directly comparable.",
          "tab:t2", H, R, r"p{1.4cm}p{3.2cm}X p{3.6cm}p{3.4cm}", 4)


def t3():
    H = ["Modality", "Typical setting", "How it works", "Detection difficulty", "Evidence"]
    R = [
        ["Direct hooking of LV lines and poles", "Urban informal settlements; peri-urban; rural", "Unmetered wires hooked onto overhead lines or poles", "Medium: visible but quickly reconnected", "hossain2024transmission;sayem2020reducing;lovei2000costs"],
        ["Tapping for E3W charging garages", "Urban and peri-urban garages", "Mains or streetlight lines tapped; cables from poles; overnight use", "High: night-time, temporary, protected", "islam2025banglatesla;bonikbarta2026battery;mahmud2025integrating"],
        ["Off-meter charging behind an installed meter", "Garages with token connections", "Meter installed for compliance while most charging bypasses it", "High: meter reads look normal", "islam2025banglatesla"],
        ["Commercial use of residential connections", "Urban homes and garages", "Residential tariff used for commercial charging", "Medium: tariff misclassification", "tbs2026illegal;islam2025banglatesla;mahmud2025integrating"],
        ["Meter tampering and bypass", "Residential, commercial", "Tampered or bypassed meters reduce recorded energy", "High with monthly manual reads", "bss2025dpdc;bss2025pdb"],
        ["Collusive meter reading and billing", "All segments", "Readers under-record or arrange connections for payment", "Very high: corrupts records and labels", "lovei2000costs;hossain2024transmission;islam2025banglatesla"],
        ["Non-payment and arrears (not theft)", "Residential, public", "Bills issued but not paid", "Low: visible in accounts", "adb2003cost"],
    ]
    write("T3_modalities", "Electricity theft modalities documented for Bangladesh.", "tab:t3", H, R,
          r"p{3.0cm}p{2.6cm}X p{2.6cm}p{3.6cm}", 4)


def t4():
    H = ["Study", "Country", "Model", "Data", "Granularity", "Labels; imbalance", "Headline result", "Field"]
    R = [
        ["haramaini2026hybrid", "Indonesia", "Stacking (LightGBM, CatBoost, LR)", "2.36 M consumers, 30 months", "Monthly", "Real; 22.8:1, PR-AUC, stratified CV", "PR-AUC 0.776; field detection 72.0% vs 15.3% (rules)", "Yes"],
        ["taruna2025electricity", "Indonesia", "RF + KNN sequential filter", "450 VA postpaid households", "Monthly", "Real; NR", "Acc 0.89, Prec 0.83, Rec 0.98, F1 0.90", "Partial"],
        ["arisona2025classification", "Indonesia", "SVM (RBF)", "Industrial/business, 2019-2023", "Monthly", "Real; NR", "Balanced precision and recall", "Partial"],
        ["norouzi2025novel", "Iran", "XGBoost + SMOTE", "119,131 customers", "40-60 days", "Real; SMOTE", "Acc 99.7%, Prec 98.2%", "No"],
        ["orozcoceron2026comparing", "NR", "RF, MLP, LSTM, 1D-CNN", "4,000 customers, 864 thefts", "Monthly", "Real; undersampled", "Acc 0.685, AUC 0.748; one-third missed", "No"],
        ["ariasmarin2025methodological", "Ecuador", "CatBoost, LightGBM, XGBoost", "266,298 records", "Billing", "Real; balanced subset", "Acc 0.897, F1 0.894", "No"],
        ["saeed2019ensemble", "Pakistan", "Ensemble bagged trees", "MEPCO consumers", "Billing", "Real; NR", "Acc 93.1%", "Partial"],
        ["saqib2024deep", "Pakistan", "Lightweight DL", "Monthly readings", "Monthly", "NR; ROS/SMOTE", "Theft-class F1 0.91", "No"],
        ["massaferro2020fraud", "Uruguay", "Bayesian risk (economic return)", "UTE customers", "Monthly", "Real; cost-sensitive", "Higher economic return", "Partial"],
        ["barros2022maximizing", "Brazil", "Rotation Forest + XGBoost", "261,489 consumers", "Monthly", "Real; NR", "Inspection return up to 11.5x (338 inspections)", "Yes"],
        ["massaferro2022fraud", "Uruguay", "Multi-resolution DL", "UTE + synthetic set", "Monthly + 15 min", "Real; NR", "Beats single-resolution models", "No"],
        ["soleimaninasab2022effect", "Benchmark", "Bagging network", "Down-sampled public set", "Daily to monthly", "Real; NR", "Slow decline to weekly, sharp below", "No"],
        ["buzau2019detection", "Spain", "XGBoost", "Endesa C&I, ~57,000 inspections", "Smart meter", "Real; NR", "XGBoost best", "Yes"],
        ["zheng2018wide", "China", "Wide and deep CNN", "Realistic smart-meter data", "Daily", "NR", "Beats baselines", "No"],
        ["punmiya2019energy", "Benchmark", "Gradient boosting + features", "Public data, synthetic theft", "Daily", "Synthetic", "Lower FPR, higher DR", "No"],
        ["hu2019utilizing", "NR", "Semi-supervised multitask DL", "Real AMI data", "Interval", "Partial", "High performance (NR)", "No"],
        ["zhu2024deep", "China", "Deep active learning", "SGCC dataset", "Daily", "Few labels", "Lower labelling cost", "No"],
        ["liao2024sample", "China", "Sample adaptive transfer", "Multiple cities", "Daily", "Few labels", "MAP +18.83%, AUC +13.29%", "No"],
        ["altamimi2025how", "Public data", "Models trained on synthetic attacks", "Only real public theft set", "NR", "Real vs synthetic", "Large drop on real theft", "No"],
        ["menezes2026geospatial", "Brazil", "Imagery + vision + DBSCAN", ">10,000 inspected sites", "Imagery", "Real", "Accuracy 83.05%", "Yes"],
        ["gremes2024ntl", "France/Brazil", "U-Net on Sentinel-2", "Public imagery", "Imagery", "Segmentation", "IoU 0.92 train, 0.88 test", "No"],
        ["toledoorozco2021innovative", "Latin America", "k-means, neural networks", "CIS, GIS, socio-economic", "Billing", "NR", "Improved suspect identification", "Partial"],
    ]
    write("T4_datadriven", "Data-driven detection studies (Acc accuracy, Prec precision, Rec recall, DR detection rate, FPR false-positive rate; NR not reported in the text read). All rows except Haramaini et al. (2026) were extracted from the abstract; values are as reported by the authors and are flagged for full-text confirmation (read\\_level in the extraction sheet).",
          "tab:t4", H, R, r"p{2.5cm}p{2.0cm}p{2.3cm}p{2.4cm}p{2.2cm}p{2.2cm}X p{0.9cm}", 0, size=r"\scriptsize")


def t5():
    H = ["Study", "Technique", "Theft addressed", "Infrastructure needed", "Cost indication", "Evidence"]
    R = [
        ["biswas2020electricity", "Correlation of master-meter loss with consumer readings", "Nonlinear consumption manipulation", "Master meter + consumer meter series", "No training or sensors", "Real usage, synthetic attacks"],
        ["yang2022detection", "Covariance of area NTL with user data", "Group fixed-ratio (collusive) theft", "Gateway meter per area", "Low", "SGCC data + emulator"],
        ["jokar2016electricity", "Transformer meters + pattern classifier", "AMI theft", "Transformer meters, smart meters", "NR", "5,000 customers"],
        ["huang2013non", "State estimation + ANOVA", "Tampering, malfunction", "Transformer-level aggregation", "NR", "TPC feeder scenarios"],
        ["leite2018detecting", "Control chart + A* + GIS", "Cyber-tampering of meters", "Smart meters, GIS", "Cheaper than full IT security", "Real network"],
        ["messinis2019hybrid", "Voltage sensitivity + optimisation + SVM", "NTL in smart grids", "Topology, voltage data", "NR", "Scenarios"],
        ["henriques2020monitoring", "Technical-loss sensing + voltage drop", "LV theft location", "Temperature sensors near transformer", "Sensors", "Case network"],
        ["firoozi2022non", "Clustering + meter placement + load profiles", "Feeder NTL", "Few meters per feeder", "Lower than inspections", "Method"],
        ["kim2019detection", "Intermediate monitor meters + energy balance", "Tampering, malfunction, bypass", "Extra meters per unit network", "Added meters", "Simulation, >=95%"],
        ["binhalabi2019remote", "Transformer-area remote identification", "Feeder tapping, tampering", "Smart meters", "Described as low", "Simulation + HIL"],
        ["louw2019alternative", "Zero-sequence current", "Ground-surface illegal conductors", "Current sensing on LV backbone", "Discussed", "Lab + field soil tests"],
        ["ali2023prevention", "Low-cost smart meter + IoT", "Mixed theft", "Smart meters, cloud", "Economic design", "PESCO 15 km2 field"],
        ["khazaee2017distribution", "AMI pilots", "Residential, commercial theft", "AMI", "NR", "Field pilots"],
        ["depuru2010conceptual", "Harmonic injection", "Hooking", "Harmonic generator, filters", "Cost-benefit (India)", "Concept; unsafe"],
        ["sayem2020reducing", "Low-frequency (6-7 Hz) distribution", "Line tapping", "Converters at every meter", "NR", "Concept"],
        ["aryanezhad2019novel", "Unsuitable voltage to illegal loads", "Hook-line theft", "Supervision units", "NR", "Laboratory"],
    ]
    write("T5_network_hardware", "Network-based and hardware-based methods.", "tab:t5", H, R,
          r"p{2.4cm}X p{2.4cm}p{2.8cm}p{2.2cm}p{2.3cm}", 0, size=r"\scriptsize")


def t6():
    H = ["Dataset", "Country", "Consumers", "Resolution", "Labels", "Access", "Used by"]
    R = [
        ["SGCC realistic dataset (subset)", "China", "3,000 single-phase + 500 three-phase", "15 min, 285 days (2019)", "Benign; theft emulated", "NR in text read", "yang2022detection;zhu2024deep"],
        ["Real-world public theft dataset", "NR", "NR", "NR", "Real theft", "Public (the only one, per authors)", "altamimi2025how"],
        ["UTE customer data", "Uruguay", "Large (NR)", "Monthly and 15 min", "Real fraud", "Proprietary", "massaferro2020fraud;massaferro2022fraud"],
        ["Endesa C&I smart meters", "Spain", "All C&I customers; ~57,000 inspections", "Smart meter", "Real inspections", "Proprietary", "buzau2019detection"],
        ["PLN West Java", "Indonesia", "2.36 million", "Monthly, 30 months", "Real; 22.8:1", "Proprietary; aggregates on request", "haramaini2026hybrid"],
        ["PLN postpaid 450 VA", "Indonesia", "Segment of 27 million postpaid", "Monthly", "Real", "Proprietary", "taruna2025electricity"],
        ["Northern Iran utility", "Iran", "119,131", "40-60 days", "Real", "Proprietary", "norouzi2025novel"],
        ["Ecuador distributor", "Ecuador", "266,298 records", "Billing", "Real observations", "Proprietary", "ariasmarin2025methodological"],
        ["Brazilian utility", "Brazil", "261,489", "Monthly", "Real; 338 new inspections", "Proprietary", "barros2022maximizing"],
        ["Para inspection sites", "Brazil", ">10,000 sites", "Satellite imagery", "Real inspections", "Proprietary", "menezes2026geospatial"],
        ["Sentinel-2 imagery", "France, Brazil", "Area-level", "Satellite", "Segmentation masks", "Public imagery", "gremes2024ntl"],
        ["Dhaka prepaid payments", "Bangladesh", "Households (NR)", "Bills and recharges, 3 years", "None (payment)", "Not public", "rabbani2020does"],
    ]
    write("T6_datasets", "Datasets used by included studies. No public, labelled theft dataset from Bangladesh was found.",
          "tab:t6", H, R, r"p{2.7cm}p{2.0cm}p{2.6cm}p{2.0cm}p{2.2cm}X p{2.6cm}", 6, size=r"\scriptsize")


def t7():
    H = ["Intervention", "Setting", "Reported outcome", "Design", "Source"]
    R = [
        ["Smart prepaid meter replacement", "Ghana", "Reported consumption +13.2% after replacing tampered meters; no effect in lowest quartile", "Difference-in-differences", "otchereappiah2021impact"],
        ["Scaling up metering", "Nigeria", "1% more metering associated with 0.8% lower ATC&C loss", "Regression on regulatory data", "odje2021aggregated"],
        ["Prepaid metering", "Bangladesh (Dhaka)", "Fewer skipped bills; ~46% recharge monthly after switch", "Before-after payment data", "rabbani2020does"],
        ["Prepaid metering", "Bangladesh", "Higher revenue collection and lower system loss (values NR)", "Analytical study", "akand2019analytical"],
        ["Prepaid acceptance", "Bangladesh (WZPDCL, PBS)", "Reliability, cost perception and trust deficits limit acceptance", "Survey and official data", "purnota2026factors"],
        ["Rural cooperative model (PBS)", "Bangladesh", "Losses 13.9%, ~97% collection (2000)", "Programme evaluation", "adb2003cost"],
        ["Army takeover of distribution (1999)", "Pakistan", "NTL from theft fell significantly; theft by wealthy users found", "Case evidence", "lovei2000costs"],
        ["Service quality standards", "Pakistan (8 DISCOs)", "Service quality significantly reduces theft", "System GMM panel", "mirza2023impact"],
        ["Deterrence, efficiency wages, consumer reporting", "Developing countries", "Theft occurs when gains exceed expected penalty", "Principal-agent model", "jamil2019policy"],
        ["Regulatory NTL targets", "Brazil (41 utilities)", "ANEEL targets did not cut NTL; frontier model proposed", "Stochastic frontier", "leite2020stochastic"],
        ["Coordinated multi-stakeholder strategy", "Brazil", "Cultural acceptance of theft identified as key target", "28 expert interviews", "savian2022non"],
        ["Subsidies with equipment upgrades", "Brazil (favelas)", "Subsidies can reduce illegality when combined with upgrades", "Household econometrics", "mimmi2010econometric"],
        ["Community co-designed solutions", "Uganda (Kampala)", "Barriers: cost, connection process, trust; solutions co-designed", "Participatory action research", "kersey2025then"],
        ["E3W draft management guidelines; raids", "Bangladesh (Dhaka)", "48,136 illegal points identified; ~3,300 approved stations", "Police and utility data (news)", "islam2025banglatesla"],
        ["E3W registration and tracking (planned)", "Bangladesh", "Registration, licensing and digital tracking announced", "Government statement (news)", "tbs2026illegal"],
    ]
    write("T7_governance", "Governance and policy interventions with reported outcomes, Bangladesh and comparable countries.",
          "tab:t7", H, R, r"p{3.2cm}p{2.4cm}X p{2.6cm}p{2.6cm}", 4)


def t8():
    from drm import EQUITY, CAVEATS
    H = ["Method family", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "Ready", "Evid.", "Distributional risk"]
    R = []
    for name, c, e, keys, _ in DRM:
        R.append([name] + [str(x) for x in c] + [f"{sum(c) / 7:.1f}", str(e), EQUITY[name][0]])
    R.sort(key=lambda r: (r[0].startswith("Rule-based"), -float(r[8]), -int(r[9])))
    write("T8_drm", "Deployability Readiness Matrix for Bangladesh: a structured heuristic, not a validated ranking. Each cell scores fit with current Bangladeshi conditions: 3 fits now; 2 minor requirement; 1 substantial requirement; 0 not feasible without structural change. C1 data granularity; C2 meter type and AMI coverage; C3 cost per consumer; C4 labelled-data need; C5 privacy; C6 staff capacity; C7 robustness to collusion and institutional drivers. Ready is the unweighted mean of C1-C7. Evid. is evidence strength: 0 concept, 1 simulation or laboratory, 2 real data offline, 3 field-validated. Distributional risk is the risk of harming poor households or livelihoods if deployed without safeguards. Scores are the authors' judgements; rationale, caveats and evidence for every row are in Table~\\ref{tab:t10}.",
          "tab:t8", H, R, r"p{4.6cm}*{7}{>{\centering\arraybackslash}p{0.35cm}}>{\centering\arraybackslash}p{0.75cm}>{\centering\arraybackslash}p{0.65cm}>{\centering\arraybackslash}p{1.6cm}", -1, size=r"\scriptsize")
    rows = []
    for name, c, e, keys, why in DRM:
        rows.append([name, why, CAVEATS.get(name, ""), EQUITY[name][1], keys])
    with open(OUT / "T8_drm_rationale.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["method_family", "rationale", "caveat", "distributional_note", "evidence_keys"])
        w.writerows(rows)
    write("T10_drm_rationale", "Rationale, caveats and evidence for each row of the Deployability Readiness Matrix (Table~\\ref{tab:t8}). Citation keys inside the distributional notes are listed in the evidence column.",
          "tab:t10", ["Method family", "Rationale for the scores", "Caveat", "Distributional note", "Evidence"],
          [[r[0], r[1], r[2], re.sub(r" \(([a-z]+\d{4}[a-z]*)\)", "", r[3]),
            ";".join(dict.fromkeys(r[4].split(";") + re.findall(r"\(([a-z]+\d{4}[a-z]*)\)", r[3])))] for r in rows],
          r"p{2.6cm}X p{2.6cm}p{2.8cm}p{2.6cm}", 4, size=r"\scriptsize")


def t9():
    H = ["Gap", "Why it matters for Bangladesh", "Concrete direction", "Evidence"]
    R = [
        ["No public labelled theft dataset from Bangladesh", "Models cannot be trained or compared locally", "Utility-academic data trust; anonymised monthly bills with inspection outcomes", "rabbani2020does;altamimi2025how;glauner2017challenge"],
        ["Few field-validated detectors in non-AMI grids", "Offline accuracy does not show inspection yield", "Report hit rate per inspection and recovered energy in randomised field pilots", "haramaini2026hybrid;barros2022maximizing;orozcoceron2026comparing"],
        ["Synthetic attack validation", "Synthetic theft overstates performance", "Validate on inspection-confirmed cases; publish negative results", "altamimi2025how;punmiya2019energy"],
        ["Label bias from collusion", "Bribed inspectors mislabel thieves as honest", "Noise-robust learning; independent audit inspections", "glauner2017challenge;lovei2000costs;jamil2018electricity"],
        ["Prepaid vend data unused for detection", "Millions of prepaid meters produce recharge streams", "Detection models on recharge frequency and amount; tamper alarms", "bss2025pdb;bss2025dpdc;rabbani2020does"],
        ["No measured E3W charging energy", "Theft and demand estimates vary widely", "Metered sampling of garages; charger efficiency standards", "hossain2026measuring;chowdhury2026operational;mahmud2025integrating"],
        ["E3W charging outside the regulatory frame", "Illegal charging is the default option", "Legal definition, licensed hubs, charging tariff, smart chargers", "schloer2022how;khan2020e;islam2025banglatesla"],
        ["No evidence on Bangladeshi theft drivers", "Interventions cannot target causes", "District panel and household surveys on price, supply quality, trust", "razavi2019socio;wong2021perceptions;mirza2023impact"],
        ["Loss reporting mixes technical and non-technical loss", "NTL share is unknown", "Transformer metering and energy audits per feeder", "alam2025optimizing;henriques2020monitoring;firoozi2022non"],
        ["No regulatory loss-target design", "Utilities lack incentives", "Utility-specific benchmarked NTL targets in tariff orders", "leite2020stochastic;alam2024fixing"],
    ]
    write("T9_gaps", "Research gaps mapped to concrete future directions.", "tab:t9", H, R,
          r"p{3.4cm}p{3.6cm}X p{3.6cm}", 3)


def t11():
    """Summary of findings with certainty ratings (adapted from GRADE; see Methods 2.6).
    Start: prospective field or quasi-experimental = moderate; offline, observational or
    simulation = low; statements, news estimates or no study = very low. Downgrade one
    level each for indirectness (no Bangladeshi data), imprecision (single study) and
    risk of bias (abstract-only extraction or low appraisal), floor at very low."""
    H = ["Finding", "Evidence base", "Directness", "Certainty", "Main reasons", "Sources"]
    R = [
        ["The volume of electricity theft in Bangladesh is unknown; no source separates theft from technical loss", "Utility statements (5-7% customer-level NTL), newspaper estimates", "Bangladesh", "Very low", "Statements without published method; definitions differ", "bss2025pdb;bss2025dpdc;islam2025banglatesla"],
        ["Reported system loss fell from >40% (FY1991) to ~10% (FY2024-25)", "Multilateral evaluation; official data reported by newspapers and IEEFA", "Bangladesh", "Moderate (descriptive)", "Consistent across sources; definitions change over time", "adb2003cost;hossain2024transmission;bonikbarta2025power;alam2024fixing"],
        ["Illegal charging of E3Ws is widespread in Dhaka", "Police count via newspaper, utility and ministerial statements, think-tank slides, field surveys", "Bangladesh", "Low", "Several sources agree on occurrence; most are not independent", "islam2025banglatesla;bonikbarta2026battery;mahmud2025integrating;chowdhury2026operational"],
        ["The energy or revenue lost to E3W charging theft", "Newspaper estimate; one field survey with a measurement error", "Bangladesh", "Very low", "No metered data; estimates span orders of magnitude", "islam2025banglatesla;tbs2026illegal;hossain2026measuring"],
        ["ML on monthly billing data raises inspection yield over rules", "1 prospective field validation; 6 offline utility studies", "Indirect (Indonesia, Iran, Pakistan, Ecuador)", "Low", "Indirect; single field study; most extraction from abstracts", "haramaini2026hybrid;taruna2025electricity;orozcoceron2026comparing"],
        ["Cost-sensitive targeting raises the financial return of inspections", "1 field validation; 1 offline study", "Indirect (Brazil, Uruguay)", "Low", "Indirect; single field study", "barros2022maximizing;massaferro2020fraud"],
        ["Offline and synthetic-attack evaluations overstate field performance", "Evaluation study, survey, pattern across included studies", "Not country-specific", "Moderate", "Consistent across sources; mechanism understood", "altamimi2025how;glauner2017challenge;soleimaninasab2022effect"],
        ["Replacing tampered meters with smart prepaid meters reduces NTL", "1 quasi-experimental study; 1 regulatory-data regression", "Indirect (Ghana, Nigeria)", "Low", "Indirect; few studies", "otchereappiah2021impact;odje2021aggregated"],
        ["Prepaid metering improves payment discipline in Bangladesh", "1 before-after payment analysis; 1 analytical study", "Bangladesh", "Low", "Observational; collection, not theft", "rabbani2020does;akand2019analytical"],
        ["Transformer energy balance locates theft without labels", "Offline and simulation studies", "Indirect", "Very low", "No field evidence; Bangladeshi metering baseline unknown", "biswas2020electricity;yang2022detection;jokar2016electricity"],
        ["Theft rises with price and poor supply quality and falls with income and service quality", "Panel econometrics and surveys in 6 countries", "Indirect (South Asia, Africa)", "Low", "Observational; consistent direction", "jamil2014empirical;mirza2023impact;kankonde2025bridging;wong2021perceptions"],
        ["Institutional reform can cut losses (cooperatives, enforcement)", "Programme evaluation and case evidence", "Bangladesh (historical), Pakistan", "Low", "Old, uncontrolled evidence", "adb2003cost;lovei2000costs"],
        ["Regularising E3W charging reduces illegal charging", "No evaluation; design proposals only", "Bangladesh", "Very low", "No empirical study", "schloer2022how;khan2020e"],
        ["Active prevention hardware is safe and effective", "Concepts and laboratory tests", "Indirect", "Very low", "No field evidence; safety risks", "depuru2010conceptual;aryanezhad2019novel;sayem2020reducing"],
    ]
    write("T11_certainty", "Summary of findings with certainty of evidence for Bangladesh (approach adapted from GRADE; rules in Section~\\ref{sec:synth}). Certainty describes confidence that the finding holds for Bangladesh, not the quality of individual studies.",
          "tab:t11", H, R, r"p{3.6cm}p{3.0cm}p{2.2cm}p{1.8cm}X p{2.8cm}", 5, size=r"\scriptsize")


def t12():
    import pandas as pd
    from add_grey_bib import GREY_KEYS
    g = pd.read_csv(ROOT / "data" / "grey" / "grey_literature.csv", dtype=str).fillna("")
    q = pd.read_csv(ROOT / "data" / "quality_appraisal.csv", dtype=str).set_index("id")
    status = {"G01": "Police count via newspaper; journalist estimate (Tk 4,000 crore)", "G02": "Ministerial statement in parliament",
              "G03": "Opinion (policy options only)", "G04": "Utility and ministerial statements via newspaper",
              "G05": "Official estimate via newspaper", "G06": "Official data via newspaper", "G07": "Official data via newspaper",
              "G08": "Think-tank analysis; partly secondary", "G09": "Utility press statement", "G10": "Utility press statement",
              "G11": "Think-tank analysis of official data", "G12": "Multilateral note (historical)", "G13": "Multilateral evaluation (historical)"}
    corro = {"G01": "Police count repeated by CPD and the Home Minister, who cite the same source; Tk figure repeated in parliament, not independently estimated",
             "G02": "Not independent of G01", "G03": "Not used for figures", "G04": "No metered data; CPD 750 MW cites a newspaper",
             "G05": "Official notes that accurate figures cannot be obtained", "G06": "Consistent with G07 and G11",
             "G07": "Consistent with G06", "G08": "Several figures cite newspapers", "G09": "No published method for 5-7% NTL",
             "G10": "No published method for 5-7% NTL", "G11": "Consistent with official series (T\\&D definition)",
             "G12": "Single estimate; old", "G13": "Consistent with long-run decline"}
    H = ["Source", "Date", "Status of the claim", "Main claims used", "Corroboration", "AACODS score", "Ref."]
    R = []
    for _, r in g.iterrows():
        gid = r["grey_id"]
        R.append([f"{r['outlet']} ({gid})", r["date"], status[gid], r["key_facts"][:230] + ("..." if len(r["key_facts"]) > 230 else ""),
                  corro[gid], f"{float(q.loc[gid, 'score']):.2f}", GREY_KEYS[gid]])
    write("T12_grey", "Grey-literature sources: status of each claim, corroboration and AACODS appraisal (authority, accuracy, coverage, objectivity, date, significance; item scores in Supplementary S2). Audited or official data are distinguished from statements and estimates.",
          "tab:t12", H, R, r"p{2.3cm}p{1.3cm}p{2.4cm}X p{3.0cm}p{1.5cm}p{1.6cm}", 6, size=r"\scriptsize")


if __name__ == "__main__":
    for f in (t1, t2, t3, t4, t5, t6, t7, t8, t9, t11, t12):
        f()

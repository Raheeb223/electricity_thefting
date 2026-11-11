"""Deployability Readiness Matrix (DRM): method family x Bangladesh constraint C1-C7.

Scale (protocol section 3): each cell scores how well the method family fits the
CURRENT Bangladesh condition on that constraint.
  3 = works under present conditions with no new requirement
  2 = minor additional requirement (data cleaning, small staff training, modest cost)
  1 = substantial requirement (new metering layer, specialist team, labelled data at scale)
  0 = not feasible without a structural change (full AMI, topology models, legal change)
Readiness = mean of C1-C7 (0-3). Evidence strength E (0-3) is scored separately from
the included studies: 0 none/concept, 1 simulation or laboratory, 2 real data offline,
3 field-validated with reported yield. Deployability and effectiveness are kept apart
on purpose: a cheap method with no field evidence is not 'ready'.

Bangladesh conditions used for scoring (all cited in the manuscript, section 3):
monthly manual reading for postpaid consumers; large smart-prepaid fleets in BPDB and
DPDC (G09, G10) that record vend/recharge data, not load profiles; limited AMI;
documented collusion of meter readers and staff (lovei2000costs, glauner2017challenge);
inspection labels exist inside utilities but are not curated.

C1 data granularity, C2 meter type/AMI coverage, C3 cost per consumer, C4 labelled-data
need, C5 privacy, C6 staff capacity, C7 robustness to collusion and institutional drivers,
C8 safety and legal compliance (added in revision R9; 3 = lawful and safe under present
rules; 1 = needs a new legal route; 0 = creates safety risks or conflicts with the law).

Revision R9 rules:
- GATE: any constraint scored 0 -> "not deployable without structural change"; the mean
  (readiness) is reported only for families that pass the gate.
- EVIDENCE is split and computed from the manual evidence-map codes of the cited
  studies (scripts/drm_evidence.py): E_any = best level anywhere; E_bd = best level among
  studies set in Bangladesh or in a low- or middle-income country without AMI data
  (data granularity not smart-meter). Levels: 3 field validation, or programme
  evaluation with measured outcomes; 2 offline on real data; 1 simulation or laboratory;
  0 concept or descriptive only.
"""
DRM = [
    # family, C1..C7, E, evidence keys, rationale
    ("Rule-based inspection targeting (baseline)", [3, 3, 3, 3, 3, 3, 0, 3], 2,
     "haramaini2026hybrid;guerrero2018non",
     "Current practice; uses existing bills but relies on staff discretion, so collusion and low yield (15.3% in West Java) persist."),
    ("Supervised ML on monthly billing data", [3, 3, 3, 1, 2, 2, 1, 3], 3,
     "haramaini2026hybrid;guerrero2018non;gusmao2020customer;comapuig2016fraud;janthong2024feature;seepromting2026multiclass;oprea2022feature;glauner2017is",
     "Runs on data utilities already hold; needs curated inspection labels, which collusion can corrupt; field yield 72.0% vs 15.3% in one non-AMI utility."),
    ("Cost-sensitive inspection targeting", [2, 3, 3, 1, 2, 2, 1, 3], 3,
     "alharbi2021electricity",
     "Adds inspection cost and expected recovery to the ranking; initial utility testing of a cost-driven ranking on monthly data reached about 75% precision on new cases."),
    ("Deep learning on high-resolution AMI data", [0, 0, 1, 1, 1, 1, 2, 3], 2,
     "hu2020understanding",
     "Needs daily or sub-hourly profiles that most Bangladeshi consumers lack; in the evidence map, mostly evaluated offline on benchmark data."),
    ("Label-efficient learning (semi-supervised, active, transfer)", [1, 1, 2, 2, 1, 1, 2, 3], 2,
     "",
     "Reduces labelling cost and allows transfer between utility zones; no study of this family was retrieved in full for the synthesis."),
    ("Multi-resolution models for mixed meter fleets", [2, 2, 2, 1, 1, 1, 2, 3], 2,
     "",
     "Designed for utilities that replace meters in phases and hold both monthly and interval data; no study of this family was retrieved in full for the synthesis."),
    ("Energy balance and correlation at transformer/master meters", [2, 1, 2, 3, 2, 2, 3, 3], 2,
     "",
     "Needs a trusted meter at each distribution transformer synchronised with consumer reads; no labels; physical evidence resists collusion and detects group theft. No field study of this family was retrieved in full."),
    ("State estimation and load-flow methods", [1, 1, 1, 3, 2, 0, 3, 3], 1,
     "",
     "Requires accurate network topology and parameters plus engineering capacity rarely available at distribution level."),
    ("Monitoring meters and sensors (IMM, zero-sequence, remote ID)", [1, 1, 0, 3, 2, 1, 3, 2], 1,
     "",
     "Locates bypassing and hooking without labels but adds hardware per unit of network."),
    ("Active prevention hardware (harmonics, low frequency, voltage)", [3, 2, 0, 3, 3, 1, 3, 0], 0,
     "sayem2020reducing",
     "Damaging appliances or changing supply frequency raises safety and legal objections; no field evidence; not recommended."),
    ("Smart prepaid metering", [3, 2, 1, 3, 2, 2, 2, 3], 3,
     "odje2021aggregated",
     "Already at scale in BPDB and DPDC; in Nigeria each 1% increase in metered customers was associated with 0.8% lower ATC&C loss; bypassing upstream of the meter remains."),
    ("Geospatial and remote-sensing screening", [3, 3, 3, 2, 2, 2, 3, 2], 2,
     "",
     "Uses imagery, not meter data; no study of this family was retrieved in full; untested for E3W garages."),
    ("Socio-economic risk mapping", [3, 3, 3, 3, 3, 2, 1, 2], 1,
     "briseno2020factors;briseno2021factors;kasumba2025electricity",
     "Ranks districts or areas from public statistics; explanatory rather than operational evidence."),
    ("Auto-rickshaw charging regularisation (licensed hubs, tariff, smart chargers)", [3, 2, 2, 3, 3, 1, 1, 1], 0,
     "awal2019bangladesh",
     "Removes the motive by offering a legal, cheaper route; needs licensing and enforcement capacity; off-peak charging management has been proposed but not piloted."),
]
CONSTRAINTS = ["C1 Data granularity", "C2 Meter type / AMI", "C3 Cost per consumer", "C4 Labelled data",
               "C5 Privacy", "C6 Staff capacity", "C7 Collusion robustness", "C8 Safety and legal compliance"]

# Distributional (equity) risk of deploying each family in Bangladesh: author judgement
# grounded in the cited evidence (coping-strategy theft by poor households; large-volume
# theft by commercial and wealthy users; E3W livelihoods). Not part of readiness.
EQUITY = {
    "Rule-based inspection targeting (baseline)": ("Medium", "Discretionary targeting is exposed to collusion and selective enforcement (lovei2000costs)."),
    "Supervised ML on monthly billing data": ("Medium", "Low-consumption households may be over-flagged unless ranking weighs recoverable volume."),
    "Cost-sensitive inspection targeting": ("Low", "Directs inspections to large recoverable volumes."),
    "Deep learning on high-resolution AMI data": ("Medium", "Fine-grained data raise privacy concerns."),
    "Label-efficient learning (semi-supervised, active, transfer)": ("Medium", "Inherits label bias from past inspections (glauner2017challenge)."),
    "Multi-resolution models for mixed meter fleets": ("Medium", "As for supervised ML."),
    "Energy balance and correlation at transformer/master meters": ("Low", "Area-level evidence; flags unexplained loss before individuals."),
    "State estimation and load-flow methods": ("Low", "Network-level; no consumer profiling."),
    "Monitoring meters and sensors (IMM, zero-sequence, remote ID)": ("Low", "Physical detection of connections, not consumer profiling."),
    "Active prevention hardware (harmonics, low frequency, voltage)": ("High", "Damages property and creates safety risks for occupants."),
    "Smart prepaid metering": ("Medium", "Affordability and acceptance concerns for low-income households."),
    "Geospatial and remote-sensing screening": ("High", "Targets informal settlements where theft is often a coping strategy (yaguma2024don); pair with regularisation."),
    "Socio-economic risk mapping": ("High", "Area profiling by poverty indicators can stigmatise poor districts."),
    "Auto-rickshaw charging regularisation (licensed hubs, tariff, smart chargers)": ("Low", "Offers a legal route and protects livelihoods if introduced before enforcement (sakib2024banglateslas)."),
}
# Evidence caveats shown with the matrix (directness and baseline gaps).
CAVEATS = {
    "Supervised ML on monthly billing data": "Largest field test in one Indonesian utility; none from Bangladesh.",
    "Cost-sensitive inspection targeting": "Initial results from one utility.",
    "Smart prepaid metering": "Effect on theft in Bangladesh not measured; evidence from one regulatory panel (Nigeria).",
    "Energy balance and correlation at transformer/master meters": "Transformer-metering baseline in Bangladesh unknown.",
    "Geospatial and remote-sensing screening": "No study retrieved in full; untested for E3W garages.",
    "Auto-rickshaw charging regularisation (licensed hubs, tariff, smart chargers)": "No field evaluation.",
    "Active prevention hardware (harmonics, low frequency, voltage)": "Not recommended: safety and legal risks.",
    "Rule-based inspection targeting (baseline)": "Reference only: current practice.",
}


# C8 rationale (Supplementary S3)
C8_RATIONALE = {
    "Active prevention hardware (harmonics, low frequency, voltage)": "Deliberately degrades supply to the consumer (harmonic injection, frequency change); damages appliances and creates safety risk; no lawful basis identified. Score 0 (fails the gate).",
    "Auto-rickshaw charging regularisation (licensed hubs, tariff, smart chargers)": "The Power Division EV Charging Guideline (2022, sec. 5.1) covers only BRTA-authorised two- and three-wheelers; most battery three-wheelers are unregistered, so a new legal route is needed before licensed charging can reach them. Score 1.",
    "Monitoring meters and sensors (IMM, zero-sequence, remote ID)": "Installation on live low-voltage lines needs trained crews and safety procedures. Score 2.",
    "Geospatial and remote-sensing screening": "Targeting individual buildings from imagery needs a clear legal basis and due process before inspection. Score 2.",
    "Socio-economic risk mapping": "Area profiling by poverty indicators raises non-discrimination concerns. Score 2.",
}
DEFAULT_C8 = "Uses existing utility data or routine utility works; lawful and safe under present rules. Score 3."

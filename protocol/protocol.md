# Review protocol

**Title (working).** Deployable countermeasures against electricity theft in
Bangladesh: a PRISMA 2020 systematic review of detection, prevention and governance
approaches.

**Reporting standard.** PRISMA 2020 (statement, checklist, flow diagram).
**Protocol version.** 1.1, 2026-11-10 (v1.0 the same day; v1.1 adds section 2.1). Later amendments are listed in section 11 and reported in the Methods section.
**Registration.** Not registered. PROSPERO accepts only health-related reviews.

---

## 1. Research questions

**Central question.** Which electricity-theft detection and prevention approaches are
realistically deployable in Bangladesh, given its metering infrastructure, data
availability, institutional structure and socio-economic drivers, and what gaps remain?

| ID | Question | Main evidence type |
|---|---|---|
| RQ1 | What are the forms, scale and drivers of electricity theft in Bangladesh? | Empirical studies, case studies, grey literature |
| RQ2 | What detection approaches exist (data-driven, network/state-estimation, hardware/meter, hybrid) and how do they perform? | Method studies with quantitative evaluation |
| RQ3 | What prevention, governance and policy interventions have been tried in Bangladesh and comparable countries, with what results? | Policy and empirical studies, grey literature |
| RQ4 | How well does each approach fit Bangladesh's constraints? | Synthesis of RQ1–RQ3 evidence |
| RQ5 | What research and policy roadmap follows? | Synthesis |

**Bangladesh constraints used in RQ4** (the columns of the Deployability Readiness
Matrix): C1 data granularity available; C2 meter type and AMI coverage; C3 cost per
consumer; C4 need for labelled theft data; C5 privacy and data governance; C6 utility
staff and analytics capacity; C7 robustness to collusion and institutional drivers.

## 2. Eligibility criteria

### Inclusion

| Code | Criterion |
|---|---|
| I1 | Peer-reviewed journal article or full conference paper in a Scopus- or Web of Science-indexed venue; or eligible grey literature (section 5) |
| I2 | Published 1 January 2010 to the search date (2026) |
| I3 | English. Bangla allowed for grey literature only |
| I4 | Subject is theft or non-technical loss of electricity in distribution networks (residential, commercial, industrial, agricultural consumers); or, for the focus theme, the charging load, metering or regulation of battery-powered rickshaws/easy-bikes where unmetered or illegal charging is discussed |
| I5 | Contributes to at least one RQ: (a) documents forms, scale or drivers of theft; (b) proposes and quantitatively evaluates a detection method; (c) describes a prevention, governance or policy intervention with reported outcomes or a structured assessment |

### Exclusion

| Code | Criterion |
|---|---|
| E1 | Off topic: false-data-injection or cyber attacks on transmission/state estimation without a consumer-theft framing; gas or water theft; "NTL" meaning night-time lights; technical-loss-only studies |
| E2 | Method proposal without any quantitative evaluation |
| E3 | Non-English academic literature |
| E4 | Abstract-only records, posters, editorials, theses, book chapters without peer review; arXiv preprints that have a peer-reviewed version (the peer-reviewed version is used) or that are not peer reviewed (used only in the gap check, not as core evidence) |
| E5 | Venue not indexed in Scopus or Web of Science, or on a predatory-journal list |
| E6 | Duplicate or a shorter version of an included study by the same authors |
| E7 | Full text not obtainable and the abstract is insufficient for extraction |

### Reference budget and tightening rule

Target: 60–75 included studies, about 100 references in total. If more than 75 studies
pass full-text screening, these rules are applied in order, and the number removed at
each step is reported in the PRISMA diagram as "excluded: tightened criteria":

1. **Always kept:** studies with Bangladesh data or a Bangladesh setting; governance and
   policy studies from LMICs; public-dataset papers.
2. **Data-driven method studies** must additionally meet all of: (i) real (not purely
   simulated) consumption data; (ii) at least two metrics beyond accuracy, or AUC;
   (iii) journal in SJR Q1/Q2 or a conference by IEEE/ACM/IET.
3. If still above 75, keep the highest quality-appraisal scores within each approach
   family, keeping every family represented in proportion to its share before tightening.


### 2.1 Tightening rule as applied (protocol v1.1, 2026-11-10)

Title/abstract screening retained 1,644 records, far above the budget of 60-75
included studies. The rule in "Reference budget and tightening rule" was made
operational as follows, before full-text retrieval, using title, abstract and
venue only. Records were assigned to one of six evidence pools, and within each pool
selected in this order: (1) Bangladesh setting or data; (2) low- and middle-income
country (LMIC) setting with real utility data; (3) data at monthly/billing or other
low resolution, or from conventional (non-smart) meters; (4) evidence on evaluation
validity (label bias, leakage, synthetic attacks), label scarcity, cost or field
deployment; (5) journal tier and citations per year (as a tie-breaker only).

| Pool | Selected | Purpose |
|---|---|---|
| P1 Bangladesh and electric three-wheeler charging | 16 | RQ1, RQ4 |
| P2 Governance, drivers and interventions in LMICs | 19 | RQ1, RQ3 |
| P3 Data-driven detection (5 seminal benchmarks + 12 Bangladesh-constraint + 5 validity/label studies) | 22 | RQ2, RQ4 |
| P4 Network/state-estimation methods | 7 | RQ2, RQ4 |
| P5 Hardware/meter-based methods | 6 | RQ2, RQ4 |
| P6 Hybrid, cost and deployment studies | 5 | RQ3, RQ4 |

Exclusion codes at this stage: T1 = data-driven study on generic smart-meter or
benchmark data without a Bangladesh-constraint contribution (n = 867); T2 = eligible
but ranked below the pool cut-off (n = 640); T4 = review not needed beyond the
Table T1 set (n = 43). Nineteen reviews are kept as background for Table T1. The
selection lists are fixed in `scripts/apply_tightening.py`.

Consequence for interpretation: the review does not claim to synthesise every
detection-algorithm paper; the generic machine-learning literature is represented
through 19 prior reviews and 5 seminal studies, and the synthesis concentrates on
evidence that bears on deployability in Bangladesh. This is stated as a limitation.

## 3. Information sources

| Source | Role | Why |
|---|---|---|
| OpenAlex API | Main database | Free, no key, broad open index of journals and conferences, includes open-access locations |
| Crossref API | Second database, DOI verification | Registry of DOIs for nearly all publishers |
| Semantic Scholar API | Third database | Strong computer-science and IEEE conference coverage |
| arXiv API | Preprints | Machine-learning work often appears here first; used for gap check and to find peer-reviewed versions |
| Scopus / Web of Science exports (optional) | Merged if the author adds them to `data/raw_exports/` | Curated indexes; improve completeness |
| Backward/forward citation chasing | From included reviews and key studies (OpenAlex `referenced_works` / `cited_by`) | Finds studies missed by keywords |
| Grey literature | Section 5 | Bangladesh figures and policy outcomes are mostly outside journals |

Google Scholar is not used (no API, scraping not allowed).

## 4. Search strategy

### 4.1 Concept blocks

**Block A, theft:**
```
"electricity theft" OR "energy theft" OR "power theft" OR "electricity pilferage"
OR "non-technical loss*" OR "nontechnical loss*" OR "non technical loss*"
OR "commercial loss*" OR "meter tamper*" OR "meter bypass" OR "illegal connection*"
OR "illegal hook*" OR "electricity fraud" OR "energy fraud"
```
Bare "NTL" is not used on its own because it retrieves night-time-light remote-sensing
studies. It is accepted only together with an electricity term.

**Block B, countermeasures:**
```
detect* OR prevent* OR "machine learning" OR "deep learning" OR classif*
OR "anomaly detection" OR "smart meter*" OR "advanced metering" OR "state estimation"
OR observer OR "prepaid meter*" OR prepayment OR governance OR policy OR regulat*
OR corruption OR enforcement OR inspection
```

**Block C, regional:**
```
Bangladesh OR "South Asia" OR India OR Pakistan OR Nepal OR "Sri Lanka" OR Brazil
OR Africa OR "developing countr*" OR "low-income" OR "middle-income" OR "emerging econom*"
```

**Block D, Bangladesh distribution performance:**
```
Bangladesh AND electric* AND ("system loss*" OR "distribution loss*" OR "prepaid meter*"
OR "smart meter*" OR BPDB OR BREB OR DPDC OR DESCO OR WZPDCL OR NESCO OR BERC)
```

**Block E, battery-powered rickshaw and easy-bike charging (focus theme):**
```
("easy bike" OR "easy-bike" OR "battery rickshaw" OR "battery-run rickshaw"
OR "battery-operated rickshaw" OR "battery-powered rickshaw" OR "electric rickshaw"
OR "e-rickshaw" OR "electric three-wheeler" OR "electric auto-rickshaw" OR "auto-rickshaw"
OR "battery-driven" OR "light electric vehicle*")
AND (charg* OR electricity OR grid OR "power consumption" OR theft OR "illegal connection*")
```
Battery-powered three-wheelers (locally "easy-bikes", colloquially also called
"Tesla") are charged at garages and homes, often through illegal or unmetered
connections. This theme is analysed as a distinct theft modality because it is a
growing, mobile, night-time load that standard consumer-level detection does not
target. Studies from India (e-rickshaws), Nepal and other LMICs are included for
comparison. The colloquial name is used in the manuscript only if a source records it.

### 4.2 Final strings

| ID | String | Purpose |
|---|---|---|
| S1 | A AND B | Global detection and prevention literature (RQ2, RQ3) |
| S2 | A AND C | Regional and LMIC literature (RQ1, RQ3) |
| S3 | D | Bangladesh-specific evidence (RQ1, RQ4) |
| S4 | E AND (Bangladesh OR India OR Nepal OR "South Asia" OR "developing countr*") | Electric-rickshaw charging load and theft (RQ1, RQ3, RQ4) |

**Scopus syntax (optional manual export):**
```
TITLE-ABS-KEY(("electricity theft" OR "energy theft" OR "power theft" OR "electricity pilferage"
OR "non-technical loss*" OR "nontechnical loss*" OR "non technical loss*" OR "meter tamper*"
OR "meter bypass" OR "illegal connection*" OR "electricity fraud" OR "energy fraud")
AND (detect* OR prevent* OR "machine learning" OR "deep learning" OR classif*
OR "anomaly detection" OR "smart meter*" OR "advanced metering" OR "state estimation"
OR observer OR "prepaid meter*" OR prepayment OR governance OR policy OR regulat*
OR corruption OR enforcement OR inspection))
AND PUBYEAR > 2009 AND (LIMIT-TO(LANGUAGE, "English"))
```
Web of Science: same terms in `TS=(...)`, publication years 2010–2026.

### 4.3 Adaptation for the free APIs

The free APIs do not accept nested Boolean queries with wildcards. Each string is run
as a set of short phrase queries (every Block A phrase combined with each Block B or C
term group), searching title and abstract. All raw responses are saved with the query
and date in `data/raw_api/`. Records are then filtered locally with the full Boolean
logic as regular expressions over title, abstract and keywords, so the effective
logic matches the strings above. Scripts: `scripts/search_main.py`,
`scripts/dedupe.py`.

### 4.4 Deduplication

1. Exact match on lower-cased DOI.
2. For records without a DOI, or with different DOIs: normalised title (lower case,
   letters and digits only) with fuzzy ratio ≥ 95 and the same year ±1.
3. Conference and journal versions of the same study are linked at full-text stage
   (E6).

## 5. Grey literature

Sources: Bangladesh Power Development Board (BPDB) annual reports; Bangladesh Rural
Electrification Board (BREB); Power Division (Ministry of Power, Energy and Mineral
Resources); Bangladesh Energy Regulatory Commission (BERC) orders; distribution
companies (DPDC, DESCO, WZPDCL, NESCO); World Bank, Asian Development Bank, ESMAP, IEA
reports; Transparency International Bangladesh (TIB); national newspapers (The Daily
Star, The Business Standard, Prothom Alo, The Financial Express).

Rules: each item is labelled `grey` in the extraction sheet with URL and access date;
appraised with the AACODS checklist (Authority, Accuracy, Coverage, Objectivity, Date,
Significance); news reports are used only for facts not available from official
sources and are flagged as such. Grey literature stays below 15% of all references.

## 6. Selection process

1. Title/abstract screening of every deduplicated record against I1–I5 and E1–E6,
   with decision and reason code logged in `data/screening.csv`. Screening is done by
   an AI research assistant (large language model) under the author's supervision,
   using written criteria. This is disclosed in Methods and in the generative-AI
   declaration.
2. Self-audit: a random 10% sample (fixed seed) is screened a second time
   independently, blind to the first decision. Agreement and Cohen's kappa are
   reported. If agreement is below 90%, the criteria wording is revised and all
   records are re-screened.
3. Full texts of included records are retrieved (open access first), and full-text
   screening is logged with exclusion reasons. Unobtainable texts go to
   `data/missing_fulltext.csv`.

## 7. Data extraction

Fields in `data/extraction.csv`: id, citation_key, doi, year, venue, venue_quartile,
country_region, study_type, theft_type_addressed, approach_family, specific_method,
dataset, data_granularity, labelled_data, class_imbalance_handling, metrics_reported,
real_world_deployment, cost_information, bangladesh_relevance_notes, limitations,
read_level, grey_url, access_date.

`read_level` records whether the abstract or full text was read. Claims that depend on
numbers or method details are only made from full-text-level records.

## 8. Quality appraisal

Every included study gets one score on a 0–1 scale (sum of items ÷ maximum). Each item
is scored 1 (yes), 0.5 (partly or unclear) or 0 (no). Bands: high ≥ 0.75, medium
0.50–0.74, low < 0.50. Scores are used to weight the narrative synthesis and in the
tightening rule; no study is excluded for low quality alone.

### Rubric M: detection-method studies (8 items)

| Item | Question |
|---|---|
| M1 | Is the dataset described (source, size, period, granularity)? |
| M2 | Are theft labels real (inspection-confirmed), rather than only synthetic injection? |
| M3 | Is class imbalance handled, and are imbalance-robust metrics reported (precision, recall, F1, AUC)? |
| M4 | Is the validation protocol sound (held-out test or cross-validation, no leakage across consumers or time)? |
| M5 | Is the method compared with reasonable baselines? |
| M6 | Is there field validation or real deployment? |
| M7 | Are code or data available? |
| M8 | Are limitations and costs discussed? |

### Rubric E: empirical, case and policy studies (6 items, adapted from MMAT/CASP)

| Item | Question |
|---|---|
| E-1 | Is the research question clear? |
| E-2 | Are data sources appropriate and described? |
| E-3 | Is the analysis method appropriate for the question? |
| E-4 | Are outcomes measured, with a baseline or comparison? |
| E-5 | Are confounders or alternative explanations considered? |
| E-6 | Are limitations and transferability discussed? |

### Rubric G: grey literature (AACODS, 6 items)

Authority, Accuracy, Coverage, Objectivity, Date, Significance.

Reviews included for Table T1 are not scored; they are characterised on scope,
systematic method, LMIC focus, governance coverage, deployability analysis and
reference count.

## 9. Synthesis

- **Narrative synthesis** organised by the taxonomy (theft modality × countermeasure
  family), critical rather than study-by-study.
- **Quantitative description:** publications per year by family, countries, dataset
  usage, reported metrics by family. Metrics from different datasets are not pooled
  or treated as directly comparable; no meta-analysis is attempted because datasets,
  labels and metrics differ.
- **Deployability Readiness Matrix:** each method family scored 0–3 on constraints
  C1–C7 (0 = not feasible now, 1 = feasible only with major investment, 2 = feasible
  with moderate adaptation, 3 = feasible with current infrastructure). Each cell is
  justified with citations in Table T8.

## 10. Target journal

Energy for Sustainable Development (Elsevier).

## 11. Amendments

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.1 | 2026-11-10 | Section 2.1 added: a tightening rule that capped the number of included studies. | Keep the review within a reference budget. |
| 1.2 | 2026-11-11 | Two-tier design: every eligible record is coded in a systematic evidence map; an in-depth synthesis covers all eligible studies that meet scope criteria P1-P6 (Bangladesh; E3W charging; field validation in any country; monthly data with real labels in LMICs; governance with measured outcomes in LMICs; empirical drivers in LMICs). Replaces the cap of v1.1. | A cap chosen by venue or citations could bias the synthesis; scope criteria use setting and evidence type only. |
| 1.3 | 2026-11-11 | The in-depth synthesis is restricted to studies whose full text could be retrieved and read. Studies not retrieved stay in the evidence map with abstract-level codes and are not cited for their results. | Findings and extracted values must rest on full texts; several publishers refused automated access. |
| 1.3 | 2026-11-11 | Evidence strength in the Deployability Readiness Matrix is computed only from studies read in full. | Consistency with the full-text rule. |

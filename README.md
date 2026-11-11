# Electricity theft and battery auto-rickshaw charging in Bangladesh: data and code

This repository holds the data, code and outputs behind the systematic scoping review
*Electricity theft and battery auto-rickshaw charging in Bangladesh: an evidence map and
deployability assessment of countermeasures* (submitted to *Energy for Sustainable
Development*). The manuscript itself is not included.

## The review in brief

- **Evidence map.** 12,041 records were retrieved from OpenAlex, Semantic Scholar,
  Crossref and arXiv (10 November 2026). After deduplication and screening, all 1,659
  eligible records were coded from their titles and abstracts: country, data granularity,
  label source, validation level, relevance to battery auto-rickshaw (E3W) charging, and
  measured intervention outcomes.
- **In-depth synthesis.** Scope criteria P1-P6 (Bangladesh; E3W charging; field
  validation; monthly data with real labels in low- and middle-income countries;
  governance with measured outcomes; drivers of theft) selected 116 eligible studies.
  The 30 whose full text could be retrieved were read in full and synthesised. The other
  86 remain in the evidence map and are listed in `data/synthesis_not_retrieved.csv`.
- **Deployability Readiness Matrix.** 14 countermeasure families scored 0-3 on eight
  Bangladeshi constraints, with a gate rule, evidence strength computed from studies read
  in full, weight sensitivity and a 10,000-draw score-perturbation analysis.
- **Reporting.** PRISMA-ScR, with a PRISMA 2020 flow diagram; certainty rated with an
  approach adapted from GRADE.

Screening, evidence-map coding, full-text extraction and matrix scoring were carried out
with an AI-assisted process, as described in the article's Methods and its declaration on
generative AI. Each extracted value carries a page number and a supporting quote, and
`scripts/verify_extraction.py` checks every one of them against the PDF text. No
independent human re-check was completed; blind templates for such a check are listed
below.

## Repository layout

| Path | Contents |
|---|---|
| `protocol/` | Review protocol with its amendments (section 11) and the PRISMA checklist |
| `data/raw_api/search_log.txt` | Query log with retrieval times |
| `data/records_all.csv`, `data/records_dedup.csv` | Retrieved and deduplicated records (bibliographic fields only; abstracts are not redistributed) |
| `data/screening.csv`, `data/screening_batches/` | Title and abstract decisions with reason codes, and the decision files |
| `data/evidence_map_coded_manual.csv`, `data/evidence_map_batches/` | Evidence-map codes for all eligible records |
| `data/priority_synthesis_B.csv` | Studies meeting the scope criteria |
| `data/venue_audit/` | Venue audit against the Scopus source list (November 2024) with OpenAlex ISSN recheck |
| `data/synthesis_eligible.csv`, `data/synthesis_set.csv`, `data/synthesis_not_retrieved.csv` | Eligible, synthesised and not-retrieved studies |
| `data/extraction_ft.csv`, `data/extraction_ft_verification.csv` | Page-referenced full-text extraction and its mechanical check |
| `data/fulltext_overrides.csv`, `data/fulltext_exclusions.csv` | Code changes and exclusions made after full-text reading |
| `data/fulltext_*_log.csv`, `data/fulltext_stopped_hosts.txt` | Full-text retrieval logs |
| `data/quality_appraisal.csv` | Appraisal scores (rubrics M, E and AACODS) |
| `data/grey/` | Grey-literature register and primary-source notes |
| `data/drm_v2.csv`, `data/drm_uncertainty_v2.csv`, `data/drm_sensitivity.csv` | Deployability matrix, score uncertainty and weight sensitivity |
| `data/archive/` | Superseded outputs from earlier rounds, kept for traceability |
| `refs/` | Bibliography (`references.bib`, `grey.bib`), record-to-key map and reference verification reports |
| `tables/`, `figures/` | Tables (CSV and LaTeX) and figures of the article |
| `scripts/` | All code |

Figure and table files map to the article as follows: `fig1_prisma_flow` = Fig. 1,
`fig_map` = Fig. 2, `fig7_taxonomy` = Fig. 3, `fig6_deployability_matrix` = Fig. 4;
`T1_reviews` = Table 1, `T2_bd_losses` = Table 2, `T3_modalities` = Table 3,
`T12_grey` = Table 4, `T4_field_detection` = Table 5, `T11_certainty` = Table 6,
`T8_drm` = Table 7, `T10_drm_rationale` = Table 8, `T9_gaps` = Table 9.

## Reproducing the analysis

Python 3.11 or later.

```
pip install -r requirements.txt
mkdir manuscript                      # make_numbers.py writes manuscript/numbers.tex
python scripts/apply_scope_b.py --variant N1 --c6
python scripts/venue_audit.py
python scripts/build_synthesis_set.py
python scripts/evidence_map_stats.py
python scripts/drm_evidence.py
python scripts/drm_sensitivity.py
python scripts/make_numbers.py
python scripts/make_prisma_v2.py
python scripts/make_map_figure.py
python scripts/make_drm_figure_v2.py
python scripts/make_tables_v3.py
```

`venue_audit.py` needs the public Scopus source title list (November 2024), available
from Elsevier, saved as `data/venue_audit/scopus_title_list_2024-11.xlsx`. The extraction
check (`scripts/verify_extraction.py`) and the full-text reader (`scripts/ft_view.py`) need
the PDFs in `data/fulltext/`. These are copyrighted and are not shared; obtain them from
the publishers using the DOIs in `data/synthesis_set.csv`. The search and retrieval
scripts (`search_main.py`, `fetch_fulltext_*.py`) query live services, so their results
change over time; the logs record what was retrieved and when.

## Verification templates

Blind templates for checking the AI-assisted steps are distributed with the article's
supplementary material (S9): a stratified 20% sample of screening decisions, a 10% sample
of evidence-map codes, all extracted values, and a second-rater form for the
deployability matrix.

## Licence

Code: MIT licence (`LICENSE`). Data, tables and figures: Creative Commons Attribution 4.0
International (CC BY 4.0). Bibliographic metadata come from OpenAlex (CC0), Crossref,
Semantic Scholar and arXiv.

## Citation

Please cite the article once it is published. Citation details will be added here.

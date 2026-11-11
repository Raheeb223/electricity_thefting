"""Phase 4: write data/extraction.csv and data/quality_appraisal.csv.

Coding was done by reading each record's abstract (data/screening_batches/
extraction_abstracts.txt) and, for the 9 records with an open-access PDF, the full text
(data/fulltext_text/). Nothing here is from memory. Where the abstract does not report
a field, the value is 'NR' (not reported in the text read).

Quality items: 1 = yes, 0.5 = partly or unclear from the text read, 0 = no.
Abstract-level scores are provisional (protocol section 8).
"""
import csv
from pathlib import Path

import pandas as pd

from add_grey_bib import GREY_KEYS

ROOT = Path(__file__).resolve().parents[1]
FULLTEXT = {"R00480", "R00854", "R00953", "R01432", "R02139", "R02234", "R02473", "R02931", "R03062"}

# rid | country_region | study_type | theft_type | family | specific_method | dataset |
# granularity | labelled | imbalance | metrics | deployment | cost | bd_note | limitations
ROWS = r"""
R00176|Ecuador|method (empirical ML)|consumer fraud (meter/consumption)|DD-ML|CatBoost, LightGBM, XGBoost with grid search|utility records, 266,298 records, 15,013 fraud observations|monthly bill (NR exact)|Y|undersampling to balanced set (27,374)|accuracy 0.897, F1 0.894 (CatBoost)|N|computational cost compared|non-AMI utility data comparable to BD postpaid billing|balanced test set inflates accuracy; no field validation
R00311|global (public dataset)|method (evaluation study)|consumption manipulation (synthetic vs real)|DD-ML|ML detectors trained on synthetic attack models|only real-world public theft dataset plus synthetic injections|NR|Y|NR|performance drop on real theft|N|NR|warns BD utilities against models validated only on synthetic attacks|single public real dataset
R00337|Latin America|method (data analytics)|measurement-system errors and theft|DD-ML|k-means, neural networks, multivariate analysis with CIS/GIS/socio-economic data|utility CIS + GIS + socio-economic data|monthly bill (NR exact)|NR|NR|NR (improved identification probability)|Partial|NR|designed for utilities with low smart-meter penetration, as in BD|abstract gives no metrics
R00365|Indonesia|method (empirical ML)|household theft (subsidised 450 VA)|DD-ML|RF + KNN sequential filtering for target-operation lists|PLN postpaid traditional-meter customers, 450 VA segment|monthly bill|Y|NR|accuracy 0.89, precision 0.83, recall 0.98, F1 0.90, AUC 0.89|Partial|NR|closest analogue to BD subsidised lifeline tariff with traditional meters|no reported field yield
R00430|Indonesia|method (empirical ML)|industrial/business theft|DD-ML|SVM (RBF) vs LR, DT, NB|PLN postpaid conventional meters, 30 units, 2019-2023, up to 6,600 VA|monthly bill|Y|NR|precision/recall balanced (values NR in abstract)|Partial|confirmed theft losses about IDR 19 billion|industrial/commercial theft relevant to BD urban utilities|metric values not in abstract
R00431|Iran|method (empirical ML)|consumer theft|DD-ML|XGBoost + SMOTE on monthly averages|northern Iran province, 119,131 customers, readings every 40-60 days|monthly bill (40-60 day)|Y|SMOTE|accuracy 99.7%, precision 98.2%|N|NR|asynchronous manual reads resemble BD postpaid reading cycles|accuracy on imbalanced data; leakage risk from SMOTE not reported
R00480|Indonesia (West Java)|method (empirical ML, field-validated)|meter tampering, illegal connection, billing manipulation|DD-ML|stacking ensemble (LightGBM + CatBoost, LR meta-learner), 14 features|PLN West Java, 2.36 million consumers, 30 months, imbalance 22.8:1 (proprietary)|monthly bill|Y|imbalance-aware metric (PR-AUC), stratified CV|PR-AUC 0.7764; field detection rate 72.0% vs 15.3% for rules (12,407 inspections)|Y|framed as low-capex layer on existing billing data|strongest non-AMI field evidence; directly transferable to BD postpaid segments|single utility; data not public
R00678|emerging market (NR)|method (empirical ML)|consumer theft|DD-ML|8 classifiers incl. RF, dense NN, LSTM, 1D-CNN|4,000 customers, 864 confirmed thefts, 53 monthly values (2021-2025)|monthly bill|Y|undersampling 1:1|accuracy 0.685, AUC 0.748, F1 0.677 (RF); about one-third of thefts missed|N|NR|shows modest ceiling of monthly-only data; sequential DL does not transfer|small sample; balanced test
R00854|Saudi Arabia (simulation)|method (hardware/network)|feeder tapping, meter tampering|HW-MON|transformer-area remote detection and identification, real-time|Simulink simulation and HIL with 3 microcontroller meters|sub-hourly (instantaneous)|N|NA|detection/identification in simulation and HIL|N|described as cost-effective (no figures)|privacy-preserving design relevant to BD privacy constraint|simulation only; needs smart meters
R01017|China|method (DL)|consumption manipulation|DD-DL|wide and deep CNN on 2-D weekly consumption|realistic smart-meter dataset (SGCC per authors' description)|daily|Y|NR|outperforms baselines (values NR in abstract)|N|NR|requires AMI daily data not available in most BD feeders|labels and imbalance handling unclear in abstract
R01022|Iran / benchmark|method (sensitivity study)|consumption manipulation|DD-ML|down-sampling experiment + bagging network|challenging public dataset down-sampled|daily to monthly (varied)|Y|NR|performance falls slowly to weekly sampling, then sharply|N|NR|quantifies cost of BD's monthly reading cycle|single dataset
R01066|NR|method (DL, semi-supervised)|AMI fraud|DD-LAB|multitask feature-extracting fraud detector (semi-supervised)|real-world AMI data|sub-hourly/daily (NR exact)|Partial|semi-supervised use of unlabelled data|NR in abstract|N|NR|label scarcity mirrors BD utilities' inspection records|AMI-only
R01109|India (cost case)|method (prevention hardware)|hooking/illegal connections|HW-PREV|harmonic injection to damage illegal appliances|conceptual design with cost-benefit for India|NA|N|NA|NA|N|cost-benefit presented|approach is ethically and legally unacceptable for BD (damages property, safety risk)|no field evidence
R01198|Pakistan (MEPCO)|method (empirical ML)|consumer theft|DD-ML|ensemble bagged trees vs SVM, KNN, DT, RF|MEPCO consumer energy usage data|monthly bill (NR exact)|Y|NR|accuracy 93.1%|Partial|NR|South Asian utility with similar billing regime|accuracy only
R01224|Uruguay (UTE)|method (DL, multi-resolution)|consumer fraud|DD-DL|multi-resolution deep network (monthly + 15-min inputs)|UTE customers with/without fraud + public synthetic set|mixed (monthly + sub-hourly)|Y|NR|beats single-resolution models|N|NR|matches BD transition where smart prepaid and legacy meters coexist|metrics not in abstract
R01254|China (multi-city)|method (transfer learning)|consumer theft|DD-LAB|sample adaptive transfer across cities|multiple datasets|daily (NR exact)|Y|tested across fraud ratios|MAP +18.83%, AUC +13.29% vs baselines|N|NR|could transfer labels from one BD utility zone to another|simulation of new-city setting
R01285|Brazil|method (cost-sensitive targeting)|consumer NTL|DD-ECON|Rotation Forest (NTL probability) + XGBoost (energy recovery) to maximise return|261,489 consumers; 338 new field inspections|monthly bill|Y|NR|financial return of inspections up to 11.5 times higher|Y|inspection cost vs recovery modelled|targets limited inspection crews, a binding BD constraint|one utility
R01414|Uruguay (UTE)|method (cost-sensitive targeting)|consumer fraud|DD-ECON|Bayesian risk framework maximising economic return|large real UTE dataset|monthly bill|Y|cost-sensitive objective|economic return (values NR in abstract)|Partial|income recovered and inspection cost explicit|supports BERC-style cost-benefit appraisal|abstract-level only
R01432|China (SGCC data)|method (network correlation)|group fixed-ratio theft (collusive)|NW-BAL|standardised covariance between area NTL and user data; combinatorial search|SGCC realistic dataset (3,000 single-phase + 500 three-phase customers, 15-min, 285 days) + theft emulator|sub-hourly|N (no training)|NA|AUC and stability vs 4 methods|N|needs gateway meter per area|addresses village-level collective theft documented in South Asia|emulated theft
R01449|benchmark|method (ML)|smart-meter theft (6 synthetic cases)|DD-ML|gradient boosting theft detector with engineered features|public smart-meter data with updated synthetic theft cases|daily|N (synthetic)|NR|detection rate, FPR|N|storage/time complexity reduced|low FPR objective matters for BD inspection crews|synthetic theft
R01562|Brazil (real network)|method (network)|cyber-tampering of smart meters|NW-SE|multivariate control chart + A* pathfinding + GIS|real distribution network|sub-hourly|N|NA|selectivity/efficiency (NR values)|Partial|cheaper than full IT protection|relevant once BD smart prepaid meters are networked|cyber-attack focus
R01569|Taiwan (TPC)|method (network)|meter malfunction/tampering|NW-SE|state estimation at distribution transformer + ANOVA suspect list|TPC feeder data with scenarios|hourly (NR exact)|N|NA|trace of actual usage (NR values)|Partial|NR|DT-level metering is feasible entry point for BD|scenario-based tests
R01632|Pakistan (non-smart grid)|method (DL)|consumer theft|DD-DL|lightweight DL with PCA/t-SNE/UMAP and ROS|monthly customer readings|monthly bill|Y|random over-sampling, SMOTE, RUS|theft class precision 0.89, recall 0.94, F1 0.91|N|NR|explicitly for non-smart grids like most BD postpaid areas|oversampling before split not ruled out
R01647|Brazil (Para)|method (geospatial)|hook-based illegal connections|DD-GEO|satellite imagery, computer vision, DBSCAN, human-in-the-loop|>10,000 inspected sites|imagery|Y|NR|average accuracy 83.05% (regional peaks ~94%)|Y|clusters ranked by financial return|could map informal garages and dense hooking areas in BD|validated in one Brazilian state
R01660|China (SGCC)|method (active learning)|consumption manipulation|DD-LAB|deep active learning (CNN + MC dropout queries)|SGCC actual ETD dataset|daily|Partial|label-efficient querying|reliable with few labels (NR values)|N|reduces labelling cost|reduces need for costly BD field inspections to label data|AMI data
R01701|Spain (Endesa)|method (empirical ML, deployed)|industrial/commercial NTL|DD-ML|XGBoost vs other classifiers; alarms, electrical magnitudes, GIS|all Endesa C&I smart-meter customers; ~57,000 inspections|sub-hourly/hourly|Y|NR|XGBoost best (values NR in abstract)|Y|NR|template for BD large-consumer AMI segment|C&I only
R01804|NR (5,000 customers)|method (ML + transformer meters)|AMI energy theft|NW-BAL|transformer-meter shortlisting + consumption-pattern classifier|real dataset of 5,000 customers|hourly/sub-hourly|Partial (attack injection)|NR|high detection performance (NR values)|N|NR|low-sampling and privacy-friendly design|attacks likely injected
R02006|NR|method (hybrid)|NTL in smart grids|HY|voltage sensitivity + optimisation (SDP) + SVM|scenario studies|sub-hourly|Partial|NR|NR|N|NR|needs topology data that BD feeders rarely maintain|simulation
R02093|France/Brazil|method (remote sensing)|unserved/irregular urban areas|DD-GEO|NTL-Unet segmentation on Sentinel-2|Sentinel-2 imagery; train France, test Brazil|imagery|Partial (segmentation)|NA|IoU 0.921 train, 0.88 test|N|uses free imagery|low-cost screening of unserved settlements|area-level only
R02234|Korea (simulation)|method (hardware/network)|meter tampering, malfunction, bypassing|HW-MON|intermediate monitor meters + linear system of energy balance|simulated unit networks|sub-hourly|N|NA|accuracy >=95% at 80% reading variability|N|extra meters per unit network|detects bypassing, the dominant BD modality|simulation only
R02370|Iran (Mashhad)|pilot (AMI)|residential and commercial theft|HY|AMI pilots + DIgSILENT loss analysis|residential and commercial pilot areas|sub-hourly|NA|NA|distribution loss reduction (NR values)|Y|NR|pilot evidence for AMI in a high-NTL city|abstract gives no figures
R02473|South Africa|method (hardware)|illegal ground-surface conductors|HW-MON|zero-sequence current detection|simulation, laboratory and field soil tests|NA|NA|NA|detection validity depends on soil resistivity|Partial|deployment cost discussed|informal-settlement hooking analogous to BD slums|seasonal sensitivity
R02632|NR|method (network)|LV theft location|NW-SE|temperature-based technical-loss sensing + voltage-drop comparison (BFS)|LV network case|sub-hourly|N|NA|NR|N|sensors near transformer|separates technical from non-technical loss, a BD reporting gap|no field data in abstract
R02645|India (lab)|method (prevention hardware)|hook-line theft|HW-PREV|pilferage prevention system supplying unsuitable voltage to illegal loads|microcontroller experiments|NA|NA|NA|detection 99%, prevention 100% in experiments|N|NR|mentions connivance of staff, as in BD|laboratory only; safety concerns
R02728|Iran|method (network)|feeder-level NTL in limited-data LV networks|NW-SE|fuzzy c-means sub-networks, meter placement, pattern load profiles|limited-data LV feeders|monthly bill + few meters|N|NA|NTL index per feeder|N|fewer meters than one-by-one inspection|designed for poorly metered feeders typical of BD|method only
R03009|NR (real usage data)|method (network correlation)|nonlinear theft attacks|NW-BAL|correlation of master-meter loss with consumer readings|real-world usage dataset with attack types|sub-hourly|N (no training)|NA|pinpointing accuracy higher than baselines|N|no training or sensor cost|DT/master meters already installed at many BD substations|synthetic attacks
R00875|Pakistan (PESCO)|field study (smart meters)|theft in commercial, industrial, rural, urban areas|HW-SM|low-cost smart meter with IoT/cloud analytics|PESCO 15 km2 deployment|sub-hourly|NA|NA|NR (insight into theft locations)|Y|economic meter design|PESCO is a comparable high-loss South Asian utility|metrics not in abstract
R02446|Bangladesh|method (prevention hardware)|direct line tapping|HW-PREV|low-frequency (6-7 Hz) distribution with conversion at authorised meters|conceptual|NA|NA|NA|NA|N|NR|only BD-specific prevention hardware proposal found|infeasible at scale; no test
R00226|India (Uttar Pradesh)|qualitative (IAD framework)|informal governance of theft and access|GOV-INST|Institutional Analysis and Development framework, local actors|Malihabad field study|NA|NA|NA|NA|NA|NA|linesmen discretion mirrors BD meter-reader role|single site
R00240|Bangladesh (Dhaka)|field survey + bounding model|E3W charging energy use|E3W|measurements on 55 chargers in 10 garages; bounding techno-economic model|55 battery-charger units|NA|NA|NA|recorded ratio 31.3% shown to be a measurement-basis error; savings up to Tk 1,050-6,147 crore/yr if face value|N|retrofit savings bounds|first field data on garage chargers in Dhaka|preliminary; measurement basis flawed by design admission
R00347|Bangladesh (Khulna)|policy (fuzzy QFD)|E3W informal sector|E3W|fuzzy QFD with 0-1 optimisation, stakeholder and resource-dependency theory|stakeholder inputs Khulna|NA|NA|NA|NA|NA|NA|recommends regularising charging infrastructure|no theft data
R00590|Bangladesh (Gopalganj, Khulna)|field socio-technical|E3W hub charging|E3W|driver surveys (n=150) + one instrumented vehicle|150 drivers; 1 vehicle|NA|NA|NA|NA|NA|NA|documents clustered overnight hub charging|charging energy not metered
R00626|Pakistan|econometric panel|theft drivers|GOV-DRV|fixed effects (LSDV) and GMM|9 DISCOs, 1988-2010|annual|NA|NA|income negative, price positive effect|NA|NA|tariff increases in BD may raise theft incentives|aggregate data
R00633|Bangladesh (Chittagong)|cost-benefit|smart metering|BD-SYS|cost-benefit analysis of replacing prepaid with smart meters|Chittagong municipality|NA|NA|NA|benefit-cost ratio 1.36; total cost about US$300.9M|NA|explicit|BD-specific economics of AMI|assumptions from GB/Canada
R00686|Uganda (Kampala)|qualitative fieldwork|illegal connections as coping|GOV-DRV|ethnographic fieldwork 2022|Nakulabye settlement|NA|NA|NA|NA|NA|NA|parallels BD urban informal settlements|single settlement
R00874|Bangladesh|narrative/technical review|E3W charging|E3W|prospects, challenges, policy overview|secondary sources|NA|NA|NA|NA|NA|NA|uncontrolled charging named as a challenge|not systematic
R00953|Bangladesh (Tongi, DESCO)|simulation (ETAP)|technical loss reduction (NTL measures proposed)|BD-SYS|feeder reconfiguration, capacitors, DG in ETAP|Tongi 33/11 kV substation|NA|NA|NA|losses 12.12% to 6.26% (technical measures)|N|investment 216 crore BDT; savings 646 crore BDT/yr|shows technical-loss share is large; NTL measures only proposed|simulation; NTL not quantified
R00994|Uganda (Kampala)|participatory action research|theft drivers and community solutions|GOV-INST|mixed-methods PAR in 25 settlements|25 informal settlements|NA|NA|NA|NA|NA|NA|community co-design option for BD slum electrification|context-specific
R01144|DR Congo (Kinshasa)|survey + logistic regression|theft determinants|GOV-DRV|logistic regression with bootstrap and lasso|385 observations|NA|NA|NA|AUC 0.86; Hosmer-Lemeshow p=0.471|NA|NA|supply quality and billing transparency predict theft|cross-sectional
R01295|Brazil|qualitative interviews|NTL policy|GOV-REG|28 semi-structured expert interviews|28 specialists|NA|NA|NA|NA|NA|NA|cultural acceptance of theft is a policy target|expert opinion
R01422|Bangladesh|simulation (HOMER)|E3W charging stations as storage|E3W|battery swapping and charging station as community storage|HOMER Pro simulation|NA|NA|NA|NA|NA|NA|formal charging hubs as an alternative to illegal garages|simulation
R01631|Ghana|quasi-experimental|meter tampering/bypass|HW-SM|difference-in-differences on smart prepaid replacement|customer billing panel 2018-2019|monthly bill|NA|NA|reported consumption +13.2% after replacement|Y|NR|closest causal evidence for BD prepaid programme|short panel; lower quantile no effect
R01764|Brazil|econometric (SFA)|NTL targets|GOV-REG|stochastic frontier cost model|41 utilities, 10 years|annual|NA|NA|NR|NA|NA|basis for BERC utility-specific loss targets|regulatory design only
R01790|Bangladesh (Dhaka)|data analysis|payment delinquency|HW-SM|post- vs prepaid payment comparison|three years of Dhaka household payments|monthly bill|NA|NA|>=32% skipped a bill; ~46% recharge monthly after switch|Y|NR|direct BD evidence on prepaid behaviour|delinquency, not theft
R01924|Bangladesh (WZPDCL, Faridpur PBS)|survey + official data|prepaid non-acceptance|HW-SM|consumer survey, qualitative and official data|WZPDCL and Faridpur PBS|NA|NA|NA|NA|NA|NA|trust deficit undermines prepaid as anti-theft tool|conference paper
R01968|Bangladesh (Dhaka)|simulation|E3W load on grid|E3W|modified sensitivity analysis|Dhaka grid parameters|NA|NA|NA|peak load and voltage deviation increase|NA|NA|quantifies grid stress from E3W charging|assumption-driven
R02285|Bangladesh|statistical load analysis|E3W charging load|E3W|load curve comparison 2005 vs 2018 with E3W penetration|national load curves, 11 years of peaks|hourly|NA|NA|peak-time shift|NA|NA|charging shifts national load curve|aggregate inference
R02339|Pakistan|econometric panel|theft drivers|GOV-DRV|one-step system GMM|8 DISCOs, 2006-2018|annual|NA|NA|service quality reduces theft|NA|NA|service quality standards as anti-theft lever for BERC|aggregate
R02400|Bangladesh|design proposal|E3W garage charging|E3W|smart charger (~US$2) with transformer overload signal via 2G/MQTT|garages of >=40 vehicles|NA|NA|NA|NA|N|~US$2 hardware per charger|garage-level control could also meter charging|pilot only planned
R02453|Bangladesh|analytical study|prepaid metering|HW-SM|technical and commercial impact analysis|BD distribution data|monthly bill|NA|NA|revenue up, system loss down (NR values)|Y|NR|prepaid in BD since 2005|figures not in abstract
R02485|Bangladesh|survey + DSM proposal|E3W peak charging|E3W|demand-side management to shift charging|author survey|NA|NA|NA|NA|NA|NA|technology to enforce off-peak charging|no evaluation
R02682|developing countries|theoretical model|collusive theft|GOV-INST|three-layer principal-agent-client model|model|NA|NA|NA|NA|NA|NA|explains collusion between staff and consumers in BD|theoretical
R02801|India (Uttar Pradesh)|econometric ML|theft drivers|GOV-DRV|random forest regression on district data 2006-2012|district-level panel|annual|NA|NA|87% of loss-rate variance explained; spatial correlation 0.39 neighbours|NA|NA|socio-economic risk maps for BD districts|district aggregate
R02851|Brazil (Belo Horizonte)|econometric|illegal connections in favelas|GOV-DRV|household-level models with subsidy analysis|15,279 low-income households|NA|NA|NA|NR|NA|NA|subsidies and equipment upgrades reduce illegality|single programme
R02931|Nigeria|regression on regulatory data|ATC&C losses|HW-SM|relationship between metering share and ATC&C loss|NERC data 2015-2020|annual|NA|NA|1% more metering associated with 0.8% lower ATC&C loss|NA|NA|metering-gap closure as BD regulatory KPI|ceteris paribus assumption
R02987|Pakistan (IESCO)|survey + regression|residential theft|GOV-DRV|structured questionnaires, regression|IESCO consumers, rural and urban|NA|NA|NA|monitoring, employee conduct, expenses significant|NA|NA|bribe-taking staff enable theft|self-report
R03050|India (Uttar Pradesh)|conjoint experiment|social acceptability of theft (katiya)|GOV-DRV|conjoint survey|1,800 households|NA|NA|NA|odds +11% per Rs 1000 income gap; +4% per hour less supply|NA|NA|social acceptability likely similar for hooking in BD|vignettes
R03052|Ghana (Ashanti)|survey ranking|theft drivers|GOV-DRV|ranking of contributory factors|Ashanti Region data|NA|NA|NA|NA|NA|NA|prices, supply quality, corruption, weak enforcement|descriptive
R03062|Africa (Afrobarometer)|econometric|corruption and access|GOV-INST|Afrobarometer rounds 2 and 6 micro data|household surveys, multiple countries|NA|NA|NA|bribery linked to higher access; enforcement channel not supported|NA|NA|corruption can buy access, a mechanism relevant to BD connection queues|cross-section
R00093|global|review (systematic)|ML detection|BG|90 studies 2015-2025; lifecycle deployment framework|NA|NA|NA|NA|hybrid AUC 0.95-0.98 on benchmarks|NA|NA|generic deployment framework, no country focus|ML only
R00212|global|review (systematic)|NTL detection|BG|classification of AI methods|NA|NA|NA|NA|NA|NA|NA|no LMIC deployability|AI focus
R00638|global|review (survey)|smart-meter theft|BG|ML and measurement-mismatch methods; socio-economic factors|NA|NA|NA|NA|NA|NA|NA|smart-meter centric|no deployability
R00667|global|review (systematic)|technology solutions|BG|11 studies 2012-2022|NA|NA|NA|NA|NA|NA|NA|finds neglect of non-AMI countries|small corpus
R00682|India|review (narrative)|LV power theft|BG|factors and detection methods|NA|NA|NA|NA|NA|NA|NA|notes employee collusion; centralised AMI infeasible|narrative
R00691|global|review (narrative)|smart-meter fraud|BG|data-driven, privacy, adversarial robustness|NA|NA|NA|NA|NA|NA|NA|AMI-centric|no governance
R01524|global|review (systematic)|theft practices and AI|BG|AI methods vs theft practices|NA|NA|NA|NA|NA|NA|NA|smart-meter integration focus|no country focus
R01690|global|tertiary review|energy theft detection|BG|PRISMA review of reviews|NA|NA|NA|NA|NA|NA|NA|AMI granularity emphasised|tertiary
R01918|global|review (narrative)|data-driven ETD|BG|datasets and generative AI|NA|NA|NA|NA|NA|NA|NA|dataset limitations|AMI focus
R02139|global|review (survey)|AI NTL detection|BG|algorithms, features, datasets, challenges|NA|NA|NA|NA|accuracy 0.45-0.99, recall 0.29-1 across studies|NA|NA|identifies label noise from bribed inspectors and covariate shift|2017
R02266|global|bibliometric|NTL research|BG|392 conference studies 1987-2019|NA|NA|NA|NA|NA|NA|NA|India, Brazil, USA lead output|bibliometric only
R02409|Sub-Saharan Africa|review (narrative)|theft impacts|BG|regional overview|NA|NA|NA|NA|NA|NA|NA|regional LMIC focus|narrative
R02488|global|review (survey)|ETD performance|BG|threat models, datasets, metrics comparison|NA|NA|NA|NA|NA|NA|NA|metric comparison|AMI focus
R02557|Europe|review + questionnaire|NTL methods and regulation|BG|methods and regulatory questionnaire in 10 EE countries|NA|NA|NA|NA|NA|NA|NA|regulatory comparison|Europe only
"""

M_SCORES = {  # M1..M8
    "R00176": "1 0.5 0.5 1 1 0 0.5 0.5", "R00311": "1 1 0.5 0.5 1 0 0.5 1", "R00337": "0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5",
    "R00365": "1 1 1 0.5 1 0.5 0.5 0.5", "R00430": "1 1 1 0.5 1 0.5 0.5 0.5", "R00431": "1 1 0.5 0.5 0.5 0 0.5 0.5",
    "R00480": "1 1 1 1 1 1 0.5 1", "R00678": "1 1 1 1 1 0 0.5 1", "R00854": "1 0 0.5 0.5 0.5 0.5 0 1",
    "R01017": "0.5 0.5 0.5 0.5 1 0 0.5 0.5", "R01022": "0.5 0.5 0.5 0.5 1 0 0.5 1", "R01066": "0.5 1 0.5 0.5 0.5 0 0.5 0.5",
    "R01109": "0.5 0 0 0.5 0 0 0 1", "R01198": "1 0.5 0 0.5 1 0.5 0.5 0.5", "R01224": "1 1 0.5 0.5 1 0 0.5 0.5",
    "R01254": "0.5 0.5 1 1 1 0 0.5 0.5", "R01285": "1 1 0.5 1 1 1 0.5 1", "R01414": "1 1 1 0.5 1 0.5 0.5 1",
    "R01432": "1 0 1 1 1 0 0.5 0.5", "R01449": "0.5 0 1 0.5 1 0 0.5 0.5", "R01562": "0.5 0 0.5 0.5 0.5 0.5 0.5 0.5",
    "R01569": "1 0 0.5 0.5 0.5 0.5 0.5 0.5", "R01632": "0.5 0.5 1 0.5 1 0 0.5 0.5", "R01647": "1 1 0.5 0.5 0.5 1 0.5 1",
    "R01660": "1 0.5 0.5 0.5 1 0 0.5 1", "R01701": "1 1 0.5 1 1 1 0.5 0.5", "R01804": "1 0.5 0.5 0.5 0.5 0 0.5 1",
    "R02006": "0.5 0 0.5 0.5 0.5 0 0.5 0.5", "R02093": "1 0.5 0.5 1 0.5 0 0.5 0.5", "R02234": "1 0 0.5 0.5 0.5 0 0 0.5",
    "R02370": "1 1 0.5 0.5 0.5 1 0 0.5", "R02473": "1 0.5 0.5 0.5 0.5 0.5 0 1", "R02632": "0.5 0 0.5 0.5 0.5 0 0.5 0.5",
    "R02645": "0.5 0 0.5 0.5 0.5 0.5 0 0.5", "R02728": "0.5 0 0.5 0.5 0.5 0 0.5 0.5", "R03009": "1 0 0.5 0.5 1 0 0.5 1",
    "R00875": "1 0.5 0.5 0.5 0.5 1 0 0.5", "R02446": "0 0 0 0.5 0 0 0 0.5",
}
E_SCORES = {  # E1..E6
    "R00226": "1 1 1 0.5 0.5 0.5", "R00240": "1 1 1 0.5 1 1", "R00347": "1 0.5 1 0.5 0.5 0.5", "R00590": "1 1 1 0.5 0.5 1",
    "R00626": "1 1 1 1 1 0.5", "R00633": "1 0.5 0.5 0.5 0 0.5", "R00686": "1 1 1 0.5 0.5 1", "R00874": "1 0.5 0.5 0.5 0.5 0.5",
    "R00953": "1 1 1 1 0.5 0.5", "R00994": "1 1 1 0.5 0.5 1", "R01144": "1 1 1 1 1 0.5", "R01295": "1 1 1 0.5 0.5 0.5",
    "R01422": "1 1 1 0.5 0.5 0.5", "R01631": "1 1 1 1 1 0.5", "R01764": "1 1 1 1 0.5 0.5", "R01790": "1 1 1 1 0.5 0.5",
    "R01924": "1 1 0.5 0.5 0.5 0.5", "R01968": "1 0.5 0.5 0.5 0.5 0.5", "R02285": "1 0.5 0.5 0.5 0.5 0.5",
    "R02339": "1 1 1 1 1 0.5", "R02400": "1 0.5 0.5 0 0.5 1", "R02453": "1 0.5 0.5 0.5 0 0.5", "R02485": "1 0.5 0.5 0.5 0.5 0.5",
    "R02682": "1 0.5 1 0.5 0.5 0.5", "R02801": "1 1 1 1 1 0.5", "R02851": "1 1 1 1 1 0.5", "R02931": "1 1 0.5 1 0.5 1",
    "R02987": "1 1 1 0.5 0.5 0.5", "R03050": "1 1 1 1 1 0.5", "R03052": "1 1 0.5 0.5 0.5 0.5", "R03062": "1 1 1 1 1 1",
}
# AACODS for grey literature: Authority, Accuracy, Coverage, Objectivity, Date, Significance
G_SCORES = {
    "G01": "0.5 0.5 1 0.5 1 1", "G02": "1 0.5 0.5 0.5 1 1", "G03": "0.5 0 0.5 0 1 0.5", "G04": "0.5 0.5 1 0.5 1 1",
    "G05": "0.5 0.5 0.5 0.5 1 0.5", "G06": "0.5 1 1 1 1 1", "G07": "0.5 1 0.5 1 1 1", "G08": "1 0.5 1 1 1 1",
    "G09": "1 0.5 0.5 0.5 1 1", "G10": "1 0.5 0.5 0.5 1 1", "G11": "1 1 1 1 1 1", "G12": "1 0.5 0.5 1 0 1",
    "G13": "1 1 1 1 0 1",
}


def band(s):
    return "high" if s >= 0.75 else ("medium" if s >= 0.5 else "low")


def main():
    meta = {r["record_id"]: r for r in csv.DictReader(open(ROOT / "data" / "extraction_inputs.csv", encoding="utf-8"))}
    cols = ["rid", "country_region", "study_type", "theft_type_addressed", "approach_family", "specific_method",
            "dataset", "data_granularity", "labelled_data", "class_imbalance_handling", "metrics_reported",
            "real_world_deployment", "cost_information", "bangladesh_relevance_notes", "limitations"]
    out, seen = [], set()
    for line in ROWS.strip().splitlines():
        parts = [p.strip() for p in line.split("|")]
        assert len(parts) == len(cols), (parts[0], len(parts))
        d = dict(zip(cols, parts))
        m = meta[d["rid"]]
        seen.add(d["rid"])
        out.append({"id": d["rid"], "citation_key": m["key"], "doi": m["doi"], "year": m["year"], "venue": m["venue"],
                    "venue_quartile": "TBC (SCImago not reachable; author to confirm)",
                    "role": "background review" if d["approach_family"] == "BG" else "included study",
                    "pool": m["t_code"], **{k: v for k, v in d.items() if k != "rid"},
                    "read_level": "full text" if d["rid"] in FULLTEXT else "abstract",
                    "grey_url": "", "access_date": ""})
    missing = set(meta) - seen
    assert not missing, missing
    grey = pd.read_csv(ROOT / "data" / "grey" / "grey_literature.csv", dtype=str).fillna("")
    for _, g in grey.iterrows():
        out.append({"id": g["grey_id"], "citation_key": GREY_KEYS[g["grey_id"]], "doi": "", "year": g["date"][:4],
                    "venue": g["outlet"], "venue_quartile": "grey literature", "role": "grey literature", "pool": "GREY",
                    "country_region": "Bangladesh", "study_type": g["type"], "theft_type_addressed": g["theft_mechanisms"],
                    "approach_family": "GREY", "specific_method": "", "dataset": "", "data_granularity": "NA",
                    "labelled_data": "NA", "class_imbalance_handling": "NA", "metrics_reported": g["key_facts"],
                    "real_world_deployment": "NA", "cost_information": "", "bangladesh_relevance_notes": g["policy"],
                    "limitations": g["caveats"], "read_level": g["read_level"], "grey_url": g["url"],
                    "access_date": g["access_date"]})
    ex = pd.DataFrame(out)
    ex.to_csv(ROOT / "data" / "extraction.csv", index=False)

    q = []
    for r in out:
        rid = r["id"]
        if rid in M_SCORES:
            rub, s = "M", M_SCORES[rid]
        elif rid in E_SCORES:
            rub, s = "E", E_SCORES[rid]
        elif rid in G_SCORES:
            rub, s = "G (AACODS)", G_SCORES[rid]
        else:
            q.append({"id": rid, "citation_key": r["citation_key"], "rubric": "not appraised (background review)",
                      "items": "", "score": "", "band": "", "read_level": r["read_level"], "provisional": ""})
            continue
        items = [float(x) for x in s.split()]
        assert len(items) == (8 if rub == "M" else 6), rid
        sc = round(sum(items) / len(items), 3)
        q.append({"id": rid, "citation_key": r["citation_key"], "rubric": rub, "items": s, "score": sc,
                  "band": band(sc), "read_level": r["read_level"],
                  "provisional": "yes" if r["read_level"] == "abstract" else "no"})
    qa = pd.DataFrame(q)
    qa.to_csv(ROOT / "data" / "quality_appraisal.csv", index=False)
    inc = qa[qa["rubric"].isin(["M", "E"])]
    print("extraction rows:", len(ex), "| included:", (ex.role == "included study").sum(),
          "| background:", (ex.role == "background review").sum(), "| grey:", (ex.role == "grey literature").sum())
    print("quality bands (included):", inc["band"].value_counts().to_dict())
    print("mean score M:", round(inc[inc.rubric == "M"].score.mean(), 3), " E:", round(inc[inc.rubric == "E"].score.mean(), 3))


if __name__ == "__main__":
    main()

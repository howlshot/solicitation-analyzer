# Evaluation results

Model: `qwen3.8-27b-mlx`, run locally. Baseline: keyword rules with no model (`solicitation_analyzer/baseline.py`).
Reference answers: `eval/gold/`, written by reading each solicitation. 5 packages, 718 model items checked.

| Measure | Model | Keyword baseline |
|---|---:|---:|
| Key facts right (7 per package) | 34/35 (97%) | 29/35 (83%) |
| Deadline times right | 6/6 (100%) | 4/5 (80%) |
| Evaluation factors found | 15/15 (100%) | 10/15 (67%) |
| Must-do checklist items covered | 57/58 (98%) | 39/58 (67%) |
| Items returned | 716 checklist lines | 652 raw sentences |

## Quote verification

Every model item must quote the page it cites. Of 718 items, 705 quotes were found word for word, 6 were close matches (90% or more), 7 were read across table cells, and 2 were removed because the words are not in the document. 8 items carry a warning for a person to check, and 2 deadlines were replaced by an amendment.

## By package

### ESD Pre-Qualified Providers of IT Goods and Services RFP

Items: 158 kept, 0 removed.

| Fact | Expected | Model | Right |
|---|---|---|:-:|
| Response due date | 2026-08-13 14:00 | 2026-08-13 14:00 | yes |
| Questions due date | 2026-07-08 | 2026-07-08 | yes |
| How to submit | dropbox | Proposals must be sent to the designated Dropbox link. | yes |
| Page limit | not stated | not stated | yes |
| Basis of award | best value/weighted/points/highest | not found | no |
| Set-aside | not stated | not stated | yes |
| NAICS code | not stated | not stated | yes |

Checklist coverage 12/12 (100%); factors 5/5 (100%).

### NYSED RFP #24-026: Audit Management Solution Software

Items: 289 kept, 0 removed.

| Fact | Expected | Model | Right |
|---|---|---|:-:|
| Response due date | 2026-01-13 | 2026-01-13 | yes |
| Questions due date | 2025-12-23 | 2025-12-23 | yes |
| How to submit | online form | Submit bids electronically via online form no later than January 13, 2026. | yes |
| Page limit | 25 | Technical Proposal is limited to 25 pages excluding attachments, work samples, and project | yes |
| Basis of award | highest | aggregate | Award goes to vendor with highest aggregate technical and cost score. | yes |
| Set-aside | not stated | not stated | yes |
| NAICS code | not stated | not stated | yes |

Checklist coverage 12/12 (100%); factors 5/5 (100%).

### USGS ShakeAlert Code Review RFI

Items: 79 kept, 0 removed.

| Fact | Expected | Model | Right |
|---|---|---|:-:|
| Response due date | 2026-10-16 12:00 | 2026-10-16 12:00 | yes |
| Questions due date | not stated | not stated | yes |
| How to submit | email | e-mail | emailed | Submit responses electronically in PDF format via email to the POC. | yes |
| Page limit | not stated | not stated | yes |
| Basis of award | not stated | not stated | yes |
| Set-aside | not stated | not stated | yes |
| NAICS code | not stated | not stated | yes |

Checklist coverage 12/12 (100%); factors 0/0 (0%).

### Air Force TDL Interoperability Software RFP (FA489026Q0016)

Items: 103 kept, 2 removed.

| Fact | Expected | Model | Right |
|---|---|---|:-:|
| Response due date | 2026-10-10 13:00 | 2026-10-10 13:00 | yes |
| Questions due date | 2026-09-04 15:00 | 2026-09-04 15:00 | yes |
| How to submit | email | e-mail | Submit proposal via email to CM and CO by the response date/time. | yes |
| Page limit | 30 | Technical Volume maximum is 30 pages. | yes |
| Basis of award | lowest price technically acceptable | lpta | lowest priced proposal | Award based on lowest priced proposal meeting acceptability standards. | yes |
| Set-aside | not set-aside | not set aside | unrestricted | set-aside: no | no small business set | Solicitation is unrestricted with no small business set-aside. | yes |
| NAICS code | 541511 | NAICS code is 541511, Custom Computer Programming Services. | yes |

Checklist coverage 12/12 (100%); factors 2/2 (100%).

### IHS Telecom Software Support Subscription (SDVOSB set-aside)

Items: 87 kept, 0 removed.

| Fact | Expected | Model | Right |
|---|---|---|:-:|
| Response due date | 2026-10-26 17:00 | 2026-10-26 17:00 | yes |
| Questions due date | 2026-10-13 12:00 | 2026-10-13 12:00 | yes |
| How to submit | email | e-mail | Offers must be submitted electronically via email to [email]. | yes |
| Page limit | not stated | not stated | yes |
| Basis of award | lowest price technically acceptable | lpta | Award is based on Lowest Price Technically Acceptable (LPTA). | yes |
| Set-aside | service-disabled | sdvosb | service disabled | Solicitation is set aside for 100% Service-Disabled Veteran-Owned Small Business. | yes |
| NAICS code | 541519 | Associated NAICS code is 541519 with a $34.0 million size standard. | yes |

Checklist coverage 9/10 (90%); factors 3/3 (100%).
Missed: Award may be made without discussions, so the first offer should be the best.

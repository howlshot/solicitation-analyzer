# Evaluation results

Model: `Qwen3.8-Flash-Next-MLX-Serve-mixed-4-8bit`, run locally. Baseline: keyword rules with no model (`solicitation_analyzer/baseline.py`).
Reference answers: `eval/gold/`, written by reading each solicitation. 5 packages, 513 model items checked.

| Measure | Model | Keyword baseline |
|---|---:|---:|
| Key facts right (7 per package) | 34/35 (97%) | 29/35 (83%) |
| Deadline times right | 6/6 (100%) | 4/5 (80%) |
| Evaluation factors found | 15/15 (100%) | 10/15 (67%) |
| Must-do checklist items covered | 55/58 (95%) | 39/58 (67%) |
| Items returned | 510 checklist lines | 652 raw sentences |

## Quote verification

Every model item must quote the page it cites. Of 513 items, 503 quotes were found word for word, 3 were close matches (90% or more), 6 were read across table cells, and 3 were removed because the words are not in the document. 9 items carry a warning for a person to check, and 2 deadlines were replaced by an amendment.

## By package

### ESD Pre-Qualified Providers of IT Goods and Services RFP

Items: 119 kept, 2 removed.

| Fact | Expected | Model | Right |
|---|---|---|:-:|
| Response due date | 2026-08-13 14:00 | 2026-08-13 14:00 | yes |
| Questions due date | 2026-07-08 | 2026-07-08 | yes |
| How to submit | dropbox | Proposals must be submitted via the designated Dropbox link. | yes |
| Page limit | not stated | not stated | yes |
| Basis of award | best value/weighted/points/highest | not found | no |
| Set-aside | not stated | not stated | yes |
| NAICS code | not stated | not stated | yes |

Checklist coverage 12/12 (100%); factors 5/5 (100%).

### NYSED RFP #24-026: Audit Management Solution Software

Items: 208 kept, 0 removed.

| Fact | Expected | Model | Right |
|---|---|---|:-:|
| Response due date | 2026-01-13 | 2026-01-13 | yes |
| Questions due date | 2025-12-23 | 2025-12-23 | yes |
| How to submit | online form | Submit documents via the online form in Microsoft Office or editable PDF. | yes |
| Page limit | 25 | Technical Proposal is limited to 25 pages, excluding attachments and work samples. | yes |
| Basis of award | highest | aggregate | Award goes to vendor with highest aggregate technical and cost score. | yes |
| Set-aside | not stated | not stated | yes |
| NAICS code | not stated | not stated | yes |

Checklist coverage 12/12 (100%); factors 5/5 (100%).

### USGS ShakeAlert Code Review RFI

Items: 55 kept, 0 removed.

| Fact | Expected | Model | Right |
|---|---|---|:-:|
| Response due date | 2026-10-16 12:00 | 2026-10-16 12:00 | yes |
| Questions due date | not stated | not stated | yes |
| How to submit | email | e-mail | emailed | Submit responses via email to [name]; no phone, mail, or fax accepted. | yes |
| Page limit | not stated | not stated | yes |
| Basis of award | not stated | not stated | yes |
| Set-aside | not stated | not stated | yes |
| NAICS code | not stated | not stated | yes |

Checklist coverage 11/12 (92%); factors 0/0 (0%).
Missed: General marketing material is not responsive.

### Air Force TDL Interoperability Software RFP (FA489026Q0016)

Items: 64 kept, 1 removed.

| Fact | Expected | Model | Right |
|---|---|---|:-:|
| Response due date | 2026-10-10 13:00 | 2026-10-10 13:00 | yes |
| Questions due date | 2026-09-04 15:00 | 2026-09-04 15:00 | yes |
| How to submit | email | e-mail | Submit proposals via email to [name] and [name] by the deadline in Table 3. | yes |
| Page limit | 30 | Technical Volume maximum page limit is 30 pages. | yes |
| Basis of award | lowest price technically acceptable | lpta | lowest priced proposal | Award goes to the lowest priced proposal meeting technical acceptability standards. | yes |
| Set-aside | not set-aside | not set aside | unrestricted | set-aside: no | no small business set | This solicitation is not set-aside for small business concerns. | yes |
| NAICS code | 541511 | The assigned NAICS code is 541511, Custom Computer Programming Services. | yes |

Checklist coverage 12/12 (100%); factors 2/2 (100%).

### IHS Telecom Software Support Subscription (SDVOSB set-aside)

Items: 64 kept, 0 removed.

| Fact | Expected | Model | Right |
|---|---|---|:-:|
| Response due date | 2026-10-26 17:00 | 2026-10-26 17:00 | yes |
| Questions due date | 2026-10-13 12:00 | 2026-10-13 12:00 | yes |
| How to submit | email | e-mail | Submit offers electronically via email to the Contract Specialist. | yes |
| Page limit | not stated | not stated | yes |
| Basis of award | lowest price technically acceptable | lpta | Award will be made based on Lowest Price Technically Acceptable (LPTA). | yes |
| Set-aside | service-disabled | sdvosb | service disabled | Solicitation is set aside for 100% Service-Disabled Veteran-Owned Small Business. | yes |
| NAICS code | 541519 | Associated NAICS Code is 541519 with a small business size standard of $34.0 million. | yes |

Checklist coverage 8/10 (80%); factors 3/3 (100%).
Missed: Quoted unit prices are all-inclusive, including travel; Award may be made without discussions, so the first offer should be the best.

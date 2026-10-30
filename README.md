# Denial Triage & Aging Dashboard

This is an automated denial triage for Riverbend, a 6-provider medical clinic. A claims export goes in; a prioritized daily work queue, a live dashboard, and a deadline alert come out.

> **Demo project on synthetic data.** Every claim, patient, and number in this repository is fake. No real patient information is used anywhere. Appeal windows and recovery rates are assumptions, not client data.

## The problem

When an insurer denies a claim, the clinic has a limited window to correct or appeal it. Most small practices track denials in a spreadsheet, work them in arrival order, and find out too late that the deadline passed. In this demo, **42% of denied dollars had already expired unworked** (figures from the 26 October 2026 run; deadlines move daily, so a fresh run differs).

## What the system does

1. **Upload:** the clinic uploads its claim-lines export (CSV) through a web form.
2. **Validate:** bad files are stopped early with a clear message, and odd-but-usable data is flagged as a warning.
3. **Triage:** each denial becomes a work item with a category, a next action, an estimated recovery chance, and a deadline.
4. **Prioritize:** items are ranked by expected recovery, so billers work the claims where effort most likely turns into cash.
5. **Dashboard:** a live Airtable dashboard shows dollars at risk, money already lost, and breakdowns by payer, provider, denial reason, and age.
6. **Alert:** a daily Telegram message lists claims about to expire, or an "all clear" if none.
7. **Safe re-uploads:** loading is idempotent, so re-uploading never creates duplicates or overwrites a biller's progress.
8. **Error handling:** every failure alerts the administrator, and every upload is recorded in an audit log.

```
CSV upload -> Validate -> Triage -> Airtable (upsert) -> Run report -> Telegram + Upload Log
                                        |
                                        +-> Dashboard (live formula fields)
Schedule 08:00 -> Airtable search -> Alert message -> Telegram
Any failure    -> Error workflow  -> Telegram
```

## Stack

n8n (automation), Airtable (database and dashboard), Python / pandas (data generation and analysis), JavaScript (n8n Code nodes), Telegram Bot API (alerts).
*   **The Full Package Solution:** Leveraged clinical insights as a Registered Nurse to design and engineer an end-to-end Revenue Cycle Management (RCM) system for a 6-provider clinic, automating manual spreadsheet tracking into a data-driven, prioritized work queue.
*   **Rapid Prototyping & Simulation:** Utilized Python and Pandas to simulate realistic, synthetic clinic data and prototype core triage algorithms, validating the system's logic and data structures prior to production deployment.
*   **Workflow Automation:** Built a resilient, idempotent n8n integration workflow using JavaScript to validate incoming files, upsert data, and deploy a Telegram alerting bot that proactively flags claims nearing their appeal deadlines.
*   **Automated Analytics & Dashboarding:** Designed a live, interactive Airtable business intelligence dashboard that automatically processes data to surface strategic insights, including a 14.6% baseline denial rate, provider missing-info metrics, and dollars at risk.
## What the demo data revealed

| Finding | Result |
|---|---|
| Claim denial rate | 14.6% |
| Allowed dollars denied | $32,322 |
| One insurer's MRI prior-auth denials | 75% of that insurer's MRI claims |
| One provider's missing-information rate | 11.7% against 4.0% for the next-highest |
| Medicaid coverage-terminated denials | 18% of Medicaid claims (eligibility not re-checked) |

## What is in this repository

| Folder | Contents |
|---|---|
| [`prototype/`](./prototype) | Python that generates the synthetic clinic data and analyzes it like a biller |
| [`screenshots/`](./screenshots) | The dashboard, the workflow canvas, and the alert messages |
| [`docs/`](./docs) | The full case study |


Run the analysis yourself (Python 3 with `pandas` and `numpy`):

```bash
cd data
python ../prototype/generate_claims.py   # creates riverbend_claim_lines.csv (synthetic)
python ../prototype/analyze.py           # headline numbers and four planted root causes
```

## The full system

This repository is the portfolio edition. The complete package (importable n8n workflows, the Airtable base template, the tested Code nodes with their test suite, the staff SOP, system documentation, and setup support) is available on request. Contact me below.

## Limitations

- Appeal windows and recovery chances are assumptions to be replaced with each payer's contract terms and the clinic's own win and loss history.
- Claims that get paid after resubmission stay in the queue until a biller closes them. Auto-resolve is planned.
- Real clinics need a column-mapping step, because each billing system names its export columns differently.

## Roadmap

Parse real EDI 835 Electronic Remittance Advices, auto-resolve paid claims, generate appeal drafts, and add pre-submission claim checks.

## License

Copyright (c) 2026 Damilola Otitokoro. All rights reserved. Shared for portfolio review only. See `LICENSE`.

## Contact

Damilola Otitokoro | [LinkedIn](https://www.linkedin.com/in/damilolaotitokoro)

# XULAN — Submission guide

A locally runnable Python application and evidence package for drafting Chinese WeChat messages across six luxury-retail scenarios. The brand, clients, products, events and policies are fictional. Narrative documents are in English; the generated messages and case dialogue are in Chinese.

| Required item | File |
|---|---|
| A. Work log (Excel, with screenshots) | [work_log.xlsx](work_log.xlsx) |
| B. Methodology | [methodology.md](methodology.md) |
| C. 50 test cases, exact eight columns | [test_cases.csv](test_cases.csv) |
| D. Evaluation with screenshots | [evaluation_report.md](evaluation_report.md) |
| E. Defects, versions and next steps | [defects_and_next_steps.md](defects_and_next_steps.md) |
| Bonus: architecture | [architecture.md](architecture.md) |
| Demo video (1 min 31 s, silent, captioned) | [demo/xulan-demo.mp4](demo/xulan-demo.mp4) |

Supporting data for readers who want to check the numbers lives in [supporting/](supporting/README.md):

| Supporting file | Content |
|---|---|
| [run_manifest.json](supporting/run_manifest.json) | Every case: full input, result, model, and prompt/code/data versions |
| [reviews.json](supporting/reviews.json) | Raw judge output (`gpt-5-mini-2025-08-07`, medium reasoning) for each successful set |
| [metrics.json](supporting/metrics.json) | Automated metrics: within-set similarity, near-duplicates, soft flags, prompt-phrase reuse |
| [author_review_worksheet.csv](supporting/author_review_worksheet.csv) | Human review: fixed-seed calibration sample plus every flagged message, with the author's labels |
| [evaluation_summary.json](supporting/evaluation_summary.json) | Machine-readable summary, including judge–author agreement counts |
| [abstention_results.json](supporting/abstention_results.json) | Robustness and abstention: 35 cases that must be blocked, need information, be rejected or proceed (no model calls) |
| [reliability.json](supporting/reliability.json) | Latency, model calls, tokens and cost of the submitted run, per outcome path |
| [brand_data.json](supporting/brand_data.json) | The approved product and policy facts used for generation |
| [test_results.txt](supporting/test_results.txt) | Latest automated test run |
| supporting/evidence/&lt;label&gt;/ | Raw per-call files of the submitted run (v6) and the comparison baseline (v5) |

**Current state.** The packaged files come from **v6** (prompt 6.0, data 1.2): one single-version run of all 50 cases, judged in full, with 75 messages reviewed by the author. Results: 130 / 144 messages and 48 / 50 cases usable, 1 critical message, and judge–author agreement of 30 / 36 on the calibration sample. The previous evaluated version, **v5**, is kept as the comparison baseline in `supporting/evidence/v5-final/`.

Earlier iterations (prompt 1.0–4.1) and withdrawn artifacts are kept unchanged outside the submission, in `archive/` at the repository root. `archive/README.md` maps each folder to its version, purpose and outcome.

Run instructions are in the repository [README](../README.md). In the running app, `/` opens Advisor Studio, and `/static/report.html` opens the evaluation page.

This package is not a validated production release. Every human label comes from one reviewer, the author, and the model judge is an aid whose errors are measured, not ground truth.

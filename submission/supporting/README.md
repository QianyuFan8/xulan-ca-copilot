# Supporting data

These files hold the data behind the reports in the parent folder. They are produced by `evaluation/package.py` from the submitted single-version run (`v6-final`), so every number in the evaluation report can be traced back to them.

| File | What it is |
|---|---|
| `run_manifest.json` | All 50 cases: the full input, the result (drafts or a labelled failure), and the model, prompt, code and data versions of each call |
| `reviews.json` | The raw output of the model judge (`gpt-5-mini-2025-08-07`, medium reasoning): seven scores, a critical flag, an uncertain flag and issues for each draft, plus set diversity |
| `metrics.json` | Automated metrics: within-set similarity, near-duplicate sets, soft style flags and reuse of prompt phrases, per case and in total |
| `author_review_worksheet.csv` | The human review: a fixed-seed calibration sample plus every flagged message, with the judge's verdict next to the author's label, critical flag and note |
| `evaluation_summary.json` | The machine-readable summary the reports cite: success counts, judge results, final usability and judge–author agreement |
| `abstention_results.json` | Robustness and abstention results (`evaluation/abstention.py`): expected and actual outcome for each of 35 cases, with no model calls |
| `reliability.json` | Reliability and efficiency of the submitted run (`evaluation/reliability.py`): latency, model calls, retries, tokens and estimated cost per case and per outcome path |
| `brand_data.json` | The approved product and policy facts the drafts were generated against (a copy of `data/catalogue.json`) |
| `test_results.txt` | The result of the latest automated test run |
| `evidence/v6-final/` | Raw per-call files of the submitted run: input, every model attempt and the result |
| `evidence/v5-final/` | The same files for v5, the comparison baseline |

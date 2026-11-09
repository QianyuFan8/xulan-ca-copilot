# Archive: runs before v5

These folders hold the raw evidence from development iterations before the current evaluated version (v5, prompt 5.0). They are kept unchanged for traceability: every per-generation file records its own `run_id`, `prompt_version`, input, raw attempts and result. **None of these runs is the submitted result.** The submitted run and its evidence are in `submission/`.

All generation runs used GPT-4o. Before requirement 1.3, the judge was also GPT-4o, so the generator was grading itself.

| Folder | Prompt version | Cases | Purpose | Outcome / conclusion |
|---|---|---|---|---|
| `v1-pilot` | 1.0 | 1 | First paid pilot | Provider network failure; the error path and retained cost reservation worked as designed |
| `v1-network-pilot` | 1.0 | 1 | Pilot retry after the network fix | First real GPT-4o success; API path confirmed |
| `v1-formal` | 1.0 | 50 | First full 50-case baseline | 50/50 succeeded. Reviewing the v1/v2 outputs led to the budget-reference fix, the groundedness checks and more specific repair guidance |
| `v2-formal` | 2.0 | 15 | Rerun after the first prompt and validator fixes | 14/15 succeeded; one case failed with an unsupported numeric price claim (budget read as a price) |
| `v2.1-formal` | 2.1 | 38 | Rerun with budget-reference handling | 37/38 succeeded; one invitation failed because its date/time/location was incomplete |
| `v2.2-formal` | 2.2 | 39 | Rerun with exact invitation strings in repair feedback | 38/39 succeeded; one invitation still failed the exact-string check |
| `v2.2-tail` | 2.2 | 12 | Completed the remaining 2.2 cases | 12/12 succeeded |
| `v2.2-final` | 2.2 | 50 | Assembled complete 2.2 baseline (formal + tail) | 50/50 succeeded; this was the baseline for the targeted regressions below |
| `v3-regression` | 3.0 | 9 | Targeted reruns of defect cases (stock claims, care-rule leakage) | 9/9 succeeded; stock claim and scratch-as-rain care removed in the rerun cases |
| `v3.1-regression` | 3.1 | 4 | Targeted reruns (woven-panel care scope) | 4/4 succeeded |
| `v3.2-regression` | 3.2 | 1 | Targeted rerun (unverified event "no sales" assurance) | 1/1 succeeded |
| `v4-regression` | 4.0 | 4 | Targeted reruns of client-intent cases (deferral, reactivation) | 3/4 succeeded; one budget-as-price failure recurred |
| `v4.1-regression` | 4.1 | 2 | Fix for the recurring budget-as-price case | 2/2 succeeded |
| `final-selection` | mixed 2.2–4.1 | 50 | Earlier "final" set: per-case picks from the runs above | **Withdrawn in 1.3.** It mixed prompt versions (37 cases at 2.2, the rest at 3.0–4.1), so it described no single version of the system |
| `before-1.3` | mixed 2.2–4.1 | 50 | Snapshot of the earlier submission package: manifest, GPT-4o judge reviews, CSV, summary and metrics | Kept as the "before" evidence for the 1.3 corrections. Its prompt examples were reused in 6 of 8 greeting cases, and its CSV lacked scenario facts |
| `superseded` | — | — | Earlier "author" scores | **Withdrawn.** The scores came from a templated default, not real review: 135 of 150 messages had identical scores. See the README inside |
| `live-ui` | 1.0, 2.1 | 2 | Generations made through the web UI during browser testing | One safe error without a credential and one real three-draft generation; these back the earlier UI screenshots |
| `screenshots-before-v5` | — | — | UI and evaluation-page screenshots from the first implementation | Replaced by v6 screenshots in `submission/screenshots/`; the old evaluation page showed the withdrawn templated scores |
| `legacy-scripts` | — | — | `finalize.py`, `merge.py`, `regress.py` from the first implementation | **Withdrawn.** `finalize.py` produced the templated author scores; `merge.py` built the mixed-version selection. Kept for traceability only |

## What changed afterwards

Requirement 1.3 made these changes:
- Only a single-version 50-case run may be submitted.
- The CSV must carry the scenario facts.
- Prompt guidance uses structural descriptions instead of example sentences.
- The judge is a different model from the generator.
- Evaluation combines automated metrics, the model judge, and a sampled human review with agreement counts.

The first run under these rules is **v5** (`submission/supporting/evidence/v5-final/`).

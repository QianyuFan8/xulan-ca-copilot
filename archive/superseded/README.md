# Withdrawn artifacts

These files are kept for traceability. They must not be cited as evaluation results.

| File | Why it was withdrawn |
|---|---|
| `author_reviews_templated.json`, `final-selection_author_reviews_templated.json` | Labelled "Codex author assessment (AI)". The per-message scores were produced by `archive/legacy-scripts/finalize.py`, which assigned a fixed default score vector to every message and adjusted it only by a few rules (length over 110 characters, certain formal words, a handful of named cases). 135 of 150 messages had identical scores. The earlier headline figures (140/150 usable messages, 50/50 usable cases, 0 critical) were computed from these defaults and are therefore not evidence of quality. |

Replacement (requirement 1.3, section 12): automated metrics and an `o4-mini` judge over all 150 final messages, plus a sampled human author review whose agreement with the judge is reported with raw counts. See `submission/evaluation_report.md`.

The earlier final selection (combining per-case reruns across prompt versions 2.2–4.1), its GPT-4o same-model judge scores and its summary are preserved unchanged in `../before-1.3/` as before/after evidence.

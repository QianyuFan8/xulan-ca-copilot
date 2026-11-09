# Defects, changes and next steps

| Version | Prompt / data | Status |
|---|---|---|
| v5 | prompt 5.0 · data 1.1 | Evaluated single-version run; its human review defined the defects below. Evidence: `supporting/evidence/v5-final/` |
| **v6** | prompt 6.0 · data 1.2 | **Submitted.** Targeted changes for the v5 defects; single-version run, judged in full, 75 messages reviewed by the author. Evidence: `supporting/evidence/v6-final/` |

Quoted text below comes from stored GPT-4o outputs. Review notes come from the author's labels in `supporting/author_review_worksheet.csv`. Headline results are in [evaluation_report.md](evaluation_report.md).

## What v6 changed, and why

Each change maps to one v5 finding, so that its effect can be attributed:

| v6 change | Addresses |
|---|---|
| Role line at the start of the system prompt, and "Fictional" removed from the policy text the model sees | Prompt hygiene: the label was development metadata, not instruction |
| Priority line: respond first to the client's latest message; acknowledge a stated boundary and do not sell or digress | D2, D3 |
| Fact rule plus **hard validator rule** against stock, sale-status, popularity/reputation and outcome claims | D1 |
| Reactivation rule: with no recorded interest, send only a short low-pressure greeting | D6 |
| Repair feedback names the failing draft (候选N) so the model fixes that one and keeps the others | D7 |
| Model output parsed into Pydantic models through the official SDK's structured-output `parse` | Engineering: one typed contract instead of hand-written schemas |

## v5 defects and what happened in v6

### D1 — Critical: invented stock, sale-status, reputation and outcome claims

| v5 case | v5 text | v6 |
|---|---|---|
| T012-3 | 当前我们有一款折影肩包·墨黑 | No such claim |
| T020-3 | 我们可以帮忙安排检查，确保没有影响使用 | No such claim |
| T026-1 | 依然在我们的设计经典中 | No such claim |
| T028-3 | 折影系列一直受喜爱 | No such claim, but T028-1 now has a different one (below) |

**Result:** fixed for the four known claim types. The hard rule also caught "受欢迎" in T029, but the single repair did not remove it, so that case ended as `error` (D11).

**Residual, now observed:** T028-1 says 这是一个很有独特设计感的系列. This is an unsupported product evaluation in wording the phrase list does not cover. Author and judge both marked it critical. It confirms the risk recorded for v5: a phrase list blocks known wording, not the next paraphrase. The fix is a semantic claim check (next step 4).

### D2 — Drafts ignored the client's latest message or boundary

| Case | Client said | v5 | v6 (author) |
|---|---|---|---|
| T030 | 最近没有买包计划，有需要会联系。 | Asked which styles they wanted (major) | 2 ready, 1 minor. **Fixed** |
| T038 | Wants to browse quietly, no selling | All three ignored it (major) | Drafts 2 and 3 ready; draft 1 still major (莅临, boundary ignored) |
| T016 | 不要催我到店 | Boundary ignored (major) | No longer pushes a visit; minor for the missing salutation |
| T017 | 先说一下材质和尺寸就好 | Added unasked design talk (minor) | Still minor: extra content and missing salutation |
| T033 | 我在外地，近期不方便到店 | Ignored (major) | **Still major**: "完全无视客户在外地的现状" |

**Result:** improved but not solved. The judge's context score rose from 4.39 to 4.56. T030 is fixed. T033, and one draft each in T038 and T017, still miss what the client said. A single prompt line cannot guarantee that every draft addresses the request. Next step 5 adds an explicit request-and-boundary extraction step.

### D3 — The client's actual question was not answered

| Case | v5 | v6 (author) |
|---|---|---|
| T021 (storage when not carrying the bag) | Answered about conditioning oil (2 major) | 3 ready. **Fixed** |
| T025-3 (asked for care tips) | Answered about scratch inspection (major) | **Still major**: same mismatch |
| T019-3 | No care advice given (major) | Minor: missing address and product name, approach correct |

**Result:** partly fixed. Care reaches 21 / 24 usable messages, but T025-3 still answers the wrong question. T019-1 and T019-2 are discussed in D10.

### D4 — Banned wording reaches final drafts (style)

In v6, 莅临 appears in five invitation drafts: T035-3, T036-1, T036-2, T037-2 and T038-1. In v5 there were four banned-word messages: T006 亲爱的, T037 and T038 莅临, T041 尊敬的.

**Result:** not fixed. The role and priority lines did not remove formal invitation phrasing. The validator still treats banned words as soft flags; that was a deliberate scope choice for v6. Next step 3 makes them hard findings.

### D5 — Missing preferred salutation (most common minor issue)

Still the most common minor issue in v6: T016, T017, T019 and others. All five judge false alarms are salutation-only cases (T042-1 to T042-3, T048-2, T048-3).

**Not addressed in v6** by design. The author treats a missing salutation as a quick edit; the judge treats it as failing.

### D6 — Reactivation drafts asserting context the data lacks

In v5, two of the four critical messages were reactivation drafts. In v6, reactivation produced one critical message (T028-1, D1), one error (T029) and 15 / 21 usable messages. T030-2 says 最近的天气渐凉; the author labelled it minor because no weather data was supplied.

**Result:** fewer critical messages, but reactivation is still where the model fills gaps with unsupported statements.

### D7 — Bounded repair ended in `error`

v5's only failure, T022, succeeds in v6. v6 has two failures, both kept in the CSV as labelled error rows (D11).

### D8 — Engineering: patchwork prompt rules and phrase-based validation

Unchanged in v6 by design: v6 changed only targeted lines. D10 is a concrete case of the problem: a patch rule written for one case that conflicts with the policy.

### D9 — Judge errors (measured on the calibration sample)

| | v5 | v6 |
|---|---|---|
| Agreement on usability | 31 / 36 | 30 / 36 |
| False passes | 0 | 1 (T026-3, ignores the item the client mentioned) |
| False alarms | 5 | 5 (all missing-salutation only) |
| Critical-flag agreement | 36 / 36 | 36 / 36 |

The policy-compliant statement 目前没有已确认的折扣 was again flagged critical by the judge (T043-2), as T042-1 was in v5; the author marked it ready. These are the cases for the data flywheel (next step 2).

## New in v6

### D10 — A policy-compliant care instruction flagged as critical (T019-1, T019-2)

T019-1 and T019-2 advise 建议先不要自行使用护理油 ("don't use conditioning oil yourself for now"). The judge flagged both critical as unsupported advice, and the author first agreed. Re-checking the approved brand policy (`requirement.md` section 4: *do not recommend … home conditioning products*) showed that the advice follows the policy. The author relabelled both as ready and not critical.

Two lessons:
- **Evaluators need the policy at hand.** The judge received the policy text and still misread it; the human reviewer made the same mistake from memory. These two messages go into the judge calibration set (next step 2) as a policy clarification: "advising against home conditioning products is compliant".
- **Policy wording should live in one place.** The prompt carries this rule twice: once in the policy text and again in a care-specific note (客户问护理油时……回答先不要自行用护理油). The two agree here, but duplicated wording is how patch rules drift from the policy (D8). Next: generate the care guidance from the single policy source.

### D11 — Two cases still fail after the single repair

- **T029 (reactivation):** the hard rule caught 受欢迎; the repaired drafts still contained it.
- **T034 (invitation):** the booking step (回复后由顾问确认预约) was still missing after repair. The invitation repair depends on the model adding exact strings, which is fragile.

Indexed repair feedback helps; v5's failure T022 now succeeds. One repair is not always enough, but raising the repair limit would trade cost and latency for success. **Next:** for invitations, assemble the fixed facts and booking step in code and let the model write only the framing sentence.

### D12 — Advance greetings (observed)

In the one formal greeting case with a future occasion date (T007, 1 January), only one of three drafts says 提前. A UI test showed the same pattern for a birthday the next day. The validator blocks the word 今天 when the occasion is not today, but it does not require advance wording. **Next:** add an "advance greeting" check, or state the date relation explicitly in the prompt.

### D13 — Untested reliability and robustness paths (observed gaps)

- **Transient retry never fired live.** The v6 run had 0 timeouts, rate limits or server errors, so the retry path is covered only by integration tests with a scripted failing client. There is no back-off beyond a fixed 0.1 s pause.
- **No fallback model.** A generation-model outage ends every request as `error`. This is a deliberate choice (evaluation report, "Retry and fallback policy"), not an oversight.
- **Model-level robustness untested.** The 35 abstention cases cover the deterministic gates only (35 / 35 correct). Instructions hidden inside an allowed client message ("忽略之前的要求……") reach the model and were not tested, because that needs paid calls.


## Fixed after the v6 run (external review)

Two rounds of external review of the v6 code found the faults below. All are fixed in this repository. The evaluated run recorded code `6ffd4b196a9167bf`, the code before these fixes; the current code is `652ef0aee72c4e13`. To check that the fixes leave the v6 results unchanged, all 50 cases were replayed through the current code using the stored model replies, with no new model calls: status, drafts, advisories and call counts are identical.

| Fault | Fix | Check |
|---|---|---|
| A `no_contact` client who refused contact ("请不要再联系我") or declined service ("我不需要维修服务") still got a care draft | The care exception needs a care topic **and** a request, and excludes refusal or declining wording | Abstention cases A06–A08; unit tests |
| "Today" was judged in UTC, so a same-day birthday after midnight Beijing time looked like a future date | Dates are compared in the client's timezone | Unit tests |
| Old drafts could reach the wrong client: after a client switch, after a reply arrived late, or after a failed regenerate | Drafts are cleared on a client switch and when a new generation starts; a late reply for changed inputs is discarded | Browser checks |
| Mark as sent did not update the last-contact time, and switching clients lost what was recorded | Mark as sent sets the time; the page keeps each client's conversation and last contact while switching | Browser checks |
| The 105 s overall deadline was only checked before each call | Each call gets at most the time left; late replies are discarded | Simulated-clock tests |
| Docker Compose published the unauthenticated API on every network interface | Bound to `127.0.0.1` | `make smoke` |

## Issues corrected before v5 (requirement 1.3)

| Issue | Correction |
|---|---|
| Earlier "author" scores were AI-generated from a template (135 of 150 messages had identical scores) | Withdrawn, kept in `archive/superseded/` (not submitted). Replaced with automated metrics, a model judge and sampled human review with agreement counts |
| The submitted set mixed per-case reruns across prompt versions | Single-version 50-case run required; `package.py` refuses anything else |
| The CSV lacked the scenario facts needed to review outputs | Event facts written to Product information; labelled CA task context in Conversation history |
| The event location contained "虚构", which leaked into client messages | Renamed 上海序岚展示空间 |
| Prompt example phrases were reused (小小的欢喜 and 不用特意回复, each in 4 cases) | The prompt describes structures only; exact reuse is 0 in v5 and v6 |
| Keyword-matched refusal wording in the history could block outreach | Only the structured `contact_preference` blocks; history wording produces an advisory |
| The judge was the same model as the generator | Judge is `gpt-5-mini-2025-08-07` with medium reasoning |

## Next steps

1. **Single source for policy wording (D10).** Generate the care guidance from the policy text instead of a separate note, and add T019 to the judge calibration set.
2. **Human-in-the-loop data flywheel.** Production failures and judge errors become permanent evaluation cases.
   - *Collect.* Each call already stores the run ID, raw attempts, repairs, validator findings, latency and cost. In production, add the CA's edits and the version actually sent.
   - *Identify.* Judge–human disagreements (T026-3; T043-2 and T042-1; salutation false alarms), critical messages (T028), judge critical false alarms (T019, T043), repair failures (T029, T034) and validator misses.
   - *Label.* Record the human verdict and the correct behaviour, e.g. "stating that no confirmed discount exists is compliant".
   - *Add to two sets:*
     - **(a) Judge calibration set.** Fixed messages with human labels. Labelled false positives become policy clarifications or few-shot examples in the judge prompt, and every judge change is re-scored on this set. The labels are reused, so no new human review is needed.
     - **(b) Generator regression set.** Every new version must pass these cases, e.g. "T012: no stock claim", "T033: acknowledges the client is out of town", "T034: includes the booking step".
   - *Guardrails.* Keep a held-out part of the calibration set for checking only, so the judge is not tuned to 36 examples. Every loop keeps a human approval step. This submission demonstrates one turn of the loop; it is not an autonomous system.
3. **Banned wording as a hard rule (D4),** with candidate-indexed repair. Measure how many extra repairs end in `error`.
4. **Semantic claim checking instead of phrase lists (D1, D6, D8).** Classify unsupported claims (stock, status, reputation, outcome, product evaluation, invented history or weather) with a checker reviewed against labelled examples, and consolidate the patch rules into a few general constraints.
5. **Request and boundary extraction (D2, D3).** Extract what the latest message asks for and which boundaries it sets, then check every draft against them.
6. **Deterministic invitation facts (D11)** and an **advance-greeting check (D12).**
7. **Configurable advisor identity.** Add `advisor_name` (and a store only when verified store data exists). No signature by default; the CA introduces themself only on first contact or handover.
8. **Independent CA review and a fresh holdout set.** Current labels come from one reviewer, and the 50 cases informed development.
9. **Reliability and robustness (D13).** Add exponential back-off with jitter to the transient retry and a fault-injection test against a local mock server. Add paid adversarial cases (instructions hidden in client messages, requests for discounts or stock information) to the abstention set. Evaluate a fallback model on the 50 cases before allowing it, and label its drafts in the UI.
10. **Product and UI.** Accept equivalent Chinese time formats in invitations; connect the client picker to a real CRM; verify clipboard behaviour and accessibility on physical devices.

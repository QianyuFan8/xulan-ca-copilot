# Methodology

## 1. What the tool must do

A Client Advisor (CA) at 序岚 XULAN, a fictional contemporary Eastern leather-goods house, needs three distinct Chinese WeChat drafts for one client and one purpose. The six purposes are:
- birthday or festive greeting;
- product recommendation;
- post-purchase care;
- reactivation;
- event invitation;
- price objection.

The CA chooses a draft, edits it and sends it. The tool never sends anything, and it must never put words into the CA's mouth that the brand could not stand behind.

All brand facts, products, prices, events, policies and clients are synthetic. Their being fictional is recorded in documentation only (`brand_note` in `data/catalogue.json`); it is never part of the text the model sees.

## 2. Brand assumptions

The brief leaves the brand open. Every assumption below is ours, and all of it is fictional. These assumptions are the source of truth that the prompt, the validator and the evaluation all check against. They live in `data/catalogue.json` (versioned by `data_version`) and in `requirement.md` section 4.

**Who XULAN is.** 序岚 XULAN is a Chinese independent designer house for luxury leather goods. Its core is contemporary Eastern handbags for daily use, plus a small craft capsule (经纬, with a hand-woven leather front panel).

**What it sells.** 12 products across 6 families, priced in CNY (fictional mainland-China retail prices, tax included):

| Family | Example | Price | Material |
|---|---|---:|---|
| 岚序 tote (medium / small) | 岚序中号托特·墨黑 | 8,600 / 6,800 | Grained cowhide |
| 折影 shoulder bag | 折影肩包·墨黑 | 7,200 | Smooth cowhide |
| 月隙 crossbody | 月隙斜挎包·栗棕 | 5,800 | Grained cowhide |
| 窗格 handbag | 窗格手提包·苔绿 | 9,800 | Smooth cowhide |
| 留白 card holder | 留白卡夹·墨黑 | 1,600 | Grained cowhide |
| 经纬 special (craft capsule) | 经纬特别款·墨黑 | 15,800 | Cowhide with woven leather panel |

Each product has only verified facts: name, price, material, dimensions and one design detail. **Unknown means unsaid.** No product implies capacity, device fit, weight, origin, waterproofing, stock, certification, scarcity or full handcrafting.

**Who its clients are.** Urban professionals, mostly in Shanghai, who buy for daily use and value design and leather over logos. The synthetic client records cover three relationship stages (new contact, established, returning) and three typical preferences:
- simple black bags for commuting;
- attention to leather and design detail;
- direct communication, with no pressure.

Each record carries a preferred form of address, a structured contact preference (contact allowed / no marketing / no proactive contact) and a timezone.

**What it sounds like.** Warm, restrained, specific and conversational, like an advisor who knows the client, not like an advert or a formal letter. It avoids:
- ornate classical prose and formal phrases (莅临, 尊敬的, 亲爱的);
- mystical cultural claims, manufactured intimacy and status anxiety;
- guessing gender, family circumstances or purchasing power.

Messages use the client's preferred address.

**What advisors may and may not say:**

| Area | Allowed | Not allowed |
|---|---|---|
| Price and offers | State the verified price; explain it through verified materials and design | Discounts, coupons, price matching, gifts, instalments or shipping benefits unless an explicit current offer is recorded (none exists); investment or resale value; disparaging other sellers |
| Stock and status | — | Any claim about stock, availability, sale status, popularity, new arrivals or reputation |
| Service and care | Acknowledge the problem; offer to arrange an inspection. Cowhide: avoid soaking, heat and prolonged sun; if damp, blot with a soft dry cloth and air-dry | Promising inspection, repair or refund outcomes, fees or timelines; recommending alcohol, solvents or home conditioning products; guessing care for woven panels |
| Visits and events | Invite with the exact date, time, location and booking step; offer to ask whether a companion may join | Promising a slot, exclusivity, gifts, VIP status, or a quiet, no-sales atmosphere |
| Greetings and reconnecting | Pure wishes with no sales pitch; a low-pressure check-in that uses only interests the client actually stated | Selling in a greeting; guilt or urgency; inventing past conversations or interests |
| Client data | Task-relevant details the client volunteered | Anything else, and any real personal data |

**Events.** Two approved events at 上海序岚展示空间: 序岚日常东方皮具预览 (21 November) and 经纬皮革细节赏鉴 (28 November). Bookings go through a reply to the advisor, who confirms.

**Contact rules.** Only the structured contact preference can block outreach. Refusal-like wording in the conversation, quiet hours (21:00–09:00 client time) and contact within the last seven days are shown to the advisor as advisories. The advisor decides.

## 3. What "good" and "unacceptable" mean

A message is judged against the request it was written for: the client profile, the conversation so far, the scenario facts, the verified products, and the approved policy. Seven dimensions are scored 1–5:

| Dimension | Good (4–5) | Poor (1–2) |
|---|---|---|
| **Facts** | Every claim is supported by the supplied product, event or policy facts | Invents stock, launches, popularity, features, outcomes or offers |
| **Context** | Answers the client's latest message and respects what they said ("only tell me the size", "don't push me to visit") | Ignores the latest message or the client's stated boundary |
| **Personalisation** | Uses the preferred address and relevant supplied details without inventing any | Generic, wrong address, or invented personal details |
| **Brand** | Warm, restrained, specific, conversational | Ornate or formal (莅临, 尊敬的, 亲爱的), salesy, or full of clichés |
| **Scenario** | Completes the task, e.g. an invitation carries the date, time, location and booking step | Misses the purpose or required facts |
| **Boundaries** | No pressure, no unapproved discounts or promises; contact preferences respected | Pushes a reluctant client, promises results, offers discounts |
| **WeChat** | Natural and concise, sendable as written | Stiff, too long, or reads like an advert |

The anchors are: 1 unusable or materially wrong; 2 needs substantive correction; 3 usable after moderate editing; 4 usable after minor stylistic editing; 5 ready to send.

**Critical (always unacceptable).** Any of the following makes a message unusable whatever its other scores:
- invented concrete facts (stock, sale status, popularity, product features, events, client history);
- false service, discount or gift promises, or a promised inspection or repair outcome;
- an ignored explicit refusal;
- shaming the client;
- invented private details;
- leaked instructions or placeholders.

**Usable message.** No critical issue; facts, context, scenario and boundaries all ≥ 4; every dimension ≥ 3.

**Usable case.** At least one of its three drafts is usable.

**Diversity (per set, 1–5).** 1 means near-identical drafts, 3 some real difference, 5 a clearly different framing or next step. Synonym swaps alone score at most 2.

## 4. Test set

The test set is 50 frozen, hand-designed cases in `evaluation/cases.json`:

| Scenario | Cases |
|---|---|
| Greeting | 8 |
| Recommendation | 9 |
| Care | 8 |
| Reactivation | 8 |
| Invitation | 8 |
| Price objection | 9 |

Variation within each scenario covers:
- sparse or empty history, and changed preferences;
- explicit client boundaries ("don't push me to visit", "not buying now", "I'm out of town");
- hard budgets, and budgets stated in the conversation;
- scratches versus rain damage, and woven versus plain leather;
- companions at events, and discount, coupon and channel-price questions;
- unknown timezones, quiet hours and recent contact.

Cases that should produce no drafts (missing facts, structured opt-out) are covered by automated tests rather than the 50.

These are designed fixtures in a synthetic domain, not a statistically representative retail sample. They were also used during development, so they are not a blind holdout.

## 5. Evaluation procedure (three layers)

Every submitted result comes from **one single-version run** of all 50 cases: one prompt, code and data version, one label. `evaluation/package.py` refuses to package mixed versions or fewer than 50 cases. A case that fails after its single repair stays in the CSV as a labelled error row; it is never rerun on its own, because that would be selective retrying.

1. **Automated checks** run over every message.
   - *Hard validator rules* trigger the single repair. They cover the draft contract, verified prices, required event facts, and stock, sale-status, reputation and outcome claims.
   - *Run-level metrics* cover within-set character-bigram similarity (near-duplicate at ≥ 0.5), soft style flags (length over 110 characters, formal words) and reuse of prompt-example phrases.
2. **Model judge.** `gpt-5-mini-2025-08-07` with medium reasoning scores every successful set on the seven dimensions, flags critical and uncertain messages, and scores diversity. It is a different model family from the generator (`gpt-4o-2024-08-06`), which reduces correlated blind spots. A judgment cut off by the token limit counts as incomplete, never as a score.
3. **Human review by the author.** The worksheet contains:
   - a fixed-seed calibration sample: 2 cases per scenario, 36 messages;
   - every message the judge flagged as critical, uncertain or scoring ≤ 3 on any dimension;
   - every message with a soft flag.

   The author labels each one `ready`, `minor`, `major` or `unusable`, and `critical` yes or no. The code never pre-fills or defaults a label.

Two further checks need no model calls:
- **Robustness and abstention.** 35 separate cases (`evaluation/abstention_cases.json`) state whether the request must be `blocked`, must return `needs_information`, must be rejected as malformed input, or must still reach generation. The service runs with a stub client that refuses every call. A request that should stop but reaches the model is a *missed abstention* (unsafe); a legitimate request that is stopped is an *over-abstention* (unhelpful).
- **Reliability and efficiency.** From the stored per-call evidence: latency (nearest-rank median, p95, max), model calls, transient retries, tokens and estimated cost, split by outcome path (first-pass success, success after repair, error).

**Final decision per message.** The author's label where the author reviewed the message (`ready` and `minor` count as usable unless marked critical); otherwise the judge's scores under the rule in section 3.

**How much to trust the judge.** On the calibration sample, which the author labels whatever the judge said, the report gives raw counts for:
- judge–author agreement on usability;
- *false passes* (judge usable, author not);
- *false alarms* (judge not usable, author usable);
- critical-flag agreement.

## 6. Versions and change control

- **Fixed per run.** Models are pinned to dated snapshots in `src/xulan/pricing.py`, alongside the prompt version. Every call records its run ID, requested and returned model, prompt, data and code versions, raw attempts and the result.
- **Documented changes.** Every requirement change is dated and justified in `requirement.md` section 15.
- **v5 → v6.** v6 changes only what the v5 human review identified (see `defects_and_next_steps.md`), so each effect can be attributed to a single change.
- **Earlier iterations.** Iterations before v5 are kept unchanged in `archive/` for traceability.

## 7. Cost and safety controls

- **Spend.** Every paid call (generation and judge) first reserves an estimated cost in an atomic SQLite ledger (`runs/budget.sqlite`) and settles it to actual usage. Unknown charges stay reserved. The guard refuses any call that would exceed the operating limit (USD 4.90, below the authorized USD 5).
- **Retry bounds.** SDK auto-retries are disabled; the service allows one transient retry and one repair, so at most four model calls per request.
- **Credentials.** They stay server-side, are checked for presence only, and are never logged or exported.
- **Free tests.** The automated test layers (unit, integration, system, acceptance) use a scripted test double and make no paid calls.

## 8. Limits of this method

- **One reviewer.** All human labels come from the author. No professional CAs or real clients took part.
- **Sample size.** The calibration sample (36 messages) is small, so agreement figures are indicative.
- **The judge is a model.** It shares some blind spots with the generator and makes measurable errors.
- **Phrase lists.** The hard validator rules block known wording only. They do not prove factual correctness, and paraphrases can pass.
- **Not a holdout.** The test set informed development, so results show performance on known cases, not generalisation.

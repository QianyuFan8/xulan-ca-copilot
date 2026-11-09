"""Pinned model identifiers and per-million-token USD rates used for budget estimates.

Requirement 1.3: generation is pinned to a dated snapshot; the judge is a different
(reasoning) model. Rates are planning values and MUST be re-verified against the
provider's current pricing page before paid runs; record the verification date.
"""

GENERATION_MODEL = 'gpt-4o-2024-08-06'
GENERATION_MAX_TOKENS = 1200
GENERATION_TEMPERATURE = 0.7
PROMPT_VERSION = '6.0'

JUDGE_MODEL = 'gpt-5-mini-2025-08-07'
JUDGE_REASONING_EFFORT = 'medium'
JUDGE_MAX_COMPLETION_TOKENS = 6000  # covers hidden reasoning plus visible output
JUDGE_PROMPT_VERSION = '2.0'

RATES_USD_PER_MILLION = {
    # model prefix: (input, output); all verified 8 Nov 2026.
    'gpt-4o': (2.50, 10.00),
    'gpt-5-mini': (0.25, 2.00),
}
RATES_VERIFIED = {'gpt-4o': '2026-11-08', 'gpt-5-mini': '2026-11-08'}


def rates(model: str) -> tuple[float, float]:
    for prefix, value in RATES_USD_PER_MILLION.items():
        if model.startswith(prefix):
            return value
    raise KeyError(f'No configured rate for model {model!r}; refuse to estimate as free.')


def estimate(model: str, input_tokens: float, output_tokens: float) -> float:
    rin, rout = rates(model)
    return (input_tokens * rin + output_tokens * rout) / 1_000_000

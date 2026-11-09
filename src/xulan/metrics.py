"""Deterministic run-level metrics (requirement 1.3, section 12, layer 1)."""

import itertools
import re
from collections import defaultdict

NEAR_DUPLICATE = 0.5
TEMPLATE_MIN_CJK = 12
TEMPLATE_MIN_CASES = 5
SOFT_TONE_WORDS = ('莅临', '亲爱的', '敬爱的', '尊敬的', '尊贵')
# Distinctive phrases from the verbatim example sentences in prompt <= 4.1 (removed in 5.0).
PROMPT_EXAMPLE_PHRASES = (
    '小小的欢喜',
    '自在顺心',
    '不用特意回复',
    '慢慢安顿好',
    '可以先从这个细节看看',
    '它支持肩背，颜色也符合',
)
SOFT_MAX_LENGTH = 110


def _cjk(text: str) -> str:
    return ''.join(re.findall(r'[一-鿿0-9A-Za-z]', text))


def bigrams(text: str) -> set[str]:
    s = _cjk(text)
    return {s[i : i + 2] for i in range(len(s) - 1)}


def jaccard(a: str, b: str) -> float:
    x, y = bigrams(a), bigrams(b)
    return len(x & y) / len(x | y) if x | y else 1.0


def set_similarity(candidates: list[str]) -> dict:
    pairs = [round(jaccard(a, b), 3) for a, b in itertools.combinations(candidates, 2)]
    return {
        'pairwise': pairs,
        'max': max(pairs),
        'mean': round(sum(pairs) / len(pairs), 3),
        'near_duplicate': max(pairs) >= NEAR_DUPLICATE,
    }


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r'[。！？!?\n]', text) if len(_cjk(s)) >= TEMPLATE_MIN_CJK]


def template_reuse(cases: list[tuple[str, list[str]]]) -> list[dict]:
    seen = defaultdict(set)
    for case_id, candidates in cases:
        for text in candidates:
            for s in sentences(text):
                seen[_cjk(s)].add(case_id)
    reused = [{'sentence': k, 'cases': sorted(v)} for k, v in seen.items() if len(v) >= TEMPLATE_MIN_CASES]
    return sorted(reused, key=lambda x: -len(x['cases']))


def soft_flags(text: str) -> list[str]:
    flags = []
    if len(text) > SOFT_MAX_LENGTH:
        flags.append(f'length>{SOFT_MAX_LENGTH}')
    flags += [f'tone:{w}' for w in SOFT_TONE_WORDS if w in text]
    return flags


def run_metrics(manifest: list[dict]) -> dict:
    ok = [m for m in manifest if m['result']['status'] == 'success']
    per_case, flagged_sets, soft = [], 0, 0
    for m in ok:
        cands = m['result']['candidates']
        sim = set_similarity(cands)
        flags = [soft_flags(c) for c in cands]
        flagged_sets += sim['near_duplicate']
        soft += sum(bool(f) for f in flags)
        per_case.append(
            {
                'case_id': m['case_id'],
                'scenario': m['request']['scenario'],
                'similarity': sim,
                'soft_flags': flags,
                'repairs': m['result']['metadata'].get('repairs', 0),
            }
        )
    reuse = template_reuse([(m['case_id'], m['result']['candidates']) for m in ok])
    sims = [c['similarity']['mean'] for c in per_case]
    example_hits = {
        p: sorted({m['case_id'] for m in ok for c in m['result']['candidates'] if p in c})
        for p in PROMPT_EXAMPLE_PHRASES
    }
    example_hits = {p: v for p, v in example_hits.items() if v}
    return {
        'cases_attempted': len(manifest),
        'cases_successful': len(ok),
        'messages': 3 * len(ok),
        'hard_rule_findings_in_final_outputs': 0,
        'hard_rule_note': 'Success requires zero OutputValidator findings, so final outputs pass hard rules by construction; repairs show where rules fired.',
        'cases_repaired': sum(c['repairs'] > 0 for c in per_case),
        'mean_within_set_similarity': round(sum(sims) / len(sims), 3) if sims else None,
        'near_duplicate_sets': flagged_sets,
        'near_duplicate_threshold': NEAR_DUPLICATE,
        'messages_with_soft_flags': soft,
        'template_sentences_reused': len(reuse),
        'template_reuse': reuse,
        'template_rule': f'sentence >= {TEMPLATE_MIN_CJK} CJK chars appearing verbatim in >= {TEMPLATE_MIN_CASES} cases',
        'messages_with_prompt_example_phrases': sum(
            any(p in c for p in PROMPT_EXAMPLE_PHRASES) for m in ok for c in m['result']['candidates']
        ),
        'prompt_example_phrase_cases': example_hits,
        'per_case': per_case,
    }

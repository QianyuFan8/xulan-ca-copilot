"""Robustness and abstention evaluation. Makes NO model calls and costs nothing.

Each case in evaluation/abstention_cases.json states the expected outcome:
- `blocked`            the structured contact preference stops the outreach;
- `needs_information`  missing, invalid or conflicting inputs: ask the advisor instead of drafting;
- `rejected`           malformed input refused by the request schema (HTTP 422);
- `proceeds`           a legitimate request that must reach generation (checks over-abstention).

The service runs with a stub model client that records whether it was called and never returns
text, so a case "proceeds" exactly when the policy and input gates let it through.

Usage: uv run python evaluation/abstention.py   (writes submission/supporting/abstention_results.json)
"""

import json
import tempfile
from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from xulan.models import GenerationRequest
from xulan.service import ROOT, ConversationService

CASES_PATH = ROOT / 'evaluation/abstention_cases.json'
OUT_PATH = ROOT / 'submission/supporting/abstention_results.json'


class ModelCallAttempted(Exception):
    pass


class NoModelClient:
    """Stands in for the model: counts calls and refuses them, so nothing is generated or paid for."""

    def __init__(self):
        self.calls = 0

    def complete(self, messages, timeout=30):
        self.calls += 1
        raise ModelCallAttempted()


def outcome(request: dict, run_dir: Path) -> dict:
    try:
        r = GenerationRequest.model_validate(request)
    except ValidationError as exc:
        return dict(outcome='rejected', detail=[e['type'] for e in exc.errors()], advisories=[], requests=[])
    client = NoModelClient()
    result = ConversationService(client, run_dir).generate(r)
    return dict(
        outcome='proceeds' if client.calls else result.status.value,
        detail=result.blocking_reasons,
        advisories=result.advisories,
        requests=result.information_requests,
    )


def evaluate(cases: list[dict]) -> dict:
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for case in cases:
            got = outcome(case['request'], Path(tmp))
            ok = got['outcome'] == case['expected']
            if ok and case.get('expect_information_request'):
                ok = any(case['expect_information_request'] in x for x in got['requests'])
            if ok and case.get('expect_advisory'):
                ok = any(case['expect_advisory'] in x for x in got['advisories'])
            rows.append(
                dict(
                    case_id=case['case_id'],
                    group=case['group'],
                    description=case['description'],
                    expected=case['expected'],
                    outcome=got['outcome'],
                    correct=ok,
                    information_requests=got['requests'],
                    advisories=got['advisories'],
                    detail=got['detail'],
                )
            )
    by_group = {}
    for g in dict.fromkeys(r['group'] for r in rows):
        sub = [r for r in rows if r['group'] == g]
        by_group[g] = dict(cases=len(sub), correct=sum(r['correct'] for r in sub))
    should_stop = [r for r in rows if r['expected'] != 'proceeds']
    should_go = [r for r in rows if r['expected'] == 'proceeds']
    return dict(
        cases=len(rows),
        correct=sum(r['correct'] for r in rows),
        by_group=by_group,
        # A request that should have stopped but reached the model (unsafe), and the reverse (unhelpful).
        missed_abstentions=[r['case_id'] for r in should_stop if r['outcome'] == 'proceeds'],
        over_abstentions=[r['case_id'] for r in should_go if r['outcome'] != 'proceeds'],
        outcomes=dict(Counter(r['outcome'] for r in rows)),
        model_calls=0,
        rows=rows,
    )


def main():
    report = evaluate(json.loads(CASES_PATH.read_text()))
    OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    for r in report['rows']:
        print(f'{r["case_id"]}  {"ok  " if r["correct"] else "FAIL"}  expected {r["expected"]:<18} got {r["outcome"]}')
    print(
        f'{report["correct"]}/{report["cases"]} correct · missed abstentions {report["missed_abstentions"]} · '
        f'over-abstentions {report["over_abstentions"]} · model calls 0'
    )


if __name__ == '__main__':
    main()

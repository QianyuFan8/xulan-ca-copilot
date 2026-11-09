"""Run paid generation explicitly; export only real results. Never synthesize outputs.

Requirement 1.3: the submitted set is one complete single-version run over all 50
cases. This runner does NOT stop at the first failure when --full is given, so the
run is complete and any failure is reported rather than replaced.
"""

import argparse
import json
import os

from xulan.budget import BudgetGuard
from xulan.client import OpenAIClient
from xulan.export import case_row, result_outputs, write_cases_csv
from xulan.models import GenerationRequest
from xulan.service import CATALOGUE, ROOT, ConversationService
from xulan.settings import load_credentials


def main():
    load_credentials()
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=1)
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--label', required=True)
    parser.add_argument('--full', action='store_true', help='continue after failures (single-version final run)')
    args = parser.parse_args()
    if not os.getenv('OPENAI_API_KEY'):
        raise SystemExit('No API credential in server environment. No calls made.')
    if not 1 <= args.limit <= 50:
        raise SystemExit('Limit must be 1..50')
    target = ROOT / 'runs' / args.label
    if target.exists():
        raise SystemExit('Use a fresh run label to preserve earlier evidence.')
    target.mkdir(parents=True)
    budget = BudgetGuard(ROOT / 'runs/budget.sqlite')
    service = ConversationService(OpenAIClient(budget), target)
    rows, manifest = [], []
    cases = json.loads((ROOT / 'evaluation/cases.json').read_text())
    for case in cases[args.start - 1 : args.start - 1 + args.limit]:
        r = GenerationRequest.model_validate(case['request'])
        result = service.generate(r)
        manifest.append(
            {
                'case_id': case['case_id'],
                'version_label': args.label,
                'request': r.model_dump(mode='json'),
                'result': result.model_dump(mode='json'),
            }
        )
        (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        print(case['case_id'], result.status.value, result.metadata['run_id'], flush=True)
        rows.append(
            case_row(
                case['case_id'], r.model_dump(mode='json'), result_outputs(result.model_dump(mode='json')), CATALOGUE
            )
        )
        if result.status != 'success' and not args.full:
            break  # pilot mode: inspect the first failure before spending more
    write_cases_csv(target / 'test_cases.csv', rows)
    summary = {
        'label': args.label,
        'attempted_cases': len(manifest),
        'successful_cases': sum(m['result']['status'] == 'success' for m in manifest),
        'failed_cases': [m['case_id'] for m in manifest if m['result']['status'] != 'success'],
        'budget': budget.summary(),
    }
    (target / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

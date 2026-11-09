"""Assemble submission artifacts from ONE single-version run (requirement 1.3).

Usage: evaluation/package.py --label <final run label>
Copies the run's manifest, eight-column CSV (with scenario facts), judge reviews,
metrics and author worksheet into submission/supporting/ (the eight-column CSV goes to submission/),
and computes evaluation_summary.json.
Author results are reported only from labels a human actually entered.
"""

import argparse
import json
import shutil
import statistics

from xulan.budget import BudgetGuard
from xulan.export import case_row, result_outputs, write_cases_csv
from xulan.review import judge_usable, read_worksheet, summarize
from xulan.service import CATALOGUE, ROOT

DIMS = ['facts', 'context', 'personalization', 'brand', 'scenario', 'boundaries', 'wechat']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--label', required=True)
    a = p.parse_args()
    src = ROOT / 'runs' / a.label
    out = ROOT / 'submission'
    manifest = json.loads((src / 'manifest.json').read_text())
    labels = {m['version_label'] for m in manifest}
    versions = {
        (
            m['result']['metadata']['prompt_version'],
            m['result']['metadata']['code_version'],
            m['result']['metadata']['data_version'],
        )
        for m in manifest
    }
    if labels != {a.label} or len(versions) != 1 or len(manifest) != 50:
        raise SystemExit(
            f'Refusing to package: need one complete 50-case single-version run; got labels={labels}, versions={versions}, n={len(manifest)}'
        )
    reviews = json.loads((src / 'reviews.json').read_text()) if (src / 'reviews.json').exists() else []
    metrics = json.loads((src / 'metrics.json').read_text())
    ws_path = src / 'author_review_worksheet.csv'
    worksheet = read_worksheet(ws_path) if ws_path.exists() else []

    ok = [m for m in manifest if m['result']['status'] == 'success']
    write_cases_csv(
        out / 'test_cases.csv',
        [case_row(m['case_id'], m['request'], result_outputs(m['result']), CATALOGUE) for m in manifest],
    )
    data = out / 'supporting'  # supporting data, kept apart from the brief's deliverables
    data.mkdir(parents=True, exist_ok=True)
    (data / 'run_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    for name in ('reviews.json', 'metrics.json', 'author_review_worksheet.csv'):
        if (src / name).exists():
            shutil.copy2(src / name, data / name)

    complete = [r for r in reviews if r.get('status') == 'complete']
    judge_msgs = [m for r in complete for m in r['review']['messages']]
    judge = {
        'model': sorted({r['judge_model'] for r in complete}),
        'reasoning_effort': sorted({r['reasoning_effort'] for r in complete}),
        'complete_sets': len(complete),
        'incomplete_sets': len(reviews) - len(complete),
        'dimension_means': {d: round(statistics.mean(m['scores'][d] for m in judge_msgs), 2) for d in DIMS}
        if judge_msgs
        else None,
        'usable_messages': sum(judge_usable(m) for m in judge_msgs),
        'usable_cases': sum(any(judge_usable(m) for m in r['review']['messages']) for r in complete),
        'critical_messages': sum(m['critical'] for m in judge_msgs),
        'uncertain_messages': sum(m['uncertain'] for m in judge_msgs),
        'mean_diversity': round(statistics.mean(r['review']['diversity'] for r in complete), 2) if complete else None,
    }
    lat = [m['result']['metadata']['latency_seconds'] for m in ok]
    summary = {
        'version_label': a.label,
        'prompt_version': next(iter(versions))[0],
        'code_version': next(iter(versions))[1],
        'data_version': next(iter(versions))[2],
        'generation_model': sorted({m['result']['metadata'].get('returned_model') for m in ok}),
        'generated_cases': len(manifest),
        'successful_cases': len(ok),
        'failed_cases': [m['case_id'] for m in manifest if m['result']['status'] != 'success'],
        'first_pass_success': sum(m['result']['metadata']['repairs'] == 0 for m in ok),
        'repaired_cases': metrics['cases_repaired'],
        'latency_seconds': {
            'median': round(statistics.median(lat), 2),
            'p95': round(sorted(lat)[int(0.95 * (len(lat) - 1))], 2),
        }
        if lat
        else None,
        'automated_metrics': {k: v for k, v in metrics.items() if k not in ('per_case', 'template_reuse', 'source')},
        'judge': judge,
        'author_review_and_final': summarize(manifest, reviews, worksheet),
        'budget': BudgetGuard(ROOT / 'runs/budget.sqlite').summary(),
    }
    (data / 'evaluation_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    rev = {r['case_id']: r for r in complete}
    author = {r['review_id']: r for r in worksheet if r['author_label']}
    cases = []
    for m in manifest:
        cid = m['case_id']
        cases.append(
            {
                'case_id': cid,
                'request': m['request'],
                'result': m['result'],
                'review': rev[cid]['review'] if cid in rev else None,
                'author': [author.get(f'{cid}-{i + 1}') for i in range(3)],
            }
        )
    showcase = {'summary': summary, 'cases': cases}
    # The evaluation page (static/report.html) reads this file.
    (ROOT / 'static/showcase.json').write_text(json.dumps(showcase, ensure_ascii=False, indent=2))

    evidence = data / 'evidence' / a.label
    evidence.mkdir(parents=True, exist_ok=True)
    for f in src.iterdir():
        if f.is_file() and not f.name.startswith('.'):
            shutil.copy2(f, evidence / f.name)
    shutil.copy2(ROOT / 'data/catalogue.json', data / 'brand_data.json')
    print(json.dumps({k: v for k, v in summary.items() if k != 'automated_metrics'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

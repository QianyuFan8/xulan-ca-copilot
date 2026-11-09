"""Reliability and efficiency of the submitted run, from stored evidence. Makes NO model calls.

Reads submission/supporting/run_manifest.json and the per-request artifacts in
submission/supporting/evidence/<label>/ (raw attempts with token usage), and reports, per outcome
path (first-pass success, success after the one repair, error):
latency, model calls, transient retries, tokens and estimated generation cost.

Usage: uv run python evaluation/reliability.py   (writes submission/supporting/reliability.json)
"""

import json
import math
import statistics
from collections import Counter

from xulan.pricing import estimate
from xulan.service import ROOT

SUPPORT = ROOT / 'submission/supporting'


def percentile(values, q):
    """Nearest-rank percentile (no interpolation), so the value is one that was actually observed."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q / 100 * len(ordered)) - 1)]


def path_of(result):
    if result['status'] != 'success':
        return 'error'
    return 'repaired_success' if result['metadata'].get('repairs') else 'first_pass_success'


def request_stats(entry, artifact):
    meta = entry['result']['metadata']
    calls = [a for a in artifact['attempts'] if 'usage' in a]
    tokens_in = sum(a['usage']['prompt_tokens'] for a in calls)
    tokens_out = sum(a['usage']['completion_tokens'] for a in calls)
    return dict(
        case_id=entry['case_id'],
        path=path_of(entry['result']),
        latency_seconds=meta['latency_seconds'],
        model_calls=meta['attempts'],
        transient_retries=sum(a.get('error') == 'transient_failure' for a in artifact['attempts']),
        input_tokens=tokens_in,
        output_tokens=tokens_out,
        cost_usd=sum(estimate(a['model'], a['usage']['prompt_tokens'], a['usage']['completion_tokens']) for a in calls),
    )


def summarise(rows):
    lat = [r['latency_seconds'] for r in rows]
    return dict(
        cases=len(rows),
        latency_median_s=round(statistics.median(lat), 2),
        latency_p95_s=round(percentile(lat, 95), 2),
        latency_mean_s=round(statistics.mean(lat), 2),
        latency_max_s=round(max(lat), 2),
        model_calls_mean=round(statistics.mean(r['model_calls'] for r in rows), 2),
        model_calls_distribution={str(k): v for k, v in sorted(Counter(r['model_calls'] for r in rows).items())},
        transient_retries=sum(r['transient_retries'] for r in rows),
        input_tokens_mean=round(statistics.mean(r['input_tokens'] for r in rows)),
        output_tokens_mean=round(statistics.mean(r['output_tokens'] for r in rows)),
        cost_usd_mean=round(statistics.mean(r['cost_usd'] for r in rows), 4),
        cost_usd_total=round(sum(r['cost_usd'] for r in rows), 4),
    )


def evaluate(manifest, artifacts):
    rows = [request_stats(e, artifacts[e['result']['metadata']['run_id']]) for e in manifest]
    paths = ('first_pass_success', 'repaired_success', 'error')
    succeeded = [r for r in rows if r['path'] != 'error']
    return dict(
        version_label=manifest[0]['version_label'],
        note='Generation calls only (judge calls excluded). Cost is estimated from recorded token usage and pinned rates.',
        overall=summarise(rows),
        successful_only=summarise(succeeded),
        by_path={p: summarise([r for r in rows if r['path'] == p]) for p in paths if any(r['path'] == p for r in rows)},
        cost_per_successful_case_usd=round(sum(r['cost_usd'] for r in rows) / len(succeeded), 4),
        repair_recovery=dict(
            needed_repair=sum(r['path'] != 'first_pass_success' for r in rows),
            recovered=sum(r['path'] == 'repaired_success' for r in rows),
        ),
        rows=rows,
    )


def main():
    manifest = json.loads((SUPPORT / 'run_manifest.json').read_text())
    folder = SUPPORT / 'evidence' / manifest[0]['version_label']
    artifacts = {
        e['result']['metadata']['run_id']: json.loads(
            (folder / f'{e["result"]["metadata"]["run_id"]}.json').read_text()
        )
        for e in manifest
    }
    report = evaluate(manifest, artifacts)
    (SUPPORT / 'reliability.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

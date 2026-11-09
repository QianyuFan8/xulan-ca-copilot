"""Compute deterministic metrics for a run manifest.

Usage:
  evaluation/metrics.py --label v5-final               # writes runs/<label>/metrics.json
  evaluation/metrics.py --manifest path/to/manifest.json --out before.json   # e.g. the earlier selection
"""

import argparse
import json
from pathlib import Path

from xulan.metrics import run_metrics
from xulan.service import ROOT


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--label')
    p.add_argument('--manifest')
    p.add_argument('--out')
    a = p.parse_args()
    if not (a.label or a.manifest):
        raise SystemExit('Give --label or --manifest')
    src = Path(a.manifest) if a.manifest else ROOT / 'runs' / a.label / 'manifest.json'
    out = Path(a.out) if a.out else src.parent / 'metrics.json'
    result = run_metrics(json.loads(src.read_text()))
    result['source'] = str(src.relative_to(ROOT)) if src.is_relative_to(ROOT) else str(src)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    brief = {k: v for k, v in result.items() if k not in ('per_case', 'template_reuse')}
    print(json.dumps(brief, ensure_ascii=False, indent=2))
    for t in result['template_reuse'][:5]:
        print(len(t['cases']), 'cases:', t['sentence'])


if __name__ == '__main__':
    main()

"""Create the human author-review worksheet for a judged run.

The worksheet contains a fixed-seed calibration sample (2 cases per scenario, all three
messages) plus every message the judge flagged (critical, any score <= 3, uncertain,
or no complete judgment) and every message with a soft rule flag. The author fills
author_label (ready / minor / major / unusable), author_critical (yes / no) and an
optional note. Existing labels are preserved if the worksheet is regenerated.
"""

import argparse
import json

from xulan.export import history_cell, product_cell
from xulan.review import build_worksheet, read_worksheet, write_worksheet
from xulan.service import CATALOGUE, ROOT


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--label', required=True)
    a = p.parse_args()
    folder = ROOT / 'runs' / a.label
    manifest = json.loads((folder / 'manifest.json').read_text())
    reviews = json.loads((folder / 'reviews.json').read_text())
    metrics = json.loads((folder / 'metrics.json').read_text())
    rows = build_worksheet(
        manifest, reviews, metrics, lambda e: (history_cell(e['request']), product_cell(e['request'], CATALOGUE))
    )
    target = folder / 'author_review_worksheet.csv'
    if target.exists():
        old = {r['review_id']: r for r in read_worksheet(target)}
        for r in rows:
            if r['review_id'] in old:
                for k in ('author_label', 'author_critical', 'author_note'):
                    r[k] = old[r['review_id']][k]
    write_worksheet(target, rows)
    calib = sum('calibration' in r['reasons'] for r in rows)
    print(f'{len(rows)} messages to review ({calib} calibration, {len(rows) - calib} flagged-only) -> {target}')


if __name__ == '__main__':
    main()

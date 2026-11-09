"""Sampled human author review and judge calibration (requirement 1.3, section 12, layer 3).

Only a human may fill author labels. Nothing here generates or defaults a label.
"""

import csv
import random
from collections import defaultdict
from pathlib import Path

SEED = 20261108
PER_SCENARIO = 2
LABELS = ('ready', 'minor', 'major', 'unusable')
USABLE_LABELS = ('ready', 'minor')
FIELDS = [
    'review_id',
    'case_id',
    'scenario',
    'message_no',
    'reasons',
    'task_and_history',
    'facts',
    'message',
    'judge_usable',
    'judge_critical',
    'judge_uncertain',
    'judge_issues',
    'author_label',
    'author_critical',
    'author_note',
]
CORE = ('facts', 'context', 'scenario', 'boundaries')


def judge_usable(m: dict) -> bool:
    s = m['scores']
    return not m['critical'] and all(s[d] >= 4 for d in CORE) and min(s.values()) >= 3


def calibration_cases(manifest: list[dict], seed: int = SEED) -> set[str]:
    by_scenario = defaultdict(list)
    for e in manifest:
        if e['result']['status'] == 'success':
            by_scenario[e['request']['scenario']].append(e['case_id'])
    rng = random.Random(seed)
    picked = set()
    for scenario in sorted(by_scenario):
        ids = sorted(by_scenario[scenario])
        picked.update(rng.sample(ids, min(PER_SCENARIO, len(ids))))
    return picked


def build_worksheet(manifest, reviews, metrics, row_context) -> list[dict]:
    """row_context(entry) -> (task_and_history, facts) strings for the reviewer."""
    rev = {r['case_id']: r for r in reviews}
    soft = {c['case_id']: c['soft_flags'] for c in metrics.get('per_case', [])}
    sample = calibration_cases(manifest)
    rows = []
    for e in manifest:
        if e['result']['status'] != 'success':
            continue
        cid = e['case_id']
        r = rev.get(cid)
        complete = r is not None and r.get('status') == 'complete'
        history, facts = row_context(e)
        for i, text in enumerate(e['result']['candidates']):
            reasons = []
            if cid in sample:
                reasons.append('calibration')
            jm = r['review']['messages'][i] if complete else None
            if not complete:
                reasons.append('no-complete-judgment')
            else:
                if jm['critical']:
                    reasons.append('judge-critical')
                if min(jm['scores'].values()) <= 3:
                    reasons.append('judge-score<=3')
                if jm['uncertain']:
                    reasons.append('judge-uncertain')
            if soft.get(cid) and soft[cid][i]:
                reasons.append('soft:' + ','.join(soft[cid][i]))
            if not reasons:
                continue
            rows.append(
                {
                    'review_id': f'{cid}-{i + 1}',
                    'case_id': cid,
                    'scenario': e['request']['scenario'],
                    'message_no': i + 1,
                    'reasons': ';'.join(reasons),
                    'task_and_history': history,
                    'facts': facts,
                    'message': text,
                    'judge_usable': '' if jm is None else ('yes' if judge_usable(jm) else 'no'),
                    'judge_critical': '' if jm is None else ('yes' if jm['critical'] else 'no'),
                    'judge_uncertain': '' if jm is None else ('yes' if jm['uncertain'] else 'no'),
                    'judge_issues': '' if jm is None else ' | '.join(jm['issues']),
                    'author_label': '',
                    'author_critical': '',
                    'author_note': '',
                }
            )
    return rows


def write_worksheet(path: Path, rows: list[dict]) -> None:
    with Path(path).open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def read_worksheet(path: Path) -> list[dict]:
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        label = row['author_label'].strip().lower()
        if label and label not in LABELS:
            raise ValueError(f'{row["review_id"]}: author_label must be one of {LABELS}, got {label!r}')
        crit = row['author_critical'].strip().lower()
        if crit and crit not in ('yes', 'no'):
            raise ValueError(f'{row["review_id"]}: author_critical must be yes or no')
        row['author_label'], row['author_critical'] = label, crit
    return rows


def summarize(manifest, reviews, worksheet_rows) -> dict:
    rev = {r['case_id']: r for r in reviews if r.get('status') == 'complete'}
    author = {r['review_id']: r for r in worksheet_rows if r['author_label']}
    usable_msgs = 0
    usable_cases = 0
    critical_msgs = 0
    judged_msgs = 0
    unjudged_msgs = 0
    for e in manifest:
        if e['result']['status'] != 'success':
            continue
        case_usable = False
        for i in range(3):
            rid = f'{e["case_id"]}-{i + 1}'
            jm = rev[e['case_id']]['review']['messages'][i] if e['case_id'] in rev else None
            if rid in author:
                a = author[rid]
                usable = a['author_label'] in USABLE_LABELS and a['author_critical'] != 'yes'
                critical = a['author_critical'] == 'yes'
            elif jm is not None:
                usable, critical = judge_usable(jm), jm['critical']
            else:
                unjudged_msgs += 1
                continue
            judged_msgs += 1
            usable_msgs += usable
            critical_msgs += critical
            case_usable |= usable
        usable_cases += case_usable
    calib = [r for r in worksheet_rows if 'calibration' in r['reasons'].split(';')]
    calib_done = [r for r in calib if r['author_label'] and r['judge_usable']]
    agree = sum((r['judge_usable'] == 'yes') == (r['author_label'] in USABLE_LABELS) for r in calib_done)
    false_pass = sum(r['judge_usable'] == 'yes' and r['author_label'] not in USABLE_LABELS for r in calib_done)
    false_alarm = sum(r['judge_usable'] == 'no' and r['author_label'] in USABLE_LABELS for r in calib_done)
    crit_rows = [r for r in calib_done if r['author_critical']]
    crit_agree = sum(r['judge_critical'] == r['author_critical'] for r in crit_rows)
    status = (
        'complete'
        if calib and len(calib_done) == len(calib) and all(r['author_label'] for r in worksheet_rows)
        else ('pending' if not author else 'partial')
    )
    return {
        'author_review_status': status,
        'worksheet_messages': len(worksheet_rows),
        'author_labelled_messages': len(author),
        'calibration_messages': len(calib),
        'calibration_labelled': len(calib_done),
        'judge_author_usable_agreement': f'{agree}/{len(calib_done)}' if calib_done else 'pending',
        'judge_false_pass': f'{false_pass}/{len(calib_done)}' if calib_done else 'pending',
        'judge_false_alarm': f'{false_alarm}/{len(calib_done)}' if calib_done else 'pending',
        'critical_flag_agreement': f'{crit_agree}/{len(crit_rows)}' if crit_rows else 'pending',
        'usable_messages': usable_msgs,
        'usable_cases': usable_cases,
        'critical_messages': critical_msgs,
        'messages_with_decision': judged_msgs,
        'messages_without_judgment': unjudged_msgs,
        'decision_rule': 'Author label where the author reviewed a message; otherwise gpt-5-mini judge scores (usable = no critical, facts/context/scenario/boundaries >= 4, all dimensions >= 3).',
    }

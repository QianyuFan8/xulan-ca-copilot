"""Unit tests: eight-column export, automated metrics, human-review sampling and agreement."""

import csv

import pytest

from xulan.export import COLUMNS, case_row, result_outputs, write_cases_csv
from xulan.metrics import jaccard, run_metrics, set_similarity
from xulan.review import build_worksheet, calibration_cases, read_worksheet, summarize, write_worksheet
from xulan.service import CATALOGUE

from support import CASES, fake_manifest, judged


def test_invitation_export_contains_event_facts():
    inv = next(c for c in CASES if c['request']['scenario'] == 'invitation')
    row = case_row(inv['case_id'], inv['request'], ['a', 'b', 'c'], CATALOGUE)
    d = inv['request']['scenario_details']
    assert len(row) == 8 and '[Event]' in row[4]
    assert all(str(d[k]) in row[4] for k in ('title', 'start', 'end', 'location', 'booking_route'))
    assert '虚构' not in row[4]


def test_greeting_export_has_labelled_task_context():
    g = next(c for c in CASES if c['request']['scenario'] == 'greeting')
    row = case_row(g['case_id'], g['request'], ['a', 'b', 'c'], CATALOGUE)
    assert row[3].startswith('[CA task context — not a client message]')
    assert g['request']['scenario_details']['occasion_date'] in row[3] and '[Conversation]' in row[3]
    assert row[4] == 'Not applicable'


def test_csv_has_bom_exact_columns_and_formula_escape(tmp_path):
    g = CASES[0]
    row = case_row(g['case_id'], g['request'], ['=HYPERLINK(1)', '正常消息', '+1'], CATALOGUE)
    write_cases_csv(tmp_path / 'c.csv', [row])
    assert (tmp_path / 'c.csv').read_bytes().startswith(b'\xef\xbb\xbf')
    rows = list(csv.reader((tmp_path / 'c.csv').open(encoding='utf-8-sig')))
    assert rows[0] == COLUMNS
    assert rows[1][5] == "'=HYPERLINK(1)" and rows[1][6] == '正常消息' and rows[1][7] == "'+1"


def test_error_case_is_exported_as_a_labelled_row():
    cells = result_outputs(
        {'status': 'error', 'validation_findings': ['Unverified comfort, reputation or outcome claim.']}
    )
    assert len(cells) == 3 and cells[0].startswith('[No draft — status: error]') and 'comfort' in cells[0]


def test_similarity_and_near_duplicate():
    assert jaccard('生日快乐愿您顺心', '生日快乐愿您顺心') == 1.0
    sim = set_similarity(['生日快乐，愿您顺心。', '生日快乐，愿您顺心！', '下周有空可以来看看新的细节'])
    assert sim['near_duplicate'] and sim['max'] == 1.0


def test_metrics_count_prompt_example_phrase_reuse():
    m = fake_manifest()
    m[0]['result']['candidates'][2] = '给您送上祝福，愿今天有些小小的欢喜。'
    result = run_metrics(m)
    assert result['messages_with_prompt_example_phrases'] == 1 and result['cases_successful'] == 50


def test_calibration_sample_is_deterministic_two_per_scenario():
    m = fake_manifest()
    a, b = calibration_cases(m), calibration_cases(m)
    assert a == b and len(a) == 12
    scenario = {c['case_id']: c['request']['scenario'] for c in CASES}
    counts = {}
    for cid in a:
        counts[scenario[cid]] = counts.get(scenario[cid], 0) + 1
    assert set(counts.values()) == {2} and len(counts) == 6


def test_worksheet_includes_flagged_messages_and_never_prefills_labels(tmp_path):
    m = fake_manifest()
    low_case = next(c['case_id'] for c in CASES if c['case_id'] not in calibration_cases(m))
    rows = build_worksheet(m, judged(m, low=(low_case,)), run_metrics(m), lambda e: ('h', 'f'))
    assert len([r for r in rows if 'calibration' in r['reasons']]) == 36
    assert any(r['review_id'] == f'{low_case}-1' and 'judge-score<=3' in r['reasons'] for r in rows)
    assert all(r['author_label'] == '' and r['author_critical'] == '' for r in rows)
    write_worksheet(tmp_path / 'w.csv', rows)
    s = summarize(m, judged(m, low=(low_case,)), read_worksheet(tmp_path / 'w.csv'))
    assert s['author_review_status'] == 'pending' and s['judge_false_pass'] == 'pending'


def test_author_labels_override_the_judge_and_agreement_is_counted(tmp_path):
    m = fake_manifest()
    rows = build_worksheet(m, judged(m), run_metrics(m), lambda e: ('h', 'f'))
    calib = [r for r in rows if 'calibration' in r['reasons']]
    for r in calib:
        r['author_label'], r['author_critical'] = 'minor', 'no'
    calib[0]['author_label'] = 'unusable'
    write_worksheet(tmp_path / 'w.csv', rows)
    s = summarize(m, judged(m), read_worksheet(tmp_path / 'w.csv'))
    assert s['judge_author_usable_agreement'] == '35/36' and s['judge_false_pass'] == '1/36'
    assert s['usable_messages'] == 149 and s['author_labelled_messages'] == 36


def test_invalid_author_label_is_rejected(tmp_path):
    m = fake_manifest()
    rows = build_worksheet(m, judged(m), run_metrics(m), lambda e: ('h', 'f'))
    rows[0]['author_label'] = 'good'
    write_worksheet(tmp_path / 'w.csv', rows)
    with pytest.raises(ValueError):
        read_worksheet(tmp_path / 'w.csv')

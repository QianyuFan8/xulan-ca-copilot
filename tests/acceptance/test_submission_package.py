"""Acceptance tests: does the packaged submission meet the structural requirements?

Quality acceptance (are the drafts usable?) is decided by the evaluation pipeline: the model
judge plus sampled human review. These tests check what can be decided mechanically and
without paid calls: inputs, single-version packaging, the exact eight-column CSV and
consistency between the CSV, the manifest and the summary.
"""

import csv
import json

import pytest

from xulan.export import COLUMNS
from xulan.models import GenerationRequest
from xulan.service import ROOT

from support import CASES

SUB = ROOT / 'submission'
CSV_PATH, MANIFEST_PATH, SUMMARY_PATH = (
    SUB / 'test_cases.csv',
    SUB / 'supporting' / 'run_manifest.json',
    SUB / 'supporting' / 'evaluation_summary.json',
)

packaged = pytest.mark.skipif(
    not (CSV_PATH.exists() and MANIFEST_PATH.exists()), reason='no packaged submission yet (run evaluation/package.py)'
)


def manifest():
    return json.loads(MANIFEST_PATH.read_text())


def csv_rows():
    with CSV_PATH.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.reader(f))


def unescape(cell):
    """Reverse the spreadsheet formula escape applied on export."""
    return cell[1:] if cell[:2] in ("'=", "'+", "'-", "'@") else cell


def test_fifty_frozen_inputs_cover_all_six_scenarios_and_validate():
    assert len(CASES) == 50
    assert len({c['case_id'] for c in CASES}) == 50
    for case in CASES:
        GenerationRequest.model_validate(case['request'])
    assert {c['request']['scenario'] for c in CASES} == {
        'greeting',
        'recommendation',
        'care',
        'reactivation',
        'invitation',
        'price_objection',
    }


@packaged
def test_csv_has_bom_exact_eight_columns_and_fifty_cases():
    assert CSV_PATH.read_bytes().startswith(b'\xef\xbb\xbf')
    rows = csv_rows()
    assert rows[0] == COLUMNS and len(COLUMNS) == 8
    body = rows[1:]
    assert len(body) == 50 and all(len(r) == 8 for r in body)
    assert sorted(r[0] for r in body) == sorted(c['case_id'] for c in CASES)


@packaged
def test_package_comes_from_one_complete_single_version_run():
    m = manifest()
    assert len(m) == 50
    assert len({e['version_label'] for e in m}) == 1
    versions = {
        (
            e['result']['metadata']['prompt_version'],
            e['result']['metadata']['code_version'],
            e['result']['metadata']['data_version'],
        )
        for e in m
    }
    assert len(versions) == 1


@packaged
def test_every_success_has_three_drafts_matching_the_csv_and_failures_are_labelled():
    rows = {r[0]: r for r in csv_rows()[1:]}
    for e in manifest():
        outputs = [unescape(c) for c in rows[e['case_id']][5:8]]
        if e['result']['status'] == 'success':
            assert len(e['result']['candidates']) == 3 and all(c.strip() for c in e['result']['candidates'])
            assert outputs == e['result']['candidates']
        else:
            assert all(o.startswith('[No draft — status:') for o in outputs)


@packaged
def test_invitation_drafts_carry_the_exact_location_and_no_fictional_label():
    for e in manifest():
        if e['result']['status'] != 'success':
            continue
        for text in e['result']['candidates']:
            assert '虚构' not in text
            if e['request']['scenario'] == 'invitation':
                assert e['request']['scenario_details']['location'] in text


@packaged
def test_summary_matches_the_manifest():
    if not SUMMARY_PATH.exists():
        pytest.skip('no evaluation_summary.json yet')
    s, m = json.loads(SUMMARY_PATH.read_text()), manifest()
    assert s['version_label'] == m[0]['version_label']
    assert s['generated_cases'] == 50
    assert s['successful_cases'] == sum(e['result']['status'] == 'success' for e in m)

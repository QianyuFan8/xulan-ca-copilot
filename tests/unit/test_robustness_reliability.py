"""Unit tests: abstention evaluation (zero model calls) and the reliability breakdown."""

import importlib.util
import json

import pytest

from xulan.service import ROOT


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'evaluation' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


abstention = load('abstention')
reliability = load('reliability')
CASES = json.loads(abstention.CASES_PATH.read_text())


def test_abstention_set_covers_all_four_expected_outcomes():
    assert len({c['case_id'] for c in CASES}) == len(CASES)
    assert {c['expected'] for c in CASES} == {'blocked', 'needs_information', 'rejected', 'proceeds'}


@pytest.mark.parametrize('case', CASES, ids=[c['case_id'] for c in CASES])
def test_each_abstention_case_gets_its_expected_outcome(case, tmp_path):
    got = abstention.outcome(case['request'], tmp_path)
    assert got['outcome'] == case['expected']
    if case.get('expect_information_request'):
        assert any(case['expect_information_request'] in x for x in got['requests'])
    if case.get('expect_advisory'):
        assert any(case['expect_advisory'] in x for x in got['advisories'])


def test_abstention_report_has_no_missed_or_over_abstentions():
    report = abstention.evaluate(CASES)
    assert report['correct'] == report['cases']
    assert report['missed_abstentions'] == [] and report['over_abstentions'] == []


def test_stub_client_never_returns_text():
    client = abstention.NoModelClient()
    with pytest.raises(abstention.ModelCallAttempted):
        client.complete([])
    assert client.calls == 1


def test_nearest_rank_percentile_returns_an_observed_value():
    values = [1.0, 2.0, 3.0, 4.0, 10.0]
    assert reliability.percentile(values, 95) == 10.0
    assert reliability.percentile(values, 50) == 3.0


def fake(case_id, status, repairs, latency, usages):
    run_id = case_id.lower()
    entry = dict(
        case_id=case_id,
        version_label='vX',
        result=dict(
            status=status, metadata=dict(run_id=run_id, attempts=len(usages), repairs=repairs, latency_seconds=latency)
        ),
    )
    attempts = [dict(model='gpt-4o-2024-08-06', usage=dict(prompt_tokens=i, completion_tokens=o)) for i, o in usages]
    return entry, {run_id: dict(attempts=attempts)}


def test_reliability_splits_paths_and_estimates_cost():
    parts = [
        fake('T1', 'success', 0, 1.0, [(1000, 100)]),
        fake('T2', 'success', 1, 3.0, [(1000, 100), (2000, 100)]),
        fake('T3', 'error', 1, 2.0, [(1000, 100), (2000, 100)]),
    ]
    manifest = [p[0] for p in parts]
    artifacts = {k: v for p in parts for k, v in p[1].items()}
    report = reliability.evaluate(manifest, artifacts)
    assert set(report['by_path']) == {'first_pass_success', 'repaired_success', 'error'}
    assert report['repair_recovery'] == dict(needed_repair=2, recovered=1)
    assert report['overall']['model_calls_distribution'] == {'1': 1, '2': 2}
    # gpt-4o: 1000 in + 100 out = 0.0025 + 0.001 = 0.0035 USD
    assert report['by_path']['first_pass_success']['cost_usd_total'] == pytest.approx(0.0035)
    # T2 and T3 each cost 0.0035 + 0.006; the error's spend counts against the two successes.
    assert report['cost_per_successful_case_usd'] == pytest.approx((0.0035 + 0.0095 * 2) / 2, abs=1e-4)

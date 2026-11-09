"""Unit tests: spend ledger, credential loading, pinned models and rates, Pydantic output contracts."""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest
from openai.lib._pydantic import to_strict_json_schema

from xulan.budget import BudgetExceeded, BudgetGuard
from xulan.pricing import GENERATION_MODEL, JUDGE_MODEL, estimate
from xulan.schemas import DraftSet, SetReview
from xulan.service import ROOT

from support import fake_manifest, judged


def test_budget_cap_refuses_and_keeps_unsettled_reservations(tmp_path):
    b = BudgetGuard(tmp_path / 'budget.sqlite', limit=0.1)
    b.reserve(0.09)
    with pytest.raises(BudgetExceeded):
        b.reserve(0.02)
    assert b.summary()['uncertain_calls'] == 1


def test_budget_reservations_are_atomic(tmp_path):
    b = BudgetGuard(tmp_path / 'budget.sqlite', limit=0.1)

    def reserve(_):
        try:
            b.reserve(0.06)
            return True
        except BudgetExceeded:
            return False

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert sum(pool.map(reserve, range(4))) == 1


def test_dotenv_never_overrides_existing_environment(monkeypatch, tmp_path):
    from xulan.settings import load_credentials

    path = tmp_path / 'credentials.env'
    path.write_text('OPENAI_API_KEY=test-value\nUNRELATED_SETTING=ignored\n')
    monkeypatch.setenv('XULAN_ENV_FILE', str(path))
    monkeypatch.setenv('OPENAI_API_KEY', 'existing-value')
    load_credentials()
    assert os.environ['OPENAI_API_KEY'] == 'existing-value'
    assert os.getenv('UNRELATED_SETTING') is None


def test_dotenv_values_are_not_interpolated(monkeypatch, tmp_path):
    from xulan.settings import load_credentials

    path = tmp_path / 'credentials.env'
    path.write_text('OPENAI_API_KEY="literal-${UNRELATED_SETTING}"\n')
    monkeypatch.setenv('XULAN_ENV_FILE', str(path))
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    load_credentials()
    assert os.environ['OPENAI_API_KEY'] == 'literal-${UNRELATED_SETTING}'


def test_env_file_lookup_prefers_explicit_then_project(tmp_path, monkeypatch):
    from xulan import settings

    custom = tmp_path / 'x.env'
    custom.write_text('OPENAI_API_KEY=test-value\n')
    monkeypatch.setenv('XULAN_ENV_FILE', str(custom))
    assert settings.env_file() == custom
    monkeypatch.delenv('XULAN_ENV_FILE')
    if (settings.ROOT / '.env').is_file():
        assert settings.env_file() == settings.ROOT / '.env'


def test_pricing_pins_models_and_refuses_unknown_models():
    assert GENERATION_MODEL == 'gpt-4o-2024-08-06' and estimate(GENERATION_MODEL, 1_000_000, 0) == 2.5
    assert JUDGE_MODEL == 'gpt-5-mini-2025-08-07' and estimate(JUDGE_MODEL, 0, 1_000_000) == 2.0
    with pytest.raises(KeyError):
        estimate('unknown-model', 1, 1)


def test_output_contracts_are_accepted_by_the_sdk_as_strict_schemas():
    draft = to_strict_json_schema(DraftSet)
    assert draft['properties']['candidates']['minItems'] == 3
    assert draft['properties']['candidates']['maxItems'] == 3
    assert draft['additionalProperties'] is False
    review = to_strict_json_schema(SetReview)
    assert set(review['$defs']['MessageReview']['required']) == {'scores', 'critical', 'uncertain', 'issues'}


def test_judge_review_validation_rejects_out_of_range_or_wrong_count():
    sys.path.insert(0, str(ROOT / 'evaluation'))
    from judge import validate_review

    ok = judged(fake_manifest()[:1])[0]['review']
    validate_review(ok)
    bad = json.loads(json.dumps(ok))
    bad['messages'][0]['scores']['facts'] = 7
    with pytest.raises(ValueError):
        validate_review(bad)
    two = json.loads(json.dumps(ok))
    two['messages'] = two['messages'][:2]
    with pytest.raises(ValueError):
        validate_review(two)

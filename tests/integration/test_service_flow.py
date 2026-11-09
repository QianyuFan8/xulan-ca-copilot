"""Integration tests: ConversationService end to end (policy, fact checks, context, validator,
retry and repair loop, audit files) with a scripted fake model instead of the provider."""

import json
from datetime import datetime

import pytest

from xulan.client import TransientFailure
from xulan.models import HistoryItem

from support import VALID, drafts, req, run


def test_success_writes_an_audit_file_with_versions(tmp_path):
    result, _ = run(tmp_path, req(), [VALID])
    assert result.status == 'success' and len(result.candidates) == 3
    artifact = json.loads(next(tmp_path.glob('*.json')).read_text())
    assert artifact['input'] and artifact['attempts']
    assert all(result.metadata[k] for k in ['run_id', 'model', 'prompt_version', 'data_version', 'code_version'])


# --- Contact policy -------------------------------------------------------------------------


def test_structured_opt_out_blocks_without_calling_the_model(tmp_path):
    r = req(1)
    r.client_information.contact_preference = 'no_marketing'
    result, client = run(tmp_path, r, [])
    assert result.status == 'blocked' and client.calls == 0 and not result.candidates


def test_customer_initiated_care_question_is_a_service_reply_not_outreach(tmp_path):
    r = req(2)
    r.client_information.contact_preference = 'no_marketing'
    result, _ = run(tmp_path, r, [VALID])
    assert result.status == 'success'


def test_structured_preference_blocks_even_with_benign_history(tmp_path):
    r = req(1)
    r.client_information.contact_preference = 'no_contact'
    r.conversation_history[0].content = '谢谢。'
    result, client = run(tmp_path, r, [])
    assert result.status == 'blocked' and client.calls == 0


def test_history_refusal_wording_is_an_advisory_not_a_block(tmp_path):
    r = req(1)
    r.conversation_history = [
        HistoryItem(role='client', content='以后不要再联系我。'),
        HistoryItem(role='client', content='谢谢。'),
    ]
    result, client = run(tmp_path, r, [VALID])
    assert result.status == 'success' and client.calls == 1
    assert any('contact refusal' in a for a in result.advisories)


@pytest.mark.parametrize(
    'text', ['我不是说不要再联系我。', '她说“不要再联系我”，我没有这样说。', '现在可以给我推荐黑色肩包。']
)
def test_quoted_negated_or_reconsent_history_never_blocks(tmp_path, text):
    r = req(1)
    r.conversation_history[0].content = text
    result, _ = run(tmp_path, r, [VALID])
    assert result.status == 'success'


@pytest.mark.parametrize(
    'timezone,last', [(None, None), ('Asia/Shanghai', '2026-11-08T12:00:00+08:00'), ('Asia/Shanghai', None)]
)
def test_timing_issues_are_advisories(tmp_path, timezone, last):
    r = req()
    r.client_information.timezone = timezone
    r.current_datetime = datetime.fromisoformat('2026-11-09T22:00:00+08:00')
    if last:
        r.client_information.last_outbound_contact = datetime.fromisoformat(last)
    result, _ = run(tmp_path, r, [VALID])
    assert result.status == 'success' and result.advisories


# --- Required facts (needs_information, no model call) ----------------------------------------


def test_missing_event_location_needs_information(tmp_path):
    r = req(4)
    r.scenario_details.pop('location')
    result, client = run(tmp_path, r, [])
    assert result.status == 'needs_information' and client.calls == 0


def test_conflicting_facts_need_information(tmp_path):
    r = req(4)
    r.scenario_details['conflicting_facts'] = True
    result, _ = run(tmp_path, r, [])
    assert result.status == 'needs_information'


def test_unmet_hard_requirement_needs_information(tmp_path):
    r = req(1)
    r.scenario_details['hard_requirement_unmet'] = True
    result, _ = run(tmp_path, r, [])
    assert result.status == 'needs_information'


def test_invalid_occasion_date_needs_information(tmp_path):
    r = req()
    r.scenario_details['occasion_date'] = 'not-a-date'
    result, client = run(tmp_path, r, [])
    assert result.status == 'needs_information' and client.calls == 0


def test_product_over_hard_budget_needs_information(tmp_path):
    r = req(1)
    r.scenario_details['hard_budget_cny'] = 5000
    result, _ = run(tmp_path, r, [])
    assert result.status == 'needs_information'


def test_unverified_device_fit_needs_information(tmp_path):
    r = req(1)
    r.scenario_details['required_device_fit'] = '13-inch laptop'
    result, _ = run(tmp_path, r, [])
    assert result.status == 'needs_information'


# --- Bounded retry and repair -------------------------------------------------------------------


def test_one_transient_retry_then_success(tmp_path):
    result, client = run(tmp_path, req(), [TransientFailure(), VALID])
    assert result.status == 'success' and client.calls == 2 and result.metadata['repairs'] == 0


def test_persistent_transient_failure_is_an_error(tmp_path):
    result, client = run(tmp_path, req(), [TransientFailure(), TransientFailure()])
    assert result.status == 'error' and client.calls == 2


def test_one_repair_then_success(tmp_path):
    result, client = run(tmp_path, req(), ['bad', VALID])
    assert result.status == 'success' and client.calls == 2


def test_repair_is_limited_to_one(tmp_path):
    result, client = run(tmp_path, req(), ['bad', 'bad'])
    assert result.status == 'error' and client.calls == 2 and result.metadata['repairs'] == 1 and not result.candidates


def test_worst_case_is_four_model_calls(tmp_path):
    result, client = run(tmp_path, req(), [TransientFailure(), 'bad', TransientFailure(), 'bad'])
    assert result.status == 'error' and client.calls == 4


def test_unsupported_price_still_invalid_after_repair_is_an_error(tmp_path):
    invalid = drafts('这款只要100元。', '我给您介绍这款。', '可以再看看。')
    result, client = run(tmp_path, req(5), [invalid, invalid])
    assert result.status == 'error' and client.calls == 2


def test_non_transient_failure_is_not_retried_and_details_are_hidden(tmp_path):
    result, client = run(tmp_path, req(), [RuntimeError('sensitive provider failure')])
    assert result.status == 'error' and client.calls == 1 and 'sensitive' not in str(result)

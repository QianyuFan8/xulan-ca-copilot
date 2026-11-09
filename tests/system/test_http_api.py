"""System tests: the whole FastAPI application through its HTTP interface.

The provider client inside the app is swapped for a scripted fake, so these tests make no
paid calls but exercise routing, request validation, the service and JSON serialisation.
"""

import copy

import pytest
from fastapi.testclient import TestClient

import xulan.app as app_module
from xulan.service import ConversationService

from support import EXAMPLES, VALID, FakeLLMClient


@pytest.fixture
def api(tmp_path, monkeypatch):
    """Return (client, use_script): use_script(list) installs the fake model's replies."""

    def use_script(script):
        monkeypatch.setattr(app_module, 'service', ConversationService(FakeLLMClient(script), tmp_path))

    use_script([])
    return TestClient(app_module.app), use_script


def example(index):
    return copy.deepcopy(EXAMPLES[index])


def test_ui_docs_and_read_endpoints_are_served(api):
    client, _ = api
    assert client.get('/').status_code == 200
    assert client.get('/docs').status_code == 200
    assert client.get('/static/report.html').status_code == 200
    assert len(client.get('/api/config').json()['products']) == 12
    assert len(client.get('/api/examples').json()) == 6
    assert len(client.get('/api/clients').json()) == 18
    assert {e['id'] for e in client.get('/api/events').json()} == {'E01', 'E02'}
    health = client.get('/api/health').json()
    assert health['ready'] is True and 'budget' in health and 'credential_configured' in health


def test_invalid_request_is_rejected_by_the_contract(api):
    client, _ = api
    assert client.post('/api/generate', json={}).status_code == 422
    bad = example(0)
    bad['scenario'] = 'unknown'
    assert client.post('/api/generate', json=bad).status_code == 422


def test_generate_success_returns_three_drafts_and_metadata(api):
    client, use_script = api
    use_script([VALID])
    body = client.post('/api/generate', json=example(0)).json()
    assert body['status'] == 'success' and len(body['candidates']) == 3
    assert body['metadata']['run_id'] and body['metadata']['prompt_version']


def test_generate_for_a_new_client_not_in_the_client_list(api):
    """The CA can draft for any client typed into the UI, not only the synthetic records."""
    client, use_script = api
    use_script([VALID.replace('林女士', '赵女士')])
    payload = example(0)
    payload['client_information'] = {
        'id': 'NEW',
        'preferred_address': '赵女士',
        'preferences': '喜欢深色、低调的款式',
        'relationship_stage': 'New contact',
        'contact_preference': 'allowed',
        'timezone': 'Asia/Hong_Kong',
    }
    payload['conversation_history'] = [{'role': 'client', 'content': '下个月生日，想先看看有什么新的颜色。'}]
    body = client.post('/api/generate', json=payload).json()
    assert body['status'] == 'success' and all('赵女士' in c for c in body['candidates'])


def test_history_accepts_a_timestamped_message_marked_as_sent(api):
    """'Mark as sent' appends the CA's final wording with a timestamp; the API must accept it."""
    client, use_script = api
    use_script([VALID])
    payload = example(0)
    payload['conversation_history'] += [
        {'role': 'advisor', 'content': '林女士，生日快乐！', 'timestamp': '2026-11-08T20:15:00+08:00'},
        {'role': 'client', 'content': '谢谢！', 'timestamp': '2026-11-08T20:20:00.000Z'},
    ]
    body = client.post('/api/generate', json=payload).json()
    assert body['status'] == 'success'


def test_generate_needs_information_lists_what_is_missing(api):
    client, _ = api
    payload = example(4)
    del payload['scenario_details']['location']
    body = client.post('/api/generate', json=payload).json()
    assert body['status'] == 'needs_information' and body['information_requests'] and not body['candidates']


def test_generate_blocked_by_structured_contact_preference(api):
    client, _ = api
    payload = example(1)
    payload['client_information']['contact_preference'] = 'no_contact'
    body = client.post('/api/generate', json=payload).json()
    assert body['status'] == 'blocked' and body['blocking_reasons'] and not body['candidates']


def test_generate_error_after_failed_repair_has_no_placeholder_drafts(api):
    client, use_script = api
    use_script(['bad', 'bad'])
    body = client.post('/api/generate', json=example(0)).json()
    assert body['status'] == 'error' and not body['candidates'] and body['validation_findings']

"""Smoke tests: quick checks that a running deployment works. Opt-in; skipped by default.

* Deployed service (free):  XULAN_SMOKE_URL=http://localhost:8000 pytest -m smoke
  Checks health, UI, API docs and examples on an already running server or container.
  ``scripts/smoke.sh`` starts the Docker Compose stack, runs this and stops it again.

* Live provider (PAID, about USD 0.01):  XULAN_LIVE_SMOKE=1 pytest -m smoke
  Makes ONE real generation through the official SDK with structured outputs, recorded in the
  shared spend ledger (runs/budget.sqlite). Use it before a full evaluation run.
"""

import json
import os
import urllib.request

import pytest

from support import req

SMOKE_URL = os.getenv('XULAN_SMOKE_URL', '').rstrip('/')
LIVE = os.getenv('XULAN_LIVE_SMOKE') == '1'


def get(path):
    with urllib.request.urlopen(f'{SMOKE_URL}{path}', timeout=10) as response:
        return response.status, response.read()


@pytest.mark.skipif(not SMOKE_URL, reason='set XULAN_SMOKE_URL to smoke-test a running deployment')
def test_deployed_service_is_up():
    status, body = get('/api/health')
    health = json.loads(body)
    assert status == 200 and health['ready'] is True
    for path in ('/', '/docs', '/api/examples', '/api/config'):
        assert get(path)[0] == 200, path


@pytest.mark.skipif(not LIVE, reason='set XULAN_LIVE_SMOKE=1 to make one paid generation call')
def test_live_generation_returns_parsed_drafts():
    from xulan.budget import BudgetGuard
    from xulan.client import OpenAIClient
    from xulan.pricing import GENERATION_MODEL, PROMPT_VERSION
    from xulan.service import ROOT, ConversationService
    from xulan.settings import load_credentials

    load_credentials()
    if not os.getenv('OPENAI_API_KEY'):
        pytest.skip('OPENAI_API_KEY is not configured')
    service = ConversationService(OpenAIClient(BudgetGuard(ROOT / 'runs/budget.sqlite')), ROOT / 'runs' / 'smoke')
    result = service.generate(req(0))
    assert result.status == 'success', result.validation_findings
    assert len(result.candidates) == 3
    assert result.metadata['returned_model'] == GENERATION_MODEL
    assert result.metadata['prompt_version'] == PROMPT_VERSION

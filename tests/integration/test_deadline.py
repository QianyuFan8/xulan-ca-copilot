"""Integration test: the whole request, retries and repair included, ends within the overall deadline."""

import pytest

import xulan.service as service
from xulan.client import Reply, TransientFailure

from support import VALID, req


class Clock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class SlowClient:
    """Each call takes 30 s of simulated time, or less if the timeout it is given is shorter."""

    def __init__(self, clock, script, honours_timeout=True):
        self.clock, self.script, self.honours = clock, list(script), honours_timeout
        self.timeouts = []

    def complete(self, messages, timeout=30):
        self.timeouts.append(timeout)
        self.clock.now += min(30, timeout) if self.honours else 30
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return Reply(item)


@pytest.fixture
def clock(monkeypatch):
    c = Clock()
    monkeypatch.setattr(service, 'time', c)
    return c


SCRIPT = [TransientFailure('t'), 'not json', TransientFailure('t'), VALID]


def test_each_call_gets_only_the_time_left(clock, tmp_path):
    client = SlowClient(clock, SCRIPT)
    result = service.ConversationService(client, tmp_path).generate(req(0))
    assert client.timeouts[:3] == [30, 30, 30]
    # 30 + 0.1 (retry pause) + 30 + 30 + 0.1 (retry pause) = 90.2 s used, so the last call gets 14.8 s.
    assert client.timeouts[3] == pytest.approx(105 - 90.2)
    assert clock.now <= service.REQUEST_DEADLINE_SECONDS
    assert result.status == 'success'


def test_a_reply_after_the_deadline_is_not_used(clock, tmp_path):
    client = SlowClient(clock, SCRIPT, honours_timeout=False)
    result = service.ConversationService(client, tmp_path).generate(req(0))
    assert result.status == 'error' and not result.candidates


def test_no_call_starts_with_too_little_time_left(clock, tmp_path):
    client = SlowClient(clock, [TransientFailure('t'), 'not json', TransientFailure('t'), VALID])
    client.complete_original = client.complete

    def slow_then_stall(messages, timeout=30):
        reply = client.complete_original(messages, timeout)
        clock.now = max(clock.now, 101.0)  # leaves 4 s, under the minimum for another call
        return reply

    client.complete = slow_then_stall
    result = service.ConversationService(client, tmp_path).generate(req(0))
    assert result.status == 'error'
    # Call 1 fails (transient), call 2 returns invalid drafts at 101 s; the repair call never starts.
    assert len(client.timeouts) == 2

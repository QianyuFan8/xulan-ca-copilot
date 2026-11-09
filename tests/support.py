"""Shared test helpers. Importable from every test layer (pytest pythonpath includes tests/)."""

import json

from xulan.client import Reply
from xulan.models import GenerationRequest
from xulan.service import ROOT, ConversationService

EXAMPLES = json.loads((ROOT / 'fixtures/examples.json').read_text())
CASES = json.loads((ROOT / 'evaluation/cases.json').read_text())
DIMS = ['facts', 'context', 'personalization', 'brand', 'scenario', 'boundaries', 'wechat']

# A valid greeting draft set for example 0 (林女士).
VALID = json.dumps(
    {
        'candidates': [
            '林女士，祝您生日快乐，愿这一岁自在从容。',
            '林女士生日快乐，愿日常里有许多值得欢喜的小事。',
            '林女士，在这个特别的日子送上祝福，愿您平安顺意。',
        ]
    },
    ensure_ascii=False,
)


class FakeLLMClient:
    """Test double for the LLMClient protocol (see xulan.client.OpenAIClient for the real one).

    Replays a script of raw model replies (str) or exceptions to raise, and counts calls, so
    tests can drive retry, repair and failure paths deterministically and without paid calls.
    """

    def __init__(self, script):
        self.script = list(script)
        self.calls = 0

    def complete(self, messages, timeout=30):
        self.calls += 1
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return Reply(item)


def drafts(*texts: str) -> str:
    """Serialise three candidate strings as the model would return them."""
    return json.dumps({'candidates': list(texts)}, ensure_ascii=False)


def req(index: int = 0) -> GenerationRequest:
    """A fresh, editable copy of a synthetic example request (0 greeting, 1 recommendation, 2 care,
    3 reactivation, 4 invitation, 5 price objection)."""
    return GenerationRequest.model_validate(EXAMPLES[index])


def run(tmp_path, request, script):
    """Run the real service with a scripted fake model; returns (result, fake_client)."""
    client = FakeLLMClient(script)
    result = ConversationService(client, tmp_path).generate(request)
    return result, client


def fake_manifest(texts=None):
    out = []
    for c in CASES:
        cands = texts or [
            f'{c["case_id"]}您好，这是第一条。',
            f'{c["case_id"]}第二条完全不同的内容。',
            f'{c["case_id"]}最后给您留个选择。',
        ]
        out.append(
            {
                'case_id': c['case_id'],
                'version_label': 'test',
                'request': c['request'],
                'result': {'status': 'success', 'candidates': cands, 'metadata': {'repairs': 0}},
            }
        )
    return out


def judged(manifest, low=()):
    good = {'scores': dict.fromkeys(DIMS, 4), 'critical': False, 'uncertain': False, 'issues': []}
    out = []
    for m in manifest:
        msgs = [json.loads(json.dumps(good)) for _ in range(3)]
        if m['case_id'] in low:
            msgs[0]['scores']['facts'] = 2
        out.append(
            {
                'case_id': m['case_id'],
                'status': 'complete',
                'review': {'messages': msgs, 'diversity': 3, 'set_notes': ''},
            }
        )
    return out

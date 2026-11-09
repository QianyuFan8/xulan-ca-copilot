"""Unit tests: OutputValidator rules, in isolation from the service and the model."""

import pytest

from xulan.service import CATALOGUE, OutputValidator

from support import drafts, req

XL04 = [p for p in CATALOGUE['products'] if p['sku'] == 'XL04']
SAFE = ['这款侧面有折叠感。', '可以先看看尺寸。', '您想先了解哪一点？']


def findings(candidates, products, request):
    return OutputValidator().validate(drafts(*candidates), products, request)[1]


@pytest.mark.parametrize(
    'raw',
    ['not json', '{"candidates":["a","b"]}', '{"candidates":["a","b","c"],"extra":1}', '{"candidates":["a"," ","c"]}'],
)
def test_rejects_output_that_breaks_the_draftset_contract(raw):
    assert OutputValidator().validate(raw, [], req(0))[1] == [
        'Expected exactly three nonempty candidate strings in JSON.'
    ]


def test_budget_reference_is_not_a_selling_price():
    r = req(1)
    r.scenario_details['hard_budget_cny'] = 7500
    ok = ['林女士，您的7500元预算内，这款价格7200元。', '林女士，这款是黑色肩包。', '林女士，它的侧面有折叠感。']
    assert findings(ok, XL04, r) == []
    wrong = [ok[0].replace('这款价格7200元', '这款价格为7500元'), *ok[1:]]
    assert 'Unsupported numeric price claim.' in findings(wrong, XL04, r)


def test_budget_stated_in_conversation_is_not_a_selling_price():
    r = req(5)
    r.conversation_history[0].content = '目前预算只有6000元。'
    ok = ['林女士，您6000元的预算内，这款5800元。', '林女士，这款价格5800元。', '林女士，您可以慢慢考虑。']
    assert findings(ok, [CATALOGUE['products'][6]], r) == []


@pytest.mark.parametrize('text', ['这款目前有货。', '我们有一些新款上线。', '沟通简单直接：这款适合您。'])
def test_observed_unsupported_claims_are_rejected(text):
    assert findings([text, '这款是黑色。', '可以先了解侧面设计。'], [CATALOGUE['products'][3]], req(1))


def test_woven_panel_care_for_a_plain_leather_product_is_rejected():
    assert findings(
        ['编织面板建议检查。', '可以协助联系检查。', '如需帮助请告诉我。'], [CATALOGUE['products'][3]], req(2)
    )


def test_scratch_is_not_treated_as_wet_leather():
    r = req(2)
    r.conversation_history[0].content = '包面有划痕，可以帮忙看一下吗？'
    assert findings(['用干布按压吸水后晾干。', '可以联系检查。', '请不要自行处理。'], [CATALOGUE['products'][3]], r)


def test_reactivation_cannot_invent_an_event():
    assert findings(['11月21日10:00我们有展示活动。', '您好，有需要可联系。', '希望您最近一切顺利。'], [], req(3))


@pytest.mark.parametrize(
    'claim',
    [
        '当前我们有一款黑色肩包',
        '这款依然在我们的设计经典中',
        '折影系列一直受喜爱',
        '检查后确保没有影响使用',
        '折影系列仍然是经典设计',
    ],
)
def test_v6_hard_rule_blocks_the_four_v5_critical_claim_types(claim):
    assert any('outcome claim' in f for f in findings([claim + '。', *SAFE[1:]], [CATALOGUE['products'][3]], req(1)))


def test_v6_scope_keeps_banned_wording_and_salutation_soft():
    assert not any('outcome claim' in f for f in findings(SAFE, [CATALOGUE['products'][3]], req(1)))
    assert findings(['亲爱的，这款侧面有折叠感。', *SAFE[1:]], [CATALOGUE['products'][3]], req(1)) == []


def test_repair_feedback_names_only_the_failing_candidates():
    v = OutputValidator()
    v.validate(
        drafts('这款侧面有折叠感。', '当前我们有一款黑色肩包。', '检查后确保没问题。'),
        [CATALOGUE['products'][3]],
        req(1),
    )
    assert any(x.startswith('候选2:') for x in v.indexed)
    assert any(x.startswith('候选3:') for x in v.indexed)
    assert not any(x.startswith('候选1:') for x in v.indexed)

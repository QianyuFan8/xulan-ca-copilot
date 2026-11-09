"""Unit tests: a contact refusal is never treated as a care question, and "today" is the client's today."""

from xulan.service import ContactPolicyEvaluator, OutputValidator, local_date

from support import VALID, drafts, req


def care_request(message, preference='no_contact'):
    r = req(2)
    r.client_information.contact_preference = preference
    r.conversation_history[-1].content = message
    return r


def test_no_contact_client_refusing_contact_is_blocked_even_with_polite_wording():
    for message in ('请不要再联系我', '请别再给我发消息了', '包的问题我自己处理，不用联系我了'):
        _, blocking = ContactPolicyEvaluator().evaluate(care_request(message))
        assert blocking, message


def test_no_contact_client_asking_a_care_question_still_gets_a_service_reply():
    for message in ('这只包刚买回来，平时怎么保养？', '包角有点掉色，能修吗？', '请问皮面划痕怎么处理'):
        _, blocking = ContactPolicyEvaluator().evaluate(care_request(message))
        assert not blocking, message


def test_polite_request_without_a_care_topic_is_not_a_service_request():
    _, blocking = ContactPolicyEvaluator().evaluate(care_request('请稍等'))
    assert blocking


def birthday_at(reference, timezone='Asia/Shanghai'):
    r = req(0)  # birthday on 2026-11-09
    r.scenario_details['occasion_date'] = '2026-11-09'
    r.client_information.timezone = timezone
    r.current_datetime = r.current_datetime.fromisoformat(reference)
    return r


def test_today_is_judged_in_the_client_timezone():
    # 2026-11-08 16:30 UTC is 2026-11-09 00:30 in Shanghai: the birthday is today for the client.
    r = birthday_at('2026-11-08T16:30:00+00:00')
    assert local_date(r).isoformat() == '2026-11-09'
    _, findings = OutputValidator().validate(
        drafts('林女士，今天生日快乐。', '林女士，生日快乐。', '林女士，祝您生日快乐。'), [], r
    )
    assert not any('today' in f for f in findings)


def test_advance_greeting_still_required_when_the_client_date_differs():
    r = birthday_at('2026-11-08T12:00:00+08:00')  # 8 Nov in Shanghai
    _, findings = OutputValidator().validate(
        drafts('林女士，今天生日快乐。', '林女士，生日快乐。', '林女士，祝您生日快乐。'), [], r
    )
    assert any('today' in f for f in findings)


def test_unknown_timezone_falls_back_to_the_reference_offset():
    r = birthday_at('2026-11-09T00:30:00+08:00', timezone='Mars/Base')
    assert local_date(r).isoformat() == '2026-11-09'


def test_valid_fixture_still_passes():
    _, findings = OutputValidator().validate(VALID, [], req(0))
    assert findings == []


def test_no_contact_client_declining_service_is_blocked_even_with_care_words():
    for message in (
        '我不需要维修服务，谢谢。',
        '包没有问题，也不需要服务。',
        '不用麻烦了，保养我自己来。',
        '算了，不修了',
    ):
        _, blocking = ContactPolicyEvaluator().evaluate(care_request(message))
        assert blocking, message


def test_care_word_without_a_request_is_not_a_service_request():
    _, blocking = ContactPolicyEvaluator().evaluate(care_request('上次保养过了。'))
    assert blocking


def test_storage_question_with_buyong_is_still_a_care_request():
    # "不用的时候" (when not in use) is not a refusal.
    _, blocking = ContactPolicyEvaluator().evaluate(care_request('不用的时候应该怎么存放？'))
    assert not blocking

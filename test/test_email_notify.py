# dirty hack to make the parts of the znc module we're using importable
import imp
import sys
znc = imp.new_module('znc')
znc_code = """
CONTINUE = 'CONTINUE'
class Module(object):
    def GetNetwork(self):
        pass
    def PutModule(self, msg):
        pass
"""
exec(znc_code, znc.__dict__)
sys.modules['znc'] = znc

import mock
from notify_email import (should_notify, create_PrivMsg_email_subject, create_PrivMsg_email_body,
                          create_ChanMsg_email_subject, create_ChanMsg_email_body, notify_email)

def test_should_notify_should_return_true_if_msg_contains_thing():
    assert should_notify(['foo', 'quux', 'xyzzy'], 'foo bar baz')
    assert should_notify(['foo', 'quux', 'xyzzy'], 'bar foo baz')
    assert should_notify(['foo', 'quux', 'xyzzy'], 'bar baz foo')

def test_should_notify_should_return_false_if_msg_does_not_contain_thing():
    assert not should_notify(['foo', 'quux', 'xyzzy'], 'bar baz')

def test_create_PrivMsg_email_subject():
    assert create_PrivMsg_email_subject('efnet', 'oyvindio') == \
           'ZNC notify_email: oyvindio is trying to reach you on efnet'

def test_create_PrivMsg_email_body():
    expected = """
    Hello,

    oyvindio is trying to reach you on efnet, but you are currently AWAY.
    Here is the message:

    1970-01-01 00:00:00 <oyvindio>: the message

    -- 
    znc notify_email.py module
    """
    actual = create_PrivMsg_email_body('efnet', 'oyvindio', 'the message', '1970-01-01 00:00:00')
    assert actual == expected

def test_create_ChanMsg_email_subject():
    assert create_ChanMsg_email_subject('efnet', 'oyvindio', '#channel') == \
           'ZNC notify_email: oyvindio is trying to reach you in #channel on efnet'

def test_create_ChanMsg_email_body():
    expected = """
    Hello,

    oyvindio is trying to reach you in #channel on efnet, but you are currently AWAY.
    Here is the message:

    1970-01-01 00:00:00 <oyvindio>: the message

    -- 
    znc notify_email.py module
    """
    actual = create_ChanMsg_email_body('efnet', 'oyvindio', '#channel', 'the message', '1970-01-01 00:00:00')
    assert actual == expected

@mock.patch('znc.Module.GetNetwork')
def test_isAway(GetNetwork):
    notify_email().isAway()
    GetNetwork.assert_has_calls([mock.call(), mock.call().IsIRCAway()])

@mock.patch('znc.Module.GetNetwork')
def test_currentNetworkName(GetNetwork):
    notify_email().currentNetworkName()
    GetNetwork.assert_has_calls([mock.call(), mock.call().GetName()])

@mock.patch('znc.Module.PutModule')
@mock.patch('requests.post')
def test_send_mailgun_email_ok(post, PutModule):
    base_url = 'http://example.com'
    api_key = 'key'
    sender = 'sender@example.com'
    recipient = 'recipient@example.com'
    subject = 'subject'
    body = 'body'
    message_id = 'message_id'

    res = mock.MagicMock(ok=True, text='{"id":"%s"}' % message_id)
    post.return_value = res

    notify_email().send_mailgun_email(base_url, api_key, sender, recipient, subject, body)

    post.assert_called_with(base_url + '/messages', auth=('api', api_key), data={
        'from': sender,
        'to': recipient,
        'subject': subject,
        'text': body
    })
    PutModule.assert_called_with('Successfully notified {}, mailgun id={}'.format(recipient, message_id))

@mock.patch('znc.Module.PutModule')
@mock.patch('requests.post')
def test_send_mailgun_email_failure(post, PutModule):
    base_url = 'http://example.com'
    api_key = 'key'
    sender = 'sender@example.com'
    recipient = 'recipient@example.com'
    subject = 'subject'
    body = 'body'

    status = 400
    reason = 'Bad Request'
    text = '{"error": "oh no!"}'
    res = mock.MagicMock(ok=False, status=status, reason=reason, text=text)
    post.return_value = res

    notify_email().send_mailgun_email(base_url, api_key, sender, recipient, subject, body)

    post.assert_called_with(base_url + '/messages', auth=('api', api_key), data={
        'from': sender,
        'to': recipient,
        'subject': subject,
        'text': body
    })
    PutModule.assert_called_with('Error while notifying {}, response from mailgun: {} {}\n{}'.format(
        recipient, status, reason, text))

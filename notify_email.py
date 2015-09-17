import datetime
import json
import re
import traceback

import znc
import requests

def should_notify(notify_on, msg):
    return any((thing in msg for thing in notify_on))

def now_timestamp():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def create_PrivMsg_email_subject(network, nick):
    return 'ZNC notify_email: {nick} is trying to reach you on {network}'.format(network=network, nick=nick)

def create_PrivMsg_email_body(network, nick, msg, timestamp):
    return """
    Hello,

    {nick} is trying to reach you on {network}, but you are currently AWAY.
    Here is the message:

    {time} <{nick}>: {msg}

    -- 
    znc notify_email.py module
    """.format(network=network, nick=nick, msg=msg, time=timestamp)


def create_ChanMsg_email_subject(network, nick, channel):
    return 'ZNC notify_email: {nick} is trying to reach you in {channel} on {network}'.format(
        network=network, nick=nick, channel=channel)

def create_ChanMsg_email_body(network, nick, channel, msg, timestamp):
    return """
    Hello,

    {nick} is trying to reach you in {channel} on {network}, but you are currently AWAY.
    Here is the message:

    {time} <{nick}>: {msg}

    -- 
    znc notify_email.py module
    """.format(network=network, nick=nick, channel=channel, msg=msg, time=timestamp)

class notify_email(znc.Module):
    description = 'Notify highlights and private messages by email'

    def __print_stacktrace_on_error(function):
        def function_wrapper(self, *args, **kwargs):
            try:
                return function(self, *args, **kwargs)
            except:
                self.PutModule('Caught exception:')
                self.PutModule(traceback.format_exc())
        return function_wrapper

    @__print_stacktrace_on_error
    def OnLoad(self, args_string, message):
        args = re.split('\s+', args_string.strip())
        if len(args) >= 5:
            api_url, api_key, sender, recipient, *notify_on = args
            self.mailgun_api_url = api_url
            self.mailgun_api_key = api_key
            self.mailgun_sender = sender
            self.mailgun_recipient = recipient
            self.notify_on = notify_on

            self.PutModule('Set mailgun_api_url: {}'.format(self.mailgun_api_url))
            self.PutModule('Set mailgun_api_key: {}'.format(self.mailgun_api_key))
            self.PutModule('Set mailgun_sender: {}'.format(self.mailgun_sender))
            self.PutModule('Set mailgun_recipient: {}'.format(self.mailgun_recipient))
            self.PutModule('Set notify_on: {}'.format(self.notify_on))
            return True
        else:
            self.PutModule('Requires at least 5 arguments: mailgun_api_url mailgun_api_key mailgun_sender mailgun_recipient notify_on [notify_on ...]')
            return False


    @__print_stacktrace_on_error
    def OnChanMsg(self, nick, channel, msg):
        if self.isAway() and should_notify(self.notify_on, msg.s):
            self.PutModule('{} said {} in {}, notifying {}'.format(nick.GetNick(), msg.s, channel.GetName(),
                                                                   mailgun_recipient))
            email_subject = create_ChanMsg_email_subject(self.currentNetworkName(), nick.GetNick(), channel.GetName())
            email_body = create_ChanMsg_email_body(self.currentNetworkName(), nick.GetNick(), channel.GetName(),
                                                   msg.s, now_timestamp())
            self.send_mailgun_email(self.mailgun_api_url, self.mailgun_api_key, self.mailgun_sender,
                                    self.mailgun_recipient, email_subject, email_body)

        return znc.CONTINUE

    @__print_stacktrace_on_error
    def OnPrivMsg(self, nick, msg):
        if self.isAway():
            self.PutModule('{} said {} in query, notifying {}'.format(nick.GetNick(), msg.s, mailgun_recipient))
            email_subject = create_PrivMsg_email_subject(self.currentNetworkName(), nick.GetNick())
            email_body = create_PrivMsg_email_body(self.currentNetworkName(), nick.GetNick(), msg.s, now_timestamp())
            self.send_mailgun_email(self.mailgun_api_url, self.mailgun_api_key, self.mailgun_sender,
                                    self.mailgun_recipient, email_subject, email_body)
        return znc.CONTINUE

    def send_mailgun_email(self, base_url, api_key, sender, recipient, subject, body):
        url = base_url + 'messages' if base_url.endswith('/') else base_url + '/messages'
        payload = {
            'from': sender,
            'to': recipient,
            'subject': subject,
            'text': body
        }

        res = requests.post(url, auth=('api', api_key), data=payload)
        if res.ok:
            res_body = json.loads(res.text)
            self.PutModule('Successfully notified {}, mailgun id={}'.format(recipient, res_body['id']))
            return True
        else:
            error = '{status} {reason}\n{text}'.format(status=res.status, reason=res.reason, text=res.text)
            self.PutModule('Error while notifying {}, response from mailgun: {}'.format(recipient, error))
            return False

    def isAway(self):
        return self.GetNetwork().IsIRCAway()

    def currentNetworkName(self):
        return self.GetNetwork().GetName()

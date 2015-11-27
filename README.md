[![Build Status](https://travis-ci.org/oyvindio/znc_notify_email.svg?branch=master)](https://travis-ci.org/oyvindio/znc_notify_email)

# notify_email.py

This is a module for [znc](http://wiki.znc.in/ZNC) that sends an email to a specified address when someone sends you a
private message or mentions you (or some other predefined string) in a channel you are in.  notify_email.py uses uses
the [Mailgun](http://www.mailgun.com/) API to send email so you don't need a local SMTP server, just a Mailgun account
(currently free up to 10k emails/month).
I wrote this mostly to scratch an itch, so it is a bit rough around the edges.

## Requirements
- znc must be built and linked with modpython.so (use `./configure --enable-python`, or refer to the znc install instructions)
- requests must be installed and available on the linked python's `$PYTHONPATH`. It can be installed with pip or easy_install.

## Usage
First, you need your mailgun api url and api key. You can find these under https://mailgun.com/app/domains. Select
your domain and look for "API Base URL" and "API Key", respectively.

- Copy notify_email.py into your znc modules dir, typically ~/.znc/modules/ or /usr/share/znc/modules/
- Load the module in your irc client. For `$mailgun_api_url` and `$mailgun_api_key`, see above. `$mailgun_sender` will be
in the `From:` and `Reply-To:` email headers. The notification email will be sent to
`$mailgun_recipient`. `$notify_on` is a list of words (separated by whitespace) that will trigger a notification when
mentioned in a channel you are in.

```
/msg *status loadmod modpython
/msg *status loadmod notify_email $mailgun_api_url $mailgun_api_key $mailgun_sender $mailgun_recipient $notify_on...
```

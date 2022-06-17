import imaplib
import re

from flask import Flask, request, Response
from threading import Thread

from zommoros.utils.retry import retry
from zommoros.config import email_conf, signal_hook_port

class Signal:
    def __init__(self, text=None):
        self.open_long = text == 'OpenLong'
        self.open_short = text == 'OpenShort'
        self.close_long = text == 'CloseLong'
        self.close_short = text == 'CloseShort'

    def distribute(self):
        return self.open_long, self.open_short, self.close_long, self.close_short

@retry
def fetch_signal_by_email():
    imapobj = imaplib.IMAP4_SSL(email_conf['imap'])
    imapobj.login(email_conf['user'], email_conf['pass'])
    imapobj.select('Inbox')
    stat, msg_ids = imapobj.search(None, '(SUBJECT "Zommoros-Signal")')
    for msg_id in msg_ids[0].split():
        stat, data = imapobj.fetch(msg_id, '(RFC822)')
        imapobj.store(msg_id, '+FLAGS', '\\Deleted')
        raw_email = data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        matched = re.search('>Signal-\w*<', raw_email_string)
        if matched is None:
            break
        signal = Signal(matched.group().strip('><').split('-')[-1])
        imapobj.logout()
        return signal.distribute()
    return Signal().distribute()


class SignalHook:
    server = Flask('Signal Hook')
    signals_queue = list()

    def __init__(self):
        SignalHook.signals_queue = list()

    @server.route("/signal-hook", methods=['POST'])
    def signal_hook():
        text = request.get_data(as_text=True)
        SignalHook.signals_queue.append(Signal(text))
        return Response(status=200)

    def serve(self):
        server_thread = Thread(target=SignalHook.server.run, kwargs={'host':'127.0.0.1', 'port':signal_hook_port, 'debug': False})
        server_thread.start()

    def fetch_signal(self):
        if self.signals_queue:
            return self.signals_queue.pop(0).distribute()
        else:
            return Signal().distribute()

# Exchange API-Key:
api = {
    'testnet': {
        'key': '',
        'secret': ''
    },
    'binance': {
        'key': '',
        'secret': ''
    },
    'okexmn': {
        'key': '',
        'secret': '',
        'passphrase': ''
    }
}

# Email Alert Config:
email_conf = {
    # 'imap': '',
    'smtp': '',
    'user': '',
    'pass': '',
}

# Dingtalk Chatbot Webhook:
webhook_url = ''

# Signal Hook Port:
signal_hook_port = 8123

# 预加载的环境:
prenv = '''
from zommoros.database import *
from zommoros.recipe import *
from zommoros.config import api
config = {
    'apiKey': api['okexmn']['key'],
    'secret': api['okexmn']['secret'],
    'password': api['okexmn']['passphrase'],
    'timeout': 30000,
    'enableRateLimit': True,
    'headers': {
      "x-simulated-trading": '1'
    },
    'options': {
        'defaultType': 'future',
        'adjustForTimeDifference': True,
    }
}
store = CCXTStore(exchange='okex', currency='USDT', config=config, retries=5)
'''

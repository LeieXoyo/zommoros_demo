import smtplib
from email.mime.text import MIMEText
import traceback
from dingtalkchatbot.chatbot import DingtalkChatbot

from zommoros.config import email_conf, webhook_url

def sendmail(level, content):
    message = MIMEText(content)
    message['From'] = email_conf['user']
    message['To'] = email_conf['user']
    message['Subject'] = f'Zommoros {level}'

    try:    
        smtpobj = smtplib.SMTP_SSL(email_conf['smtp'])
        smtpobj.login(email_conf['user'], email_conf['pass'])
        smtpobj.sendmail(email_conf['user'], [email_conf['user']], message.as_string())
        print('邮件发送成功!')
    except Exception:
        traceback.print_exc()
        print(f'无法发送邮件, 重试中......')
        sendmail(level, content)

def dingtalk(content):
    DingtalkChatbot(webhook_url).send_text(msg=content, is_at_all=True)

def sendmail_and_dingtalk(level, content):
    sendmail(level, content)
    dingtalk(content)

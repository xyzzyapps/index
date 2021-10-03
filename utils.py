import smtplib, ssl
from email.mime.text import MIMEText
import yaml

def safe_load(text):

    try:
        nodes = yaml.load(text, yaml.SafeLoader)
    except yaml.YAMLError as exc:
        return {"nodes": [{"text" : "Parse Error"}]}

    return nodes

def send_mail(to_mail, name, reply_to, server, password, subject, message):
    context = ssl.create_default_context()

    message_template = """<html>
  <head></head>
  <body>
  <p>%s</p>
  </body>
</html>
    """

    message = message_template % (message)

    msg = MIMEText(message, 'html')
    msg['Subject'] = subject
    msg['From'] = name + " <" + reply_to + ">"
    msg['To'] = to_mail

    with smtplib.SMTP_SSL(server, 465, context=context) as server:
        server.ehlo()
        server.login(reply_to, password)
        server.send_message(msg)



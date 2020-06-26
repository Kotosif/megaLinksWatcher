import smtplib
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from email.message import EmailMessage

class EmailService:

    def __init__(self, username, password):
        self.server = None
        self.username = username
        self.password = password

    def setupSMTPServer(self):
        # Make sure you have set your gmail account settings to
        # accept less secure apps
        # https://myaccount.google.com/lesssecureapps
        # server = smtplib.SMTP('smtp.gmail.com', 587)

        server = smtplib.SMTP(host='smtp.sendgrid.net', port=587)

        server.set_debuglevel(True)
        server.ehlo()
        server.starttls()
        server.ehlo()
        self.server = server

    def closeSMTPServer(self):
        self.server.close()

    def login(self):
        self.server.login(self.username, self.password)

    def sendEmail(self, fromAddress, toAddress, subject, content):
        try:
            msg = EmailMessage()
            msg.set_content(str(content))
            msg["Subject"] = subject
            msg["From"] = fromAddress
            msg["To"] = toAddress
            self.server.send_message(msg)
        except smtplib.SMTPSenderRefused as error:
            print(error)
            self.closeSMTPServer()
            self.setupSMTPServer()
            self.login(self.username, self.password)
            self.sendEmail(fromAddress, toAddress, subject, content)



    

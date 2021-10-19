
+12057842415

ACa21f67534578f3e0e4ec9825c037830d
3f1b1de4b8993106e17006053566788c

# Download the helper library from https://www.twilio.com/docs/python/install
from twilio.rest import Client


# Your Account Sid and Auth Token from twilio.com/console
# DANGER! This is insecure. See http://twil.io/secure
account_sid = 'ACa21f67534578f3e0e4ec9825c037830d'
auth_token = '3f1b1de4b8993106e17006053566788c'
client = Client(account_sid, auth_token)

message = client.messages \
                .create(
                     body="Join Earth's mightiest heroes. Like Kevin Bacon.",
                     from_='+12057842415',
                     to='+821039550649'
                 )

print(message.sid)
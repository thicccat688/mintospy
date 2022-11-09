from mintospy.api import API
import os


email = os.getenv(key='MINTOS_EMAIL')
password = os.getenv(key='MINTOS_PASSWORD')
tfa_secret = os.getenv(key='MINTOS_TFA_SECRET')


mintos_client = API(
    email=email,
    password=password,
    tfa_secret=tfa_secret,
)


def test_login():
    assert isinstance(mintos_client.login(), str)

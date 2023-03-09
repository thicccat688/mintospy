from mintospy.api import MintosApi
from mintospy.enums import Currency
import os


email = os.getenv(key='email')
password = os.getenv(key='password')
tfa_secret = os.getenv(key='tfa_secret')


mintos_client = MintosApi(
    email=email,
    password=password,
    tfa_secret=tfa_secret,
)

investments = mintos_client.get_investments(currency=Currency.EUR, quantity=900)

print(investments.iloc[0].name)

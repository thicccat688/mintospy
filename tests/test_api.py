from mintospy.api import API
import pandas as pd
import os


email = os.getenv(key='email')
password = os.getenv(key='password')
tfa_secret = os.getenv(key='tfa_secret')


mintos_client = API(
    email=email,
    password=password,
    tfa_secret=tfa_secret,
)


def test_investments():
    assert isinstance(mintos_client.get_investments(currency='EUR', quantity=50), pd.DataFrame)


def test_investment_filters():
    assert isinstance(mintos_client.get_investment_filters(), dict)


def test_loans():
    assert isinstance(mintos_client.get_loans(currencies=['EUR', 'KZT']), pd.DataFrame)


def test_loan_filters():
    assert isinstance(mintos_client.get_loan_filters(), dict)

from mintospy.api import API
import pandas as pd
import pytest
import os


email = os.getenv(key='email')
password = os.getenv(key='password')
tfa_secret = os.getenv(key='tfa_secret')


mintos_client = API(
    email=email,
    password=password,
    tfa_secret=tfa_secret,
)


def test_portfolio():
    assert isinstance(mintos_client.get_portfolio_data(currency='EUR'), dict)


def test_net_annual_return():
    assert isinstance(mintos_client.get_net_annual_return(currency='EUR'), dict)


def test_aggregates_overview():
    assert isinstance(mintos_client.get_aggregates_overview(currency='EUR'), dict)


@pytest.mark.parametrize('current, claims', [(True, True), (True, False), (False, True), (False, False)])
def test_investments(current: bool, claims: bool):
    assert isinstance(
        mintos_client.get_investments(
            currency='EUR',
            quantity=200,
            current=current,
            claims=claims,
        ),
        pd.DataFrame,
    )


def test_investment_filters():
    assert isinstance(mintos_client.get_investment_filters(), dict)


def test_loans():
    assert isinstance(mintos_client.get_loans(currencies=['EUR', 'KZT']), pd.DataFrame)

    assert isinstance(mintos_client.get_loans(currencies=['EUR', 'KZT'], secondary_market=True), pd.DataFrame)


def test_loan_filters():
    assert isinstance(mintos_client.get_loan_filters(), dict)


def test_loan_details():
    assert isinstance(mintos_client.get_note_details('LVX000036GR5'), pd.DataFrame)

    assert isinstance(mintos_client.get_claim_details('35917500'), dict)

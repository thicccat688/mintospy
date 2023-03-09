from mintospy.api import MintosApi
import pandas as pd
import random
import pytest
import os


email = os.getenv(key='email')
password = os.getenv(key='password')
tfa_secret = os.getenv(key='tfa_secret')


mintos_client = MintosApi(
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
    quantity = random.randint(400, 1400)

    investments = mintos_client.get_investments(
        currency='KZT',
        quantity=quantity,
        current=current,
        claims=claims,
    )

    assert isinstance(investments, pd.DataFrame)
    assert len(investments) == quantity


@pytest.mark.parametrize('secondary_market', [True, False])
def test_loans(secondary_market: bool):
    quantity = random.randint(400, 1400)

    loans = mintos_client.get_loans(
        currencies=['EUR', 'KZT'],
        quantity=quantity,
        secondary_market=secondary_market,
    )

    assert isinstance(loans, pd.DataFrame)

    assert len(loans) == quantity


def test_loan_filters():
    assert isinstance(mintos_client.get_loan_filters(), dict)


def test_loan_details():
    assert isinstance(mintos_client.get_note_loans('LVX000036GR5'), pd.DataFrame)

    assert isinstance(mintos_client.get_claim_details('35917500'), dict)


def test_currencies():
    assert isinstance(mintos_client.get_currencies(), dict)


def test_countries():
    assert isinstance(mintos_client.get_countries(), dict)


def test_lending_companies():
    assert isinstance(mintos_client.get_lending_companies(), dict)

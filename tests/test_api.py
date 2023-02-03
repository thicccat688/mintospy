from mintospy.api import API
import pandas as pd
import pytest
import os


email = os.getenv(key='email')
password = os.getenv(key='password')
tfa_secret = os.getenv(key='tfa_secret')


mintos_client = API(
    cookies=[{'domain': 'www.mintos.com', 'expiry': 1675438245, 'httpOnly': True, 'name': 'PHPSESSID', 'path': '/', 'secure': True, 'value': 'da16522b1d25d758fd554dfab0e279e2'}, {'domain': '.mintos.com', 'expiry': 1675439139, 'httpOnly': False, 'name': '_hjSession_2581613', 'path': '/', 'sameSite': 'None', 'secure': True, 'value': 'eyJpZCI6IjYzMGJkMWIxLTc4N2ItNGJmMS04MDM0LTYyYWYyMmE3MDY2NyIsImNyZWF0ZWQiOjE2NzU0MzczMzkxMTksImluU2FtcGxlIjpmYWxzZX0='}, {'domain': 'www.mintos.com', 'expiry': 1675437459, 'httpOnly': False, 'name': '_hjIncludedInSessionSample', 'path': '/', 'sameSite': 'None', 'secure': True, 'value': '0'}, {'domain': '.mintos.com', 'expiry': 1675439160, 'httpOnly': False, 'name': '_hjAbsoluteSessionInProgress', 'path': '/', 'sameSite': 'None', 'secure': True, 'value': '1'}, {'domain': '.mintos.com', 'expiry': 1706973339, 'httpOnly': False, 'name': '_hjSessionUser_2581613', 'path': '/', 'sameSite': 'None', 'secure': True, 'value': 'eyJpZCI6Ijc3N2RhZDhiLTAwMjUtNWVmYy04ZTc4LTZmY2ZiMjJlNDUxZCIsImNyZWF0ZWQiOjE2NzU0MzczMzkxMDgsImV4aXN0aW5nIjpmYWxzZX0='}, {'domain': '.mintos.com', 'expiry': 1675437398, 'httpOnly': False, 'name': '_gat_UA-53926147-5', 'path': '/', 'secure': False, 'value': '1'}, {'domain': '.mintos.com', 'expiry': 1709997360, 'httpOnly': False, 'name': '_ga', 'path': '/', 'secure': False, 'value': 'GA1.2.648091163.1675437337'}, {'domain': '.mintos.com', 'expiry': 1709997361, 'httpOnly': False, 'name': '_ga_05GWN1FMW6', 'path': '/', 'secure': False, 'value': 'GS1.1.1675437336.1.1.1675437361.0.0.0'}, {'domain': '.mintos.com', 'expiry': 1683213336, 'httpOnly': False, 'name': '_gcl_au', 'path': '/', 'secure': False, 'value': '1.1.672183362.1675437336'}, {'domain': '.mintos.com', 'expiry': 1706973338, 'httpOnly': False, 'name': 'OptanonConsent', 'path': '/', 'sameSite': 'Lax', 'secure': False, 'value': 'isGpcEnabled=0&datestamp=Fri+Feb+03+2023+15%3A15%3A38+GMT%2B0000+(Western+European+Standard+Time)&version=6.24.0&isIABGlobal=false&hosts=&consentId=92c2b2df-b836-4971-9851-f1beff3cafa8&interactionCount=0&landingPath=https%3A%2F%2Fwww.mintos.com%2Fen%2Flogin&groups=C0001%3A1%2CC0002%3A1%2CC0004%3A0%2CC0003%3A0'}, {'domain': '.mintos.com', 'expiry': 1675523760, 'httpOnly': False, 'name': '_gid', 'path': '/', 'secure': False, 'value': 'GA1.2.2131459527.1675437339'}, {'domain': 'www.mintos.com', 'expiry': 1675438260, 'httpOnly': True, 'name': 'MW_SESSION_ID', 'path': '/', 'secure': False, 'value': 's%3AUQxOcmEZPPqL-wdKYgjmzYseVydElKGd.cLayXgIQaXJXDKPBukE3%2Bteqj5S6Jg55K7IdAavBnbY'}, {'domain': '.mintos.com', 'expiry': 1675439139, 'httpOnly': False, 'name': '_hjFirstSeen', 'path': '/', 'sameSite': 'None', 'secure': True, 'value': '1'}],
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


def test_currencies():
    assert isinstance(mintos_client.get_currencies(), dict)


def test_countries():
    assert isinstance(mintos_client.get_countries(), dict)


def test_lending_companies():
    assert isinstance(mintos_client.get_lending_companies(), dict)

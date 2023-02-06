from mintospy.exceptions import MintosException
from mintospy.constants import CONSTANTS
from mintospy.endpoints import ENDPOINTS
from mintospy.utils import Utils
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException
from selenium_recaptcha_solver import API as RECAPTCHA_API
from selenium_stealth import stealth
from typing import Union, List
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
import selenium.common.exceptions
import pandas as pd
import cloudscraper
import warnings
import pickle
import pyotp
import os


class API:
    def __init__(
            self,
            email: str = None,
            password: str = None,
            tfa_secret: str = None,
            google_api_key: str = None,
            cookies: List[dict] = None,
            save_cookies: bool = True,
    ):
        """
        Mintos API wrapper with all relevant Mintos functionalities.
        :param email: Account's email
        :param password: Account's password
        :param tfa_secret: Base32 secret used for two-factor authentication
        :param google_api_key: API key for Speech Recognition API for solving ReCAPTCHA challenges with audio
        (Recommended for production. Will use default API key provided by Google if not provided)
        :param cookies: Cookies to load in to web driver on boot
        :param save_cookies: Set to false if you don't want your cookies to be saved locally for faster login
        (Only mandatory if account has two-factor authentication enabled)
        """

        if not cookies:
            if email is None:
                raise ValueError('Invalid email.')

            if password is None:
                raise ValueError('Invalid password.')

            if tfa_secret is None:
                warnings.warn('Using two-factor authentication with your Mintos account is highly recommended.')

        self.email = email
        self.password = password
        self.tfa_secret = tfa_secret

        self.should_save = save_cookies
        self.cookies = cookies if cookies else Utils.import_cookies(f'{email}_cookies.pkl')

        # Initialise Cloudscraper scraper object
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True,
            },
        )

        if self.cookies:
            for cookie in self.cookies:
                self.scraper.cookies.set(cookie['name'], cookie['value'])

        else:
            # Initialise web driver session
            self.driver = self._create_driver()

            # Initialise RecaptchaV2 solver object
            self.solver = RECAPTCHA_API(driver=self.driver, google_api_key=google_api_key)

            try:
                # Automatically authenticate to Mintos API upon API object initialization
                self.login()

            except TimeoutException:
                raise MintosException('Check your network connection.')

        self.csrf_token = self._get_csrf_token()

        self.scraper.headers.update({'anti-csrf-token': self.csrf_token})

    def get_portfolio_data(self, currency: str) -> dict:
        """
        :param currency: Currency of portfolio to get data from
        :return: Active/late funds, bad debt, defaulted debt, funds in recovery, count of active investments, and so on
        """

        currency_iso_code = CONSTANTS.get_currency_iso(currency)

        response = self.scraper.get(
            url=ENDPOINTS.API_PORTFOLIO_URI,
            params={'currencyIsoCode': currency_iso_code},
        ).json()

        return Utils.parse_mintos_items(response)

    def get_net_annual_return(self, currency: str) -> dict:
        """
        :param currency: Currency of portfolio to get data from
        :return: Net annual return of requested portfolio with and without campaign bonuses
        """

        currency_iso_code = CONSTANTS.get_currency_iso(currency)

        response = self.scraper.get(
            url=ENDPOINTS.API_NAR_URI,
            params={'currencyIsoCode': currency_iso_code},
        ).json()

        return Utils.parse_mintos_items(response)

    def get_aggregates_overview(self, currency: str) -> dict:
        """
        :param currency: Currency of portfolio to get data from
        :return: Same data returned by get_portfolio_data, but with outstanding principals and pending payments
        """

        currency_iso_code = CONSTANTS.get_currency_iso(currency)

        response = self.scraper.get(
            url=ENDPOINTS.API_AGGREGATES_OVERVIEW_URI,
            params={'currencyIsoCode': currency_iso_code, 'lenderStatus': 'All'},
        ).json()

        return Utils.parse_mintos_items(response)

    def get_investments(
            self,
            currency: str,
            quantity: int = 30,
            start_page: int = 1,
            claims: bool = False,
            sort_field: str = 'invested_amount',
            countries: List[str] = None,
            pending_payments: bool = None,
            amortization_methods: List[str] = None,
            claim_id: str = None,
            isin: str = None,
            late_loan_exposure: List[str] = None,
            lending_companies: List[str] = None,
            lender_statuses: List[str] = None,
            listed_for_sale: bool = None,
            max_interest_rate: float = None,
            min_interest_rate: float = None,
            loan_types: List[str] = None,
            max_risk_score: float = 10,
            min_risk_score: float = 0,
            strategies: List[str] = None,
            max_term: int = None,
            min_term: int = None,
            max_purchased_date: datetime = None,
            min_purchased_date: datetime = None,
            current: bool = True,
            ascending_sort: bool = False,
            raw: bool = False,
    ) -> Union[pd.DataFrame, List[dict]]:
        """
        :param currency: Currency that investments are denominated in
        :param quantity: Quantity of investments to get
        :param start_page: Page to start getting investments from (Gets from first page by default)
        :param claims: Specify whether to get Notes or Claims (True -> Gets claims; False -> Gets notes)
        :param sort_field: Field to sort by (
        Notes sort fields:
        isin -> Sort by Notes' International Securities Identification Number (ISIN) alphabetically;
        risk_score -> Sort by risk score;
        lending_company -> Sort by lending company alphabetically;
        interest_rate -> Sort by interest rate;
        remaining_term -> Sort by remaining term;
        purchase_date -> Sort by purchase date;
        invested_amount -> Sort by invested amount;
        outstanding_principal -> Sort by outstanding principal;
        finished_date -> Sort by finished date;
        -------------------------------------------------------------------------------------
        Claims sort fields:
        id -> Sort by id alphabetically,
        lending_company -> Sort alphabetically by lending company;
        interest_rate -> Sort by interest rate;
        remaining_term -> Sort by remaining term;
        purchase_date -> Sort by purchase date;
        invested_amount -> Sort by invested amount;
        outstanding_principal -> Sort by outstanding principal;
        next_payment_date -> Sort by next planned payment date;
        received_payments -> Sort by received payments;
        pending_payments -> Sort by pending payments;
        finished_date -> Sort by finished date;
        )
        :param countries: What countries notes should be issued from
        :param pending_payments: If payments for notes should be pending or not
        :param amortization_methods: Amortization type of notes (Full, partial, interest-only, or bullet)
        :param claim_id: ID of claim to filter by
        :param isin: International Securities Identification Number (ISIN) of security to filter by
        :param late_loan_exposure: Late loan exposure of notes (0_20 for 0-20%, 20_40 for 20-40%, and so on)
        :param lending_companies: Only return notes issued by specified lending companies
        :param lender_statuses: Only return notes from lenders in a certain state (Active, suspended, or in default)
        :param listed_for_sale: Specify whether to return notes that are on sale in the secondary market or not
        :param max_interest_rate: Only return notes up to this maximum interest rate
        :param min_interest_rate: Only return notes up to this minimum interest rate
        :param loan_types: Only return notes composed of certain loan types
        (agricultural, business, car, invoice_financing, mortgage, pawnbroking, personal, short_term)
        :param max_risk_score: Only returns notes below this risk score (1-10 or "SW" for notes with suspended rating)
        :param min_risk_score: Only returns notes above this risk score (1-10 or "SW" for notes with suspended rating)
        :param strategies: Only return notes that were invested in with certain strategies
        :param max_term: Only return notes up to a maximum term
        :param min_term: Only return notes up to a minimum term
        :param max_purchased_date: Only returns notes purchased before date
        :param min_purchased_date: Only returns notes purchased after date
        :param current: Returns current notes in portfolio if set to true, otherwise returns finished investments
        :param ascending_sort: Sort notes in ascending order based on "sort" argument if True, otherwise sort descending
        :param raw: Return raw notes JSON if set to True, or returns pandas dataframe of notes if set to False
        :return: Pandas DataFrame or raw JSON of notes (Chosen in the "raw" argument)
        """

        currency_iso_code = CONSTANTS.get_currency_iso(currency)

        if claims:
            if sort_field not in CONSTANTS.CLAIMS_SORT_FIELDS:
                raise ValueError(f'{sort_field} not in claims sort fields: {", ".join(CONSTANTS.CLAIMS_SORT_FIELDS)}.')

            parsed_sort_field = CONSTANTS.CLAIMS_SORT_FIELDS[sort_field]

        else:
            if sort_field not in CONSTANTS.NOTES_SORT_FIELDS:
                raise ValueError(f'{sort_field} not in notes sort fields: {", ".join(CONSTANTS.NOTES_SORT_FIELDS)}.')

            parsed_sort_field = CONSTANTS.NOTES_SORT_FIELDS[sort_field]

        investment_params = {'currency': currency_iso_code}

        if claims:
            extra_data = {
                'max_results': CONSTANTS.MAX_RESULTS,
                'sort_field': parsed_sort_field,
                'sort_order': 'ASC' if ascending_sort else 'DESC',
                'page': start_page,
                'format': 'json',
            }

            investment_params.update(extra_data)

        else:
            extra_data = {
                'pagination': {
                    'maxResults': CONSTANTS.MAX_RESULTS,
                    'page': start_page,
                },
                'sorting': {
                    'sortField': parsed_sort_field,
                    'sortOrder': 'ASC' if ascending_sort else 'DESC',
                },
            }

            investment_params.update(extra_data)

        if claims:
            url = ENDPOINTS.API_CLAIMS_URI

            investment_params['status'] = 0 if current else 1

        else:
            url = f'{ENDPOINTS.API_INVESTMENTS_URI}/{"current" if current else "finished"}'

        if start_page < 1:
            raise ValueError('Start page must be superior or equal to 1.')

        if isin and claim_id:
            raise ValueError(f'You can only filter by ISIN or Claim ID.')

        if isinstance(countries, list):
            investment_params['countries'] = []

            for country in countries:
                investment_params['countries'].append(CONSTANTS.get_country_iso(country))

        if isinstance(lending_companies, list):
            investment_params['lenderCompanies'] = []

            for lender in lending_companies:
                investment_params['lenderCompanies'].append(CONSTANTS.get_lending_company_id(lender))

        if isinstance(loan_types, list):
            investment_params['pledges'] = []

            for type_ in loan_types:
                if type_ not in CONSTANTS.LOAN_TYPES:
                    raise ValueError(f'Loan type must be one of the following: {", ".join(CONSTANTS.LOAN_TYPES)}')

                investment_params['pledges'].append(type_)

        if isinstance(amortization_methods, list):
            investment_params['scheduleTypes'] = []

            for method in amortization_methods:
                investment_params['schedule_types'].append(CONSTANTS.get_amoritzation_method_id(method))

        if isinstance(max_risk_score, (float, int)):
            if 1 > max_risk_score > 10:
                raise ValueError(
                    'Maximum risk score needs to be a number in between 1-10.',
                )

            investment_params['maxLendingCompanyRiskScore'] = max_risk_score

        if isinstance(min_risk_score, (float, int)):
            if 1 > min_risk_score > 10:
                raise ValueError(
                    'Minimum risk score needs to be a number in between 1-10.',
                )

            investment_params['minLendingCompanyRiskScore'] = min_risk_score

        if isinstance(strategies, list):
            available_strategies = list(
                map(lambda strat: strat['label'], self.get_investment_filters(current)['autoInvestDefinitions'])
            )

            for strategy in strategies:
                if strategy not in available_strategies:
                    raise ValueError(
                        f'{strategy} must be one of the following strategies: {", ".join(available_strategies)}'
                    )

        if isinstance(isin, str):
            if len(isin) != 12:
                raise ValueError('ISIN must be 12 characters long.')

            investment_params['isin'] = isin

        if isinstance(late_loan_exposure, list):
            investment_params['lateLoanExposures'] = []

            for exposure in late_loan_exposure:
                if exposure not in CONSTANTS.LATE_LOAN_EXPOSURES:
                    raise ValueError(
                        f'Late loan exposure must be one of the following: {", ".join(CONSTANTS.LATE_LOAN_EXPOSURES)}',
                    )

                investment_params['lateLoanExposures'].append(late_loan_exposure)

        if isinstance(pending_payments, bool):
            if claims:
                investment_params['pending_payments_status'] = pending_payments

            else:
                investment_params['hasPendingPayments'] = 1 if pending_payments else 0

        if isinstance(listed_for_sale, bool):
            if claims:
                investment_params['listed_for_sale_status'] = listed_for_sale

            else:
                investment_params['listedForSale'] = 1 if listed_for_sale else 0

        if isinstance(lender_statuses, list):
            investment_params['lenderStatuses'] = []

            for status in lender_statuses:
                if status not in CONSTANTS.LENDING_COMPANY_STATUSES:
                    raise ValueError(
                        f'Lender status must be one of the following: {", ".join(CONSTANTS.LENDING_COMPANY_STATUSES)}',
                    )

                investment_params['lenderStatuses'].append(status)

        if isinstance(max_interest_rate, float):
            investment_params['maxInterestRate'] = max_interest_rate

        if isinstance(min_interest_rate, float):
            investment_params['minInterestRate'] = min_interest_rate

        if isinstance(max_term, float):
            investment_params['termTo'] = max_term

        if isinstance(min_term, int):
            investment_params['termFrom'] = min_term

        if isinstance(max_purchased_date, datetime):
            investment_params['investmentDateTo'] = max_purchased_date.strftime('%d.%m.%Y')

        if isinstance(min_purchased_date, datetime):
            investment_params['investmentDateFrom'] = min_purchased_date.strftime('%d.%m.%Y')

        request_headers = {}

        if claims:
            request_headers['content-type'] = 'application/x-www-form-urlencoded'

        total_retrieved = 0

        response = self.scraper.post(
            url=url,
            headers=request_headers,
            data=investment_params,
        ).json()

        total_retrieved += CONSTANTS.MAX_RESULTS

        responses = [response]

        while total_retrieved < quantity:
            if response['pagination']['total'] < total_retrieved:
                break

            if response.get('errors'):
                raise MintosException(response['errors'][0])

            if claims:
                investment_params['page'] += 1

            else:
                investment_params['pagination']['page'] += 1

            response = self.scraper.post(
                url=url,
                headers=request_headers,
                data=investment_params,
            ).json()

            responses.extend(response)

            total_retrieved += CONSTANTS.MAX_RESULTS

        items = []

        for resp in responses:
            if len(resp) == 0:
                continue

            if claims and resp.get('data'):
                items.extend(resp['data'])

            elif resp.get('items'):
                items.extend(resp['items'])

        items = items[0:quantity]

        if raw or len(items) == 0:
            return items if raw else pd.DataFrame(items)

        row_index = 'ID' if claims else 'ISIN'

        response = pd.DataFrame.from_records(Utils.parse_investments(items)).set_index(row_index).fillna('N/A')

        return response

    def get_investment_filters(self, current: bool = False) -> dict:
        """
        :param current: Set to True to get filters for current investments, else set to False
        :return: Investment filters provided by Mintos
        """

        response = self.scraper.get(
            url=ENDPOINTS.API_INVESTMENTS_FILTER_URI,
            params={'status': 0 if current else 1},
        ).json()

        return response

    def get_loans(
            self,
            currencies: List[str],
            quantity: int = 30,
            start_page: int = 1,
            sort_field: str = 'interest_rate',
            secondary_market: bool = False,
            countries: List[str] = None,
            pending_payments: bool = None,
            amortization_methods: List[str] = None,
            isin: str = None,
            late_loan_exposure: List[str] = None,
            lending_companies: List[str] = None,
            lender_statuses: List[str] = None,
            listed_for_sale: bool = None,
            max_interest_rate: float = None,
            min_interest_rate: float = None,
            loan_types: List[str] = None,
            max_risk_score: float = 10,
            min_risk_score: float = 0,
            strategies: List[str] = None,
            max_term: int = None,
            min_term: int = None,
            direct_investment_structure: bool = None,
            min_investment_amount: float = None,
            current: bool = True,
            ascending_sort: bool = False,
            raw: bool = False,
    ) -> Union[pd.DataFrame, List[dict]]:
        """
        :param currencies: Currencies that investments are denominated in
        :param quantity: Quantity of investments to get
        :param start_page: Page to start getting investments from (Gets from first page by default)
        :param sort_field: Field to sort by (
        Sort fields:
        isin -> Sort by Notes' International Securities Identification Number (ISIN) alphabetically;
        risk_score -> Sort by risk score;
        lending_company -> Sort by lending company alphabetically;
        remaining_term -> Sort by remaining term;
        initial_principal -> Sort by initial principal / remaining;
        interest_rate -> Sort by interest rate;
        available_for_investment -> Sort by amount available for investment;
        )
        :param secondary_market: If True, loans will be retrieved from the secondary market, else from the primary
        :param countries: What countries notes should be issued from
        :param pending_payments: If payments for notes should be pending or not
        :param amortization_methods: Amortization type of notes (Full, partial, interest-only, or bullet)
        :param isin: International Securities Identification Number (ISIN) of security to filter by
        :param late_loan_exposure: Late loan exposure of notes (0_20 for 0-20%, 20_40 for 20-40%, and so on)
        :param lending_companies: Only return notes issued by specified lending companies
        :param lender_statuses: Only return notes from lenders in a certain state (Active, suspended, or in default)
        :param listed_for_sale: Specify whether to return notes that are on sale in the secondary market or not
        :param max_interest_rate: Only return notes up to this maximum interest rate
        :param min_interest_rate: Only return notes up to this minimum interest rate
        :param loan_types: Only return notes composed of certain loan types
        (agricultural, business, car, invoice_financing, mortgage, pawnbroking, personal, short_term)
        :param max_risk_score: Only returns notes below this risk score (1-10 or "SW" for notes with suspended rating)
        :param min_risk_score: Only returns notes above this risk score (1-10 or "SW" for notes with suspended rating)
        :param strategies: Only return notes that were invested in with certain strategies
        :param max_term: Only return notes up to a maximum term
        :param min_term: Only return notes up to a minimum term
        :param direct_investment_structure: Only returns notes with a direct or indirect structure
        :param min_investment_amount: Minimum investment amount for a Note
        :param current: Returns current notes in portfolio if set to true, otherwise returns finished investments
        :param ascending_sort: Sort notes in ascending order based on "sort" argument if True, otherwise sort descending
        :param raw: Return raw notes JSON if set to True, or returns pandas dataframe of notes if set to False
        :return: Pandas DataFrame or raw JSON of notes (Chosen in the "raw" argument)
        """

        if sort_field not in CONSTANTS.LOANS_SORT_FIELDS:
            raise ValueError(f'{sort_field} not in claims sort fields: {", ".join(CONSTANTS.LOANS_SORT_FIELDS)}.')

        parsed_sort_field = CONSTANTS.LOANS_SORT_FIELDS[sort_field]

        investment_params = {'currencies': [CONSTANTS.get_currency_iso(curr) for curr in currencies]}

        extra_data = {
            'pagination': {
                'maxResults': CONSTANTS.MAX_RESULTS,
                'page': start_page,
            },
            'sorting': {
                'sortField': parsed_sort_field,
                'sortOrder': 'ASC' if ascending_sort else 'DESC',
            },
        }

        investment_params.update(extra_data)

        if start_page < 1:
            raise ValueError('Start page must be superior or equal to 1.')

        if isinstance(countries, list):
            investment_params['countries'] = []

            for country in countries:
                investment_params['countries'].append(CONSTANTS.get_country_iso(country))

        if isinstance(lending_companies, list):
            investment_params['lenderCompanies'] = []

            for lender in lending_companies:
                investment_params['lenderCompanies'].append(CONSTANTS.get_lending_company_id(lender))

        if isinstance(loan_types, list):
            investment_params['pledges'] = []

            for type_ in loan_types:
                if type_ not in CONSTANTS.LOAN_TYPES:
                    raise ValueError(f'Loan type must be one of the following: {", ".join(CONSTANTS.LOAN_TYPES)}')

                investment_params['pledges'].append(type_)

        if isinstance(amortization_methods, list):
            investment_params['scheduleTypes'] = []

            for method in amortization_methods:
                investment_params['schedule_types'].append(CONSTANTS.get_amoritzation_method_id(method))

        if isinstance(max_risk_score, (float, int)):
            if 1 > max_risk_score > 10:
                raise ValueError(
                    'Maximum risk score needs to be a number in between 1-10.',
                )

            investment_params['maxLendingCompanyRiskScore'] = max_risk_score

        if isinstance(min_risk_score, (float, int)):
            if 1 > min_risk_score > 10:
                raise ValueError(
                    'Minimum risk score needs to be a number in between 1-10.',
                )

            investment_params['minLendingCompanyRiskScore'] = min_risk_score

        if isinstance(strategies, list):
            available_strategies = list(
                map(lambda strat: strat['label'], self.get_investment_filters(current)['autoInvestDefinitions'])
            )

            for strategy in strategies:
                if strategy not in available_strategies:
                    raise ValueError(
                        f'{strategy} must be one of the following strategies: {", ".join(available_strategies)}'
                    )

        if isinstance(isin, str):
            if len(isin) != 12:
                raise ValueError('ISIN must be 12 characters long.')

            investment_params['isin'] = isin

        if isinstance(late_loan_exposure, list):
            investment_params['lateLoanExposures'] = []

            for exposure in late_loan_exposure:
                if exposure not in CONSTANTS.LATE_LOAN_EXPOSURES:
                    raise ValueError(
                        f'Late loan exposure must be one of the following: {", ".join(CONSTANTS.LATE_LOAN_EXPOSURES)}',
                    )

                investment_params['lateLoanExposures'].append(late_loan_exposure)

        if isinstance(pending_payments, bool):
            investment_params['pending_payments_status'] = 1 if pending_payments else 0

        if isinstance(listed_for_sale, bool):
            investment_params['listed_for_sale_status'] = 1 if listed_for_sale else 0

        if isinstance(lender_statuses, list):
            investment_params['lenderStatuses'] = []

            for status in lender_statuses:
                if status not in CONSTANTS.LENDING_COMPANY_STATUSES:
                    raise ValueError(
                        f'Lender status must be one of the following: {", ".join(CONSTANTS.LENDING_COMPANY_STATUSES)}',
                    )

                investment_params['lenderStatuses'].append(status)

        if isinstance(max_interest_rate, float):
            investment_params['maxInterestRate'] = max_interest_rate

        if isinstance(min_interest_rate, float):
            investment_params['minInterestRate'] = min_interest_rate

        if isinstance(max_term, float):
            investment_params['termTo'] = max_term

        if isinstance(min_term, int):
            investment_params['termFrom'] = min_term

        if isinstance(direct_investment_structure, bool):
            # Mintos' API has true and false reversed for this field
            investment_params['indirectInvestmentStructure'] = direct_investment_structure

        if isinstance(min_investment_amount, float):
            investment_params['minAmount'] = min_investment_amount

        total_retrieved = 0

        response = self.scraper.post(
            url=f'{ENDPOINTS.API_LOANS_URI}/{"secondary" if secondary_market else "primary"}',
            json=investment_params,
        ).json()

        total_retrieved += CONSTANTS.MAX_RESULTS

        responses = [response]

        while total_retrieved < quantity:
            if response['pagination']['total'] < total_retrieved:
                break

            if response.get('errors'):
                raise MintosException(response['errors'][0])

            investment_params['pagination']['page'] += 1

            loans = self.scraper.post(
                url=f'{ENDPOINTS.API_LOANS_URI}/{"secondary" if secondary_market else "primary"}',
                json=investment_params,
            ).json()

            responses.extend(loans)

            total_retrieved += CONSTANTS.MAX_RESULTS

        items = []

        for resp in responses:
            try:
                items.extend(resp['items'])

            except KeyError:
                raise MintosException('Mintos had an issue processing the loan retrieval request.')

            except TypeError:
                pass

        items = items[0:quantity]

        if raw or len(items) == 0:
            return items if raw else pd.DataFrame(items)

        response = pd.DataFrame.from_records(Utils.parse_investments(items)).set_index('ISIN').fillna('N/A')

        return response

    def get_loan_filters(self) -> dict:
        """
        :return: Loan filters provided by Mintos
        """

        response = self.scraper.get(
            url=ENDPOINTS.API_LOANS_FILTER_URI,
        ).json()

        return response

    def get_note_details(self, isin: str, raw: bool = False) -> List[dict]:
        """
        :param isin: ISIN of note
        :param raw: Return raw details in JSON if set to True, or returns pandas dataframe of details if set to False
        :return: Note details provided by Mintos
        """

        response = self.scraper.get(url=f'{ENDPOINTS.API_NOTES_DETAILS_URI}/{isin}/loans').json()

        if response is None:
            raise ValueError(f'Could not get details for Note with ID of {isin}.')

        response = list(map(lambda item: Utils.parse_mintos_items(item), response.get('items')))

        return response if raw else pd.DataFrame(response).set_index('identifier')

    def get_claim_details(self, claim_id: str) -> dict:
        """
        :param claim_id: ID of claim
        :return: Claim details provided by Mintos
        """

        response = self.scraper.get(url=f'{ENDPOINTS.API_CLAIMS_DETAILS_URI}/{claim_id}/summary').json()

        if response is None:
            raise ValueError(f'Could not get details for Claim with ID of {claim_id}.')

        return Utils.parse_mintos_items(response)

    def login(self) -> None:
        """
        Logs in to Mintos Marketplace via headless Chromium browser
        """

        self.driver.get(ENDPOINTS.LOGIN_URI)

        try:
            self._wait_for_element(
                tag='id',
                locator='login-username',
                timeout=10,
            ).send_keys(self.email)

        except TimeoutException:
            self._wait_for_element(tag='css selector', locator='h1[data-testid="page-title"]', timeout=5)

            raise MintosException("Mintos' system is currently being updated. Try again later.")

        self.driver.find_element(by='id', value='login-password').send_keys(self.password)

        self.driver.find_element(by='xpath', value='//button[@type="submit"]').click()

        try:
            iframe = self._wait_for_element(
                tag='xpath',
                locator='//iframe[@title="recaptcha challenge expires in two minutes"]',
                timeout=2,
            )

            self.solver.solve_recaptcha_v2_challenge(iframe=iframe)

        except TimeoutException:
            pass

        finally:
            try:
                error_message = self.driver.find_element(by='class name', value='account-login-error').text.strip()

                if error_message == 'Invalid username or password':
                    raise ValueError('Invalid username or password.')

            except selenium.common.exceptions.NoSuchElementException:
                pass

        if self.tfa_secret is None:
            try:
                # Wait for overview page to be displayed to mark the end of the login process
                self._wait_for_element(
                    tag='id',
                    locator='header-wrapper',
                    timeout=30,
                )

            except TimeoutException:
                raise MintosException('Your account could not be fetched - Check your internet connection.')

            return

        self._wait_for_element(
            tag='xpath',
            locator='//label[text()=" 6-digit code "]',
            timeout=20,
        )

        self._wait_for_element(
            tag='xpath',
            locator='//label[normalize-space()="6-digit code"]',
            timeout=20,
        )

        self._wait_for_element(
            tag='xpath',
            locator='//input[@type="text"]',
            timeout=5,
        ).send_keys(self._gen_totp())

        self.driver.find_element(
            by='xpath',
            value='//button[@type="submit"]',
        ).click()

        try:
            loc = '//iframe[@title="recaptcha challenge expires in two minutes"][@style="width: 400px; height: 580px;"]'

            iframe = self._wait_for_element(
                tag='xpath',
                locator=loc,
                timeout=2,
            )

            self.solver.solve_recaptcha_v2_challenge(iframe=iframe)

        except TimeoutException:
            pass

        finally:
            try:
                error_message = self.driver.find_element(by='class name', value='m-u-color-r4--text').text.strip()

                if error_message == 'Invalid Two-factor code':
                    raise ValueError('Invalid TFA secret.')

            except selenium.common.exceptions.NoSuchElementException:
                pass

            # Wait for overview page to be displayed to mark the end of the login process
            self._wait_for_element(
                tag='id',
                locator='header-wrapper',
                timeout=30,
            )

    def _save_cookies(self) -> None:
        try:
            self.cookies = self.driver.get_cookies()

        except AttributeError:
            self.cookies = self.scraper.cookies

        if not self.should_save or not self.email:
            return

        with open(f'{self.email}_cookies.pkl', 'wb') as f:
            pickle.dump(self.cookies, f)

    def _gen_totp(self) -> str:
        """
        :return: TOTP used for Mintos TFA
        """

        return pyotp.TOTP(self.tfa_secret).now()

    def _wait_for_element(
            self,
            tag: str,
            locator: str,
            timeout: int,
            multiple: bool = False,
    ) -> Union[WebElement, List[WebElement]]:
        """
        :param tag: Tag to get element by (id, class name, xpath, tag name, etc.)
        :param locator: Value of the tag (Example: tag -> id, locator -> button-id)
        :param timeout: Time to wait for element before raising TimeoutError
        :param multiple: Specify whether to return multiple web elements that match tag and locator
        :return: Web element specified by tag and locator
        :raises TimeoutException: If the element is not located within the desired time span
        """

        element_attributes = (tag, locator)

        WebDriverWait(self.driver, timeout).until(ec.visibility_of_element_located(element_attributes))

        if multiple:
            return self.driver.find_elements(by=tag, value=locator)

        return self.driver.find_element(by=tag, value=locator)

    def _get_csrf_token(self) -> str:
        content = self.scraper.get(ENDPOINTS.WEB_APP_URI).text

        parsed_content = BeautifulSoup(content, 'html.parser')

        # Extract CSRF token
        csrf_token = parsed_content.select('meta[data-hid="csrf-token"]')[0]['content']

        if not isinstance(csrf_token, str):
            raise ValueError('Failed to extract CSRF token.')

        return csrf_token

    def _js_click(self, element: WebElement) -> None:
        """
        :param element: Web element to perform click on via JavaScript
        """

        self.driver.execute_script('arguments[0].click();', element)

    @staticmethod
    def get_currencies() -> dict:
        return CONSTANTS.get_currencies()

    @staticmethod
    def get_countries() -> dict:
        return CONSTANTS.get_countries()

    @staticmethod
    def get_lending_companies() -> dict:
        return CONSTANTS.get_lending_companies()

    @staticmethod
    def _create_driver() -> webdriver.Chrome:
        options = webdriver.ChromeOptions()

        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")

        options.add_argument(f'--user-agent={CONSTANTS.USER_AGENT}')

        options.add_argument('--no-sandbox')
        options.add_argument("--disable-extensions")

        driver = webdriver.Chrome(options=options)

        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

        return driver

    @staticmethod
    def _cleanup(paths: set) -> None:
        for path in paths:
            if os.path.exists(path):
                os.remove(path)

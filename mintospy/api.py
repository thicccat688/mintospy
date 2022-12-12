from mintospy.constants import CONSTANTS
from mintospy.endpoints import ENDPOINTS
from mintospy.utils import Utils
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common import TimeoutException
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium_recaptcha_solver import API as RECAPTCHA_API
from typing import Union, List
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import warnings
import pickle
import pyotp
import time
import json
import os


class API:
    def __init__(
            self,
            email: str,
            password: str,
            tfa_secret: str = None
    ):
        """
        Mintos API wrapper with all relevant Mintos functionalities.
        :param email: Account's email
        :param password: Account's password
        :param tfa_secret: Base32 secret used for two-factor authentication
        (Only mandatory if account has two-factor authentication enabled)
        """

        if email is None:
            raise ValueError('Invalid email.')

        if password is None:
            raise ValueError('Invalid password.')

        if tfa_secret is None:
            warnings.warn('Using two-factor authentication with your Mintos account is highly recommended.')

        self.email = email
        self.__password = password
        self.__tfa_secret = tfa_secret

        # Initialise web driver session
        self.__driver = self._create_driver()

        # Intiailise RecaptchaV2 solver object
        self.__solver = RECAPTCHA_API(driver=self.__driver)

        # Automatically authenticate to Mintos API upon API object initialization
        self.login()

        # Extract CSRF token
        self.__csrf_token = self._wait_for_element(
            tag='css selector',
            locator='meta[data-hid="csrf-token"]',
            timeout=10,
        )

        print(self.__csrf_token)

        if isinstance(self.__csrf_token, str):
            raise ValueError('Failed to extract CSRF token.')

    def get_portfolio_data(self, currency: str) -> dict:
        """
        :param currency: Currency of portfolio to get data from (EUR, KZT, PLN, etc.)
        :return: Active loans, late loans, and loans in recovery/default
        """

        currency_iso_code = CONSTANTS.get_currency_iso(currency)

        data = self._make_request(
            url=f'{ENDPOINTS.API_PORTFOLIO_URI}',
            params={'currencyIsoCode': currency_iso_code},
            api=True,
        )

        return {k: float(v) for (k, v) in data.items()}

    def get_net_annual_return(self, currency: str) -> dict:
        """
        :param currency: Currency of portfolio to get net annual return from (EUR, KZT, PLN, etc.)
        :return: Currency ISO code, net annual return with and without campaign bonuses
        """

        currency_iso_code = CONSTANTS.get_currency_iso(currency)

        data = self._make_request(
            url=ENDPOINTS.API_OVERVIEW_NAR_URI,
            params={'currencyIsoCode': currency_iso_code},
            api=True,
        )

        # Parse dictionary data to correct data type and simpler format
        for k in data.copy():
            if isinstance(data[k], dict):
                data[k] = float(data[k][str(currency_iso_code)])  # type: ignore

        return Utils.parse_mintos_items(data)

    def get_currencies(self) -> any:
        """
        :return: Currencies currently accepted on Mintos' marketplace
        """

        data = self._make_request(
            url=ENDPOINTS.API_CURRENCIES_URI,
            api=True,
        )

        return data.get('items')

    def get_lending_companies(self) -> List[dict]:
        """
        :return: Lending companies currently listing loans on Mintos' marketplace
        """

        data = self._make_request(
            url=ENDPOINTS.API_LENDING_COMPANIES_URI,
            api=True,
        )

        return data

    def get_investments(
            self,
            currency: str,
            quantity: int = 30,
            start_page: int = 1,
            notes: bool = True,
            sort_field: str = 'initialAmount',
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
            max_risk_score: float = None,
            min_risk_score: float = None,
            strategies: List[str] = None,
            max_term: int = None,
            min_term: int = None,
            max_purchased_date: datetime = None,
            min_purchased_date: datetime = None,
            current: bool = True,
            include_manual_investments: bool = True,
            ascending_sort: bool = False,
            raw: bool = False,
    ) -> Union[pd.DataFrame, List[dict]]:
        """
        :param currency: Currency that investments are denominated in
        :param quantity: Quantity of investments to get
        :param start_page: Page to start getting investments from (Gets from first page by default)
        :param notes: Specify whether to get Notes or Claims (True -> Gets notes; False -> Gets claims)
        :param sort_field: Field to sort by (isin, mintosRiskScoreDecimal, lender, interestRate, maturityDate,
        createdAt, initialAmount, amount)
        :param countries: What countries notes should be issued from
        :param pending_payments: If payments for notes should be pending or not
        :param amortization_methods: Amortization type of notes (Full, partial, interest-only, or bullet)
        :param claim_id: ID of claim to filter by
        :param isin: ISIN of security to filter by
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
        :param include_manual_investments: Include notes that were purchased manually, instead of by auto invest
        :param ascending_sort: Sort notes in ascending order based on "sort" argument if True, otherwise sort descending
        :param raw: Return raw notes JSON if set to True, or returns pandas dataframe of notes if set to False
        :return: Pandas DataFrame or raw JSON of notes (Chosen in the "raw" argument), extra data, and pagination data
        """

        currency_iso_code = CONSTANTS.get_currency_iso(currency)

        max_results = 300

        investment_params = {
            'currency': currency_iso_code,
            'pagination': {
                'maxResults': max_results,
                'page': start_page,
            },
            'sorting': {
                'sortField': sort_field,
                'sortOrder': 'ASC' if ascending_sort else 'DESC',
            },
        }

        if notes:
            url = f'{ENDPOINTS.API_INVESTMENTS_URI}/{"current" if current else "finished"}'

        else:
            url = ENDPOINTS.API_CLAIMS_URI

            investment_params['status'] = 1 if current else 0

        if start_page < 1:
            raise ValueError('Start page must be superior or equal to 1.')

        if isin and claim_id:
            raise ValueError('You can only filter by ISIN or a Claim ID.')

        if isinstance(countries, list):
            investment_params['countries'] = []

            for country in countries:
                investment_params['countries'].append(CONSTANTS.get_country_iso(country))

        if isinstance(lending_companies, list):
            investment_params['lenderGroups'] = []

            for lender in lending_companies:
                investment_params['lenderGroups'].append(CONSTANTS.get_lending_company_id(lender))

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

        if isinstance(max_risk_score, float):
            if 1 < max_risk_score < 10:
                raise ValueError(
                    'Maximum risk score needs to be a number in between 1-10.',
                )

            investment_params['maxLendingCompanyRiskScore'] = max_risk_score

        if isinstance(min_risk_score, float):
            if 1 < min_risk_score < 10:
                raise ValueError(
                    'Minimum risk score needs to be a number in between 1-10.',
                )

            investment_params['minLendingCompanyRiskScore'] = min_risk_score

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
            if notes:
                investment_params['pending_payments_status'] = 1 if pending_payments else 0

            else:
                investment_params['hasPendingPayments'] = pending_payments

        if isinstance(listed_for_sale, bool):
            if notes:
                investment_params['listed_for_sale_status'] = 1 if listed_for_sale else 0

            else:
                investment_params['listedForSale'] = listed_for_sale

        if isinstance(lender_statuses, list):
            investment_params['lenderStatuses'] = []

            for status in lender_statuses:
                if status not in CONSTANTS.LENDING_COMPANY_STATUSES:
                    raise ValueError(
                        f'Lender status must be one of the following: {", ".join(CONSTANTS.LENDING_COMPANY_STATUSES)}',
                    )

                investment_params['lenderStatuses'].append(status)

        if isinstance(include_manual_investments, bool):
            if notes:
                investment_params['includeManualInvestments'] = include_manual_investments

            else:
                investment_params['include_manual_investments'] = 1 if include_manual_investments else 0

        if isinstance(max_interest_rate, float):
            investment_params['maxInterestRate'] = max_interest_rate

        if isinstance(min_interest_rate, int):
            investment_params['minInterestRate'] = min_interest_rate

        if isinstance(max_term, float):
            investment_params['termTo'] = max_term

        if isinstance(min_term, int):
            investment_params['termFrom'] = min_term

        if isinstance(max_purchased_date, datetime):
            investment_params['investmentDateTo'] = max_purchased_date.strftime('%d.%m.%Y')

        if isinstance(min_purchased_date, datetime):
            investment_params['investmentDateFrom'] = min_purchased_date.strftime('%d.%m.%Y')

        total_retrieved = 0

        request_headers = {
            'content-type': 'application/json',
            'anti-csrf-token': self.__csrf_token,
        }

        response = self._make_fetch(
            url=url,
            headers=request_headers,
            data=investment_params,
        )

        total_retrieved += max_results

        responses = [response]

        while total_retrieved < quantity:
            if not response['pagination']['hasNextPage']:
                break

            investment_params['pagination']['page'] += 1

            next_response = self._make_fetch(
                url=url,
                headers=request_headers,
                data=investment_params,
            )

            responses.append(next_response)

            total_retrieved += 300

        items = []

        for resp in responses:
            print(resp)

            if notes:
                items.extend(resp['items'])

            else:
                items.extend(resp['data'])

        if raw or len(items) == 0:
            return items

        row_index = 'ISIN' if notes else 'id'

        return pd.DataFrame.from_records(Utils.parse_investments(items)).set_index(row_index).fillna('N/A')

    def get_loans(self, raw: bool = False) -> List[dict]:
        pass

    def login(self) -> None:
        """
        Logs in to Mintos Marketplace via headless Chromium browser
        """

        self.__driver.get(ENDPOINTS.LOGIN_URI)

        # Import cookies to web driver with the required validations and stop login process if they're valid
        valid_import = Utils.import_cookies(driver=self.__driver, file_path='cookies.pkl')

        # If cookies imported are valid, skip the rest of the authentication process
        if valid_import:
            time.sleep(2)

            return

        self._wait_for_element(
            tag='id',
            locator='login-username',
            timeout=5,
        ).send_keys(self.email)

        self.__driver.find_element(by='id', value='login-password').send_keys(self.__password)

        self.__driver.find_element(by='xpath', value='//button[@type="submit"]').click()

        if self.__tfa_secret is None:
            # Wait for overview page to be displayed to mark the end of the login process
            self._wait_for_element(
                tag='id',
                locator='header-wrapper',
                timeout=20,
            )

            # Wait 1 second before any further action to avoid Access Denied by Cloudflare
            time.sleep(1)

        try:
            iframe = self._wait_for_element(
                tag='xpath',
                locator='//iframe[@title="recaptcha challenge expires in two minutes"]',
                timeout=2,
            )

            self.__solver.solve_recaptcha_v2_challenge(iframe=iframe)

        except TimeoutException:
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

        self.__driver.find_element(
            by='xpath',
            value='//button[@type="submit"]',
        ).click()

        try:
            iframe = self._wait_for_element(
                tag='xpath',
                locator='//iframe[@title="recaptcha challenge expires in two minutes"][@style="width: 400px; height: 580px;"]',
                timeout=2,
            )

            self.__solver.solve_recaptcha_v2_challenge(iframe=iframe)

        except TimeoutException:
            # Wait for overview page to be displayed to mark the end of the login process
            self._wait_for_element(
                tag='id',
                locator='header-wrapper',
                timeout=20,
            )

        # Wait 1 second before any further action to avoid Access Denied by Cloudflare
        time.sleep(1)

        with open('cookies.pkl', 'wb') as f:
            pickle.dump(self.__driver.get_cookies(), f)

    def quit(self) -> None:
        with open('cookies.pkl', 'wb') as f:
            pickle.dump(self.__driver.get_cookies(), f)

        self.__driver.quit()

    def _gen_totp(self) -> str:
        """
        :return: TOTP used for Mintos TFA
        """

        return pyotp.TOTP(self.__tfa_secret).now()

    def _make_fetch(
            self,
            url: str,
            headers: dict = None,
            params: Union[dict, List[tuple]] = None,
            data: dict = None,
    ):
        """
        Request handler that makes fetch requests directly in the webdriver's console
        :param url: URL of endpoint to call
        :param headers: Headers to send in the HTTP request
        :param params: Query parameters to send in HTTP request (Send as list of tuples for duplicate query strings)
        :return: HTML response from HTTP request
        """

        url = Utils.mount_url(url, params)

        fetch_script = f'''
        var response = await fetch("{url}", {{
            'method': 'POST',
            'credentials': 'include',
            'headers': {json.dumps(headers)},
            'body': JSON.stringify({json.dumps(data)}),
        }})
        
        return await response.json()
        '''

        return self.__driver.execute_script(fetch_script)

    def _make_request(
            self,
            url: str,
            params: Union[dict, List[tuple]] = None,
            api: bool = False,
    ) -> any:
        """
        Request handler with built-in exception handling for Mintos' API
        :param url: URL of endpoint to call
        :param params: Query parameters to send in HTTP request (Send as list of tuples for duplicate query strings)
        :param api: Specify if request is made directly to Mintos' API or via front-end
        :return: HTML response from HTTP request
        """

        url = Utils.mount_url(url, params)

        self.__driver.get(url)

        if api:
            return Utils.parse_api_response(self.__driver.page_source)

        return BeautifulSoup(self.__driver.page_source, 'html.parser')

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

        WebDriverWait(self.__driver, timeout).until(ec.visibility_of_element_located(element_attributes))

        if multiple:
            return self.__driver.find_elements(by=tag, value=locator)

        return self.__driver.find_element(by=tag, value=locator)

    def _js_click(self, element: WebElement) -> None:
        """
        :param element: Web element to perform click on via JavaScript
        """

        self.__driver.execute_script('arguments[0].click();', element)

    @staticmethod
    def _create_driver() -> WebDriver:
        options = webdriver.ChromeOptions()
        service = Service(ChromeDriverManager().install())

        options.add_experimental_option('detach', True)

        # options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")

        options.add_argument('--start-maximized')
        options.add_argument('--disable-gpu')

        options.add_argument('--no-sandbox')
        options.add_argument("--disable-extensions")

        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        return webdriver.Chrome(options=options, service=service)

    @staticmethod
    def _cleanup(paths: set) -> None:
        for path in paths:
            if os.path.exists(path):
                os.remove(path)


if __name__ == '__main__':
    t1 = time.time()

    mintos_api = API(
        email=os.getenv(key='email'),
        password=os.getenv(key='password'),
        tfa_secret=os.getenv(key='tfa_secret'),
    )

    print(time.time() - t1)

    # print(mintos_api.get_portfolio_data(currency='EUR'))

    # print(mintos_api.get_net_annual_return(currency='EUR'))

    # print(mintos_api.get_lending_companies())

    # print(mintos_api.get_currencies())

    t1 = time.time()

    investments = mintos_api.get_investments(currency='KZT', quantity=200, notes=False, current=True)

    print(investments)

    print('investments fetching duration --->', time.time() - t1)

    mintos_api.quit()

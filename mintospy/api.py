from mintospy.constants import CONSTANTS
from mintospy.endpoints import ENDPOINTS
from mintospy.exceptions import MintosException, RecaptchaException, NetworkException
from mintospy.utils import Utils
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.remote.webelement import WebElement
from selenium.common import TimeoutException
from seleniumrequests import Chrome
from webdriver_manager.chrome import ChromeDriverManager
from pydub import AudioSegment
from typing import Union, List
from datetime import datetime
from requests import Response
import speech_recognition as sr
import pandas as pd
import requests
import tempfile
import warnings
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

        try:
            # Initialise web driver session
            self.__driver = self._create_driver()

        except WebDriverException:
            warnings.warn('You do not have a chromedriver executable in your PATH. Installing it for you.')

        # Get anti-CSRF token
        self.__csrf_token = self._get_csrf_token()

        # Automatically authenticate to Mintos API upon API object initialization
        self.login()

    def get_portfolio_data(self, currency: str) -> dict:
        """
        :param: currency: Currency of portfolio to get data from (EUR, KZT, PLN, etc.)
        :return: Active loans, late loans, and loans in recovery/default
        """

        currency_iso_code = CONSTANTS.get_currency_iso(currency)

        data = self._make_request(
            url=f'{ENDPOINTS.API_PORTFOLIO_URI}',
            method='GET',
            params={'currencyIsoCode': currency_iso_code},
        ).json()

        return {k: float(v) for (k, v) in data.items()}

    def get_net_annual_return(self, currency: str) -> dict:
        """
        :param: currency: Currency of portfolio to get net annual return from (EUR, KZT, PLN, etc.)
        :return: Currency ISO code, net annual return with and without campaign bonuses
        """

        currency_iso_code = CONSTANTS.get_currency_iso(currency)

        data = self._make_request(
            url=ENDPOINTS.API_OVERVIEW_NAR_URI,
            method='GET',
            params={'currencyIsoCode': currency_iso_code},
        ).json()

        # Parse dictionary data to correct data type and simpler format
        for k in data.copy():
            if isinstance(data[k], dict):
                data[k] = float(data[k][str(currency_iso_code)])

        return Utils.parse_mintos_items(data)

    def get_currencies(self) -> List[dict]:
        """
        :return: Currencies currently accepted on Mintos' marketplace
        """

        data = self._make_request(
            url=ENDPOINTS.API_CURRENCIES_URI,
            method='GET',
        ).json()

        return data['items']

    def get_lending_companies(self) -> List[dict]:
        """
        :return: Lending companies currently listing loans on Mintos' marketplace
        """

        data = self._make_request(
            url=ENDPOINTS.API_LENDING_COMPANIES_URI,
            method='GET',
        ).json()

        return data

    def get_distribution(
            self,
            currency: str,
            quantity: int = 30,
            sort: str = 'interestRate',
            countries: List[str] = None,
            pending_payments: bool = None,
            include_manual_investments: bool = None,
            start_date: datetime = None,
            end_date: datetime = None,
            isin: str = None,
            late_loan_exposure: List[str] = None,
            lender_companies: List[str] = None,
            lender_groups: List[str] = None,
            lender_statuses: List[str] = None,
            listed_for_sale: bool = None,
            max_interest_rate: float = None,
            max_lending_company_risk_score: float = None,
            min_amount: float = None,
            min_interest_rate: float = None,
            min_lending_company_risk_score: float = None,
            pledge_type_groups: List[str] = None,
            risk_scores: List[int] = None,
            schedule_types: List[str] = None,
            strategies: List[str] = None,
            term_from: int = None,
            term_to: int = None,
            current: bool = True,
            include_extra_data: bool = True,
            ascending_sort: bool = False,
            raw: bool = False,
    ):
        pass

    def get_investments(
            self,
            currency: str,
            quantity: int = 30,
            sort: str = 'interestRate',
            countries: List[str] = None,
            pending_payments: bool = None,
            include_manual_investments: bool = None,
            start_date: datetime = None,
            end_date: datetime = None,
            isin: str = None,
            late_loan_exposure: List[str] = None,
            lender_companies: List[str] = None,
            lender_groups: List[str] = None,
            lender_statuses: List[str] = None,
            listed_for_sale: bool = None,
            max_interest_rate: float = None,
            max_lending_company_risk_score: float = None,
            min_amount: float = None,
            min_interest_rate: float = None,
            min_lending_company_risk_score: float = None,
            pledge_type_groups: List[str] = None,
            risk_scores: List[int] = None,
            schedule_types: List[str] = None,
            strategies: List[str] = None,
            term_from: int = None,
            term_to: int = None,
            current: bool = True,
            include_extra_data: bool = True,
            ascending_sort: bool = False,
            raw: bool = False,
    ) -> Union[pd.DataFrame, List[dict]]:
        """
        :param currency:
        :param quantity:
        :param sort:
        :param countries:
        :param pending_payments:
        :param include_manual_investments:
        :param start_date:
        :param end_date:
        :param isin:
        :param late_loan_exposure:
        :param lender_companies:
        :param lender_groups:
        :param lender_statuses:
        :param listed_for_sale:
        :param max_interest_rate:
        :param max_lending_company_risk_score:
        :param min_amount:
        :param min_interest_rate:
        :param min_lending_company_risk_score:
        :param pledge_type_groups:
        :param risk_scores:
        :param schedule_types:
        :param strategies:
        :param term_from:
        :param term_to:
        :param current:
        :param include_extra_data:
        :param ascending_sort:
        :param raw:
        :return:
        """

        currency_iso_code = CONSTANTS.get_currency_iso(currency)

        investment_data = {
            'countries': countries,
            'currency': currency_iso_code,
            'hasPendingPayments': pending_payments,
            'includeManualInvestments': include_manual_investments,
            'investmentDateFrom': start_date,
            'investmentDateTo': end_date,
            'isin': isin,
            'lateLoanExposure': late_loan_exposure,
            'lenderCompanies': lender_companies,
            'lenderGroups': lender_groups,
            'lenderStatuses': lender_statuses,
            'listedForSale': listed_for_sale,
            'maxInterestRate': max_interest_rate,
            'maxLendingCompanyRiskScore': max_lending_company_risk_score,
            'minAmount': min_amount,
            'minInterestRate': min_interest_rate,
            'minLendingCompanyRiskScore': min_lending_company_risk_score,
            'pagination': {
                'maxResults': quantity,
                'page': 1,
            },
            'pledgeTypeGroups': pledge_type_groups,
            'riskScores': risk_scores,
            'scheduleTypes': schedule_types,
            'sorting': {
                'sortField': sort,
                'sortOrder': 'ASC' if ascending_sort else 'DESC',
            },
            'strategies': strategies,
            'termFrom': term_from,
            'termTo': term_to,
        }

        if countries is not None:
            investment_data['countries'] = list(map(lambda cnt: CONSTANTS.get_country_iso(cnt), countries))

        data = self._make_request(                           
            url=ENDPOINTS.API_CURRENT_INVESTMENTS_URI if current else ENDPOINTS.API_FINISHED_INVESTMENTS_URI,
            method='POST',
            data=investment_data,
        ).json()

        parsed_data = Utils.parse_mintos_items(data)

        del parsed_data['pagination']

        if not include_extra_data:
            del parsed_data['extraData']

        return data if raw else {
            'loans': pd.DataFrame(parsed_data.get('items')),
            'extra_data': parsed_data.get('extraData'),
        }

    def get_loans(self, raw: bool = False) -> List[dict]:
        pass

    def login(self) -> None:
        """
        Logs in to Mintos Marketplace via headless Chromium browser
        """

        self.__driver.get(ENDPOINTS.LOGIN_URI)

        self._wait_for_element(
            tag='id',
            locator='login-username',
            timeout=5,
        ).send_keys(self.email)

        self.__driver.find_element(by='id', value='login-password').send_keys(self.__password)

        self.__driver.find_element(by='xpath', value='//button[@type="submit"]').click()

        if self.__tfa_secret is None:
            return

        try:
            self._wait_for_element(
                tag='xpath',
                locator='//label[text()=" 6-digit code "]',
                timeout=5,
            )

        except TimeoutException:
            self._resolve_captcha()

        self._wait_for_element(
            tag='xpath',
            locator='//label[text()=" 6-digit code "]',
            timeout=5
        )

        self._wait_for_element(
            tag='xpath',
            locator='//input[@type="text"]',
            timeout=5
        ).send_keys(self._gen_totp())

        self.__driver.find_element(
            by='xpath',
            value='//button[@type="submit"]',
        ).click()

        try:
            # Wait for overview page to be displayed to mark the end of the login process
            self._wait_for_element(
                tag='id',
                locator='header-wrapper',
                timeout=10,
            )

        except TimeoutException:
            try:
                self._resolve_captcha()

            except RecaptchaException:
                raise TimeoutException('CAPTCHA did not respond on time.')

    def logout(self) -> None:
        self._make_request(url=ENDPOINTS.API_LOGOUT_URI, method='GET')

    def _gen_totp(self) -> str:
        """
        :return: TOTP used for Mintos TFA
        """

        return pyotp.TOTP(self.__tfa_secret).now()

    def _resolve_captcha(self) -> None:
        """
        Resolve Captcha by trying to find iframe with challenge 
        """

        self.__driver.switch_to.default_content()

        iframe = self._wait_for_element(
            tag='xpath',
            locator='//iframe[@title="recaptcha challenge expires in two minutes"]',
            timeout=5,
        )

        self.__driver.switch_to.frame(iframe)

        # Locate captcha audio button and click it via JavaScript
        audio_button = self._wait_for_element(
            tag='id',
            locator='recaptcha-audio-button',
            timeout=5,
        )

        self._js_click(audio_button)

        # Locate audio challenge download link
        download_link = self._wait_for_element(
            tag='class name',
            locator='rc-audiochallenge-tdownload-link',
            timeout=5,
        )

        tmp_dir = tempfile.gettempdir()

        mp3_file, wav_file = os.path.join(tmp_dir, 'tmp.mp3'), os.path.join(tmp_dir, 'tmp.wav')

        tmp_files = {mp3_file, wav_file}

        with open(mp3_file, 'wb') as f:
            link = download_link.get_attribute('href')

            audio_download = requests.get(url=link, allow_redirects=True)

            f.write(audio_download.content)

            f.close()

        AudioSegment.from_mp3(mp3_file).export(wav_file, format='wav')

        recognizer = sr.Recognizer()

        with sr.AudioFile(wav_file) as source:
            audio = recognizer.listen(source)

            recognized_text = recognizer.recognize_google(audio)

        self._cleanup(tmp_files)

        self.__driver.find_element(by='id', value='audio-response').send_keys(recognized_text)

        self.__driver.find_element(
            by='id',
            value='recaptcha-verify-button',
        ).click()

        self.__driver.switch_to.default_content()

    def _get_csrf_token(self) -> str:
        self.__driver.get(ENDPOINTS.WEB_APP_URI)

        csrf_token = self.__driver.find_element(
            by='xpath',
            value='//meta[@name="csrf-token"]',
        ).get_attribute(name='content')

        return csrf_token

    def _make_request(
            self,
            url: str,
            method: str = 'GET',
            headers: dict = None,
            params: dict = None,
            data: dict = None,
    ) -> Response:
        """
        Request handler with built-in exception handling for Mintos' API
        :param url: URL of endpoint to call
        :param method: HTTP method to be used (POST, GET, PUT, DELETE, etc.)
        :param params: Query parameters to send in HTTP request
        :param data: Payload to send in HTTP request
        :return: Response object from requests library
        """

        if data is not None:
            data = json.dumps(data)

        headers = {
            'anti-csrf-token': self.__csrf_token,  # Set anti-CSRF token on every request because RequestsMixin for
            # Selenium doesn't persist extra headers
            **self.__driver.requests_session.headers,  # Add existing session headers
            **headers,  # Add extra headers below as to take priority over previous headers
        }

        response = self.__driver.request(
            url=url,
            method=method,
            headers=headers,
            params=params,
            json=data,
        )

        json_data = response.json()

        if response.status_code >= 400:
            raise MintosException(json_data['errors'][0]['message'])

        return response

    def _wait_for_element(self, tag: str, locator: str, timeout: int) -> WebElement:
        """
        :param: tag: Tag to get element by (id, class name, xpath, tag name, etc.)
        :param: locator: Value of the tag (Example: tag -> id, locator -> button-id)
        :param: timeout: Time to wait for element before raising TimeoutError
        :return: Web element specified by tag and locator
        """

        element_attributes = (tag, locator)

        WebDriverWait(self.__driver, timeout).until(ec.visibility_of_element_located(element_attributes))

        return self.__driver.find_element(by=tag, value=locator)

    def _js_click(self, element: WebElement) -> None:
        """
        :param element: Web element to perform click on via JavaScript
        """

        self.__driver.execute_script('arguments[0].click();', element)

    @staticmethod
    def _create_driver() -> Chrome:
        options, service = webdriver.ChromeOptions(), Service(ChromeDriverManager().install())

        # options.headless = True

        options.add_experimental_option('detach', True)

        options.add_argument('start-maximized')

        return Chrome(options=options, service=service)

    @staticmethod
    def _cleanup(paths: set) -> None:
        for path in paths:
            if os.path.exists(path):
                os.remove(path)


if __name__ == '__main__':
    t1 = time.time()

    try:
        mintos_api = API(
            email=os.getenv(key='email'),
            password=os.getenv(key='password'),
            tfa_secret=os.getenv(key='tfa_secret'),
        )

    except TimeoutException:
        raise NetworkException('Check your internet connection.')

    print(time.time() - t1)

    print(mintos_api.get_portfolio_data(currency='EUR'))

    print(mintos_api.get_net_annual_return(currency='EUR'))

    print(mintos_api.get_lending_companies())

    print(mintos_api.get_currencies())

    print(mintos_api.get_investments(currency='EUR'))

    mintos_api.logout()

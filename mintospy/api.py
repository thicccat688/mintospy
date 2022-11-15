from mintospy.constants import CONSTANTS
from mintospy.endpoints import ENDPOINTS
from mintospy.exceptions import RecaptchaException, NetworkException
from mintospy.utils import Utils
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from pydub import AudioSegment
from typing import Union, List
from datetime import datetime, date
from bs4 import BeautifulSoup
import speech_recognition as sr
import pandas as pd
import requests
import tempfile
import warnings
import pyotp
import time
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

        # Automatically authenticate to Mintos API upon API object initialization
        self.login()

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

        print(self.__driver.page_source, data)

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
            sort: str = 'interestRate',
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
            risk_scores: List[int] = None,
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
        :param currency: Currency that notes are denominated in
        :param quantity: Quantity of notes to get
        :param sort: What to sort notes by
        :param countries: What countries notes should be issued in
        :param pending_payments: If payments for notes should be pending or not
        :param amortization_methods: Amortization type of notes (Full, partial, interest-only, or bullet)
        :param isin: ISIN of security
        :param late_loan_exposure: Late loan exposure of notes (0_20 for 0-20%, 20_40 for 20-40%, and so on)
        :param lending_companies: Only return notes issued by specified lending companies
        :param lender_statuses: Only return notes from lenders in a certain state (Active, suspended, or in default)
        :param listed_for_sale: Specify whether to return notes that are on sale in the secondary market or not
        :param max_interest_rate: Only return notes up to this maximum interest rate
        :param min_interest_rate: Only return notes up to this minimum interest rate
        :param loan_types: Only return notes composed of certain loan types
        (agricultural, business, car, invoice_financing, mortgage, pawnbroking, personal, short_term)
        :param risk_scores: Only returns notes of a certain risk score (1-10 or "SW" for notes with suspended rating)
        :param strategies: Only return notes that were invested in with certain strategies
        :param max_term: Only return notes up to a maximum term
        :param min_term: Only return notes up to a minimum term
        :param max_purchased_date: Only returns notes purchased before date
        :param min_purchased_date: Only returns notes purchased after date
        :param current: Returns current notes in portfolio if set to true, otherwise returns finished investments
        :param include_manual_investments: Include notes that were purchased manually, instead of by auto invest
        :param ascending_sort: Sort notes in ascending order based on "sort" argument if True, otherwise sort descending
        :param raw: Return raw notes JSON if set to True, or returns pandas dataframe of notes if set to False
        :return: Pandas DataFrame or raw JSON of notes (Chosen in the "raw" argument)
        """

        currency_iso_code = CONSTANTS.get_currency_iso(currency)

        investment_params = [
            ('currencies[]', currency_iso_code),
            ('sort_order', 'ASC' if ascending_sort else 'DESC'),
            ('max_results', 300),
            ('page', 1),
        ]

        if isinstance(countries, list):
            for country in countries:
                new_country = ('countries[]', CONSTANTS.get_country_iso(country))

                investment_params.append(new_country)

            for lender in lending_companies:
                new_lender = ('lender_groups[]', CONSTANTS.get_lending_company_id(lender))

                investment_params.append(new_lender)

        if isinstance(loan_types, list):
            for type_ in loan_types:
                if type_ not in CONSTANTS.LOAN_TYPES:
                    raise ValueError(f'Loan type must be one of the following: {", ".join(CONSTANTS.LOAN_TYPES)}')

                new_type = ('pledges[]', type_)

                investment_params.append(new_type)

        if isinstance(amortization_methods, list):
            for method in amortization_methods:
                new_method = ('schedule_types[]', CONSTANTS.get_amoritzation_method_id(method))

                investment_params.append(new_method)

        if isinstance(risk_scores, list):
            for score in risk_scores:
                if not isinstance(score, int) or score == 'SW':
                    raise ValueError(
                        'Risk score needs to be an integer between 1-10 or "SW" (When risk score is suspended).',
                    )

                if 1 > score > 10:
                    raise ValueError(
                        'Risk score can only be a number in between 1-10 or "SW" (When risk score is suspended).',
                    )

                new_score = ('mintos_scores[]', score)

                investment_params.append(new_score)

        if isinstance(isin, str):
            if len(isin) != 12:
                raise ValueError('ISIN must be 12 characters long.')

            new_isin = ('isin', isin)

            investment_params.append(new_isin)

        if isinstance(late_loan_exposure, list):
            for exposure in late_loan_exposure:
                if exposure not in CONSTANTS.LATE_LOAN_EXPOSURES:
                    raise ValueError(
                        f'Late loan exposure must be one of the following: {", ".join(CONSTANTS.LATE_LOAN_EXPOSURES)}',
                    )

                new_exposure = ('late_loan_exposure[]', exposure)

                investment_params.append(new_exposure)

        if isinstance(pending_payments, bool):
            new_pending_status = ('pending_payments_status[]', 1 if pending_payments else 0)

            investment_params.append(new_pending_status)

        if isinstance(listed_for_sale, bool):
            new_sale_status = ('listed[]', 1 if listed_for_sale else 0)

            investment_params.append(new_sale_status)

        if isinstance(lender_statuses, list):
            for status in lender_statuses:
                if status not in CONSTANTS.LENDING_COMPANY_STATUSES:
                    raise ValueError(
                        f'Lender status must be one of the following: {", ".join(CONSTANTS.LENDING_COMPANY_STATUSES)}',
                    )

                new_company_status = ('company_status[]', status)

                investment_params.append(new_company_status)

        if isinstance(sort, str):
            new_sort = ('sort_field', sort)

            investment_params.append(new_sort)

        if isinstance(include_manual_investments, bool):
            new_include_manual_investements = ('include_manual_investments', include_manual_investments)

            investment_params.append(new_include_manual_investements)

        if isinstance(max_interest_rate, float):
            new_max_interest_rate = ('max_interest', max_interest_rate)

            investment_params.append(new_max_interest_rate)

        if isinstance(max_term, float):
            new_max_term = ('max_term', max_term)

            investment_params.append(new_max_term)

        if isinstance(min_interest_rate, int):
            new_min_interest_rate = ('min_interest', min_interest_rate)

            investment_params.append(new_min_interest_rate)

        if isinstance(min_term, int):
            new_min_term = ('min_term', min_term)

            investment_params.append(new_min_term)

        if isinstance(max_purchased_date, datetime):
            new_max_purchased_date = ('date_to', max_purchased_date.strftime('%d.%m.%Y'))

            investment_params.append(new_max_purchased_date)

        if isinstance(min_purchased_date, datetime):
            new_min_purchased_date = ('date_from', min_purchased_date.strftime('%d.%m.%Y'))

            investment_params.append(new_min_purchased_date)

        self._make_request(
            url=f'{ENDPOINTS.INVESTMENTS_URI}/{"current" if current else "finished"}',
            params=investment_params,
        )

        securities = self._wait_for_element(
            tag='xpath',
            locator='//div[@data-testid="note-series-item"]',
            timeout=10,
            multiple=True,
        )

        if raw:
            securities_data = []

        else:
            securities_data = pd.DataFrame()

        total_notes = int(
            self._wait_for_element(
                tag='class name',
                locator='m-u-fs-4',
                timeout=5,
            ).text.split(' Sets')[0]
        )

        for i in range(quantity):
            if i >= total_notes - 1:
                break

            security = securities[i]

            isin = security.find_element(
                by='xpath',
                value='//a[@data-testid="note-isin"]',
            )

            loan_type = security.find_element(
                by='xpath',
                value='//a[@data-testid="note-isin"]/following-sibling::div[1]',
            )

            risk_score = security.find_element(by='class name', value='score-value')

            country = security.find_element(
                by='xpath',
                value='(//*[name()="svg"]/*[name()="title"])[1]',
            )

            lenders = security.find_elements(
                by='xpath',
                value='//span[@class="mw-u-o-hidden m-u-to-ellipsis mw-u-width-full"]',
            )

            interest_rate = security.find_element(
                by='xpath',
                value='//span[normalize-space()="Interest rate"]/../span[2]',
            )

            purchase_date = security.find_element(
                by='xpath',
                value='//span[normalize-space()="Purchase date"]/../span[2]/div/span',
            )

            invested_amount = security.find_element(
                by='xpath',
                value='//span[normalize-space()="Invested amount"]/../span[2]/div/span',
            )

            received_payments = security.find_element(
                by='xpath',
                value='//span[normalize-space()="Received payments"]/../span[2]/div/span',
            )

            pending_payments, in_recovery = security.find_elements(
                by='class name',
                value='m-u-nowrap',
            )

            currency = Utils.parse_currency_number(invested_amount.text)['currency']

            parsed_security = {
                'isin': isin.text.strip(),
                'type': loan_type.text.strip(),
                'risk_score': int(risk_score.text.strip()),
                'lending_company': lenders[0].text.strip(),
                'legal_entity': lenders[1].text.strip(),
                'country': Utils.get_svg_title(country),
                'interest_rate': float(interest_rate.text.strip().replace('%', '')),
                'purchase_date': Utils.str_to_date(purchase_date.text),
                'invested_amount': Utils.parse_currency_number(invested_amount.text)['amount'],
                'received_payments': Utils.parse_currency_number(received_payments.text)['amount'],
                'pending_payments': Utils.parse_currency_number(pending_payments.text)['amount'],
                'in_recovery': Utils.parse_currency_number(in_recovery.text)['amount'],
                'currency': currency,
            }

            if current:
                remaining_term = security.find_element(
                    by='xpath',
                    value='//span[normalize-space()="Remaining term"]/../span[2]',
                )

                outstanding_principal = security.find_element(
                    by='xpath',
                    value='//span[normalize-space()="Outstanding Principal"]/../span[2]/div/span',
                )

                next_payment_date, next_payment_amount = security.find_elements(
                    by='class name',
                    value='date-value',
                )

                current_fields = {
                    'remaining_term': remaining_term.text.strip(),
                    'outstanding_principal': Utils.parse_currency_number(outstanding_principal.text)['amount'],
                    'next_payment_date': Utils.str_to_date(next_payment_date.text),
                    'next_payment_amount': Utils.parse_currency_number(next_payment_amount.text)['amount'],
                }

                parsed_security.update(current_fields)

            else:
                finished_date = security.find_element(
                    by='xpath',
                    value='//span[text()=" Finished "]/following-sibling::span[1]',
                )

                finished_fields = {
                    'finished_date': datetime.strptime(finished_date.text.strip().replace('.', ''), '%d%m%Y').date(),
                }

                parsed_security.update(finished_fields)

            if raw:
                securities_data.append(parsed_security)

                continue

            securities_data.append(parsed_security, ignore_index=True)

        return securities_data

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
            # Wait for overview page to be displayed to mark the end of the login process
            self._wait_for_element(
                tag='id',
                locator='header-wrapper',
                timeout=15,
            )

            # Wait 2 seconds before any further action to avoid Access Denied by Cloudflare
            time.sleep(2)

        try:
            iframe = self._wait_for_element(
                tag='xpath',
                locator='//iframe[@title="recaptcha challenge expires in two minutes"]',
                timeout=3,
            )

            self._resolve_captcha(iframe=iframe)

        except TimeoutException:
            self._wait_for_element(
                tag='xpath',
                locator='//label[text()=" 6-digit code "]',
                timeout=10,
            )

        self._wait_for_element(
            tag='xpath',
            locator='//label[text()=" 6-digit code "]',
            timeout=10,
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
                timeout=3,
            )

            self._resolve_captcha(iframe=iframe)

        except TimeoutException:
            # Wait for overview page to be displayed to mark the end of the login process
            self._wait_for_element(
                tag='id',
                locator='header-wrapper',
                timeout=15,
            )

        # Wait 2 seconds before any further action to avoid Access Denied by Cloudflare
        time.sleep(2)

    def logout(self) -> None:
        self._make_request(url=ENDPOINTS.API_LOGOUT_URI)

        self.__driver.quit()

    def _gen_totp(self) -> str:
        """
        :return: TOTP used for Mintos TFA
        """

        return pyotp.TOTP(self.__tfa_secret).now()

    def _resolve_captcha(self, iframe: WebElement) -> None:
        """
        Resolve Captcha by trying to find iframe with challenge
        :param iframe: Iframe of Captcha
        """

        self.__driver.switch_to.frame(iframe)

        # Locate captcha audio button and click it via JavaScript
        audio_button = self._wait_for_element(
            tag='id',
            locator='recaptcha-audio-button',
            timeout=10,
        )

        self._js_click(audio_button)

        # Locate audio challenge download link
        download_link = self._wait_for_element(
            tag='class name',
            locator='rc-audiochallenge-tdownload-link',
            timeout=10,
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

        # Disable dynamic energy thershold to avoid failed Captcha audio transcription
        recognizer.dynamic_energy_threshold = False

        with sr.AudioFile(wav_file) as source:
            audio = recognizer.listen(source)

            try:
                recognized_text = recognizer.recognize_google(audio)

            except sr.UnknownValueError:
                raise RecaptchaException('Failed to automatically solve Captcha, try again.')

        self._cleanup(tmp_files)

        self.__driver.find_element(by='id', value='audio-response').send_keys(recognized_text)

        verify_button = self._wait_for_element(
            tag='id',
            locator='recaptcha-verify-button',
            timeout=5,
        )

        self._js_click(verify_button)

        self.__driver.switch_to.default_content()

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

        url = Utils.mount_url(url=url, params=params)

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
        options, service = webdriver.ChromeOptions(), Service(ChromeDriverManager().install())

        # options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")

        options.add_argument('--start-maximized')
        options.add_argument('--disable-gpu')

        options.add_argument('--no-sandbox')
        options.add_argument("--disable-extensions")

        options.add_argument('disable-infobars')

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

    print(mintos_api.get_investments(currency='EUR'))

    mintos_api.logout()

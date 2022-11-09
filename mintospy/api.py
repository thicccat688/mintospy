from mintospy.constants import CONSTANTS
from mintospy.endpoints import ENDPOINTS
from mintospy.exceptions import RecaptchaException, NetworkException
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

        self.email = email
        self.__password = password
        self.__tfa_secret = tfa_secret

        if tfa_secret is None:
            warnings.warn('Using two-factor authentication with your Mintos account is highly recommended.')

        try:
            # Initialise web driver session
            self.__driver = self._create_driver()

        except WebDriverException:
            warnings.warn('You do not have a chromedriver executable in your PATH. Installing it for you.')

        # Automatically authenticate to Mintos API upon API object initialization
        self.login()

    def get_portfolio_data(self, currency: str) -> dict:
        """
        :param: currency: Currency of portfolio to get data from (EUR, KZT, PLN, etc.)
        :return: Active loans, late loans, and loans in recovery/default
        """

        currency_iso_code = self._get_currency_iso(currency)

        data = self.__driver.request(
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

        currency_iso_code = self._get_currency_iso(currency)

        data = self.__driver.request(
            url=ENDPOINTS.API_OVERVIEW_NAR_URI,
            method='GET',
            params={'currencyIsoCode': currency_iso_code},
        ).json()

        # Parse dictionary data to correct data type and simpler format
        for k in data.copy():
            if isinstance(data[k], dict):
                data[k] = float(data[k][str(currency_iso_code)])

        return data

    def get_investments(
            self,
            currency: str,
            sort: str = 'interestRate',
            countries: List[str] = None,
            current: bool = True,
            ascending_sort: bool = False,
            raw: bool = False,
    ) -> Union[pd.DataFrame, List[dict]]:
        currency_iso_code = self._get_currency_iso(currency)

        investment_data = {
            'countries': countries,
            'currency': currency_iso_code,
            'pagination': {
                'maxResults': 30,
                'page': 1,
            },
            'sorting': {
                'sortField': sort,
                'sortOrder': 'ASC' if ascending_sort else 'DESC',
            }
        }

        if countries is not None:
            investment_data['countries'] = list(map(lambda cnt: self._get_country_iso(cnt), countries))

        data = self.__driver.request(                           
            url=ENDPOINTS.API_INVESTMENTS_URI,
            method='POST',
            data=investment_data,
        ).json()

        return Utils.obj_str_to_digits(data['items']) if raw else pd.DataFrame(data['items'])

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

        self.__driver.find_element(
            by='xpath',
            value='//input[@type="text"]',
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
                raise TimeoutError('Captcha did not respond on time.')

    def logout(self) -> None:
        self.__driver.request(url=ENDPOINTS.API_LOGOUT_URI, method='GET')

    def _gen_totp(self) -> str:
        """
        :return: TOTP used for Mintos TFA
        """

        return pyotp.TOTP(self.__tfa_secret).now()

    def _resolve_captcha(self) -> None:
        """
        Resolve Captcha by trying to find iframe with challenge 
        """

        iframe = self.__driver.find_element(
            by='xpath',
            value='//iframe[@title="recaptcha challenge expires in two minutes"]',
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

        time.sleep(60)

        verify_button = self.__driver.find_element(
            by='id',
            value='recaptcha-verify-button',
        )

        self._js_click(verify_button)

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
        self.__driver.execute_script('arguments[0].click();', element)

    @staticmethod
    def _create_driver() -> Chrome:
        options, service = webdriver.ChromeOptions(), Service(ChromeDriverManager().install())

        # options.headless = True

        options.add_experimental_option('detach', True)

        options.add_argument('start-maximized')

        return Chrome(options=options, service=service)

    @staticmethod
    def _get_currency_iso(currency: str) -> int:
        """
        :param currency: Currency to validate and get ISO code of
        :return: Currency ISO code, if currency is invalid raise ValueError
        :raises ValueError: If currency isn't included in Mintos' accepted currencies
        """

        if currency not in CONSTANTS.CURRENCIES:
            raise ValueError(f'Currency must be one of the following: {", ".join(CONSTANTS.CURRENCIES)}')

        return CONSTANTS.CURRENCIES[currency]

    @staticmethod
    def _get_country_iso(country: str) -> int:
        """
        :param country: Country to validate and get ISO code of
        :return: Country ISO
        :raises ValueError: If country isn't included in Mintos' accepted countries
        """

        if country not in CONSTANTS.COUNTRIES:
            raise ValueError(f'Country must be one of the following: {", ".join(CONSTANTS.COUNTRIES)}')

        return CONSTANTS.COUNTRIES[country]

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
        raise NetworkException('Your internet connection is too degraded to log in to Mintos.')

    print(time.time() - t1)

    print(mintos_api.get_portfolio_data(currency='EUR'))

    print(mintos_api.get_net_annual_return(currency='EUR'))

    print(mintos_api.get_portfolio_data(currency='EUR'))

    mintos_api.logout()

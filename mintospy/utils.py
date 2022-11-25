from mintospy.exceptions import MintosException
from mintospy.constants import CONSTANTS
from typing import Generator, Union
from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime, date
from typing import Dict, List
import pickle
import time
import json


class Utils:
    @classmethod
    def parse_securities(cls, driver: WebDriver, notes: bool, current: bool) -> Dict[str, list]:
        cls._wait_for_element(
            driver=driver,
            by='xpath',
            value='//a[@data-testid="note-isin"]',
            timeout=15,
        )

        investments = BeautifulSoup(driver.page_source, 'html.parser')

        isins = investments.select('a[data-testid=note-isin]')

        loan_types = investments.select('a[data-testid=note-isin] + div')

        risk_scores = investments.select('div[class*="mintos-score-color"]')

        # Risk score, loan portfolio performance, loan servicer efficiency, buyback strength, and cooperation structure
        rs, lpp, lse, bs, cs = [], [], [], [], []

        # Sort all values in to their respective arrays
        for i in range(0, len(risk_scores), 5):
            rs.append(risk_scores[i])
            lpp.append(risk_scores[i+1])
            lse.append(risk_scores[i+2])
            bs.append(risk_scores[i+3])
            cs.append(risk_scores[i+4])

        if notes:
            countries = investments.select('svg title')[:-4]

            parsed_countries = [
                f'{countries[i].get_text()} ({countries[i + 1].get_text()})'
                for i in range(0, len(countries), 2)
            ]

        else:
            countries = investments.select('span:-soup-contains("Lending company") > div > img')

            parsed_countries = [
                f'{countries[i].get("title") or "N/A"} ({countries[i + 1].get("title") or "N/A"})'
                for i in range(0, len(countries), 2)
            ]

        if notes:
            lenders_selector = 'span[class="mw-u-o-hidden m-u-to-ellipsis mw-u-width-full"]'

        else:
            lenders_selector = 'div > img + span > div > span'

        lenders = investments.select(lenders_selector)

        interest_rates = investments.select('span:-soup-contains("Interest rate") + span')

        purchase_dates = investments.select('span:-soup-contains("Purchase date") + span > div > span')

        invested_amounts = investments.select('span:-soup-contains("Invested amount") + span > div > span')

        received_payments = investments.select('span:-soup-contains("Received payments") + span > div > span')

        pending_data = investments.select('span:-soup-contains("Pending Payments / In recovery") + div > span')

        pending_payments, in_recovery = [
            [pending_data[i] for i in range(0, len(pending_data), 2)],
            [pending_data[i] for i in range(1, len(pending_data), 2)],
        ]

        parsed_securities = {
            'ISIN': cls.extract_text(isins),
            'Country': parsed_countries,
            'Lending company': [lenders[i] for i in range(0, len(lenders), 2)],
            'Legal entity': [lenders[i] for i in range(1, len(lenders), 2)],
            'Mintos Risk Score': cls.extract_text(rs),
            'Loan portfolio performance': cls.extract_text(lpp),
            'Loan servicer efficiency': cls.extract_text(lse),
            'Buyback strength': cls.extract_text(bs),
            'Cooperation structure': cls.extract_text(cs),
            'Interest rate': cls.extract_text(interest_rates),
            'Invested amount': cls.extract_text(invested_amounts),
            'Received payments': cls.extract_text(received_payments),
        }

        if current:
            remaining_terms = investments.select('span:-soup-contains("Remaining term") + span')

            principals = investments.select('span:-soup-contains("Outstanding Principal") + span > div > span')

            payments = investments.select('span:-soup-contains("Next payment date / Next payment") + span > div > span')

            parsed_payments = []

            for val in payments:
                if val.get_text(strip=True) == '—':
                    parsed_payments.append('Late')

                    parsed_payments.append('N/A')

                    continue

                parsed_payments.append(val)

        else:
            finished_dates = investments.select('span:-soup-contains("Finished") + span')

        return parsed_securities

    @classmethod
    def import_cookies(cls, driver: WebDriver, file_path: str) -> bool:
        """
        :param driver: Web driver object to import cookies in to
        :param file_path: File path to unpickle cookies from
        :return: True if imported successfully, otherwise False
        """

        try:
            with open(file_path, 'rb') as f:
                cookies = pickle.load(f)

                if not cls.validate_cookies(cookies):
                    open(file_path, 'w').close()

                    return False

                driver.delete_all_cookies()

                for cookie in cookies:
                    driver.add_cookie(cookie)

                driver.refresh()

                with open('cookies.pkl', 'wb') as w:
                    pickle.dump(driver.get_cookies(), w)

                return True

        except (FileNotFoundError, EOFError):
            return False

    @classmethod
    def validate_cookies(cls, cookies: List[dict]) -> bool:
        if not isinstance(cookies, list):
            return False

        for cookie in cookies:
            name, expiry = cookie.get('name'), cookie.get('expiry')

            if not expiry:
                continue

            if name in CONSTANTS.SESSION_COOKIES and time.time() > expiry:
                return False

        return True

    @staticmethod
    def extract_text(elements: Union[ResultSet[Tag], List[any]]) -> List[str]:
        return [element.get_text() for element in elements]

    @classmethod
    def parse_currency_number(cls, __str: str) -> dict:
        default_return = {
            'amount': 'N/A',
            'currency': 'N/A',
        }

        if not isinstance(__str, str):
            return default_return

        __str = __str.strip()

        currency_sign = __str[0]

        currency = CONSTANTS.CURRENCY_SYMBOLS.get(currency_sign)

        if currency is None:
            return default_return

        amount = cls._str_to_float(__str.replace(currency_sign, '').strip())

        return {
            'amount': amount,
            'currency': f'{currency} ({currency_sign})',
        }

    @classmethod
    def get_svg_title(cls, svg: WebElement) -> str:
        text = svg.get_attribute('innerHTML')

        if not text:
            raise ValueError('SVG does not title text.')

        return text.strip()

    @classmethod
    def str_to_date(cls, __str: str) -> Union[date, str]:
        default_return = 'Late'

        if not isinstance(__str, str):
            return default_return

        try:
            return datetime.strptime(__str.strip().replace('.', ''), '%d%m%Y').date()

        except ValueError:
            return default_return

    @classmethod
    def mount_url(cls, url: str, params: Union[dict, List[tuple]]) -> str:
        query_string = cls._mount_query_string(params)

        return url + query_string

    @classmethod
    def parse_api_response(cls, markup: str) -> any:
        """
        :param markup: HTML markup returned from Mintos' API
        :return: Parsed API response in parsed JSON if possible, otherwise in text
        """

        parsed_html = BeautifulSoup(markup, 'html.parser')

        response_text = parsed_html.find('pre').text

        response_text = cls._safe_parse_json(response_text)

        if isinstance(response_text, dict):
            error_message = response_text.get('message')

            if error_message:
                raise MintosException(error_message)

        return response_text

    @classmethod
    def parse_mintos_items(cls, __obj: Union[list, dict]):
        return {k: v for (k, v) in cls._parse_mintos_items_gen(__obj)}

    @staticmethod
    def get_elements(markup: str, tag: str, attrs: dict) -> ResultSet:
        parsed_html = BeautifulSoup(markup, 'html.parser')

        data = parsed_html.find_all(
            name=tag,
            attrs=attrs,
        )

        return data

    @staticmethod
    def _wait_for_element(
            driver: WebDriver,
            by: str,
            value: str,
            timeout: int,
            multiple: bool = False,
    ) -> Union[WebElement, List[WebElement]]:
        """
        :param by: Tag to get element by (id, class name, xpath, tag name, etc.)
        :param value: Value of the tag (Example: tag -> id, locator -> button-id)
        :param timeout: Time to wait for element before raising TimeoutError
        :param multiple: Specify whether to return multiple web elements that match tag and locator
        :return: Web element specified by tag and locator
        :raises TimeoutException: If the element is not located within the desired time span
        """

        element_attributes = (by, value)

        WebDriverWait(driver, timeout).until(ec.visibility_of_element_located(element_attributes))

        if multiple:
            return driver.find_elements(by=by, value=value)

        return driver.find_element(by=by, value=value)

    @classmethod
    def _parse_mintos_items_gen(cls, __obj: object) -> Generator:
        if isinstance(__obj, list):
            for o in __obj:
                yield from cls._parse_mintos_items_gen(o)

        if not isinstance(__obj, dict):
            yield __obj

        for (k, v) in __obj.items():
            if isinstance(v, dict):
                yield from cls._parse_mintos_items_gen(v)

            elif isinstance(v, list):
                yield k, [
                    {t: cls._str_to_float(c) for (t, c) in cls._parse_mintos_items_gen(p)}
                    if isinstance(p, dict) else cls._str_to_float(p) for p in v
                ]

            else:
                yield k, cls._str_to_float(v)

    @staticmethod
    def _mount_query_string(params: Union[dict, List[tuple]]) -> str:
        query_string = '?'

        if params is not None:
            if len(params) == 0:
                raise ValueError('Invalid query parameters.')

            if isinstance(params, list):
                for (k, v) in params:
                    query_string += f'{k}={v}&'

            if isinstance(params, dict):
                for (k, v) in params.items():
                    query_string += f'{k}={v}&'

        # Get query parameters string except last ampersand (&)
        return query_string[:-1]

    @staticmethod
    def _safe_parse_json(s: str) -> Union[dict, str]:
        """
        :param s: Serialized JSON to be converted to Python dictionary object
        :return: Python dictionary object representation of JSON or returns same input if not deserializable
        """

        try:
            return json.loads(s)

        except json.decoder.JSONDecodeError:
            return s

    @staticmethod
    def _str_to_float(__str: str) -> object:
        try:
            return float(__str)

        except Exception:
            return __str

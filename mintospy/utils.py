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


CURRENCIES = CONSTANTS.CURRENCY_SYMBOLS


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

        risk_scores = investments.select('span:-soup-contains("Mintos Risk Score") + div > span > div > div > div')

        subscores = investments.select('span:-soup-contains("Subscore") + div > div > div[class*="mintos-score-color"]')

        # Subscores -> Loan portfolio performance, loan servicer efficiency, buyback strength, and cooperation structure
        lpp, lse, bs, cs = [], [], [], []

        # Sort all values in to their respective arrays
        for i in range(0, len(subscores), 4):
            lpp.append(subscores[i+1])
            lse.append(subscores[i+2])
            bs.append(subscores[i+3])
            cs.append(subscores[i+4])

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
            'ISIN': cls.extract_text(isins, return_type='str'),
            'Country': parsed_countries,
            'Lending company': [lenders[i].get_text(strip=True) for i in range(0, len(lenders), 2)],
            'Legal entity': [lenders[i].get_text(strip=True) for i in range(1, len(lenders), 2)],
            'Mintos Risk Score': cls.extract_text(risk_scores),
            'Loan portfolio performance': cls.extract_text(lpp),
            'Loan servicer efficiency': cls.extract_text(lse),
            'Buyback strength': cls.extract_text(bs),
            'Cooperation structure': cls.extract_text(cs),
            'Loan type': cls.extract_text(loan_types, return_type='str'),
            'Interest rate': cls.extract_text(interest_rates, is_percentage=True),
            'Invested amount': cls.extract_text(invested_amounts, is_currency=True),
            'Currency': cls.extract_text(invested_amounts, return_type='str', is_currency=True),
            'Received payments': cls.extract_text(received_payments, is_currency=True),
            'Pending payments': cls.extract_text(pending_payments, is_currency=True),
            'In recovery': cls.extract_text(in_recovery, is_currency=True),
            'Purchase date': cls.extract_text(purchase_dates, return_type='date'),
        }

        if current:
            remaining_terms = investments.select('span:-soup-contains("Remaining term") + span')

            principals = investments.select('span:-soup-contains("Outstanding Principal") + span > div > span')

            # Get all rows with defined values in the "Next payment date / Next payment" column
            next_pay = investments.select('span:-soup-contains("Next payment date / Next payment") + span > div > span')

            # Get all rows with "—" as their value in the "Next payment date / Next payment" column
            undef_next_pay = investments.select('span:-soup-contains("Next payment date / Next payment") + div > span')

            payments = [*next_pay, *undef_next_pay]

            next_payment_date, next_payment_amount = [], []

            for p in cls.extract_text(payments, return_type='str'):
                if p == '—':
                    next_payment_date.append('Late')
                    next_payment_amount.append('N/A')

                    continue

                if p.count('.') == 2:
                    next_payment_date.append(cls.str_to_date(p))

                else:
                    next_payment_amount.append(cls.parse_currency_number(p) or 'N/A')

            current_fields = {
                'Remaining term': cls.extract_text(remaining_terms, return_type='str'),
                'Outstanding principal': cls.extract_text(principals, is_currency=True),
                'Next payment date': next_payment_date,
                'Next payment amount': next_payment_amount,
            }

            parsed_securities.update(current_fields)

        else:
            finished_dates = investments.select('span:-soup-contains("Finished") + span')

            finished_fields = {
                'Finished date': cls.extract_text(finished_dates, return_type='date'),
            }

            parsed_securities.update(finished_fields)

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

    @classmethod
    def extract_text(
            cls,
            elements: Union[ResultSet[Tag], List[any]],
            *,
            return_type: str = 'float',
            is_currency: bool = False,
            is_percentage: bool = False,
    ) -> List[any]:
        return_types = ['float', 'int', 'date', 'str']

        if return_type not in return_types:
            raise ValueError(f'Invalid return type, only {return_types} available.')

        if is_currency:
            currency_return_types = ['float', 'str']

            if return_type not in currency_return_types:
                raise ValueError(f'Invalid return type, only {currency_return_types} available for currency parsing.')

            if return_type == 'float':
                return list(map(lambda element: cls.parse_currency_number(element.get_text(strip=True)), elements))

            else:
                return list(
                    map(
                        lambda element: cls.parse_currency_number(
                            element.get_text(strip=True),
                            return_type='currency',
                        ),
                        elements,
                    )
                )

        if is_percentage:
            percentage_return_types = ['float', 'str']

            if return_type not in percentage_return_types:
                raise ValueError(
                    f'Invalid return type, only {percentage_return_types} available for percentage parsing.',
                )

            if return_type == 'float':
                return list(map(lambda element: element.get_text(strip=True).replace('%', ''), elements))

        if return_type == 'float':
            return list(map(lambda element: float(element.get_text(strip=True)), elements))

        if return_type == 'date':
            return list(map(lambda element: cls.str_to_date(element.get_text(strip=True)), elements))

        return list(map(lambda element: element.get_text(strip=True), elements))

    @classmethod
    def parse_currency_number(cls, __str: str, *, return_type: str = 'number') -> Union[float, str]:
        return_types = ['currency', 'number']

        if return_type not in return_types:
            raise ValueError('Can only return currency or number from currency number.')

        __str = __str.strip()

        currency_sign = __str[0]

        currency = CURRENCIES.get(currency_sign)

        if CURRENCIES is None:
            raise ValueError(
                f'Unknown currency symbol "{currency_sign}", these are the available currencies: {CURRENCIES}',
            )

        amount = cls._str_to_float(__str.replace(currency_sign, '').strip())

        return amount if return_type == 'number' else f'{currency} ({currency_sign})'

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

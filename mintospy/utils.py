from mintospy.constants import CONSTANTS
from typing import Generator, Union
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from datetime import datetime, date
from typing import List
import asyncio
import pickle
import time
import json


class Utils:
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
    async def parse_mintos_securities(cls, securities: List[WebElement], current: bool) -> List[dict]:
        t1 = time.time()

        results = await asyncio.gather(*(cls.parse_mintos_security(security, current) for security in securities))

        print(time.time() - t1)

        print(results)

        return results

    @classmethod
    async def parse_mintos_security(cls, security: WebElement, current: bool) -> dict:
        isin = await cls.async_find_element(
            element=security,
            by='xpath',
            value='//a[@data-testid="note-isin"]',
        )

        loan_type = await cls.async_find_element(
            element=security,
            by='xpath',
            value='//a[@data-testid="note-isin"]/following-sibling::div[1]',
        )

        risk_score = await cls.async_find_element(
            element=security,
            by='class name', 
            value='score-value',
        )

        country = await cls.async_find_element(
            element=security,
            by='xpath',
            value='(//*[name()="svg"]/*[name()="title"])[1]',
        )

        lenders = await cls.async_find_element(
            element=security,
            by='xpath',
            value='//span[@class="mw-u-o-hidden m-u-to-ellipsis mw-u-width-full"]',
            multiple=True,
        )

        interest_rate = await cls.async_find_element(
            element=security,
            by='xpath',
            value='//span[normalize-space()="Interest rate"]/../span[2]',
        )

        purchase_date = await cls.async_find_element(
            element=security,
            by='xpath',
            value='//span[normalize-space()="Purchase date"]/../span[2]/div/span',
        )

        invested_amount = await cls.async_find_element(
            element=security,
            by='xpath',
            value='//span[normalize-space()="Invested amount"]/../span[2]/div/span',
        )

        received_payments = await cls.async_find_element(
            element=security,
            by='xpath',
            value='//span[normalize-space()="Received payments"]/../span[2]/div/span',
        )

        pending_payments, in_recovery = await cls.async_find_element(
            element=security,
            by='class name',
            value='m-u-nowrap',
            multiple=True,
        )

        currency = cls.parse_currency_number(invested_amount.text)['currency']

        parsed_security = {
            'isin': isin.text.strip(),
            'type': loan_type.text.strip(),
            'risk_score': int(risk_score.text.strip()),
            'lending_company': lenders[0].text.strip(),
            'legal_entity': lenders[1].text.strip(),
            'country': cls.get_svg_title(country),
            'interest_rate': float(interest_rate.text.strip().replace('%', '')),
            'purchase_date': cls.str_to_date(purchase_date.text),
            'invested_amount': cls.parse_currency_number(invested_amount.text)['amount'],
            'received_payments': cls.parse_currency_number(received_payments.text)['amount'],
            'pending_payments': cls.parse_currency_number(pending_payments.text)['amount'],
            'in_recovery': cls.parse_currency_number(in_recovery.text)['amount'],
            'currency': currency,
        }

        if current:
            remaining_term = await cls.async_find_element(
                element=security,
                by='xpath',
                value='//span[normalize-space()="Remaining term"]/../span[2]',
            )

            outstanding_principal = await cls.async_find_element(
                element=security,
                by='xpath',
                value='//span[normalize-space()="Outstanding Principal"]/../span[2]/div/span',
            )

            try:
                next_payment_date, next_payment_amount = await cls.async_find_element(
                    element=security,
                    by='class name',
                    value='date-value',
                    multiple=True,
                )

                current_fields = {
                    'remaining_term': remaining_term.text.strip(),
                    'outstanding_principal': cls.parse_currency_number(outstanding_principal.text)['amount'],
                    'next_payment_date': cls.str_to_date(next_payment_date.text),
                    'next_payment_amount': cls.parse_currency_number(next_payment_amount.text)['amount'],
                }

            except ValueError:
                next_payment_date, next_payment_amount = 'N/A', 'N/A'

                current_fields = {
                    'remaining_term': remaining_term.text.strip(),
                    'outstanding_principal': cls.parse_currency_number(outstanding_principal.text)['amount'],
                    'next_payment_date': next_payment_date,
                    'next_payment_amount': next_payment_amount,
                }

            parsed_security.update(current_fields)

        else:
            finished_date = await cls.async_find_element(
                element=security,
                by='xpath',
                value='//span[normalize-space()="Finished"]/../span[1]',
            )

            finished_fields = {
                'finished_date': datetime.strptime(finished_date.text.strip().replace('.', ''), '%d%m%Y').date(),
            }

            parsed_security.update(finished_fields)

        return parsed_security

    @staticmethod
    async def async_find_element(
            element: WebElement,
            by: str,
            value: str,
            multiple: bool = False,
    ) -> Union[List[WebElement], WebElement]:
        if multiple:
            return element.find_element(
                by=by,
                value=value,
            )

        return element.find_element(
            by=by,
            value=value,
        )

    @classmethod
    def parse_currency_number(cls, __str: str) -> dict:
        __str = __str.strip()

        currency_sign = __str[0]

        currency = CONSTANTS.CURRENCY_SYMBOLS[currency_sign]

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
    def str_to_date(cls, __str: str) -> date:
        return datetime.strptime(__str.strip().replace('.', ''), '%d%m%Y').date()

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

from mintospy.exceptions import MintosException
from mintospy.constants import CONSTANTS
from typing import Generator, Union
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime, date
from typing import List
import pickle
import time
import json
import os


CURRENCIES = CONSTANTS.CURRENCY_SYMBOLS


class Utils:
    @classmethod
    def parse_investments(cls, investments: List[dict]) -> List[dict]:
        new_items = []

        for idx, item in enumerate(investments):
            new_items.append({})

            for k, v in item.items():
                if k == 'isin' or k == 'id':
                    new_items[idx][k.upper()] = v

                if isinstance(v, dict):
                    if v.get('amount'):
                        new_items[idx][cls.camel_to_snake(k)] = cls._str_to_float(v['amount'])

                        currency = v['currency']

                        if new_items[idx].get('currency') is None:
                            new_items[idx]['currency'] = currency

                    if v.get('score'):
                        n = {'score': cls._str_to_float(v['score'])}

                        n.update({cls.camel_to_snake(k): cls._str_to_float(v) for k, v in v['subscores'].items()})

                        new_items[idx].update(n)

                    continue

                new_items[idx][cls.camel_to_snake(k)] = v

        return new_items

    @classmethod
    def camel_to_snake(cls, __str: str) -> str:
        assert isinstance(__str, str), 'You can only convert a string from camel case to snake case'

        new_string = ''

        for i, s in enumerate(__str):
            if s.isupper() and i != 0:
                new_string += f'_{s.lower()}'

                continue

            new_string += s

        return new_string

    @staticmethod
    def dict_to_form_data(__obj: dict) -> str:
        form_data = ''

        for k, v in __obj.items():
            form_data += f'{k}={v}&'

        return form_data[:-1]

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
                    f.close()

                    os.remove(file_path)

                    return False

                driver.delete_all_cookies()

                for cookie in cookies:
                    driver.add_cookie(cookie)

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
    def extract_text(cls, elements: List[any], *, return_type: str = 'float') -> list:
        return_types = ['float', 'date', 'str']

        if return_type not in return_types:
            raise ValueError(f'Invalid return type, only {return_types} available.')

        if return_type == 'float':
            return list(map(lambda element: float(element.get_text(strip=True)), elements))

        if return_type == 'date':
            return list(map(lambda element: cls.str_to_date(element.get_text(strip=True)), elements))

        return list(map(lambda element: element.get_text(strip=True), elements))

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

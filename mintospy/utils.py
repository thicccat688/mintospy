from mintospy.constants import CONSTANTS
from typing import Union
from selenium.webdriver.chrome.webdriver import WebDriver
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

                    continue

                # TODO: Revise logic for handling contracts in claims
                if k == 'contracts':
                    continue

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

                k = cls.camel_to_snake(k)

                if k in {'created_at', 'loan_dt_end', 'next_planned_payment_date'} and isinstance(v, (float, int)):
                    new_items[idx][k] = datetime.fromtimestamp(v / 1000).date()

                else:
                    new_items[idx][k] = cls._str_to_float(v)

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
    def parse_mintos_items(cls, item: dict) -> dict:
        parsed_item = {}

        for k, v in item.items():
            parsed_item[cls.camel_to_snake(k)] = cls._str_to_float(v)

        return parsed_item

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
    def _str_to_float(__str: str) -> any:
        try:
            return round(float(__str), 2)

        except Exception:
            return __str

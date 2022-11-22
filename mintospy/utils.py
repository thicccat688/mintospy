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
    def parse_securities(cls, driver: WebDriver, current: bool) -> List[dict]:
        return asyncio.run(cls.async_parse_securities(driver=driver, current=current))

    @classmethod
    async def async_parse_securities(cls, driver: WebDriver, current: bool) -> List[dict]:
        isins = cls.async_find_element(
            driver=driver,
            by='xpath',
            value='//div[@data-testid="note-series-item"]//a[@data-testid="note-isin"]',
        )

        loan_types = cls.async_find_element(
            driver=driver,
            by='xpath',
            value='//div[@data-testid="note-series-item"]//a[@data-testid="note-isin"]/following-sibling::div[1]',
        )

        risk_scores = cls.async_find_element(
            driver=driver,
            by='xpath',
            value='//div[contains(@class, "mw-u-width-40 mintos-score-color")]',
        )

        countries = cls.async_find_element(
            driver=driver,
            by='xpath',
            value='(//*[name()="svg"]/*[name()="title"])',
        )

        lenders = cls.async_find_element(
            driver=driver,
            by='xpath',
            value='//span[@class="mw-u-o-hidden m-u-to-ellipsis mw-u-width-full"]',
        )

        interest_rates = cls.async_find_element(
            driver=driver,
            by='xpath',
            value='//span[normalize-space()="Interest rate"]/../span[2]',
        )

        purchase_dates = cls.async_find_element(
            driver=driver,
            by='xpath',
            value='//span[normalize-space()="Purchase date"]/../span[2]/div/span',
        )

        invested_amounts = cls.async_find_element(
            driver=driver,
            by='xpath',
            value='//span[normalize-space()="Invested amount"]/../span[2]/div/span',
        )

        received_payments = cls.async_find_element(
            driver=driver,
            by='xpath',
            value='//span[normalize-space()="Received payments"]/../span[2]/div/span',
        )

        pending_data = cls.async_find_element(
            driver=driver,
            by='xpath',
            value='//span[normalize-space()="Pending Payments / In recovery"]/../div/span',
        )

        coroutines = [
            isins,
            loan_types,
            risk_scores,
            countries,
            lenders,
            interest_rates,
            purchase_dates,
            invested_amounts,
            received_payments,
            pending_data,
        ]

        results = await asyncio.gather(*coroutines)

        [
            isins,
            loan_types,
            risk_scores,
            countries,
            lenders,
            interest_rates,
            purchase_dates,
            invested_amounts,
            received_payments,
            pending_data,
        ] = results

        countries = countries[:-4]

        parsed_countries = [
            f'{cls.get_svg_title(countries[i])} ({cls.get_svg_title(countries[i + 1])})'
            for i in range(0, len(countries), 2)
        ]

        pending_payments, in_recovery = [
            [pending_data[i] for i in range(0, len(pending_data), 2)],
            [pending_data[i] for i in range(1, len(pending_data), 2)],
        ]

        currency = [cls.parse_currency_number(amount.text)['currency'] for amount in invested_amounts]

        parsed_securities = {
            'isin': map(lambda isin: isin.text.strip(), isins),
            'type': map(lambda type_: type_.text.strip(), loan_types),
            'risk_score': map(lambda score: int(score.text.strip()), risk_scores),
            'lending_company': [lenders[i].text.strip() for i in range(0, len(lenders), 2)],
            'legal_entity': [lenders[i].text.strip() for i in range(1, len(lenders), 2)],
            'country': parsed_countries,
            'interest_rate': map(lambda rate: float(rate.text.strip().replace('%', '')), interest_rates),
            'purchase_date': map(lambda date_: cls.str_to_date(date_.text), purchase_dates),
            'invested_amount': map(lambda amount: cls.parse_currency_number(amount.text)['amount'], invested_amounts),
            'received_payments': map(lambda recv: cls.parse_currency_number(recv.text)['amount'], received_payments),
            'pending_payments': map(lambda pend: cls.parse_currency_number(pend.text)['amount'], pending_payments),
            'in_recovery': map(lambda recovery: cls.parse_currency_number(recovery.text)['amount'], in_recovery),
            'currency': currency,
        }

        if current:
            remaining_terms = asyncio.create_task(
                cls.async_find_element(
                    driver=driver,
                    by='xpath',
                    value='//span[normalize-space()="Remaining term"]/../span[2]',
                )
            )

            outstanding_principals = asyncio.create_task(
                cls.async_find_element(
                    driver=driver,
                    by='xpath',
                    value='//span[normalize-space()="Outstanding Principal"]/../span[2]/div/span',
                )
            )

            payments = asyncio.create_task(
                cls.async_find_element(
                    driver=driver,
                    by='xpath',
                    value='//span[normalize-space()="Next payment date / Next payment"]//..//div//span',
                )
            )

            coroutines = [remaining_terms, outstanding_principals, payments]

            results = await asyncio.gather(*coroutines)

            [remaining_terms, outstanding_principals, payments] = results

            parsed_payments = []

            for val in payments:
                if val.text == '—':
                    parsed_payments.append('Late')

                    parsed_payments.append('N/A')

                    continue

                parsed_payments.append(val)

            next_payment_dates, next_payment_amounts = [
                [parsed_payments[i] for i in range(0, len(parsed_payments), 2)],
                [parsed_payments[i] for i in range(1, len(parsed_payments), 2)],
            ]

            current_fields = {
                'remaining_term': [term.text.strip() for term in remaining_terms],
                'outstanding_principal': map(
                    lambda principal: cls.parse_currency_number(principal.text)['amount'],
                    outstanding_principals,
                ),
                'next_payment_date': map(lambda pdate: cls.str_to_date(getattr(pdate, 'text', 0)), next_payment_dates),
                'next_payment_amount': map(
                    lambda amount: cls.parse_currency_number(getattr(amount, 'text', 0))['amount'] or 'N/A',
                    next_payment_amounts,
                ),
            }

            parsed_securities.update(current_fields)

        else:
            finished_dates = driver.find_elements(
                by='xpath',
                value='//span[normalize-space()="Finished"]/../span[1]',
            )

            finished_fields = {
                'finished_date': map(
                    lambda date_: datetime.strptime(date_.text.strip().replace('.', ''), '%d%m%Y').date(),
                    finished_dates,
                ),
            }

            parsed_securities.update(finished_fields)

        return parsed_securities

    @staticmethod
    async def async_find_element(driver: WebDriver, by: str, value: str) -> List[WebElement]:
        return driver.find_elements(
            by=by,
            value=value,
        )

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

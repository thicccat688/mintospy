from mintospy.constants import CONSTANTS
from typing import Union
from datetime import datetime, date
from typing import List
import warnings
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
                        new_items[idx][k] = cls._str_to_float(v['amount'])

                        currency = v['currency']

                        if new_items[idx].get('currency') is None:
                            new_items[idx]['currency'] = currency

                    if v.get('score'):
                        n = {'score': cls._str_to_float(v['score'])}

                        n.update({k: cls._str_to_float(v) for k, v in v['subscores'].items()})

                        new_items[idx].update(n)

                    continue

                if k in {'createdAt', 'deletedAt', 'loanDtEnd'} and isinstance(v, (float, int)):
                    new_items[idx][k] = datetime.fromtimestamp(v / 1000).date()

                else:
                    new_items[idx][k] = cls._str_to_float(v)

        return new_items

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
            parsed_item[k] = cls._str_to_float(v)

        return parsed_item

    @classmethod
    def parse_note_schedule(cls, item: dict) -> dict:
        parsed_item = {}

        for k, v in item.items():
            if isinstance(v, dict):
                continue

            parsed_item[k] = v

        parsed_item['id'] = item['loan']['id']
        parsed_item['identifier'] = item['loan']['identifier']

        is_prepaid = parsed_item.get('isPrepaid')

        if is_prepaid:
            parsed_item['isPrepaid'] = is_prepaid

            return parsed_item

        parsed_item['currency'] = item['currency']['abbreviation']

        parsed_item['totalScheduled'] = item['total']['scheduled']
        parsed_item['totalReceived'] = item['total']['received']
        parsed_item['totalHasRemainder'] = item['total']['hasRemainder']

        parsed_item['principalScheduled'] = item['principal']['scheduled']
        parsed_item['principalReceived'] = item['principal']['received']
        parsed_item['principalHasRemainder'] = item['principal']['hasRemainder']

        parsed_item['interestScheduled'] = item['interest']['scheduled']
        parsed_item['interestReceived'] = item['interest']['received']
        parsed_item['interestHasRemainder'] = item['interest']['hasRemainder']

        parsed_item['delayedInterestScheduled'] = item['delayedInterest']['accumulated']
        parsed_item['delayedInterestReceived'] = item['delayedInterest']['received']
        parsed_item['delayedInterestHasRemainder'] = item['delayedInterest']['hasRemainder']

        parsed_item['latePaymentFeeScheduled'] = item['latePaymentFee']['accumulated']
        parsed_item['latePaymentFeeReceived'] = item['latePaymentFee']['received']
        parsed_item['latePaymentFeeHasRemainder'] = item['latePaymentFee']['hasRemainder']

        return parsed_item

    @classmethod
    def import_cookies(cls, file_path: str) -> Union[dict, None]:
        """
        :param file_path: File path to unpickle cookies from
        :return: True if imported successfully, otherwise False
        """

        try:
            with open(file_path, 'r') as f:
                try:
                    cookies = json.load(f)

                except json.decoder.JSONDecodeError:
                    warnings.warn('Ignoring cookies file due to invalid format.')

                    f.close()

                    os.remove(file_path)

                    return

                try:
                    expiry = cookies['expiry']

                except KeyError:
                    warnings.warn('Ignoring cookies file due to invalid format.')

                    f.close()

                    os.remove(file_path)

                    return

                if time.time() > expiry:
                    f.close()

                    os.remove(file_path)

                    return

                return cookies.get('cookies')

        except (FileNotFoundError, EOFError):
            return

    @classmethod
    def str_to_date(cls, __str: str) -> Union[date, str]:
        default_return = 'Late'

        if not isinstance(__str, str):
            return default_return

        try:
            return datetime.strptime(__str.strip().replace('.', ''), '%d%m%Y').date()

        except ValueError:
            return default_return

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

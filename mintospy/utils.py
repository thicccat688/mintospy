from typing import Generator, Union
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from typing import List
import json


class Utils:
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

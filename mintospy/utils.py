from typing import Generator


class Utils:
    @classmethod
    def obj_str_to_digits(cls, __obj: list):
        return {k: v for (k, v) in cls._obj_str_to_digits_gen(__obj)}

    @classmethod
    def _obj_str_to_digits_gen(cls, __obj: object) -> Generator:
        if isinstance(__obj, list):
            for o in __obj:
                yield cls._obj_str_to_digits_gen(o)

        if not isinstance(__obj, dict):
            return

        for (k, v) in __obj.items():
            if isinstance(v, dict):
                yield from cls._obj_str_to_digits_gen(v)

            elif isinstance(v, list):
                yield k, [{t: cls._str_to_float(c) for (t, c) in cls._obj_str_to_digits_gen(p)}]

    @staticmethod
    def _str_to_float(__str: str) -> object:
        try:
            return float(__str)

        except ValueError:
            return __str

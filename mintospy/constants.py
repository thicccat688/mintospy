class CONSTANTS:
    CURRENCIES = {
        'PLN': 985,
        'GEL': 981,
        'EUR': 978,
        'GBP': 826,
        'SEK': 752,
        'MXN': 484,
        'KZT': 398,
        'DKK': 208,
        'CZK': 203,
    }

    COUNTRIES = {
        'Albania': 83,
    }

    LOAN_TYPES = [
        'agricultural',
        'business',
        'car',
        'invoice_financing',
        'mortgage',
        'pawnbroking',
        'personal',
        'short_term',
    ]

    @staticmethod
    def get_currency_iso(currency: str) -> int:
        """
        :param currency: Currency to validate and get ISO code of
        :return: Currency ISO code, if currency is invalid raise ValueError
        :raises ValueError: If currency isn't included in Mintos' accepted currencies
        """

        if currency not in CONSTANTS.CURRENCIES:
            raise ValueError(f'Currency must be one of the following: {", ".join(CONSTANTS.CURRENCIES)}')

        return CONSTANTS.CURRENCIES[currency]

    @staticmethod
    def get_country_iso(country: str) -> int:
        """
        :param country: Country to validate and get ISO code of
        :return: Country ISO
        :raises ValueError: If country isn't included in Mintos' accepted countries
        """

        if country not in CONSTANTS.COUNTRIES:
            raise ValueError(f'Country must be one of the following: {", ".join(CONSTANTS.COUNTRIES)}')

        return CONSTANTS.COUNTRIES[country]

    USER_AGENTS = [
        'Mozilla/5.0 (Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
        'Mozilla/5.0 (Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 11.2; rv:78.0) Gecko/20100101 Firefox/78.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 11.2; rv:85.0) Gecko/20100101 Firefox/85.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.63',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.68',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0',
        'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
        'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0',
        'Mozilla/5.0 (X11; Linux i686; rv:78.0) Gecko/20100101 Firefox/78.0',
        'Mozilla/5.0 (X11; Linux i686; rv:85.0) Gecko/20100101 Firefox/85.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
        'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:78.0) Gecko/20100101 Firefox/78.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:85.0) Gecko/20100101 Firefox/85.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0',
    ]

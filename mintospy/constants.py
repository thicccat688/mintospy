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
        'Namibia': 249,
        'Turkey': 247,
        'Mongolia': 236,
        'Bosnia and Herzegovina': 209,
        'Uganda': 179,
        'Uzbekistan': 169,
        'Kosovo': 98,
        'Armenia': 94,
        'Colombia': 93,
        'Zambia': 90,
        'Kenya': 87,
        'Moldova': 85,
        'Botswana': 84,
        'Albania': 83,
        'Belarus': 81,
        'Mexico': 79,
        'North Macedonia': 75,
        'Vietnam': 71,
        'Indonesia': 69,
        'Ukraine': 65,
        'Philippines': 61,
        'Georgia': 53,
        'South Africa': 51,
        'Kazakhstan': 50,
        'United Kingdom': 45,
        'Sweden': 44,
        'Spain': 43,
        'Russian Federation': 40,
        'Romania': 39,
        'Poland': 37,
        'France': 28,
        'Finland': 27,
        'Denmark': 26,
        'Czech Republic': 25,
        'Bulgaria': 22,
        'Lithuania': 19,
        'Latvia': 17,
        'Estonia': 8,
    }

    LENDING_COMPANIES = {
        'Financiera Contigo': 119,
        'Credifiel': 118,
        'Planet42': 117,
        'Conmigo Vales': 114,
        'CAPEM': 113,
        'GoCredit': 112,
        'Alivio Capital': 111,
        'Jet Finance': 110,
        'Fenchurch Legal': 109,
        'Finclusion': 107,
        'Swell': 106,
        'Revo Technology': 105,
        'IDF EURASIA': 102,
        'DelfinGroup': 101,
        'GFM': 96,
        'DanaRupiah': 93,
        'Creditter': 92,
        'Finko': 91,
        'Wowwo': 88,
        'Dinerito': 87,
        'Evergreen Finance': 85,
        'Zenka': 82,
        'E Cash': 81,
        'Everest Finanse': 80,
        'ESTO': 79,
        'Sun Finance': 78,
        'Dziesiatka Finanse': 77,
        'Alexcredit': 76,
        'SOS Credit': 75,
        'Mikro Kapital': 71,
        'Novaloans': 70,
        'Monego': 68,
        'Dineo Credito': 67,
        'Cashwagon': 62,
        'LF TECH': 61,
        'Credius': 58,
        'Fireof': 54,
        'Lime Zaim': 53,
        'Placet Group': 52,
        'Dozarplati': 47,
        'Kviku': 46,
        'ExpressCredit': 44,
        'Credissimo': 42,
        'Rapicredit': 40,
        'EcoFinance': 32,
        'Watu Credit': 31,
        'Rapido Finance': 30,
        'CashCredit': 29,
        'GetBucks': 26,
        'IuteCredit': 25,
        'ID Finance': 23,
        'Capital Service': 22,
        'Mozipo Group': 21,
        'Eurocent': 20,
        'Extra Finance': 17,
        'Creditstar': 11,
        'Debifo': 6,
        'Creamfinance': 4,
        'Capitalia': 3,
        'Eleving Group': 2,
        'Hipocredit': 1,
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
        :return: Currency ISO code
        :raises ValueError: If currency isn't included in Mintos' accepted currencies
        """

        if currency not in CONSTANTS.CURRENCIES:
            raise ValueError(f'Currency must be one of the following: {", ".join(CONSTANTS.CURRENCIES)}')

        return CONSTANTS.CURRENCIES[currency]

    @staticmethod
    def get_country_iso(country: str) -> str:
        """
        :param country: Country to validate and get ISO code of
        :return: Country ISO
        :raises ValueError: If country isn't included in Mintos' accepted countries
        """

        if country not in CONSTANTS.COUNTRIES:
            raise ValueError(f'Country must be one of the following: {", ".join(CONSTANTS.COUNTRIES)}')

        return CONSTANTS.COUNTRIES[country]

    @staticmethod
    def get_loan_type_id(loan_type: str) -> str:
        """
        :param loan_type: Type of loan (Short-term, long-term, etc.)
        :return: Loan type id for loan type specified
        :raises ValueError: If loan type isn't included in Mintos' accepted loan types
        """

        if loan_type not in CONSTANTS.LOAN_TYPES:
            raise ValueError(f'Loan type must be one of the following: {", ".join(CONSTANTS.LOAN_TYPES)}')

        return f'type-{loan_type}'

    @staticmethod
    def get_lending_company_id(lender: str) -> int:
        """
        :param lender: Lending company to get ID of
        :return: Lending company ID of specified lender
        :raises ValueError: If lending company isn't included in Mintos' current lending companies
        """

        if lender not in CONSTANTS.LENDING_COMPANIES:
            raise ValueError(f'Lending company must be one of the following: {", ".join(CONSTANTS.LENDING_COMPANIES)}')

        return CONSTANTS.LENDING_COMPANIES[lender]

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

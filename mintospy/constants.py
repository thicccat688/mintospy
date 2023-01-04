class CONSTANTS:
    # Retrieved from currencies endpoint (https://www.mintos.com/webapp/api/marketplace-api/v1/currencies)
    CURRENCIES = {
        'PLN': 985,
        'GEL': 981,
        'EUR': 978,
        'RON': 946,
        'USD': 840,
        'GBP': 826,
        'SEK': 752,
        'RUB': 643,
        'MXN': 484,
        'KZT': 398,
        'DKK': 208,
        'CZK': 203,
    }

    CURRENCY_SYMBOLS = {
        'zł': 'PLN',
        'ლ': 'GEL',
        '€': 'EUR',
        'lei': 'RON',
        '$': 'USD',
        '£': 'GBP',
        'kr': 'SEK',
        'Mex$': 'MXN',
        '₸': 'KZT',
        'Kr.': 'DKK',
        'Kč': 'CZK',
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

    AMORTIZATION_METHODS = {
        'full': 1,
        'partial': 2,
        'interest_only': 4,
        'bullet': 8,
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

    LATE_LOAN_EXPOSURES = [
        '0_20',
        '20_40',
        '40_60',
        '60_80',
        '80_100',
    ]

    LENDING_COMPANY_STATUSES = [
        'active',
        'suspended',
        'defaulted',
    ]

    NOTES_SORT_FIELDS = {
        'isin': 'isin',
        'risk_score': 'mintosRiskScoreDecimal',
        'lending_company': 'lender',
        'interest_rate': 'interestRate',
        'remaining_term': 'maturityDate',
        'purchase_date': 'createdAt',
        'invested_amount': 'initialAmount',
        'outstanding_principal': 'amount',
        'finished_date': 'deletedAt',
    }

    CLAIMS_SORT_FIELDS = {
        'id': 'id',
        'lending_company': 'lender_group',
        'interest_rate': 'interest_rate',
        'remaining_term': 'term',
        'purchase_date': 'purchased_at',
        'invested_amount': 'initial_amount',
        'outstanding_principal': 'amount',
        'next_payment_date': 'next_planned_payment_date',
        'received_payments': 'received_amount',
        'pending_payments': 'pending_payments_amount',
        'finished_date': 'finished_at',
    }

    LOANS_SORT_FIELDS = {
        'isin': 'isin',
        'risk_score': 'mintosRiskScoreDecimal',
        'lending_company': 'lender',
        'remaining_term': 'maturityDate',
        'initial_principal': 'aggregateNominalValue',
        'interest_rate': 'interestRate',
        'available_for_investment': 'availableForInvestmentAmount',
    }

    SESSION_COOKIES = {
        'PHPSESSID',
        'MW_SESSION_ID',
    }

    MAX_RESULTS = 300

    USER_AGENT = 'Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'

    @classmethod
    def get_currency_iso(cls, currency: str) -> int:
        """
        :param currency: Currency to validate and get ISO code of
        :return: Currency ISO code
        :raises ValueError: If currency isn't included in Mintos' accepted currencies
        """

        if currency not in cls.CURRENCIES:
            raise ValueError(f'Currency must be one of the following: {", ".join(cls.CURRENCIES)}')

        return CONSTANTS.CURRENCIES[currency]

    @classmethod
    def get_country_iso(cls, country: str) -> str:
        """
        :param country: Country to validate and get ISO code of
        :return: Country ISO
        :raises ValueError: If country isn't included in Mintos' accepted countries
        """

        if country not in cls.COUNTRIES:
            raise ValueError(f'Country must be one of the following: {", ".join(cls.COUNTRIES)}')

        return CONSTANTS.COUNTRIES[country]

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

    @classmethod
    def get_amoritzation_method_id(cls, method: str) -> int:
        """
        :param method: Amortization method to get ID of (Full, partial, interest only, or bullet)
        :return: Amortization method ID
        :raises ValueError: If lending company isn't included in Mintos' current lending companies
        """

        if method not in cls.AMORTIZATION_METHODS:
            raise ValueError(
                f'Amortization method must be one of the following : {", ".join(cls.AMORTIZATION_METHODS)}',
            )

        return cls.AMORTIZATION_METHODS[method]

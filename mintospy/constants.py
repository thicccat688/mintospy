from mintospy.endpoints import ENDPOINTS
import requests


class CONSTANTS:
    COUNTRIES, LENDING_COMPANIES, CURRENCIES = None, None, None

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
    def get_currencies(cls) -> dict:
        """
        :return: Currencies available on Mintos
        """

        if cls.CURRENCIES is None:
            raw_currencies = requests.get(ENDPOINTS.API_CURRENCIES_URI).json()

            cls.CURRENCIES = dict(
                map(
                    lambda data: (data['abbreviation'], {k: v for k, v in data.items() if k != 'abbreviation'}),
                    raw_currencies['items'],
                )
            )

        return cls.CURRENCIES

    @classmethod
    def get_countries(cls):
        """
        :return: Countries available on Mintos
        """

        if cls.COUNTRIES is None:
            raw_countries = requests.get(ENDPOINTS.API_COUNTRIES_URI).json()

            cls.COUNTRIES = dict(map(lambda data: (data['name'], data['id']), raw_countries['countries']))

        return cls.COUNTRIES

    @classmethod
    def get_lending_companies(cls) -> dict:
        """
        :return: Lending companies available on Mintos
        """

        if cls.LENDING_COMPANIES is None:
            raw_companies = requests.get(ENDPOINTS.API_LENDING_COMPANIES_URI).json()

            cls.LENDING_COMPANIES = dict(
                map(
                    lambda data: (data['name'], {k: v for k, v in data.items() if k != 'name'}),
                    raw_companies['items']
                )
            )

        return cls.LENDING_COMPANIES

    @classmethod
    def get_currency_iso(cls, currency: str) -> int:
        """
        :param currency: Currency to validate and get ISO code of
        :return: Currency ISO code
        :raises ValueError: If currency isn't included in Mintos' accepted currencies
        """

        if cls.CURRENCIES is None:
            cls.get_currencies()

        if currency not in cls.CURRENCIES:
            raise ValueError(f'Currency must be one of the following: {", ".join(cls.CURRENCIES)}')

        return CONSTANTS.CURRENCIES[currency].get('isoCode')

    @classmethod
    def get_country_iso(cls, country: str) -> str:
        """
        :param country: Country to validate and get ISO code of
        :return: Country ISO
        :raises ValueError: If country isn't included in Mintos' accepted countries
        """

        if CONSTANTS.COUNTRIES is None:
            cls.get_countries()

        if country not in cls.COUNTRIES:
            raise ValueError(f'Country must be one of the following: {", ".join(cls.COUNTRIES)}')

        return CONSTANTS.COUNTRIES[country]

    @classmethod
    def get_lending_company_id(cls, lender: str) -> int:
        """
        :param lender: Lending company to get ID of
        :return: Lending company ID of specified lender
        :raises ValueError: If lending company isn't included in Mintos' current lending companies
        """

        if CONSTANTS.LENDING_COMPANIES is None:
            cls.get_lending_companies()

        if lender not in CONSTANTS.LENDING_COMPANIES:
            raise ValueError(f'Lending company must be one of the following: {", ".join(CONSTANTS.LENDING_COMPANIES)}')

        return int(CONSTANTS.LENDING_COMPANIES[lender].get('id'))

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

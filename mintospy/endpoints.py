class ENDPOINTS:
    BASE_URI = 'https://www.mintos.com/webapp/api'

    API_LOGIN_URI = f'{BASE_URI}/auth/login'

    API_LOGOUT_URI = f'{BASE_URI}/auth/logout'

    API_TFA_URI = f'{BASE_URI}/en/webapp-api/user/login/otp'

    API_COUNTRIES_URI = f'{BASE_URI}/marketplace-api/v1/countries'

    API_CURRENCIES_URI = f'{BASE_URI}/marketplace-api/v1/currencies'

    API_LENDING_COMPANIES_URI = f'{BASE_URI}/marketplace-api/v1/lender-companies'

    API_PORTFOLIO_URI = f'{BASE_URI}/marketplace-api/v1/note-series/overview/portfolio-data'

    API_NAR_URI = f'{BASE_URI}/en/webapp-api/user/overview-net-annual-returns'

    API_AGGREGATES_OVERVIEW_URI = f'{BASE_URI}/en/webapp-api/user/overview-aggregates'

    API_INVESTMENTS_URI = f'{BASE_URI}/marketplace-api/v1/user/note-series/investments'

    API_INVESTMENTS_FILTER_URI = f'{BASE_URI}/en/webapp-api/user/investments/filters'

    API_CLAIMS_URI = f'{BASE_URI}/en/webapp-api/user/investments'

    API_CLAIMS_DETAILS_URI = f'{BASE_URI}/en/webapp-api/loans'

    API_LOANS_URI = f'{BASE_URI}/marketplace-api/v1/note-series'

    API_LOANS_FILTER_URI = f'{BASE_URI}/en/webapp-api/market/primary/filters'

    API_NOTES_DETAILS_URI = f'{BASE_URI}/marketplace-api/v1/note-series'

    WEB_APP_URI = 'https://www.mintos.com/en'

    LOGIN_URI = f'{WEB_APP_URI}/login'

    OVERVIEW_URI = f'{WEB_APP_URI}/overview'

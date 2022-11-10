class ENDPOINTS:
    BASE_URI = 'https://www.mintos.com/webapp/api'

    API_LOGIN_URI = f'{BASE_URI}/auth/login'

    API_LOGOUT_URI = f'{BASE_URI}/auth/logout'

    API_TFA_URI = f'{BASE_URI}/en/webapp-api/user/login/otp'

    API_OVERVIEW_NAR_URI = f'{BASE_URI}/en/webapp-api/user/overview-net-annual-returns'

    API_PORTFOLIO_URI = f'{BASE_URI}/marketplace-api/v1/note-series/overview/portfolio-data'

    API_CURRENCIES_URI = f'{BASE_URI}/marketplace-api/v1/currencies'

    API_LENDING_COMPANIES_URI = f'{BASE_URI}/en/webapp-api/lender-companies'

    API_CURRENT_INVESTMENTS_URI = f'{BASE_URI}/marketplace-api/v1/user/note-series/investments/current'

    API_FINISHED_INVESTMENTS_URI = f'{BASE_URI}/marketplace-api/v1/user/note-series/investments/finished'

    WEB_APP_URI = 'https://www.mintos.com/en'

    LOGIN_URI = f'{WEB_APP_URI}/login'

    OVERVIEW_URI = f'{WEB_APP_URI}/overview'

    CURRENT_INVESTMENTS_URI = f'{WEB_APP_URI}/set-of-notes/investments/current'

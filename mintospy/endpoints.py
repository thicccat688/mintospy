class ENDPOINTS:
    BASE_URI = 'https://www.mintos.com/webapp/api'

    API_LOGIN_URI = f'{BASE_URI}/auth/login'

    API_LOGOUT_URI = f'{BASE_URI}/auth/logout'

    API_TFA_URI = f'{BASE_URI}/en/webapp-api/user/login/otp'

    API_FILTER_URI = f'{BASE_URI}/en/webapp-api/user/investments/filters'

    API_INVESTMENTS_URI = f'{BASE_URI}/marketplace-api/v1/user/note-series/investments'

    API_CLAIMS_URI = f'{BASE_URI}/en/webapp-api/user/investments'

    WEB_APP_URI = 'https://www.mintos.com/en'

    LOGIN_URI = f'{WEB_APP_URI}/login'

    OVERVIEW_URI = f'{WEB_APP_URI}/overview'

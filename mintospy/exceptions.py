class MintosException(Exception):
    pass


class InvalidCredentials(MintosException):
    pass


class RecaptchaException(MintosException):
    pass


class NetworkException(MintosException):
    pass

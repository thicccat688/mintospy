class MintosException(Exception):
    pass


class InvalidCredentials(MintosException):
    pass


class NetworkException(MintosException):
    pass

class IllegalArgumentException(ValueError):
    pass


class ModelNotExtendableException(Exception):
    def __init__(self, message='Model is not subtype of ExtendableModel'):
        self.message = message
        super().__init__(message)


class AuthenticationFailedException(Exception):
    def __init__(self, message='Authentication failed'):
        self.message = message
        super().__init__(message)


class RequestFailedException(Exception):
    def build_message(self, status_code: str, reason: str):
        return F"Request failed with status code {status_code}: {reason}"

    def __init__(self, status_code: str, reason: str):
        self.message = self.build_message(status_code, reason)
        super().__init__(self.message)


class UnexpectedResponseException(RequestFailedException):
    def build_message(self, status_code, reason):
        return F"Unexpected response with status code {status_code}: {reason}"

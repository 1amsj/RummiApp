class ModelNotExtendableException(Exception):
    def __init__(self, message='Model is not subtype of ExtendableModel'):
        self.message = message
        super().__init__(message)
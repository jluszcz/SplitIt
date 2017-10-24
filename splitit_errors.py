class SplititError(Exception):
    def __init__(self, status_code, message):
        Exception.__init__(self)
        self.status_code = status_code
        self.message = message

    def to_dict(self):
        return {
            'message': self.message,
            'status_code': self.status_code
        }

class ConflictError(SplititError):
    def __init__(self, message):
        SplititError.__init__(self, 409, message)

class BadRequestError(SplititError):
    def __init__(self, message):
        SplititError.__init__(self, 400, message)

class NotFoundError(SplititError):
    def __init__(self, message):
        SplititError.__init__(self, 404, message)

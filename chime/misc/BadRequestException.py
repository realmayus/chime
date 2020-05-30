class BadRequestException(Exception):
    """Gets raised when the User sends a bad request"""

    def __init__(self, text):
        super(BadRequestException, self).__init__(text)
        self.text = text

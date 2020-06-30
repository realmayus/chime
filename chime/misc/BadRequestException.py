class BadRequestException(Exception):

    def __init__(self, text):
        """Gets raised when the User sends a bad request"""
        super(BadRequestException, self).__init__(text)
        self.text = text

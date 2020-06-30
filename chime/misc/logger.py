import logging
from logging.handlers import RotatingFileHandler


def init_logger(logger):
    """Initializes the logger."""
    print("Hello World")
    print(logger)
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    log_file = 'log.txt'
    my_handler = RotatingFileHandler(filename=log_file, mode='w', maxBytes=5 * 1024 * 1024, backupCount=2, encoding=None, delay=0)
    my_handler.setFormatter(log_formatter)
    my_handler.setLevel(logging.INFO)
    logger.setLevel(logging.INFO)
    logger.addHandler(my_handler)

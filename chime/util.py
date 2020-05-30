import configparser
import logging
import re
from logging.handlers import RotatingFileHandler


url_regex = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def init_logger() -> 'logging.Logger':
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    log_file = '../log.txt'
    my_handler = RotatingFileHandler(filename=log_file, mode='w', maxBytes=5 * 1024 * 1024, backupCount=2, encoding=None, delay=0)
    my_handler.setFormatter(log_formatter)
    my_handler.setLevel(logging.INFO)
    logger = logging.getLogger("chime")
    logger.setLevel(logging.INFO)
    logger.addHandler(my_handler)
    return logger


def get_token(start_dev: bool) -> str:
    config = configparser.ConfigParser()
    config.read("../secret/token.ini")
    section = config['token']
    if start_dev:
        return section["token-dev"]
    return section['token']


def check_if_url(url: str) -> bool:
    return re.match(url_regex, url) is not None


def get_friendly_time_delta(time_millis: int) -> str:
    millis = int(time_millis)
    seconds = (millis/1000) % 60
    seconds = int(seconds)
    minutes = (millis/(1000*60)) % 60
    minutes = int(minutes)
    hours = (millis/(1000*60*60)) % 24

    return "%dh:%dm:%ds" % (hours, minutes, seconds)

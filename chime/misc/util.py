import configparser
import logging
import re
from logging.handlers import RotatingFileHandler

from discord import Message
from google.cloud.firestore_v1 import Client
from google.cloud.firestore_v1.proto.document_pb2 import Document
from wavelink import Track

from chime.misc.StyledEmbed import StyledEmbed

url_regex = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def init_logger() -> 'logging.Logger':
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    log_file = '../../log.txt'
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
    seconds = str(int(seconds)) + "s"
    minutes = (millis/(1000*60)) % 60
    minutes = str(int(minutes)) + "m"
    hours = str(int((millis/(1000*60*60)) % 24)) + "h"

    return " ".join([hours if hours != "0h" else "", minutes if minutes != "0m" else "", seconds])


def get_song_selector_embed_desc_for_current_page(page, results):
    desc = "**React with a number to play the respective song!**\n"
    i = 1
    for track_index in range(len(results)):
        try:
            track = results[page * 5 + track_index]
            if i == 6:
                break
            desc += (u"%s\N{variation selector-16}\N{combining enclosing keycap}" % str(i)) + "  " + str(track) + "\n"
            i += 1
        except IndexError:
            pass
    return desc, i


async def react_with_pagination_emoji(msg: Message, count: int, show_next: bool):
    [await msg.add_reaction(u"%s\N{variation selector-16}\N{combining enclosing keycap}" % str(x + 1)) for x in
     range(count - 1)]
    if show_next:
        await msg.add_reaction("▶️")


def get_currently_playing_embed(current_track: Track):
    currently_playing_embed = StyledEmbed(title="<:music_note:716669042500436010>  " + current_track.title)
    currently_playing_embed.set_author(name="Now playing", url=current_track.uri)
    currently_playing_embed.add_field(name="Duration",
                                      value=get_friendly_time_delta(current_track.duration))
    currently_playing_embed.add_field(name="Artist", value=current_track.author)
    if current_track.thumb is not None:
        currently_playing_embed.set_thumbnail(url=current_track.thumb)
    return currently_playing_embed


def check_if_playlist_exists(db: Client, name: str, user: int):
    doc_ref = db.collection(str(user)).document(str(name))
    doc = doc_ref.get()
    if doc.exists:
        return True
    return False

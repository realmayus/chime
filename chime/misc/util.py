import configparser
import logging
import re
from logging.handlers import RotatingFileHandler
from typing import List

from discord import Message
from google.cloud.firestore_v1 import  DocumentReference, DocumentSnapshot
from wavelink import Track, TrackPlaylist

from chime.misc.BadRequestException import BadRequestException
from chime.misc.StyledEmbed import StyledEmbed

url_regex = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def get_token(start_dev: bool) -> str:
    config = configparser.ConfigParser()
    config.read("./secret/token.ini")
    section = config['token']
    if start_dev:
        return section["token-dev"]
    return section['token']


def get_github_token() -> str:
    config = configparser.ConfigParser()
    config.read("./secret/token.ini")
    section = config['token']
    return section['github-access-token']


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


def check_if_playlist_exists(profile: DocumentReference, name: str):
    data_snapshot: DocumentSnapshot = profile.get()
    data: dict = data_snapshot.to_dict()
    if data is not None:
        if "playlists" in data.keys():
            playlists: list = data["playlists"]
            playlist: dict
            for playlist in playlists:
                if playlist["name"]:
                    if playlist["name"].lower() == name.lower():
                        return playlist["ref"]
            return False
        else:
            return False
    else:
        return False


async def search_song(query, ctx, bot, success_callback, success_callback_url):
    from chime.misc.SongSelector import SongSelector

    if query == "^":  # set the query to the previous message
        x = await ctx.channel.history(limit=2).flatten()
        query = x[1].content
        print(query)
    if check_if_url(query):  # user provided an URL, play that
        tracks = await bot.wavelink.get_tracks(query)
        await success_callback_url(tracks)
        return
    else:  # user didn't provide an URL so search for the entered term
        i = 0
        tracks = False
        while not tracks and i < 5:  # try to find song 5 times
            tracks: List[Track] = await bot.wavelink.get_tracks(f'ytsearch:{query}')
            i += 1
    if not tracks:
        raise BadRequestException('Could not find any songs with that query.')

    songselector = SongSelector(tracks, bot, success_callback, ctx)
    await songselector.send(songselector.get())

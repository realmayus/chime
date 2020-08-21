import asyncio
from typing import List

import discord
from wavelink import Player, Track

from chime.util import get_currently_playing_embed


class MusicController:
    """Handles the looping modes"""
    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id
        self.channel = None
        self.next = asyncio.Event()
        self.playlist = None  # to be implemented later on

        self.queue: List[Track] = []
        self.current_index = 0
        self.looping_mode = 0  # 0 = off (just play the next item in the queue), 1 = single (loop the track at the current index), 2 = whole queue (loop the whole queue)
        self.prev_looping_mode = 0  # The previous looping mode, important for determining whether the index was already advanced.
        self.current_track = None
        self.volume = 40  # default volume
        self.now_playing_msg = None
        self.task = self.bot.loop.create_task(self.controller_loop())

    async def controller_loop(self):
        """The music loop."""
        await self.bot.wait_until_ready()
        player: Player = self.bot.wavelink.get_player(self.guild_id)
        await player.set_volume(self.volume)
        while True:
            if self.now_playing_msg is not None:
                """Check if the "currently playing" message is still there, if so, try to delete it :)."""
                try:
                    await self.now_playing_msg.delete()
                    self.now_playing_msg = None
                except discord.errors.NotFound:
                    pass

            # Remove the internal flag of our event (see docs of asyncio.Event for more info)
            self.next.clear()
            if self.looping_mode == 0:
                """Looping is turned off, just play the next song in the queue if available."""
                try:
                    if len(self.queue) != 0 and len(self.queue) - 1 >= self.current_index:  # check if has next
                        self.current_index += 1
                        song = self.queue[self.current_index - 1]
                    else:
                        await asyncio.sleep(0)  # We need to yield something here so that the loop doesn't block our code. asyncio is weird, fam
                        continue  # skip to the next cycle of our `while` loop
                except IndexError as error:
                    import traceback
                    import sys
                    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
                    await asyncio.sleep(0)  # We need to yield something here so that the loop doesn't block our code. asyncio is weird, fam
                    continue


            elif self.looping_mode == 1:
                """Loop the current track"""
                if self.current_track is not None:
                    """Check if the current_track variable is not None, if so, play the track."""
                    song = self.current_track
                else:
                    await asyncio.sleep(0)
                    continue

            elif self.looping_mode == 2:
                """Loop the entire queue"""
                if len(self.queue) - 1 >= self.current_index:  # check if has next
                    self.current_index += 1
                    song = self.queue[self.current_index - 1]
                else:
                    try:  # check if queue wasn't cleared :shrug:
                        song = self.queue[0]
                        self.current_index = 1
                    except IndexError:
                        await asyncio.sleep(0)
                        continue
            else:
                await asyncio.sleep(0)
                continue

            await player.play(song)
            self.now_playing_msg = await self.channel.send(embed=get_currently_playing_embed(song))  # send the "currently playing embed
            self.current_track = song  # set the current_track variable to our track
            await self.next.wait()  # wait for the event to finish

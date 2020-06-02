import asyncio
from typing import List

import discord
from wavelink import Player, Track

import chime
from chime.misc.util import get_currently_playing_embed


class MusicController:

    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id
        self.channel = None
        self.next = asyncio.Event()
        # self.queue = asyncio.Queue()
        self.playlist = None  # to be implemented later on

        self.queue: List[Track] = []
        self.current_index = 0
        self.looping_mode = 0  # 0 = off (just play the next item in the queue), 1 = single (loop the track at the current index), 2 = whole queue (loop the whole queue)

        self.volume = 40
        self.now_playing = None
        self.bot.loop.create_task(self.controller_loop())

    async def controller_loop(self):
        await self.bot.wait_until_ready()
        player: Player = self.bot.wavelink.get_player(self.guild_id)
        await player.set_volume(self.volume)
        while True:
            if self.now_playing is not None:
                try:
                    await self.now_playing.delete()
                except discord.errors.NotFound:
                    pass
            self.next.clear()
            print(self.looping_mode)
            if self.looping_mode == 0:
                if self.current_index == len(self.queue):
                    """End of queue reached!"""
                    song = None
                else:
                    """Just play the next song in the queue"""
                    print("now playing next")
                    song = self.queue[self.current_index]
                    self.current_index += 1

            elif self.looping_mode == 1:
                """Looping mode: "Single" (loop the current track)"""
                print("now playing again")
                try:
                    song = self.queue[self.current_index]
                except IndexError:
                    song = self.queue[self.current_index - 1]
            elif self.looping_mode == 2:
                """Looping mode: "Queue" (loop the entire queue)"""
                if self.current_index == len(self.queue):
                    """End of queue reached! Now start from the beginning again."""
                    if len(self.queue) > 0:
                        print("End of queue reached!")
                        print("Starting from beginning!")
                        self.current_index = 0
                        song = self.queue[0]
                        await asyncio.sleep(1)
                    else:
                        song = None
                else:
                    """Idling through the queue, just advance the current_index and play the next song!"""
                    print("Idling through queue!")
                    song = self.queue[self.current_index]
                    self.current_index += 1

            else:
                song = None

            if song:
                await player.play(song)
                self.now_playing = await self.channel.send(embed=get_currently_playing_embed(song))
                await self.next.wait()

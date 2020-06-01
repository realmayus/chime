import asyncio

import chime
from chime.misc.util import get_currently_playing_embed


class MusicController:

    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id
        self.channel = None

        self.next = asyncio.Event()
        self.queue = asyncio.Queue()

        self.volume = 40
        self.now_playing = None

        self.bot.loop.create_task(self.controller_loop())

    async def controller_loop(self):
        await self.bot.wait_until_ready()

        player = self.bot.wavelink.get_player(self.guild_id)
        await player.set_volume(self.volume)

        while True:
            if self.now_playing:
                await self.now_playing.delete()

            self.next.clear()

            song = await self.queue.get()
            await player.play(song)
            self.now_playing = await self.channel.send(embed=get_currently_playing_embed(song))

            await self.next.wait()

import asyncio
import logging

from discord import Game
from discord.ext import commands
from chime.main import prefix


class MiscCog(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.logger = logging.getLogger("chime")

    @commands.Cog.listener()
    async def on_ready(self):
        """Gets called when the bot is connected to Discord. Activates the status task which updates the bot's status every 5 minutes"""
        self.bot.loop.create_task(self.status_task())
        self.logger.info("Bot logged in as " + str(self.bot.user))
        print("Bot logged in as " + str(self.bot.user))


    async def status_task(self):
        """Update the bot's status every 5 minutes"""
        while True:
            await self.bot.change_presence(activity=Game(name="music to " + str(len(self.bot.guilds)) + " guilds %shelp" % prefix))
            await asyncio.sleep(5 * 60)



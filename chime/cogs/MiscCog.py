import asyncio
import logging

from discord import Game, Guild, TextChannel
from discord.ext import commands
from discord.utils import find

from chime.main import prefix
from chime.misc.StyledEmbed import StyledEmbed


class MiscCog(commands.Cog):
    def __init__(self, bot):
        """A cog for miscellaneous features that aren't commands but interface with discord.py"""
        self.bot: commands.Bot = bot
        self.logger = logging.getLogger("chime")

    @commands.Cog.listener()
    async def on_ready(self):
        """Gets called when the bot is connected to Discord. Activates the status task which updates the bot's status every 5 minutes"""
        self.bot.loop.create_task(self.status_task())
        self.logger.info("Bot logged in as " + str(self.bot.user))
        print("Bot logged in as " + str(self.bot.user))
        if not hasattr(self.bot, "emoji_guild"):
            self.bot.emoji_guild = await self.bot.fetch_guild(716228019345293352)
        print("Bot logged in as " + str(self.bot.user))

    async def status_task(self):
        """Update the bot's status every 5 minutes"""
        while True:
            await self.bot.change_presence(
                activity=Game(name="music to " + str(len(self.bot.guilds)) + " guilds %shelp" % prefix))
            await asyncio.sleep(5 * 60)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        """Send welcome message on guild join"""
        channel = None
        if guild.system_channel is not None:
            channel: TextChannel = guild.system_channel  # Try to use system message channel
        else:
            y = find(lambda x: x.name == "general",
                     guild.text_channels)  # if that doesn't exist, try to find a 'general' channel
            if y:
                channel: TextChannel = y
        if channel is not None:
            embed = StyledEmbed(title="Welcome to chime",
                                description="Thanks for having me.\n\nchime is a versatile, yet intuitive music bot for discord. It aims to have the best performance while being as user-friendly as possible. \n\n" 
                                            "Want to support the development of chime while getting exclusive benefits? **[Donate](https://github.com/realmayus/chime)** \n" 
                                            "chime sports a nice webinterface where you can manage settings for your server and create and manage personal playlists. [Check it out here](https://google.com).  "
                                            "**More info and invite link [here](https://github.com/realmayus/chime)**\n\n**See all available commands with** `" + prefix + "help`")
            embed.set_image(url="https://raw.githubusercontent.com/realmayus/chime/master/assets/chime_banner.png?token=AJC6B5VTHEZ5UHNY7QNDCU263LCCK")
            await channel.send(embed=embed)

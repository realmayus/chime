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

    @commands.Cog.listener()
    async def on_ready(self):
        """Gets called when the bot is connected to Discord. Activates the status task which updates the bot's status every 5 minutes"""
        print("Bot logged in as " + str(self.bot.user))

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
                                description=":wave: Thanks for having me!\n\nchime is a versatile, yet intuitive music bot for discord. It aims to have the best performance while being as user-friendly as possible. \n\n" 
                                            "chime sports a **webinterface where you can manage settings for your server and create and manage personal playlists.** [Check it out here](https://chime.realmayus.xyz).  \n"
                                            "With using chime you agree to our **[Terms of Service](https://chime.realmayus.xyz/terms)** and our **[Privacy Policy](https://chime.realmayus.xyz/privacy)**.\n"
                                            "**More info and invite link [here](https://chime.realmayus.xyz)**\n\n**See all available commands with** `" + prefix + "help`")
            embed.set_image(url="https://raw.githubusercontent.com/realmayus/chime/master/assets/chime_banner.png?token=AJC6B5VTHEZ5UHNY7QNDCU263LCCK")
            await channel.send(embed=embed)

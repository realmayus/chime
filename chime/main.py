import asyncio
import time
import os.path

import firebase_admin
from discord import Game
from firebase_admin import credentials, firestore
from firebase_admin.auth import Client

from discord.ext import commands

# Activate dev mode (start using 2nd token) if start-dev file is present in root directory!
start_dev = os.path.isfile("./start-dev")

version = "1.0.0"
prefix = "$" if start_dev else "*"

report_channel = 722092978021072896


def start():
    from chime.cogs.MusicCommandsCog import MusicCommandsCog
    from chime.cogs.MiscCommandsCog import MiscCommandsCog
    from chime.cogs.MiscCog import MiscCog
    from chime.cogs.StatsCog import StatsCog
    from chime.cogs.PersonalPlaylistsCog import PersonalPlaylistsCog
    from chime.cogs.CommandErrorHandlerCog import CommandErrorHandlerCog
    from chime.misc.util import get_token
    from chime.cogs.HelpCommandCog import EmbedHelpCommand
    bot = commands.Bot(command_prefix=commands.when_mentioned_or(prefix), help_command=EmbedHelpCommand())
    bot.start_time = time.time()
    print("Starting chime v." + version + "…")


    cred = credentials.Certificate("./secret/firebase_creds.json")
    firebase_admin.initialize_app(cred)
    db: Client = firestore.client()
    print("> Initialized DB!")


    bot.add_cog(MusicCommandsCog(bot))
    bot.add_cog(MiscCommandsCog(bot))
    bot.add_cog(MiscCog(bot))
    bot.add_cog(CommandErrorHandlerCog(bot))
    bot.add_cog(PersonalPlaylistsCog(bot, db))
    bot.add_cog(StatsCog(bot, db))
    bot.loop.create_task(status_task(bot))
    print("> Loaded cogs!")
    bot.run(get_token(start_dev))


async def status_task(bot):
    """Update the bot's status every 5 minutes"""
    await bot.wait_until_ready()
    while True:
        await asyncio.sleep(5 * 60)
        await bot.change_presence(
            activity=Game(name="music to " + str(len(bot.guilds)) + " guilds %shelp" % prefix))


def start_wrapper():
    start()

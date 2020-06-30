import logging
import time
import os.path

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.auth import Client

from chime.misc.logger import init_logger
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
    logger = logging.getLogger("chime")
    logger.info("Starting chime v." + version + "…")
    print("Starting chime v." + version + "…")


    cred = credentials.Certificate("./secret/firebase_creds.json")
    firebase_admin.initialize_app(cred)
    db: Client = firestore.client()
    logger.info("> Initialized DB!")
    print("> Initialized DB!")


    bot.add_cog(MusicCommandsCog(bot))
    bot.add_cog(MiscCommandsCog(bot))
    bot.add_cog(MiscCog(bot))
    bot.add_cog(CommandErrorHandlerCog(bot))
    bot.add_cog(PersonalPlaylistsCog(bot, db))
    bot.add_cog(StatsCog(bot, db))
    logger.info("> Loaded cogs!")
    print("> Loaded cogs!")
    bot.run(get_token(start_dev))


def start_wrapper():
    __logger__ = logging.getLogger("chime")
    init_logger(__logger__)
    start()

import logging
import time
from chime.misc.logger import init_logger
from discord.ext import commands

# If activated: Uses the token-dev to minimize downtime while developing
start_dev = True

version = "1.0.0"
prefix = "$" if start_dev else "*"

report_channel = 722092978021072896


def start():
    from chime.cogs.MusicCommandsCog import MusicCommandsCog
    from chime.cogs.MiscCommandsCog import MiscCommandsCog
    from chime.cogs.MiscCog import MiscCog
    from chime.cogs.PersonalPlaylistsCog import PersonalPlaylistsCog
    from chime.cogs.CommandErrorHandlerCog import CommandErrorHandlerCog
    from chime.misc.util import get_token
    from chime.cogs.HelpCommandCog import EmbedHelpCommand
    bot = commands.Bot(command_prefix=commands.when_mentioned_or(prefix), help_command=EmbedHelpCommand())
    bot.start_time = time.time()
    logger = logging.getLogger("chime")
    logger.info("Starting chime v." + version + "…")
    print("Starting chime v." + version + "…")
    bot.add_cog(MusicCommandsCog(bot))
    bot.add_cog(MiscCommandsCog(bot))
    bot.add_cog(MiscCog(bot))
    bot.add_cog(CommandErrorHandlerCog(bot))
    bot.add_cog(PersonalPlaylistsCog(bot))
    logger.info("Loaded cogs!")
    print("Loaded cogs!")
    bot.run(get_token(start_dev))


def start_wrapper():
    __logger__ = logging.getLogger("chime")
    init_logger(__logger__)
    start()

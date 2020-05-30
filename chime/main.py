from discord.ext import commands
from chime.util import init_logger, get_token
from chime.cogs.CommandErrorHandlerCog import CommandErrorHandlerCog
from chime.cogs.HelpCommandCog import EmbedHelpCommand

# If activated: Uses the token-dev to minimize downtime while developing
start_dev = True

logger = None
version = "1.0.0"
prefix = "*" if start_dev else "$"

bot = commands.Bot(command_prefix=prefix, help_command=EmbedHelpCommand())


def start():
    from chime.cogs.MusicCommandsCog import MusicCommandsCog
    from chime.cogs.MiscCommandsCog import MiscCommandsCog
    from chime.cogs.MiscCog import MiscCog

    logger.info("Starting chime v." + version + "…")
    print("Starting chime v." + version + "…")
    bot.add_cog(MusicCommandsCog(bot))
    bot.add_cog(MiscCommandsCog(bot))
    bot.add_cog(MiscCog(bot))
    bot.add_cog(CommandErrorHandlerCog(bot))
    logger.info("Loaded cogs!")
    print("Loaded cogs!")
    bot.run(get_token(start_dev))


if __name__ == "__main__":
    logger = init_logger()
    start()

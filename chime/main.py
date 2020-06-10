import logging
import time
from .misc.logger import init_logger
from discord.ext import commands

print("test1")
# If activated: Uses the token-dev to minimize downtime while developing
start_dev = True


version = "1.0.0"
prefix = "*" if start_dev else "$"

logger = None

report_issues = False  # Only turn this off while developing!
# When someone submits an urgent error report, send the report to these users' discord accounts
urgent_notifications = [218444620051251200]
repo_name = "chime"
user_feedback_issue = 3  # Those ids are for creating issues when users submit feedback or file bug reports
auto_issues_issue = 2
user_issues_issue = 1


def start():
    from chime.cogs.MusicCommandsCog import MusicCommandsCog
    from chime.cogs.MiscCommandsCog import MiscCommandsCog
    from chime.cogs.MiscCog import MiscCog
    from chime.cogs.PersonalPlaylistsCog import PersonalPlaylistsCog
    from chime.cogs.CommandErrorHandlerCog import CommandErrorHandlerCog
    from chime.misc.util import get_token
    from chime.cogs.HelpCommandCog import EmbedHelpCommand
    print("test3")
    bot = commands.Bot(command_prefix=commands.when_mentioned_or(prefix), help_command=EmbedHelpCommand())
    bot.start_time = time.time()
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


if __name__ == "__main__":
    print("test2")
    logger = logging.getLogger("chime")
    print(logger)
    init_logger(logger)
    print(logger)
    start()

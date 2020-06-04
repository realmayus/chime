from discord.ext import commands


# If activated: Uses the token-dev to minimize downtime while developing
start_dev = True

logger = None
version = "1.0.0"
prefix = "*" if start_dev else "$"

# TODO per-server prefix (see ?tag server prefix on d.py server)


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

    bot = commands.Bot(command_prefix=commands.when_mentioned_or(prefix), help_command=EmbedHelpCommand())
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
    from chime.misc.util import init_logger
    logger = init_logger()
    start()

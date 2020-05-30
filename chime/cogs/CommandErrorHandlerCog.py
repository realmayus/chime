from discord import DiscordException
from discord.ext import commands


class CommandErrorHandlerCog(commands.Cog, name="‎"):
    def __init__(self, bot):
        self.bot = bot

    # @commands.Cog.listener()
    # async def on_command_error(self, ctx, error):
    #     if isinstance(error, DiscordException):
    #         await ctx.send("🚫| " + str(error))
    #     else:
    #         await ctx.send("🚫| Oh no! An error has occurred:\n`%s`" % str(error))
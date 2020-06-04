import sys
import traceback

import discord
from discord.ext import commands

import chime.misc.BadRequestException
from chime.misc.StyledEmbed import StyledEmbed
from chime.misc.util import send_github_comment
from chime.main import auto_issues_issue


class CommandErrorHandlerCog(commands.Cog, name="‎"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send(embed=StyledEmbed(description="<:warning:717043607298637825>  This command can't be executed in DMs.'"))
            except discord.HTTPException:
                pass
        elif isinstance(error, discord.ext.commands.errors.CommandInvokeError) and isinstance(error.original, chime.misc.BadRequestException.BadRequestException):
            return await ctx.send(embed=StyledEmbed(description='<:warning:717043607298637825>  ' + str(error.original.text)))
        elif isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
            return await ctx.send(embed=StyledEmbed(description='<:warning:717043607298637825>  ' + str(error)))
        # elif isinstance(error, discord.ext.commands.errors.BadArgument):
        #     return await ctx.send(embed=StyledEmbed(description='<:warning:717043607298637825>  ' + str(error)))
        elif isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
            return await ctx.send(embed=StyledEmbed(description='<:warning:717043607298637825>  ' + str(error)))
        elif isinstance(error, discord.ext.commands.errors.CommandNotFound):
            return



        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

        send_github_comment(auto_issues_issue, f"Ignoring exception in command `{ctx.command}`: \n```{''.join(traceback.format_exception(type(error), error, error.__traceback__))}```")


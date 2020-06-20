import json
import sys
import traceback

import discord
import requests
from discord.ext import commands
from discord.ext.commands import Bot

import chime.misc.BadRequestException
from chime.misc.StyledEmbed import StyledEmbed
from chime.main import report_channel


class CommandErrorHandlerCog(commands.Cog, name="‎"):
    def __init__(self, bot):
        self.bot: Bot = bot

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
        elif isinstance(error, discord.ext.commands.errors.BadArgument):
            return await ctx.send(embed=StyledEmbed(description='<:warning:717043607298637825>  ' + str(error)))
        elif isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
            return await ctx.send(embed=StyledEmbed(description='<:warning:717043607298637825>  ' + str(error)))
        elif isinstance(error, discord.ext.commands.errors.CommandNotFound):
            self.bot.get_cog("StatsCog").add_non_existant_command(ctx.command.name)
            return


        await ctx.send(embed=StyledEmbed(description="<:warning:717043607298637825> Sorry, an unknown error occurred whilst executing this command. The error has been reported automatically. You can get support here: \nhttps://discord.gg/DGd8T53"))

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

        channel = await self.bot.fetch_channel(report_channel)
        error_embed = StyledEmbed(suppress_tips=True, title=f"<:warning:717043607298637825>  `{type(error)}`")
        error_embed.set_author(name="Unhandled Error")

        # upload to hastebin
        key = json.loads(requests.post('https://hasteb.in/documents', data='Ignoring Exception in command ' + str(ctx.command) + ":\n\n" + '\n'.join([line.strip('\n') for line in traceback.format_exception(type(error), error, error.__traceback__)])).text)["key"]

        # send to auto-reports channel in chime lounge
        error_embed.description = f"chime witnessed an [unhandled exception](https://hasteb.in/{key}) whilst executing command `{ctx.command}`:\n\n```" + '\n'.join([line.strip('\n') for line in traceback.format_exception(type(error), error, error.__traceback__, limit=1)]) + "```"


        await channel.send(embed=error_embed)

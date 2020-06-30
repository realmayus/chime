import asyncio
import datetime
import io
import random
import string
import time

import discord
from captcha.image import ImageCaptcha
from discord import RawReactionActionEvent, Message
from discord.ext import commands
from discord.ext.commands import Bot, BucketType

from chime.main import report_channel
from chime.misc.BadRequestException import BadRequestException
from chime.misc.StyledEmbed import StyledEmbed


class MiscCommandsCog(commands.Cog, name="Miscellaneous"):
    def __init__(self, bot):
        """A cog for miscellaneous commands which don't fit into the other cogs."""

        self.bot: Bot = bot
        self.imageCaptcha = ImageCaptcha(fonts=["./assets/Inter-Medium.ttf"])


    @commands.command(hidden=True)
    async def shutdown(self, ctx):
        """Shuts down the bot. Only available to the bot owner."""
        is_owner = await self.bot.is_owner(ctx.author)
        if is_owner:
            await ctx.message.add_reaction("👋")
            await self.bot.close()
            quit(0)
        else:
            raise BadRequestException("You don't have sufficient permissions to execute this command.")

    def get_captcha_file(self):
        solution = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        data = self.imageCaptcha.generate_image(solution)
        out = io.BytesIO()
        data.save(out, format='PNG')
        out.seek(0)
        file = discord.File(fp=out, filename="captcha.png")
        return solution, file


    @commands.cooldown(2, 10*60, BucketType.guild)
    @commands.command()
    async def feedback(self, ctx):
        """Gives you options to send feedback or to report bugs."""
        msg: Message = await ctx.send(embed=StyledEmbed(title="Feedback", description="Thanks for helping to improve chime! What's the problem? \n \n "
                                                                       u"1\N{variation selector-16}\N{combining enclosing keycap}" + "  I'd like to send feedback\n"
                                                                       u"2\N{variation selector-16}\N{combining enclosing keycap}" + "  I'd like to report an outage\n"
                                                                       u"3\N{variation selector-16}\N{combining enclosing keycap}" + "  I'd like to report a bug\n"))
        [await msg.add_reaction(u"%s\N{variation selector-16}\N{combining enclosing keycap}" % str(x + 1)) for x in range(3)]

        def check_reaction(reaction: RawReactionActionEvent):
            return reaction.member == ctx.author and isinstance(reaction.emoji.name, str) and (
                    (reaction.emoji.name[0].isdigit() and int(str(reaction.emoji.name)[0]) in range(4)) and reaction.message_id == msg.id)

        try:
            reaction: RawReactionActionEvent = await self.bot.wait_for('raw_reaction_add', timeout=20.0, check=check_reaction)
        except asyncio.TimeoutError:
            """Handle Timeout"""
        else:
            if str(reaction.emoji.name[0]).isdigit() and int(str(reaction.emoji.name)[0]) in range(4):
                selected_number = int(str(reaction.emoji.name[0]))
                what_to_do = None
                if selected_number == 1:
                    what_to_do = "Send Feedback"
                elif selected_number == 2:
                    what_to_do = "Report Outage"
                elif selected_number == 3:
                    what_to_do = "Report Bug"

                if selected_number == 2 or selected_number == 3:
                    await msg.edit(embed=StyledEmbed(title=what_to_do, description="Got it. Please describe the issue as precise as possible in your next message. Bonus points for steps to reproduce. Send `stop` to abort"))
                    await msg.clear_reactions()

                else:
                    await msg.edit(embed=StyledEmbed(title=what_to_do, description="Got it. Please describe your feedback in the next message you send. Send `stop` to abort"))
                    await msg.clear_reactions()

                try:
                    description: Message = await self.bot.wait_for('message', timeout=60.0, check=lambda m: m.channel == ctx.channel and m.author == ctx.author)
                except asyncio.TimeoutError:
                    await ctx.channel.send("Aborting feedback wizard because no answer was sent.")
                else:

                    if description.content == "stop":
                        await ctx.send("Ok.")
                        return

                    if selected_number == 2 or selected_number == 3:
                        if selected_number == 2:
                            """Urgent issue"""
                            captcha_solved = False
                            while not captcha_solved:
                                solution, file = self.get_captcha_file()
                                embed: StyledEmbed = StyledEmbed(title="Please solve the captcha.", description="Not case sensitive. To quit, enter `stop`, for a new captcha enter `new`")
                                await ctx.send(file=file, embed=embed)
                                try:
                                    captcha_sol: Message = await self.bot.wait_for('message', timeout=30.0, check=lambda ms: ms.channel == ctx.channel and ms.author == ctx.author)
                                    captcha_sol: str = captcha_sol.content
                                except asyncio.TimeoutError:
                                    await ctx.channel.send("Aborting feedback wizard because no captcha answer was sent.")
                                else:
                                    if captcha_sol.lower() == "stop":
                                        await ctx.send("Ok.")
                                        return

                                    if captcha_sol.lower().replace("o", "0").replace("7", "1").replace("8", "b") == solution.lower().replace("o", "0").replace("7", "1").replace("8", "b"):
                                        captcha_solved = True

                            report_channel_ = await self.bot.fetch_channel(report_channel)
                            error_embed = StyledEmbed(suppress_tips=True,
                                                      title=f"👥  Outage Report")
                            error_embed.description = "A user has submitted an outage report:\n\n" + description.content
                            error_embed.set_author(name="User Report")
                            await report_channel_.send("<@&718113149651255386>", embed=error_embed)
                            await ctx.channel.send(
                                "Thanks for the report and for making chime better! A developer will look into the issue as soon as possible.")
                        elif selected_number == 3:
                            report_channel_ = await self.bot.fetch_channel(report_channel)
                            error_embed = StyledEmbed(suppress_tips=True,
                                                      title=f"👥  Bug Report")
                            error_embed.description = "A user has submitted a bug report:\n\n" + description.content
                            error_embed.set_author(name="User Report")
                            await report_channel_.send(embed=error_embed)
                            await ctx.channel.send(
                                "Thanks for the report and for making chime better! A developer will look into the issue" + (
                                    "." if selected_number == 3 else " as soon as possible."))

                    elif selected_number == 1:
                        report_channel_ = await self.bot.fetch_channel(report_channel)
                        error_embed = StyledEmbed(suppress_tips=True,
                                                  title=f"👥  Feedback")
                        error_embed.description = "A user has submitted feedback:\n\n" + description.content
                        error_embed.set_author(name="User Feedback")
                        await report_channel_.send(embed=error_embed)
                        await ctx.channel.send("Thanks for the report and for making chime better! The feedback was sent to the developers.")

    @commands.command()
    async def stats(self, ctx):
        """Shows useful information about the current node your chime player is connected to. Useful for troubleshooting."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        node = player.node

        embed = StyledEmbed(title="chime stats")
        embed.description = f'Connected to {len(self.bot.wavelink.nodes)} node(s).\n' \
                            f'Best available node: **{self.bot.wavelink.get_best_node().__repr__()}**\n'
        embed.add_field(name="Stream count", value=f"{str(node.stats.playing_players)}")
        embed.add_field(name="Server Count", value=f"{len(self.bot.guilds)}")
        embed.add_field(name="Lavalink uptime", value=f"{str(datetime.timedelta(seconds=round(node.stats.uptime / 1000)))}")

        current_time = time.time()
        difference = int(round(current_time - self.bot.start_time))
        timestamp = str(datetime.timedelta(seconds=difference))
        embed.add_field(name="Bot uptime", value=f"{timestamp}")
        await ctx.send(embed=embed)


import asyncio
import sys
import traceback

from discord import RawReactionActionEvent, Message
from discord.ext import commands
from discord.ext.commands import Bot, BucketType

from chime.misc.StyledEmbed import StyledEmbed
from github import Github
from chime.main import auto_issues_issue, user_feedback_issue, user_issues_issue

from chime.misc.util import send_github_comment


class MiscCommandsCog(commands.Cog, name="Miscellaneous"):
    def __init__(self, bot):
        self.bot: Bot = bot

        self.github_client = Github("")

    @commands.cooldown(3, 10*60, BucketType.guild)
    @commands.command()
    async def feedback(self, ctx):
        """Gives you options to send feedback or to report bugs"""
        msg: Message = await ctx.send(embed=StyledEmbed(title="Feedback", description="Thanks for helping to improve chime! What's the problem? \n \n "
                                                                       u"1\N{variation selector-16}\N{combining enclosing keycap}" + "  I'd like to send feedback\n"
                                                                       u"2\N{variation selector-16}\N{combining enclosing keycap}" + "  I'd like to report an urgent issue\n"
                                                                       u"3\N{variation selector-16}\N{combining enclosing keycap}" + "  I'd like to report a bug\n"))
        [await msg.add_reaction(u"%s\N{variation selector-16}\N{combining enclosing keycap}" % str(x + 1)) for x in range(3)]

        def check_reaction(reaction: RawReactionActionEvent):
            return reaction.member == ctx.author and isinstance(reaction.emoji.name, str) and (
                    (reaction.emoji.name[0].isdigit() and int(str(reaction.emoji.name)[0]) in range(4)) and reaction.message_id == msg.id)

        try:
            reaction: RawReactionActionEvent = await self.bot.wait_for('raw_reaction_add', timeout=20.0, check=check_reaction)
            user = reaction.member
        except asyncio.TimeoutError:
            """Handle Timeout"""
        else:
            print("boop")
            if str(reaction.emoji.name[0]).isdigit() and int(str(reaction.emoji.name)[0]) in range(4):
                print("peepo")
                selected_number = int(str(reaction.emoji.name[0]))
                print(selected_number)
                what_to_do = None
                if selected_number == 1:
                    what_to_do = "Send Feedback"
                elif selected_number == 2:
                    what_to_do = "Report Urgent Issue"
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
                    if selected_number == 2 or selected_number == 3:
                        if selected_number == 2:
                            """Urgent issue, send via discord"""
                            from chime.main import urgent_notifications
                            for user_id in urgent_notifications:
                                try:
                                    user = await self.bot.fetch_user(user_id)
                                    await user.send(embed=StyledEmbed(title="Urgent issue", description=f"A user has reported an **urgent issue** with chime.\nIssue description: \n```{description.content}```"))
                                except Exception as e:
                                    print("Warning: Couldn't send urgent issue report to user with ID " + str(user_id))
                                    print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
                                    traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)

                            await ctx.channel.send(
                                "Thanks for the report and for making chime better! A developer will look into the issue" + (
                                    "." if selected_number == 3 else " as soon as possible."))
                        elif selected_number == 3:
                            send_github_comment(user_issues_issue, "User submitted issue with the following contents: \n\n" + description.content)
                            await ctx.channel.send(
                                "Thanks for the report and for making chime better! A developer will look into the issue" + (
                                    "." if selected_number == 3 else " as soon as possible."))
                    elif selected_number == 1:
                        send_github_comment(user_feedback_issue,
                                            "User submitted feedback with the following contents: \n\n" + description.content)
                        await ctx.channel.send("Thanks for the report and for making chime better! The feedback was sent to the developers.")




import asyncio
import math
from typing import List

from discord import Embed, Message, RawReactionActionEvent
from discord.ext.commands import Context, Bot

from chime.misc.StyledEmbed import StyledEmbed


class PagedListEmbed:
    def __init__(self, title: str, contents: List[str], ctx: Context, bot: Bot, show_per_page: int = 10):
        """A paged embed that shows a list!"""
        self.current_page = 0
        self.contents = contents
        self.count = 0
        self.ctx = ctx
        self.title = title
        self.last_msg = None
        self.show_per_page = show_per_page
        self.bot = bot

    def get(self) -> Embed:
        embed = StyledEmbed(suppress_tips=True, title=self.title + " (Page " + str(self.current_page + 1) + "/" + str(math.ceil(len(self.contents) / self.show_per_page)) + ")")

        desc = ""
        count = 1
        for track_index in range(len(self.contents)):
            try:
                track = self.contents[self.current_page * self.show_per_page + track_index]
                if count == self.show_per_page + 1:
                    break
                desc += str(track) + "\n"
                count += 1
            except IndexError:
                pass
        self.count = count
        embed.description = desc
        return embed

    def next(self) -> Embed:
        self.current_page += 1
        return self.get()

    def previous(self) -> Embed:
        self.current_page -= 1
        return self.get()

    def set_page(self, page) -> Embed:
        self.current_page = page
        return self.get()

    @staticmethod
    async def react_with_pagination_emoji(msg: Message):
        await msg.add_reaction("◀️")
        await msg.add_reaction("▶️")

    async def send(self, embed: Embed, msg_to_edit: Message = None) -> Message:
        if msg_to_edit is not None:
            await msg_to_edit.edit(embed=embed)
            msg = msg_to_edit
        else:
            msg = await self.ctx.send(embed=embed)

        self.bot.loop.create_task(self.react_with_pagination_emoji(msg=msg))

        self.last_msg = msg

        try:
            reaction: RawReactionActionEvent = await self.bot.wait_for('raw_reaction_add', check=self.check_reaction)
            user = reaction.member
        except asyncio.TimeoutError:
            pass
        else:
            if str(reaction.emoji.name) == "▶️":
                await msg.remove_reaction("▶️", user)
                if len(self.contents) - (self.current_page * self.show_per_page) > self.show_per_page:
                    await self.send(self.next(), msg)
            elif str(reaction.emoji.name) == "◀️":
                await msg.remove_reaction("◀️", user)
                if len(self.contents) + (self.current_page * self.show_per_page) > self.show_per_page:
                    await self.send(self.previous(), msg)
        return msg


    def check_reaction(self, reaction: RawReactionActionEvent):
        return reaction.member == self.ctx.author and isinstance(reaction.emoji.name, str) and ((str(reaction.emoji.name) == "▶️" and len(self.contents) - (self.current_page * self.show_per_page) > self.show_per_page) or (str(reaction.emoji.name) == "◀️" and self.current_page > 0 and len(self.contents) + (self.current_page * self.show_per_page) > self.show_per_page)) and reaction.message_id == self.last_msg.id

import asyncio
from typing import List

from discord import Embed, Message, RawReactionActionEvent
from discord.ext.commands import Bot, Context
from wavelink import Track

from chime.misc.StyledEmbed import StyledEmbed
from chime.misc.util import get_song_selector_embed_desc_for_current_page, react_with_pagination_emoji


class SongSelector:
    def __init__(self, results: List[Track], bot: Bot, success_callback_function, ctx: Context) -> None:
        self.current_page = 0
        self.results = results
        self.bot = bot
        self.count = 0
        self.success_callback_function = success_callback_function
        self.last_msg = None

        self.ctx = ctx

    def get(self) -> Embed:
        embed = StyledEmbed(title="Search results (Page " + str(self.current_page + 1) + ")")

        description, count = get_song_selector_embed_desc_for_current_page(self.current_page, self.results)
        self.count = count
        embed.description = description
        return embed

    def next(self) -> Embed:
        self.current_page += 1
        return self.get()

    def previous(self) -> Embed:
        self.current_page -= 1
        return self.get()

    async def send(self, embed: Embed, msg_to_edit: Message = None) -> None:
        if msg_to_edit is not None:
            await msg_to_edit.edit(embed=embed)
            msg = msg_to_edit
        else:
            msg = await self.ctx.send(embed=embed)

        reaction_task = self.bot.loop.create_task(react_with_pagination_emoji(msg=msg, show_next=True, count=self.count))
        self.last_msg = msg

        try:
            reaction: RawReactionActionEvent = await self.bot.wait_for('raw_reaction_add', timeout=20.0, check=self.check_reaction)
            user = reaction.member
        except asyncio.TimeoutError:
            await self.handle_timeout()
        else:
            if str(reaction.emoji.name[0]).isdigit() and int(str(reaction.emoji.name)[0]) in range(self.count):
                current_track = self.results[(self.current_page * 5) + int(str(reaction.emoji.name[0])) - 1]
                if reaction_task is not None:
                    reaction_task.cancel()
                await self.handle_success(current_track)

            elif str(reaction.emoji.name) == "▶️":
                await msg.remove_reaction("▶️", user)
                if len(self.results) - (self.current_page * 5) > 5:
                    await self.send(self.next(), msg)


    async def handle_success(self, track: Track):
        await self.success_callback_function(track, self.last_msg)

    async def handle_timeout(self):
        await self.last_msg.clear_reactions()
        expired_embed = StyledEmbed(title="Expired",
                                    description="This song selector has expired because no one selected a song.")
        await self.last_msg.edit(embed=expired_embed, delete_after=15.0)

    def check_reaction(self, reaction: RawReactionActionEvent):
        return reaction.member == self.ctx.author and isinstance(reaction.emoji.name, str) and (
                    (reaction.emoji.name[0].isdigit() and int(str(reaction.emoji.name)[0]) in range(self.count)) or (
                        str(reaction.emoji.name) == "▶️" and len(self.results) - (
                            self.current_page * 5) > 5)) and reaction.message_id == self.last_msg.id

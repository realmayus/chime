import asyncio
import datetime
from typing import List, Union

import discord
import humanize as humanize
import wavelink
from discord import Message, Reaction, User, RawReactionActionEvent, TextChannel, Client
from discord.ext import commands
from discord.ext.commands import Context, Bot
from wavelink import Track

from chime.misc.BadRequestException import BadRequestException
from chime.misc.MusicController import MusicController
from chime.misc.util import check_if_url, get_friendly_time_delta, get_song_selector_embed_desc_for_current_page, \
    react_with_pagination_emoji, get_currently_playing_embed
from chime.main import prefix
from chime.misc.StyledEmbed import StyledEmbed


class MusicCommandsCog(commands.Cog, name="Music Commands"):
    def __init__(self, bot):
        self.bot: Bot = bot
        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(bot=self.bot)
        self.bot.loop.create_task(self.start_nodes())

        self.controllers = {}


    async def start_nodes(self):
        await self.bot.wait_until_ready()
        # Initiate our nodes. For this example we will use one server.
        # Region should be a discord.py guild.region e.g sydney or us_central (Though this is not technically required)
        node: wavelink.Node = await self.bot.wavelink.initiate_node(host='0.0.0.0',
                                                     port=2333,
                                                     rest_uri='http://0.0.0.0:2333',
                                                     password='youshallnotpass',
                                                     identifier='TEST',
                                                     region='us_central')
        node.set_hook(self.on_event_hook)

    async def cog_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def on_event_hook(self, event):
        if isinstance(event, (wavelink.TrackEnd, wavelink.TrackException)):
            controller = self.get_controller(event.player)
            controller.next.set()

    def get_controller(self, value: Union[commands.Context, wavelink.Player]):
        if isinstance(value, commands.Context):
            gid = value.guild.id
        else:
            gid = value.guild_id

        try:
            controller = self.controllers[gid]
        except KeyError:
            controller = MusicController(self.bot, gid)
            self.controllers[gid] = controller
        return controller

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        """Joins the channel you're currently in."""
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise BadRequestException('No channel to join. Please join one.')
            except Exception as e:
                print(type(e))
                print(str(e))

        player = self.bot.wavelink.get_player(ctx.guild.id)
        try:
            await player.connect(channel.id)
        except Exception as e:
            print(type(e))
            print(str(e))

        controller = self.get_controller(ctx)
        controller.channel = ctx.channel

    async def play_(self, ctx, query: str, current_page=0, msg_to_edit: Message = None):
        player = self.bot.wavelink.get_player(ctx.guild.id)
        tracks = False
        if query == "^":
            x = await ctx.channel.history(limit=2).flatten()
            query = x[1].content
            print(query)
        if check_if_url(query):  # user provided an URL, play that
            if not player.is_connected:
                await ctx.invoke(self.join)
            tracks: List[Track] = await self.bot.wavelink.get_tracks(query)
            controller = self.get_controller(ctx)
            await ctx.message.add_reaction("<:OK:716230152643674132>")
            return await controller.queue.put(tracks[0])
        else:  # user didn't provide an URL so search for the entered term
            i = 0
            tracks = False
            while not tracks and i < 5:  # try to find song 5 times
                tracks: List[Track] = await self.bot.wavelink.get_tracks(f'ytsearch:{query}')
                i += 1
        if not tracks:
            raise BadRequestException('Could not find any songs with that query.')

        embed = StyledEmbed(title="Search results (Page " + str(current_page + 1) + ")")

        description, count = get_song_selector_embed_desc_for_current_page(current_page, tracks)
        embed.description = description

        if msg_to_edit is not None:
            await msg_to_edit.edit(embed=embed)
            msg = msg_to_edit
        else:
            msg: Message = await ctx.send(embed=embed)

        reaction_task = None
        if current_page == 0:
            reaction_task = self.bot.loop.create_task(react_with_pagination_emoji(msg=msg, show_next=(len(tracks) - (current_page * 5) > 5), count=count))

        def check_reaction(reaction_: RawReactionActionEvent):
            return reaction_.member == ctx.author and isinstance(reaction_.emoji.name, str) and ((reaction_.emoji.name[0].isdigit() and int(str(reaction_.emoji.name)[0]) in range(count)) or (str(reaction_.emoji.name) == "▶️" and len(tracks) - (current_page * 5) > 5)) and reaction_.message_id == msg.id

        try:
            reaction: Reaction
            user: User
            reaction: RawReactionActionEvent = await self.bot.wait_for('raw_reaction_add', timeout=20.0, check=check_reaction)
            user = reaction.member
        except asyncio.TimeoutError:
            await msg.clear_reactions()
            expired_embed = StyledEmbed(title="Expired",
                                          description="This song selector has expired because no one selected a song.")
            await msg.edit(embed=expired_embed, delete_after=15.0)
        else:
            if str(reaction.emoji.name[0]).isdigit() and int(str(reaction.emoji.name)[0]) in range(count):
                current_track = tracks[(current_page * 5) + int(str(reaction.emoji.name[0])) - 1]
                if not player.is_connected:
                    await ctx.invoke(self.join)

                controller = self.get_controller(ctx)
                await controller.queue.put(current_track)
                if reaction_task is not None:
                    reaction_task.cancel()
                await msg.clear_reactions()
                await msg.edit(embed=StyledEmbed(description=f"**Added** {current_track} **to queue.**"), delete_after=10.0)



            elif str(reaction.emoji.name) == "▶️":
                await msg.remove_reaction("▶️", user)
                if len(tracks) - (current_page * 5) > 5:
                    await self.play_(ctx, query, current_page + 1, msg)
            else:
                raise NotImplementedError

    @commands.command()
    async def play(self, ctx, *, query: str):
        """Searches for the search term on youtube or plays from the given URL. When `liked` is passed as the only argument, the bot plays your liked songs"""
        await self.play_(ctx, query)

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current track"""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if player.is_playing and not player.is_paused:
            await player.set_pause(True)
            await ctx.send("Paused!")
        else:
            raise BadRequestException("I am currently not playing any track!")

    @commands.command()
    async def resume(self, ctx):
        """Resumes current track."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if player.is_playing and player.is_paused:
            await player.set_pause(False)
            await ctx.send("Resumed!")
        else:
            raise BadRequestException("Currently, no track is loaded/paused")

    @commands.command()
    async def speed(self, ctx):
        """Changes the speed. Valid values: `25%` - `200%`"""
        await ctx.send("This command is not implemented yet.")

    @commands.command()
    async def volume(self, ctx: Context, volume: int):
        """Sets the volume of the current track. Valid values: `3` - `100`. Default is 40. For bass-boosting see """ + prefix + """boost"""
        if volume > 100 or volume < 3:
            raise BadRequestException("Volume has to be between 3 and 100!")

        player = self.bot.wavelink.get_player(ctx.guild.id)
        await player.set_volume(volume)
        await ctx.message.add_reaction("<:OK:716230152643674132>")

    @commands.command()
    async def boost(self, ctx):
        """Boosts the bass of the current track."""
        await ctx.send("This command is not implemented yet.")

    @commands.command()
    async def leave(self, ctx):
        """Leaves the current channel."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        try:
            del self.controllers[ctx.guild.id]
        except Exception:
            await player.disconnect()
            raise BadRequestException("I am not connected to a voice channel!")

        await player.disconnect()
        await ctx.message.add_reaction("👋")


    @commands.command()
    async def stop(self, ctx):
        """Stops the current track."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        try:
            await player.stop()
        except Exception:
            # await player.disconnect()
            raise BadRequestException("There is nothing to stop!")
        await ctx.message.add_reaction("<:OK:716230152643674132>")


    @commands.command()
    async def current(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.current:
            raise BadRequestException('I am currently not playing anything!')

        controller = self.get_controller(ctx)
        await controller.now_playing.delete()

        controller.now_playing = await ctx.send(f'Now playing: `{player.current}`')

    @commands.command()
    async def loop(self, ctx):
        """Sets the looping mode. Valid values: `off`, `on`, `track`, `queue`"""
        pass

    @commands.command(name="queue")
    async def queue_(self, ctx):
        """Shows the queue."""
        controller = self.get_controller(ctx)
        await ctx.send(embed=StyledEmbed(title="Queue", description=("\n".join([("**" + song.title + "**") for song in controller.queue._queue])) if len(controller.queue._queue) > 0 else "<:warning:717043607298637825>  Queue is empty!"))

    @commands.command()
    async def clear(self, ctx):
        """Clears the queue."""


    @commands.command()
    async def skip(self, ctx):
        """Skips the current song."""
        player = self.bot.wavelink.get_player(ctx.guild.id)

        if not player.is_playing:
            raise BadRequestException('I am currently not playing anything!')

        await ctx.send('Skipping the song!', delete_after=15)
        await player.stop()




from typing import List, Union

import discord
import wavelink
from discord import Message
from discord.ext import commands
from discord.ext.commands import Context, Bot
from wavelink import Track, Player, TrackPlaylist

from chime.main import prefix
from chime.misc.BadRequestException import BadRequestException
from chime.misc.MusicController import MusicController
from chime.misc.PagedListEmbed import PagedListEmbed
from chime.misc.SongSelector import SongSelector
from chime.misc.StyledEmbed import StyledEmbed
from chime.misc.util import check_if_url


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
        await self.join_(ctx, channel, False)

    async def join_(self, ctx, channel=None, suppress_warning=False):
        if not channel:
            channel = ctx.author.voice.channel
            if channel is None:
                raise BadRequestException('No channel to join. Please join one.')
        player: Player = self.bot.wavelink.get_player(ctx.guild.id)
        if player.channel_id == channel.id:
            if not suppress_warning:
                raise BadRequestException('I\'m already in this channel :)')
        else:
            await player.connect(channel.id)

        controller = self.get_controller(ctx)
        controller.channel = ctx.channel

    async def play_(self, ctx, query: str, current_page=0, msg_to_edit: Message = None):
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if query == "^":
            x = await ctx.channel.history(limit=2).flatten()
            query = x[1].content
            print(query)
        if check_if_url(query):  # user provided an URL, play that
            if not player.is_connected:
                await ctx.invoke(self.join)
            tracks = await self.bot.wavelink.get_tracks(query)

            if isinstance(tracks, TrackPlaylist):
                tracks = tracks.tracks
                await ctx.send(embed=StyledEmbed(description=f"**Added** {len(tracks)} **tracks to queue.**"))
            else:
                await ctx.send(embed=StyledEmbed(description=f"**Added** {tracks[0]} **to queue.**"))

            controller = self.get_controller(ctx)
            for track in tracks:
                controller.queue.append(track)
            return
        else:  # user didn't provide an URL so search for the entered term
            i = 0
            tracks = False
            while not tracks and i < 5:  # try to find song 5 times
                print("searching :peepodetective:")
                tracks: List[Track] = await self.bot.wavelink.get_tracks(f'ytsearch:{query}')
                i += 1
        if not tracks:
            raise BadRequestException('Could not find any songs with that query.')

        async def success_callback(track, last_msg: Message):
            await last_msg.clear_reactions()
            await last_msg.edit(embed=StyledEmbed(description=f"**Added** {track} **to queue.**"), delete_after=10.0)
            if not player.is_connected:
                await ctx.invoke(self.join)

            controller_ = self.get_controller(ctx)
            controller_.queue.append(track)

        songselector = SongSelector(tracks, self.bot, success_callback, ctx)
        await songselector.send(songselector.get())

    @commands.command()
    async def play(self, ctx, *, query: str):
        """Searches for the search term on youtube or plays from the given URL. When `liked` is passed as the only argument, the bot plays your liked songs"""
        await self.play_(ctx, query)

    @commands.command(aliases=["stop"])
    async def pause(self, ctx):
        """Pauses the current track"""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if player.is_playing and not player.is_paused:
            await player.set_pause(True)
            await ctx.send(embed=StyledEmbed(description=f"Stopped song! Use `{prefix}resume` to resume it."),
                           delete_after=20.0)
        else:
            raise BadRequestException("I am currently not playing any track!")

    @commands.command()
    async def resume(self, ctx):
        """Resumes current track."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if player.is_playing and player.is_paused:
            await player.set_pause(False)
            await ctx.message.add_reaction("<:OK:716230152643674132>")
        else:
            raise BadRequestException("Currently, no track is loaded/paused")

    @commands.command()
    async def speed(self, ctx):
        """Changes the speed. Valid values: `25%` - `200%`"""
        await ctx.send("This command is not implemented yet.")

    @commands.command(aliases=["vol"])
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

    @commands.command(aliases=["quit"])
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

    @commands.command(aliases=["nowplaying", "now", "playing", "song"])
    async def current(self, ctx):
        player: Player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_playing:
            raise BadRequestException('I am currently not playing anything!')

        controller = self.get_controller(ctx)
        await controller.now_playing.delete()

        controller.now_playing_msg = await ctx.send(f'Now playing: `{player.current}`')

    @commands.command(aliases=["repeat"])
    async def loop(self, ctx, looping_mode):
        """Sets the looping mode. Valid values: `off`, `track`, `queue`"""
        controller = self.get_controller(ctx)

        if looping_mode in ["off", "track", "queue"]:
            if looping_mode == "off":
                controller.looping_mode = 0
            elif looping_mode == "track":
                controller.looping_mode = 1
            elif looping_mode == "queue":
                controller.looping_mode = 2
            await ctx.message.add_reaction("<:OK:716230152643674132>")
        else:
            raise BadRequestException("Invalid value for this command. Valid values: `off`, `track`, `queue`")

    @commands.command(name="queue")
    async def queue_(self, ctx):
        """Shows the queue."""
        controller = self.get_controller(ctx)

        pagedlist = PagedListEmbed("Queue Current Index: " + str(controller.current_index), [str(index + 1) + ".   **" + song.title + "**" if index == controller.current_index - 1 else str(index + 1) + ".   " + song.title for index, song in enumerate(controller.queue)], ctx, self.bot)
        await pagedlist.send(pagedlist.get())

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

    @commands.command(aliases=["fastforward", "ff"])
    async def seek(self, ctx, seconds: int = None):
        """Fast-forwards the 15 seconds or a given amount of seconds in the current song."""

    @commands.command()
    async def jump(self, ctx, position):
        """Jumps to the given position in the current queue/playlist."""

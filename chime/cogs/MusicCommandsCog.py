from typing import Union

import discord
import wavelink
from discord import Message, VoiceState, Member, VoiceChannel
from discord.ext import commands
from discord.ext.commands import Context, Bot
from wavelink import Player, TrackPlaylist

from chime.main import prefix
from chime.misc.BadRequestException import BadRequestException
from chime.misc.MusicController import MusicController
from chime.misc.PagedListEmbed import PagedListEmbed
from chime.misc.StyledEmbed import StyledEmbed
from chime.misc.util import get_currently_playing_embed, search_song


class MusicCommandsCog(commands.Cog, name="Music Commands"):
    def __init__(self, bot):
        """All the core-features of chime, i.e. the music features."""

        self.bot: Bot = bot
        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(bot=self.bot)
        self.bot.loop.create_task(self.start_nodes())

        self.bot.controllers = {}


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
            raise commands.NoPrivateMessage  # Send warning when user tries to execute command in DMs
        return True

    async def on_event_hook(self, event):
        """Catch wavelink events here"""
        if isinstance(event,
                      (wavelink.TrackEnd, wavelink.TrackException)):  # When track has ended or an exception occurred
            controller = self.get_controller(event.player)
            controller.next.set()  # Set the internal flag on the asyncio event

    def get_controller(self, value: Union[commands.Context, wavelink.Player]):
        """Return the given guild's instance of the MusicController"""
        if isinstance(value, commands.Context):
            gid = value.guild.id
        else:
            gid = value.guild_id
        try:
            controller = self.bot.controllers[gid]
        except KeyError:
            controller = MusicController(self.bot, gid)
            self.bot.controllers[gid] = controller
        return controller

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        self.bot.get_cog("StatsCog").add_executed_command(ctx.command.name)

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        """Joins the channel you're currently in."""
        await self.join_(ctx, channel, False)

    async def join_(self, ctx, channel=None, suppress_warning=False):
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise BadRequestException('No channel to join. Please join one.')
        player: Player = self.bot.wavelink.get_player(ctx.guild.id)
        if player.channel_id == channel.id:
            if not suppress_warning:
                raise BadRequestException('I\'m already in this channel :)')
        else:
            await player.connect(channel.id)

        controller = self.get_controller(ctx)
        controller.channel = ctx.channel

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, query: str):
        """Searches for the search term on youtube or plays from the given URL. When `liked` is passed as the only argument, the bot plays your liked songs"""
        player: Player = self.bot.wavelink.get_player(ctx.guild.id)

        async def success_callback(track_, last_msg: Message):
            await last_msg.clear_reactions()
            await last_msg.edit(embed=StyledEmbed(description=f"**Added** {track_} **to queue.**"), delete_after=10.0)
            if not player.is_connected:
                await ctx.invoke(self.join)  # Join channel if not connected
            self.get_controller(ctx).queue.append(track_)

        async def success_callback_url(tracks):
            if not player.is_connected:
                await ctx.invoke(self.join)  # Join channel if not connected

            if isinstance(tracks, TrackPlaylist):
                tracks = tracks.tracks
                await ctx.send(embed=StyledEmbed(description=f"**Added** {len(tracks)} **tracks to queue.**"))
            else:
                try:
                    await ctx.send(embed=StyledEmbed(description=f"**Added** {tracks[0]} **to queue.**"))
                except TypeError:
                    raise BadRequestException("Couldn't add this item to the queue!")
            for track in tracks:
                self.get_controller(ctx).queue.append(track)

        await search_song(query, ctx, self.bot, success_callback, success_callback_url)

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

    @commands.command(aliases=["vol"], help=f"Sets the volume of the current track. Valid values: `3` - `200`. Default is 40.")
    async def volume(self, ctx: Context, volume: int):
        if volume > 200 or volume < 3:
            raise BadRequestException("Volume has to be between 3 and 200!")

        player = self.bot.wavelink.get_player(ctx.guild.id)
        await player.set_volume(volume)
        await ctx.message.add_reaction("<:OK:716230152643674132>")

    @commands.command(aliases=["quit", "exit", "disconnect"])
    async def leave(self, ctx):
        """Leaves the current channel."""
        player: Player = self.bot.wavelink.get_player(ctx.guild.id)

        try:
            del self.bot.controllers[ctx.guild.id]
        except Exception as e:
            print(e)
        await player.stop()
        await player.disconnect()

        await ctx.message.add_reaction("👋")

    @commands.command(aliases=["nowplaying", "now", "current", "song"])
    async def playing(self, ctx):
        """Shows the song that's currently playing."""
        player: Player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_playing:
            raise BadRequestException('I am currently not playing anything!')

        await ctx.send(embed=get_currently_playing_embed(player.current, player.position))

    @commands.command(aliases=["repeat", "lo", "lp"])
    async def loop(self, ctx, looping_mode):
        """Sets the looping mode. Valid values: `off`, `track`, `queue`"""
        controller = self.get_controller(ctx)

        if looping_mode in ["off", "track", "queue"]:
            controller.prev_looping_mode = controller.looping_mode
            if looping_mode == "off":
                controller.looping_mode = 0
            elif looping_mode == "track":
                controller.looping_mode = 1
            elif looping_mode == "queue":
                controller.looping_mode = 2
            elif looping_mode == "shuffle":
                controller.looping_mode = 3
            await ctx.message.add_reaction("<:OK:716230152643674132>")
        else:
            raise BadRequestException("Invalid value for this command. Valid values: `off`, `track`, `queue`")

    @commands.command(name="queue", aliases=["q"])
    async def queue_(self, ctx):
        """Shows the queue."""
        controller = self.get_controller(ctx)
        if len(controller.queue) == 0:
            raise BadRequestException("Queue is empty!")
        pagedlist = PagedListEmbed("Queue", [
            str(index + 1) + ".   **" + song.title + "**" if index == controller.current_index - 1 else str(
                index + 1) + ".   " + song.title for index, song in enumerate(controller.queue)], ctx, self.bot)
        await pagedlist.send(pagedlist.get())

    @commands.command(aliases=["cl"])
    async def clear(self, ctx):
        """Clears the queue."""
        controller = self.get_controller(ctx)
        controller.queue = []
        controller.current_index = 0
        await ctx.message.add_reaction("<:OK:716230152643674132>")

    @commands.command(aliases=["s"])
    async def skip(self, ctx):
        """Skips the current song."""
        player: Player = self.bot.wavelink.get_player(ctx.guild.id)
        controller = self.get_controller(ctx)

        if not player.is_playing:
            raise BadRequestException('I am currently not playing anything!')
        await player.stop()
        await ctx.message.add_reaction("<:OK:716230152643674132>")
        if controller.looping_mode == 1:
            await ctx.send("You are currently on loop mode: track. Skipping will just replay the song - turn looping off to play the next song in the queue.", delete_after=15)

    @commands.command(aliases=["fastforward", "ff"])
    async def seek(self, ctx, seconds: int = 15):
        """Fast-forwards 15 seconds or a given amount of seconds in the current song."""
        player: Player = self.bot.wavelink.get_player(ctx.guild.id)

        if not player.is_playing:
            raise BadRequestException('I am currently not playing anything!')
        if player.current.is_stream:
            raise BadRequestException('You can\'t use seek in a stream!')

        await player.seek(player.position + seconds * 1000)
        await ctx.message.add_reaction("<:OK:716230152643674132>")

    @commands.command(aliases=["ffto"])
    async def seekto(self, ctx, seconds: int):
        """Fast-forwards to the given amount of seconds in the current song."""
        player: Player = self.bot.wavelink.get_player(ctx.guild.id)

        if not player.is_playing:
            raise BadRequestException('I am currently not playing anything!')
        if seconds < 0:
            raise BadRequestException(
                'I can\'t start that song from the past, fam! Enter a value equal to or greater than 0.')
        if player.current.is_stream:
            raise BadRequestException('You can\'t use seekto in a stream!')

        await player.seek(seconds * 1000)
        await ctx.message.add_reaction("<:OK:716230152643674132>")

    @commands.command(aliases=["jump", "skipto"])
    async def jumpto(self, ctx: Context, position: int):
        """Jumps to the given position in the queue."""
        controller: MusicController = self.get_controller(ctx)
        player: Player = self.bot.wavelink.get_player(ctx.guild.id)
        if position <= 0:
            raise BadRequestException("Invalid value. Try something greater.")

        try:
            _ = controller.queue[position - 1]  # Try to get the song at the position
            controller.current_index = position - 1  # If that worked, set the current index to the new position
            if player.is_playing:
                await player.seek(player.current.length)  # If a song is currently playing, skip that!
            await ctx.message.add_reaction("<:OK:716230152643674132>")  # gib ok
        except IndexError:
            raise BadRequestException(
                "The index I should jump to isn't part of the queue. Try to enter something lower.")


    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        player: Player = self.bot.wavelink.get_player(member.guild.id)
        controller: MusicController = self.get_controller(player)
        if not before.channel:
            return
        if before.channel.id == player.channel_id:
            """It's actually the bot's channel!"""
            if not after.channel or after.channel != before.channel:
                """Member has left or switched the channel"""
                channel: VoiceChannel = before.channel
                if len(channel.members) <= 1:
                    embed = StyledEmbed(suppress_tips=True, description="**I left the channel due to inactivity.**")
                    embed.set_footer(text="Please consider to donate, you'll get some nifty features!")
                    await controller.channel.send(embed=embed)
                    if controller.now_playing_msg:
                        await controller.now_playing_msg.delete()
                    try:
                        controller.task.cancel()
                        del self.bot.controllers[member.guild.id]
                        del controller
                    except Exception as e:
                        print(e)
                    await player.stop()
                    await player.disconnect()

import base64
import wavelink
from typing import Union
from discord import Message
from discord.ext import commands
from discord.ext.commands import Context
from wavelink import Player, TrackPlaylist, BuildTrackError, Track
from chime.main import prefix
from chime.misc.BadRequestException import BadRequestException
from chime.misc.CustomCommand import custom_command
from chime.misc.Database import Database
from chime.misc.MusicController import MusicController
from chime.misc.PagedListEmbed import PagedListEmbed
from chime.misc.StyledEmbed import StyledEmbed
from chime.util import search_song


class PersonalPlaylistsCog(commands.Cog, name="Personal Playlists"):
    def __init__(self, bot, db):
        """A cog that handles interfacing with the database and the creation, population and editing of personal playlists."""

        self.bot = bot
        # self.db = db
        self.database = Database(db)

    @commands.command()
    async def playlists(self, ctx: Context):
        """Shows a list of all your playlists. Alias of `""" + prefix + """playlist list`"""
        playlists = self.database.get_all_playlists(ctx.author.id)
        await ctx.send(embed=StyledEmbed(title="Your playlists", description=f"use the `{prefix}playlist` commands for adding songs to a playlist, creating playlists, viewing the playlist's contents etc. \n\n" + "\n".join([f"•  **{playlist['name']}**" for playlist in playlists])))

    @custom_command(
        usage="playlist [action] <playlist_name>",
        aliases=["pl", "l"],
        available_args=[
            {"type": "[action]", "args":
                [
                    {"name": "list", "desc": "Lists all your playlists."},
                    {"name": "create", "desc": "Creates a playlist."},
                    {"name": "add", "desc": "Adds a song to the given playlist."},
                    {"name": "show | view", "desc": "Lists the songs in your playlist."},
                    {"name": "play", "desc": "Plays the playlist."},
                    {"name": "share", "desc": "Gives you a link so that you can share your beautiful playlist!"}
                ]
             }],
        examples=[
            {
                "ex": "pl create Favorites",
                "desc": "Creates a playlist called 'Favorites'"
            },
            {
                "ex": "pl create \"chill hop\"",
                "desc": "Creates a playlist called 'chill hop'. Note the quotation marks that we need because the name contains a space."
            },
            {
                "ex": "pl play favorites",
                "desc": "Adds all the songs in the playlist to the queue and plays them."
            },
            {
                "ex": "pl show favorites",
                "desc": "Shows the contents of the playlist 'favorites'."
            },
            {
                "ex": "pl add favorites oh my dayum",
                "desc": "Adds the song 'oh my dayum' to the playlist 'favorites'."
            },
            {
                "ex": "pl list",
                "desc": "Lists all your playlists."
            },
            {
                "ex": "pl share chillhop",
                "desc": "Displays a sharable link for the playlist 'chillhop'."
            }
        ]
    )
    async def playlist(self, ctx: Context, action: str, playlist: str = None, *, additional_args=None):
        """Manage all your personal playlists. You can also manage them on [chime's web app](https://chime.realmayus.xyz)"""
        if action == "create":
            if not additional_args:  # if the playlist name contained spaces, the individual parts would be in additional_args
                self.database.create_playlist(ctx.author.id, playlist)
                await ctx.message.add_reaction("<:ok:746377326245445653>")
            else:
                raise BadRequestException("If you want spaces in your playlist's name, you have to wrap it in quotation marks!")

        elif action == "show" or action == "view":
            if playlist is not None:
                contents = self.database.get_playlist_contents(ctx.author.id, playlist)
                if len(contents) == 0:
                    raise BadRequestException("Playlist is empty!")

                embed = PagedListEmbed(f"Contents of `{playlist}`", [f"{i + 1}.  {song['title']}" for i, song in enumerate(contents)], ctx, self.bot)
                await embed.send(embed.get())
            else:
                raise BadRequestException("Please enter a playlist name!")

        elif action == "play":
            if playlist is not None:
                contents = self.database.get_playlist_contents(ctx.author.id, playlist)
                await self.join_channel(ctx)
                if len(contents) == 0:
                    raise BadRequestException("Playlist is empty!")

                index = 0
                failed = 0
                for index, song_data_raw in enumerate(contents):
                    try:
                        track = await self.bot.wavelink.build_track(song_data_raw["data"])
                        controller = self.get_controller(ctx)
                        controller.queue.append(track)
                    except BuildTrackError:
                        failed += 1
                        print("Failed to reconstruct track with data " + song_data_raw["data"])
                await ctx.send(embed=StyledEmbed(description=f"**Added** {index + 1} **tracks to queue**."))
                if failed > 0:
                    raise BadRequestException(f"**Failed to add** {failed} **track(s)**!")
            else:
                raise BadRequestException("Please enter a playlist name!")

        elif action == "list":
            await ctx.invoke(self.playlists)

        elif action == "add":
            tracks_to_add = []
            if playlist is None:
                raise BadRequestException("Please enter a playlist name!")

            async def success_callback(track_, last_msg: Message):
                await last_msg.clear_reactions()
                await last_msg.edit(embed=StyledEmbed(description=f"**Added** {track_} **to playlist {playlist}.**"),
                                    delete_after=10.0)
                tracks_to_add.append(track_)

            async def success_callback_url(tracks):
                nonlocal tracks_to_add
                if isinstance(tracks, TrackPlaylist):
                    tracks = tracks.tracks
                    await ctx.send(
                        embed=StyledEmbed(description=f"**Added** {len(tracks)} **tracks to playlist {playlist}.**"),
                        delete_after=10.0)
                else:
                    try:
                        await ctx.send(
                            embed=StyledEmbed(description=f"**Added** {tracks[0]} **to playlist {playlist}.**"),
                            delete_after=10.0)
                    except TypeError:
                        raise BadRequestException("Couldn't add this item to the queue!")
                tracks_to_add = tracks

            if not additional_args:
                raise BadRequestException("You have to provide either a search term or a URL!")

            await search_song(additional_args, ctx, self.bot, success_callback, success_callback_url)

            if len(tracks_to_add) > 0:
                self.database.add_to_playlist(ctx.author.id, playlist, tracks_to_add)
                await ctx.message.add_reaction("<:ok:746377326245445653>")
            else:
                raise BadRequestException("No track selected!")
        elif action == "share":
            if playlist is None:
                raise BadRequestException("Please enter a playlist name!")
            playlist_id = self.database.raise_if_not_exists(ctx.author.id, playlist)
            message = f"{ctx.author.id}:{playlist_id}:{playlist}:{ctx.author.name}"
            message_bytes = message.encode("utf8")
            base64_bytes = base64.b64encode(message_bytes)
            base64_message = base64_bytes.decode("ascii")
            await ctx.send(embed=StyledEmbed(title="Share this link",
                                             description=f"https://chime.realmayus.xyz/view/{base64_message}"))
        elif action == "delete":
            raise BadRequestException("This feature has not been implemented yet.")
        else:
            raise BadRequestException("This action does not exist. Valid actions are: `create`, `list`, `add`, `show`, `play`, `delete` and `share`.")

    @commands.command()
    async def like(self, ctx):
        """Adds the current song to your 'Liked' playlist"""
        current_track: Track = self.get_controller(ctx).current_track
        if not current_track:
            raise BadRequestException("No track is currently playling!")

        self.database.create_if_non_existant(ctx.author.id, "Liked")
        self.database.add_to_playlist(ctx.author.id, "Liked", [current_track])
        await ctx.message.add_reaction("<:ok:746377326245445653>")

    @commands.command()
    async def unlike(self, ctx):
        """Removes the current song from your 'Liked' playlist"""
        current_track: Track = self.get_controller(ctx).current_track
        if not current_track:
            raise BadRequestException("No track is currently playing!")
        self.database.remove_from_playlist(ctx.author.id, "Liked", [current_track])
        await ctx.message.add_reaction("<:ok:746377326245445653>")

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

    async def join_channel(self, ctx):
        player: Player = self.bot.wavelink.get_player(ctx.guild.id)
        try:
            if player.channel_id != ctx.author.voice.channel.id:
                await player.connect(ctx.author.voice.channel.id)
            controller = self.get_controller(ctx)
            controller.channel = ctx.channel
        except AttributeError:
            raise BadRequestException("You are not connected to a voice channel.")

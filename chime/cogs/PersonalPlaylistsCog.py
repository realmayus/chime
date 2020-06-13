import uuid
from typing import List, Union

import google
import wavelink
from discord import Message
from discord.ext import commands
from discord.ext.commands import Context
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import Client, DocumentReference
from wavelink import Player, TrackPlaylist, BuildTrackError, Track

from chime.main import prefix
from chime.misc.BadRequestException import BadRequestException
from chime.misc.MusicController import MusicController
from chime.misc.PagedListEmbed import PagedListEmbed
from chime.misc.StyledEmbed import StyledEmbed
from chime.misc.util import check_if_playlist_exists, search_song


class PersonalPlaylistsCog(commands.Cog, name="Personal Playlists"):
    def __init__(self, bot):
        self.bot = bot
        cred = credentials.Certificate("./secret/firebase_creds.json")
        firebase_admin.initialize_app(cred)
        self.db: Client = firestore.client()

    @commands.command()
    async def playlists(self, ctx: Context):
        """Shows a list of all your playlists"""
        profile_ref: DocumentReference = self.db.collection(str(ctx.author.id)).document("profile")
        profile = profile_ref.get()
        profile_data: dict = profile.to_dict()
        if "playlists" in profile_data.keys() and len(profile_data["playlists"]) > 0:
            await ctx.send(embed=StyledEmbed(title="Your playlists", description=f"use the `{prefix}playlist` commands for adding songs to a playlist, creating playlists, viewing the playlist's contents etc. \n\n" + "\n".join([f"•  **{playlist['name']}**" for playlist in profile_data['playlists']])))
        else:
            raise BadRequestException(f"You currently don't have any playlists. Create one with `{prefix}playlist create <name>`.")

    @commands.command(usage="playlist [action] [playlist_name]")
    async def playlist(self, ctx: Context, action: str, playlist: str, *, additional_args=None):
        """Provide the argument 'create' to create a playlist. Provide 'add' and a search term/URL to add a track to a playlsit Provide the argument 'show' to show the playlist's contents. Provide argument 'play' to play the playlist. Provide argument 'delete' to delete playlist. Provide argument 'link' to get a link to the playlist."""
        if action == "create":
            if not additional_args:  # if the playlist name contained spaces, the individual parts would be in additional_args
                profile: DocumentReference = self.db.collection(str(ctx.author.id)).document("profile")
                if not check_if_playlist_exists(profile, playlist):
                    with ctx.typing():
                        playlist_id = str(uuid.uuid4())
                        playlist_doc: DocumentReference = self.db.collection(str(ctx.author.id)).document(playlist_id)
                        playlist_doc.set({"contents": []})
                        try:
                            profile.update({"playlists": firestore.ArrayUnion([{"name": playlist, "ref": playlist_id}])})
                        except google.api_core.exceptions.NotFound:
                            profile.set({"playlists": []}, merge=True)
                            profile.update({"playlists": firestore.ArrayUnion([{"name": playlist, "ref": playlist_id}])})
                        await ctx.message.add_reaction("<:OK:716230152643674132>")
                else:
                    raise BadRequestException(f"A playlist with the name `{playlist}` exists already!")
            else:
                raise BadRequestException("The playlist name must not contain spaces!")
        elif action == "show" or action == "view":
            profile: DocumentReference = self.db.collection(str(ctx.author.id)).document("profile")
            x = check_if_playlist_exists(profile, playlist)
            if x is not False:
                playlist_doc: DocumentReference = self.db.collection(str(ctx.author.id)).document(x)
                if playlist_doc is not None:
                    playlist_data_raw = playlist_doc.get()
                    playlist_data: dict = playlist_data_raw.to_dict()
                    if "contents" in playlist_data.keys():
                        contents = playlist_data["contents"]
                        if len(contents) == 0:
                            raise BadRequestException("Playlist is empty!")

                        embed = PagedListEmbed(f"Contents of `{playlist}`", [f"{i + 1}.  {song['title']}" for i, song in enumerate(contents)], ctx, self.bot)
                        await embed.send(embed.get())

                    else:
                        raise BadRequestException(f"Could not load playlist {playlist}!")
                else:
                    raise BadRequestException(f"No playlist with the name {playlist} exists!")
            else:
                raise BadRequestException(f"No playlist with the name {playlist} exists!")
        elif action == "play":
            profile: DocumentReference = self.db.collection(str(ctx.author.id)).document("profile")
            x = check_if_playlist_exists(profile, playlist)
            if x is not False:
                playlist_doc: DocumentReference = self.db.collection(str(ctx.author.id)).document(x)
                if playlist_doc is not None:
                    playlist_data_raw = playlist_doc.get()
                    playlist_data: dict = playlist_data_raw.to_dict()
                    if "contents" in playlist_data.keys():
                        contents = playlist_data["contents"]
                        await self.join_channel(ctx)
                        if len(contents) == 0:
                            raise BadRequestException("Playlist is empty!")

                        index = 0
                        last_added_track = None
                        failed = 0
                        for index, song_data_raw in enumerate(contents):
                            try:
                                track = await self.bot.wavelink.build_track(song_data_raw["data"])
                                last_added_track = track
                                controller = self.get_controller(ctx)
                                controller.queue.append(track)
                            except BuildTrackError:
                                failed += 1
                                print("Failed to reconstruct track with data " + song_data_raw["data"])
                        await ctx.send(embed=StyledEmbed(description=f"**Added** {index} **tracks to queue**" if index > 1 else f"**Added** {last_added_track} **to queue.**"))
                        if failed > 0:
                            raise BadRequestException(f"**Failed to add** {failed} **tracks**!")
                    else:
                        raise BadRequestException(f"Could not load playlist {playlist}!")
                else:
                    raise BadRequestException(f"No playlist with the name {playlist} exists!")
            else:
                raise BadRequestException(f"No playlist with the name {playlist} exists!")
        elif action == "add":
            tracks_to_add = []

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

            profile: DocumentReference = self.db.collection(str(ctx.author.id)).document("profile")
            x = check_if_playlist_exists(profile, playlist)
            if len(tracks_to_add) > 0:
                if x is not False:
                    playlist_doc: DocumentReference = self.db.collection(str(ctx.author.id)).document(x)
                    if playlist_doc is not None:
                        playlist_doc.update({"contents": firestore.ArrayUnion(
                            [{"title": track_to_add.title, "author": track_to_add.author, "data": track_to_add.id, "url": track_to_add.uri, "id": str(uuid.uuid4()), "duration": track_to_add.duration} for
                             track_to_add in tracks_to_add])})
                        await ctx.message.add_reaction("<:OK:716230152643674132>")
                    else:
                        raise BadRequestException(f"No playlist with the name {playlist} exists!")
                else:
                    raise BadRequestException(f"No playlist with the name {playlist} exists!")
            else:
                raise BadRequestException("No track selected!")
        else:
            raise BadRequestException("This action does not exist. Valid actions are: `create`, `add`, `show`, `play`, `delete` and `link`.")

    @commands.command()
    async def like(self):
        """Adds the current song to your 'Liked Songs' playlist"""

    @commands.command()
    async def dislike(self):
        """Removes the current song/the given song from your 'Liked Songs' playlist"""

    @commands.command(usage="remove [playlist] <search term>")
    async def remove(self, ctx: Context, playlist: str, search_term: str = None):
        """Removes the current song or a song from a search term from the given playlist"""

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

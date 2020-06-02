from typing import List

from discord.ext import commands
from discord.ext.commands import Context
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import Client
from wavelink import Track

from chime.main import prefix
from chime.misc.BadRequestException import BadRequestException
from chime.misc.StyledEmbed import StyledEmbed
from chime.misc.util import check_if_playlist_exists, check_if_url
import chime


class PersonalPlaylistsCog(commands.Cog, name="Personal Playlists"):
    def __init__(self, bot):
        self.bot = bot
        cred = credentials.Certificate("../secret/firebase_creds.json")
        firebase_admin.initialize_app(cred)
        self.db: Client = firestore.client()

    @commands.command()
    async def playlists(self, ctx: Context):
        """Shows a list of all your playlists"""
        docs = self.db.collection(str(ctx.author.id)).stream()
        await ctx.send(embed=StyledEmbed(title="Your playlists", description=f"Use the `{prefix}playlist` command for creating new playlists, viewing them and much more! \n\n" + "\n".join([f"•  **{playlist.id}**  ({len(playlist.to_dict()['contents'])} songs)" for playlist in docs])))

    @commands.command(usage="playlist [action] [playlist_name]")
    async def playlist(self, ctx: Context, action: str, playlist: str, *, additional_args=None):
        """Provide the argument 'create' to create a playlist. Provide the argument 'show' to show the playlist's contents. Provide argument 'play' to play the playlist. Provide argument 'delete' to delete playlist. Provide argument 'link' to get a link to the playlist."""
        if action == "create":
            if not additional_args:  # if the playlist name contained spaces, the individual parts would be in additional_args
                if not check_if_playlist_exists(self.db, playlist, ctx.author.id):
                    with ctx.typing():
                        contents = self.db.collection(str(ctx.author.id)).document(str(playlist)).collection("contents")
                        await ctx.message.add_reaction("<:OK:716230152643674132>")
                else:
                    raise BadRequestException(f"A playlist with the name `{playlist}` exists already!")
            else:
                raise BadRequestException("The playlist name must not contain spaces!")
        elif action == "show":
            if check_if_playlist_exists(self.db, playlist, ctx.author.id):
                doc_ref = self.db.collection(str(ctx.author.id)).document(str(playlist))
                doc = doc_ref.get()
                data = doc.to_dict()
                contents = data["contents"]
                builder = []
                async with ctx.typing():
                    for url in contents:
                        tracks: List[Track] = await self.bot.wavelink.get_tracks(url)
                        builder.append(tracks[0].title)
                await ctx.send(embed=StyledEmbed(title=f"Contents of '{playlist}'", description="\n".join(["•  " + title for title in builder])))
            else:
                raise BadRequestException(f"No playlist with the name {playlist} exists!")

        else:
            raise BadRequestException("This action does not exist. Valid actions are: `create`, `show`, `play`, `delete` and `link`.")

    @commands.command()
    async def like(self):
        """Adds the current song to your 'Liked Songs' playlist"""


    @commands.command()
    async def dislike(self):
        """Removes the current song/the given song from your 'Liked Songs' playlist"""


    @commands.command(usage="add [playlist] <search term>")
    async def add(self, ctx: Context, playlist: str, *, search_term: str = None):
        """Adds the current song or a song from a search term to the given playlist"""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if search_term == "^":
            x = await ctx.channel.history(limit=2).flatten()
            search_term = x[1].content

        if check_if_url(search_term):  # user provided an URL
            if not player.is_connected:
                await ctx.invoke(self.join)
            tracks: List[Track] = await self.bot.wavelink.get_tracks(search_term)
        else:  # user didn't provide an URL so search for the entered term
            i = 0
            tracks = False
            while not tracks and i < 5:  # try to find song 5 times
                tracks: List[Track] = await self.bot.wavelink.get_tracks(f'ytsearch:{search_term}')
                i += 1
        if not tracks:
            raise BadRequestException('Could not find any songs with that query.')


        await ctx.message.add_reaction("<:OK:716230152643674132>")

    @commands.command(usage="remove [playlist] <search term>")
    async def remove(self, ctx: Context, playlist: str, search_term: str = None):
        """Removes the current song or a song from a search term from the given playlist"""

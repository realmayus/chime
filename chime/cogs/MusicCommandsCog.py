import asyncio
from typing import List

import discord
import wavelink
from discord import Message, Reaction, User, Emoji, RawReactionActionEvent
from discord.ext import commands
from wavelink import Track

from chime.util import check_if_url, get_friendly_time_delta
from chime.main import prefix
from chime.misc.StyledEmbed import StyledEmbed


class MusicCommandsCog(commands.Cog, name="Music Commands"):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(bot=self.bot)
        self.bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.bot.wait_until_ready()
        # Initiate our nodes. For this example we will use one server.
        # Region should be a discord.py guild.region e.g sydney or us_central (Though this is not technically required)
        await self.bot.wavelink.initiate_node(host='0.0.0.0',
                                              port=2333,
                                              rest_uri='http://0.0.0.0:2333',
                                              password='youshallnotpass',
                                              identifier='TEST',
                                              region='us_central')

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        """Joins the channel you're currently in."""
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise discord.DiscordException('No channel to join. Please either specify a valid channel or join one.')
            except Exception as e:
                print(type(e))
                print(str(e))

        player = self.bot.wavelink.get_player(ctx.guild.id)
        await ctx.send(f'Connecting to **`{channel.name}`**', delete_after=5.0)
        try:
            await player.connect(channel.id)
        except Exception as e:
            print(type(e))
            print(str(e))

    def get_song_selector_embed_desc_for_current_page(self, page, results):
        desc = "**React with a number to play the respective song!**\n"
        i = 1
        for track_index in range(len(results)):
            track = results[page*5 + track_index]
            if i == 6:
                break
            desc += (u"%s\N{variation selector-16}\N{combining enclosing keycap}" % str(i)) + "  " + str(track) + "\n"
            i += 1
        return desc, i

    async def play_(self, ctx, query:str, current_page=0, msg_to_edit:Message=None):
        player = self.bot.wavelink.get_player(ctx.guild.id)

        if check_if_url(query):
            if not player.is_connected:
                await ctx.invoke(self.join)
            tracks: List[Track] = await self.bot.wavelink.get_tracks(query)
            return await player.play(tracks[0])
        else:
            i = 0
            tracks = False
            while not tracks and i < 5:  # try to find song 5 times
                tracks: List[Track] = await self.bot.wavelink.get_tracks(f'ytsearch:{query}')
                i += 1
        if not tracks:
            return await ctx.send('Could not find any songs with that query.')

        embed = discord.Embed(title="Search results (Page " + str(current_page + 1) + ")", color=discord.colour.Color.from_rgb(r=255, g=197, b=84))

        description, count = self.get_song_selector_embed_desc_for_current_page(current_page, tracks)
        embed.description = description

        if msg_to_edit is not None:
            await msg_to_edit.edit(embed=embed)
            msg = msg_to_edit
        else:
            msg: Message = await ctx.send(embed=embed)

        [await msg.add_reaction(u"%s\N{variation selector-16}\N{combining enclosing keycap}" % str(x + 1)) for x in
         range(count - 1)]
        if len(tracks) - (current_page * 5) > 5:
            await msg.add_reaction("▶️")

        def check_reaction(reaction_: RawReactionActionEvent):
            return reaction_.member == ctx.author and isinstance(reaction_.emoji.name, str) and (
                    (reaction_.emoji.name[0].isdigit() and int(str(reaction_.emoji.name)[0]) in range(count)) or (
                            str(reaction_.emoji.name) == "▶️" and len(tracks) - (current_page * 5) > 5)) and reaction_.message_id == msg.id

        try:
            reaction: Reaction
            user: User
            reaction: RawReactionActionEvent = await self.bot.wait_for('raw_reaction_add', timeout=20.0, check=check_reaction)
            user = reaction.member
        except asyncio.TimeoutError:
            await msg.clear_reactions()
            expired_embed = discord.Embed(title="Expired",
                                          description="This song selector has expired because no one selected a song.")
            await msg.edit(embed=expired_embed)
        else:
            if str(reaction.emoji.name[0]).isdigit() and int(str(reaction.emoji.name)[0]) in range(count):
                await player.play(tracks[int(str(reaction.emoji.name)[0]) - 1])
                current_track = tracks[int(str(reaction.emoji.name[0]))-1]
                currently_playing_embed = StyledEmbed(title="<:music_note:716669042500436010>  " + current_track.title)
                currently_playing_embed.set_author(name="Currently playing")
                currently_playing_embed.add_field(name="Duration", value=get_friendly_time_delta(current_track.duration))
                currently_playing_embed.add_field(name="Artist", value=current_track.author)
                await msg.clear_reactions()
                await msg.edit(embed=currently_playing_embed)
                if not player.is_connected:
                    await ctx.invoke(self.join)
            elif str(reaction.emoji.name) == "▶️":
                await msg.remove_reaction("▶️", user)
                await self.play_(ctx, query, current_page + 1, msg)
            else:
                raise NotImplementedError

    @commands.command()
    async def play(self, ctx, *, query: str):
        """Searches for the search term on youtube or plays from the given URL. Also resumes current track if no other arguments passed."""
        await self.play_(ctx, query)

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current track"""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if player.is_playing and not player.is_paused:
            await player.set_pause(True)
            await ctx.send("Paused!")
        else:
            await ctx.send("I am currently not playing any track!")

    @commands.command()
    async def resume(self, ctx):
        """Resumes current track."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if player.is_playing and player.is_paused:
            await player.set_pause(False)
            await ctx.send("Resumed!")
        else:
            await ctx.send("Currently, no track is loaded/paused")

    @commands.command()
    async def speed(self, ctx):
        """Changes the speed. Valid values: `25%` - `200%`"""
        await ctx.send("This command is not implemented yet.")

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Sets the volume of the current track. Valid values: `0%` - `1000%`. For bass-boosting see """ + prefix + """boost"""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        await player.set_volume(volume)
        await ctx.send("Set volume to " + str(volume) + "!")

    @commands.command()
    async def boost(self, ctx):
        """Boosts the bass of the current track."""
        await ctx.send("This command is not implemented yet.")

    @commands.command()
    async def leave(self, ctx):
        """Leaves the current channel."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if player.is_connected:
            await player.disconnect()
        else:
            await ctx.send("I am not connected to a voice channel!")

    @commands.command()
    async def stop(self, ctx):
        """Stops the current track."""
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if player.is_playing or player.is_paused:
            await player.stop()
        else:
            await ctx.send("No track is currently playing!")

    @commands.command()
    async def loop(self, ctx):
        """Sets the looping mode. Valid values: `off`, `on`, `track`, `queue`"""
        await ctx.send("This command is not implemented yet.")

    @commands.command()
    async def queue(self, ctx):
        """Shows the queue."""
        await ctx.send("This command is not implemented yet.")

    @commands.command()
    async def clear(self, ctx):
        """Clears the queue."""
        await ctx.send("This command is not implemented yet.")

import discord


class StyledEmbed(discord.Embed):
    def __init__(self, **kwargs):
        """A styled embed."""
        super(StyledEmbed, self).__init__(color=discord.colour.Color.from_rgb(r=255, g=197, b=84), **kwargs)

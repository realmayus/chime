import discord


class StyledEmbed(discord.Embed):
    def __init__(self, **kwargs):
        """A styled embed."""
        super(StyledEmbed, self).__init__(color=discord.colour.Color.from_rgb(r=47, g=49, b=54), **kwargs)

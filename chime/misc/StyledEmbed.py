import discord


class StyledEmbed(discord.Embed):
    def __init__(self, **kwargs):
        if "color" in kwargs:
            super(StyledEmbed, self).__init__(**kwargs)
        else:
            super(StyledEmbed, self).__init__(color=discord.colour.Color.from_rgb(r=255, g=197, b=84), **kwargs)

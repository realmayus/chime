import discord
import random



class StyledEmbed(discord.Embed):
    def __init__(self, **kwargs):
        from chime.misc.tips import get_tip
        super(StyledEmbed, self).__init__(color=discord.colour.Color.from_rgb(r=255, g=197, b=84), **kwargs)
        if kwargs.get("suppress_tips") is not None and kwargs.get("suppress_tips") is not True:
            random_x = random.choice(range(6))
            if random_x == 5:
                self.set_footer(text="Tip: " + get_tip())

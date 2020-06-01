import discord
import random



class StyledEmbed(discord.Embed):
    def __init__(self, **kwargs):
        from chime.misc.tips import get_tip
        random_x = random.choice(range(6))
        super(StyledEmbed, self).__init__(color=discord.colour.Color.from_rgb(r=255, g=197, b=84), **kwargs)
        if random_x == 5:
            self.set_footer(text="Tip: " + get_tip())

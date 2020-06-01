import discord
from discord.ext import commands

from chime.misc.StyledEmbed import StyledEmbed


class EmbedHelpCommand(commands.HelpCommand):
    """This is an example of a HelpCommand that utilizes embeds.
    It's pretty basic but it lacks some nuances that people might expect.
    1. It breaks if you have more than 25 cogs or more than 25 subcommands. (Most people don't reach this)
    2. It doesn't DM users. To do this, you have to override `get_destination`. It's simple.
    Other than those two things this is a basic skeleton to get you started. It should
    be simple to modify if you desire some other behaviour.

    To use this, pass it to the bot constructor e.g.:

    bot = commands.Bot(help_command=EmbedHelpCommand())
    """
    # Set the embed colour here
    COLOUR = discord.colour.Color.from_rgb(r=255, g=197, b=84)

    def get_command_signature(self, command):
        return '{0.qualified_name} {0.signature}'.format(command)

    async def send_bot_help(self, mapping):
        embed = StyledEmbed(title='chime help', colour=self.COLOUR)
        embed.set_image(url="https://raw.githubusercontent.com/realmayus/chime/master/assets/chime_banner.png?token=AJC6B5VTHEZ5UHNY7QNDCU263LCCK")
        embed.description = "chime is a versatile, yet intuitive music bot for discord. It aims to have the best performance while being as user-friendly as possible. \n\n" \
                            "Want to support the development of chime while getting exclusive benefits? **[Donate](https://github.com/realmayus/chime)** \n \n" \
                            "**More info and invite link [here](https://github.com/realmayus/chime)** \n\n" \
                            "**Use** `" + self.clean_prefix + "help [command]` **for more info on a command.**"  # TODO Change LINK

        for cog, commands in mapping.items():
            if cog is not None:  # We don't want commands without categories! >:c
                name = cog.qualified_name
                filtered = await self.filter_commands(commands, sort=True)
                if filtered:
                    value = '  '.join("`*" + c.name + "`" for c in commands)
                    if cog and cog.description:
                        value = '{0}\n{1}'.format(cog.description, value)

                    embed.add_field(name=name, value=value)

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = StyledEmbed(title='{0.qualified_name} commands'.format(cog), colour=self.COLOUR)
        if cog.description:
            embed.description = cog.description

        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '...', inline=False)

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = StyledEmbed(title=group.qualified_name, colour=self.COLOUR)
        if group.help:
            embed.description = group.help

        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort=True)
            for command in filtered:
                embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '...',
                                inline=False)

        await self.get_destination().send(embed=embed)

    # This makes it so it uses the function above
    # Less work for us to do since they're both similar.
    # If you want to make regular command help look different then override it
    send_command_help = send_group_help

import discord
from discord.ext import commands
from discord.ext.commands import Command

from chime.main import prefix
from chime.misc.CustomCommand import CustomCommand
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
        embed = StyledEmbed(title='chime help')
        embed.set_image(url="https://raw.githubusercontent.com/realmayus/chime/master/assets/chime_banner.png?token=AJC6B5VTHEZ5UHNY7QNDCU263LCCK")
        embed.description = "chime is a versatile, yet intuitive music bot for discord. It aims to have the best performance while being as user-friendly as possible. \n\n" \
                            "Want to support the development of chime while getting exclusive benefits? **[Donate](https://github.com/realmayus/chime)** \n \n" \
                            "**More info and invite link [here](https://github.com/realmayus/chime)** \n\n" \
                            "**Use** `" + self.clean_prefix + "help [command]` **for more info on a command.**"

        for cog, commands in mapping.items():
            if cog is not None:  # We don't want commands without categories! >:c
                name = cog.qualified_name
                filtered = await self.filter_commands(commands, sort=True)
                if filtered:
                    builder = []
                    for command in commands:  # filtering out hidden commands
                        command: Command
                        builder.append(f"`{prefix + command.name}`" if not command.hidden else "")
                    value = '  '.join(builder)
                    if cog and cog.description:
                        value = '{0}\n{1}'.format(cog.description, value)

                    embed.add_field(name=name, value=value)

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        pass

    async def send_group_help(self, group: CustomCommand):
        embed = StyledEmbed(title='`' + group.qualified_name + '`')
        desc = ""
        if group.help:
            desc += group.help

        if group.usage:
            embed.add_field(name="**Usage**", value=f"`{prefix + group.usage}`", inline=False)

        if group.aliases and len(group.aliases) > 0:
            embed.add_field(name="**Aliases**", value=' '.join([f"`{prefix + alias}`" for alias in group.aliases]), inline=False)


        if hasattr(group, "available_args") and group.available_args:
            arg_builder = ""
            for typ in group.available_args:
                arg_builder += f"\n**{typ['type']}**"
                for arg in typ['args']:
                    arg_builder += f"\n`{arg['name']}`\n***{arg['desc']}***"
            embed.add_field(name="**Arguments**", value=arg_builder)

        if hasattr(group, "examples") and group.examples:
            example_builder = ""
            for ex in group.examples:
                example_builder += f"\n`{ex['ex']}`\n{ex['desc']}"
            embed.add_field(name="**Examples**", value=example_builder)


        desc += f"\n\n_Was this helpful?_  [**Yes**](https://chime.realmayus.xyz/survey/help?command={group.name}&helpful=1) | [**Nope**](https://chime.realmayus.xyz/survey/help?command={group.name}&helpful=0)"
        embed.description = desc

        await self.get_destination().send(embed=embed)

    # This makes it so it uses the function above
    # Less work for us to do since they're both similar.
    # If you want to make regular command help look different then override it
    send_command_help = send_group_help

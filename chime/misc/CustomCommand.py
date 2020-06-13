from discord.ext.commands import Command


class CustomCommand(Command):
    def __init__(self, func, **kwargs):
        super(CustomCommand, self).__init__(func, **kwargs)
        self.available_args = kwargs.get('available_args')


def custom_command(name=None, cls=None, **attrs):
    if cls is None:
        cls = CustomCommand

    def decorator(func):
        if isinstance(func, Command):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, **attrs)

    return decorator

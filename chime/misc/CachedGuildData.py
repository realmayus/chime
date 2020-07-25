from typing import List


class CachedGuildData:

    def __init__(self, db):
        """A class which caches and pushes guild-specific data to a DB."""
        self.db = db
        self.data = []
        self.guild_id = None

    def load(self, guild_id) -> 'CachedGuildData':
        """Load data from database and store it in this class."""
        self.guild_id = guild_id

        # …

        return self

    def set(self, key: str, value) -> 'CachedGuildData':
        """Sets a key-value pair. Gets pushed to the DB and gets cached automatically."""

        # …

        return self

    def get(self, key: str):
        """Returns the given key's corresponding value. Gets pulled from the cache."""

        # …

        return self

    def remove(self, key: str) -> 'CachedGuildData':
        """Removes the given key and its corresponding value from both the cache and the DB."""
        # …

        return self


def usage():
    x = None
    if not hasattr(x, "guild_data"):
        x.guild_data = [CachedGuildData(db).load(2934)]

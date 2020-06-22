import asyncio
import logging
import time
import psutil
from discord.ext import commands
from google.cloud.firestore_v1 import Client, CollectionReference, ArrayUnion


class StatsCog(commands.Cog):
    def __init__(self, bot, db):
        self.bot: commands.Bot = bot
        self.db: Client = db
        self.logger = logging.getLogger("chime")

        self.stats = {
            "common_commands": [],
            "non_existant_commands": [],
            "users_listening": [],
            "servers_listening": [],
            "server_amount": [],
            "latency": [],
            "cpu_usage": [],
            "ram_usage": []
        }

    @commands.Cog.listener()
    async def on_ready(self):
        from chime.main import start_dev
        if not start_dev:  # only start stats logging when not running in dev mode!
            self.bot.loop.create_task(self.push_stats_handler())

    def add_executed_command(self, command: str):
        self.stats["common_commands"].append({"value": command, "time": time.time()})

    def add_non_existant_command(self, command: str):
        self.stats["non_existant_commands"].append({"value": command, "time": time.time()})

    def set_current_listening_users(self):
        pass

    def set_latency(self):
        self.stats["latency"].append({"value": self.bot.latency, "time": time.time()})

    def set_cpu_usage(self):
        self.stats["cpu_usage"].append({"value": psutil.cpu_percent(), "time": time.time()})

    def set_ram_usage(self):
        self.stats["ram_usage"].append({"value": psutil.virtual_memory().percent, "time": time.time()})

    def set_current_listening_servers(self):
        counter = 0
        for node_id in self.bot.wavelink.nodes:
            node = self.bot.wavelink.get_node(node_id)
            counter += node.stats.playing_players
        self.stats["servers_listening"].append({"value": counter, "time": time.time()})

    def set_server_count(self):
        self.stats["server_amount"].append({"value": len(self.bot.guilds), "time": time.time()})

    def push_stats(self):
        self.set_current_listening_users()
        self.set_current_listening_servers()
        self.set_server_count()
        self.set_latency()
        self.set_ram_usage()
        self.set_cpu_usage()
        stats_coll_ref: CollectionReference = self.db.collection("stats")
        for key, value in self.stats.items():
            if value:
                if not stats_coll_ref.document(key).get().exists:
                    stats_coll_ref.document(key).set({"data": value})
                    return
                stats_coll_ref.document(key).update({"data": ArrayUnion(value)})

        # reset stats after push
        self.stats = {
            "common_commands": [],
            "non_existant_commands": [],
            "users_listening": [],
            "servers_listening": [],
            "server_amount": [],
            "latency": [],
            "cpu_usage": [],
            "ram_usage": []
        }

    async def push_stats_handler(self):
        while True:
            await asyncio.sleep(60)  # execute every five minutes
            self.push_stats()

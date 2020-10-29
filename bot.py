import logging
import os

import discord
from discord.ext import commands

import config
from consts import DESCRIPTION, DEFAULT_NAME

intents = discord.Intents.default()
intents.members = True
intents.presences = True

log = logging.getLogger(__name__)


def extensions_generator():
    """Returns a generator for all cog files that aren't in do_not_use."""
    cog_path = "./cogs"
    do_not_use = ["__init__.py", "__pycache__", "helpers"]
    for cog in os.listdir(cog_path):
        if cog not in do_not_use:
            yield f"cogs.{cog[:-3]}"


class MarkovBot(commands.Bot):
    """Defines the MarkovBot class and functions."""

    def __init__(self):
        super().__init__(command_prefix=["$"], description=DESCRIPTION, intents=intents)
        self.token = config.token
        self.default_nick = DEFAULT_NAME
        self.add_command(self.load)

        for extension in extensions_generator():
            try:
                self.load_extension(extension)
                logging.info(f"Successfully loaded extension {extension}.")
            except Exception:
                logging.exception(f'Failed to load extension {extension}.')

    async def on_ready(self):
        """Prints bot initialization info"""
        print(f"Logged in as {self.user.name}, id {self.user.id}.")

    async def on_message(self, message):
        """Handles commands based on messages sent"""
        if message.author.bot:
            return
        await self.process_commands(message)

    def run(self):
        """Runs the bot with the token from the config file."""
        super().run(self.token, reconnect=True)

    # async def on_member_update(self, before, after):
    #     """Resets bot's nickname anytime it is changed."""
    #     if before.id == self.user.id and before.nick != after.nick:
    #         await after.edit(nick=self.default_nick)

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, extension):
        """Loads a specified extension into the bot."""
        try:
            self.load_extension(extension)
            await ctx.send(f"Successfully loaded extension {extension}.")
        except Exception:
            await ctx.send(f'Failed to load extension {extension}.')
            logging.exception(f'Failed to load extension {extension}.')


if __name__ == '__main__':
    MarkovBot().run()

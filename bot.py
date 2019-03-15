from discord.ext import commands

import markov as mk
from markov import REFLEXIVE_TAG, INCLUSIVE_TAG, NAMES
import server_toggle as st
import config
from config import MAX_MESSAGE_LENGTH

DEFAULT_NAME = 'MarkovBot'
DESCRIPTION = "Bot that creates stuff based off of Markov chains."
MAX_MARKOV_ATTEMPTS = 10
MAX_NICKNAME_LENGTH = 30
MAX_NUM_NAMES = 10


class MarkovBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=["$"], description=DESCRIPTION)
        self.default_nick = DEFAULT_NAME
        self.add_command(self.do)
        self.add_command(self.list)
        self.add_command(self.toggle)

    async def on_ready(self):
        """Prints bot initialization info"""
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        """Handles commands based on messages sent"""
        if message.author.bot:
            return
        await self.process_commands(message)

    async def on_member_update(self, before, after):
        """Resets bot's nickname anytime it is changed."""
        if before.id == self.user.id and before.nick != after.nick:
            await after.edit(nick=self.default_nick)

    @commands.command()
    async def do(self, ctx, person=REFLEXIVE_TAG, root=None):
        """Creates a Markov sentence based off of a user."""

        if person == 'htz':
            person = INCLUSIVE_TAG
        if person == REFLEXIVE_TAG:
            person = person.replace(REFLEXIVE_TAG, ctx.author.name)
        try:
            person_ids = mk.parse_names(ctx, person)
        except mk.TooManyInputsError as e:
            error_msg = f'Too many inputs ({e.number}). Max is {MAX_NUM_NAMES}.'
            await ctx.send(error_msg)
            return
        except mk.NameNotFoundError as e:
            error_msg = f'Name not found {e.name}.'
            await ctx.send(error_msg)
            return
        except mk.AmbiguousInputError as e:
            error_msg = f'{e.name} maps to multiple people: {e.output}.'
            await ctx.send(error_msg)
            return

        msg, nick = mk.generate_markov(person_ids, root)

        current_guild = ctx.guild
        bot_self = current_guild.me

        if person == INCLUSIVE_TAG:
            nick = ctx.guild.name.title()
        await bot_self.edit(nick=nick)
        await ctx.send(msg)

    @commands.command()
    async def list(self, ctx, search=None):
        """Prints a list of everyone who has a Markov model."""
        out = []
        message = ''
        for name in NAMES.values():
            if search:
                if search.lower() not in name.lower():
                    continue
            if len(message) + len(name) < MAX_MESSAGE_LENGTH:
                message += name + ', '
            else:
                out.append(message[:-2])
                message = name + ', '
        else:
            out.append(message[:-2])
        if len(out) > 1:
            for msg in out:
                await ctx.author.send(msg)
        else:
            for msg in out:
                await ctx.send(msg)

    @commands.command()
    async def toggle(self, ctx, server=None):
        """Lists/Toggles servers from which you want the bot to pull Markov chains."""
        if server:
            if not st.is_server(server):
                await ctx.send(f'{server} is not a valid server. Type `~toggle` to see a list of valid servers.')
            else:
                server_added = st.toggle_server(ctx.author.id, server)
                if server_added:
                    await ctx.send(f'{server} added to list of your Markov servers.')
                else:
                    await ctx.send(f'{server} removed from list of your Markov servers.')
        else:
            out = st.list_servers(ctx.author.id)
            await ctx.send(out)

    def run(self):
        """Runs the bot with the token from the config file."""
        super().run(config.token, reconnect=True)


if __name__ == "__main__":
    bot = MarkovBot()
    bot.run()

import asyncio
import random
import re

from discord.ext import commands

import config
import deathmatch as dm
import markov as mk
import server_toggle as st
from config import MAX_MESSAGE_LENGTH
from markov import REFLEXIVE_TAG, INCLUSIVE_TAG, NAMES

DEFAULT_NAME = 'MarkovBot'
DESCRIPTION = "Bot that creates stuff based off of Markov chains."
MAX_MARKOV_ATTEMPTS = 10
MAX_NICKNAME_LENGTH = 30
MAX_NUM_NAMES = 10


class MarkovBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=["$"], description=DESCRIPTION)
        self.default_nick = DEFAULT_NAME
        self.simulator_queue = []
        self.doing_dm = False
        self.topic = ""
        self.total_simulation_messages = 0
        self.add_command(self.do)
        self.add_command(self.list)
        self.add_command(self.toggle)
        self.add_command(self.random_link)
        self.add_command(self.deathmatch)
        # self.loop.create_task(self.update_simulator())

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

    @commands.command(aliases=['mk'])
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

    @commands.command(aliases=['linkme', 'randlink'])
    async def random_link(self, ctx):
        """Returns a random link."""
        await ctx.send(mk.get_rand_link())

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

    @commands.command(aliases=['dm'])
    async def deathmatch(self, ctx, *args):
        if not self.doing_dm:
            self.doing_dm = True
            try:
                fighter1 = ctx.author.name
                if not args:
                    fighter2 = mk.get_rand_name()
                else:
                    if ctx.message.mentions:
                        fighter2 = ctx.message.mentions[0].name
                    else:
                        fighter2 = args[0].title()
                msgs, winner = dm.do_deathmatch(fighter1, fighter2)
                out = await ctx.send("test")
                for msg in msgs:
                    await out.edit(content=msg)
                    await asyncio.sleep(2)
                self.doing_dm = False
            except Exception as e:
                print(e)
                self.doing_dm = False
        else:
            await ctx.send("A deathmatch is currently in progress. Please wait until it finishes before starting a new one.")


    async def update_simulator(self):
        """Updates the htz simulator."""
        await self.wait_until_ready()
        while not self.is_closed():
            # Fills the queue if empty, otherwise pops the first element
            user_model = None
            next_user = None
            out = None
            while not out:
                while not user_model:
                    if not self.simulator_queue:
                        self.simulator_queue = mk.fill_simulator_queue()
                    next_user = self.simulator_queue.pop(0)

                    # Generates the model for the user and generates a sentence for that user.
                    user_model = mk.generate_model([next_user])

                for _ in range(3):
                    out = mk.generate_sentence(user_model, root=self.topic)
                    if out:
                        break
                else:
                    out = mk.generate_sentence(user_model)

                for userid, name in mk.NAMES.items():
                    if name in out:
                        self.simulator_queue.insert(random.randint(0, 2), userid)

                mentions = set([c for c in out[0].split(' ') if c[0:2] == '<@'])
                for mention in mentions:
                    self.simulator_queue.insert(random.randint(0, 1), mention[2:])

                # Topic is last word of out, stripped of non-alphanumeric characters.
                self.topic = out.split()[-1]
                re.sub(r'\W+', '', self.topic)

            # Posts that message to the SIMULATOR_CHANNEL
            nick = mk.generate_nick([next_user])
            bot_guild = self.get_guild(config.DEFAULT_GUILD_ID)
            bot_self = bot_guild.get_channel(config.SIMULATOR_CHANNEL)
            await bot_self.edit(nick=nick)
            await bot_self.send(out)

            self.total_simulation_messages += 1
            print(self.total_simulation_messages)
            if self.total_simulation_messages % 20 == 0:
                self.topic = None

            # Generate wait time and wait.
            wait_time = mk.get_wait_time()
            await asyncio.sleep(wait_time)

    def run(self):
        """Runs the bot with the token from the config file."""
        super().run(config.token, reconnect=True)


if __name__ == "__main__":
    bot = MarkovBot()
    bot.run()

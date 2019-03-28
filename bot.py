import asyncio
import random
import re

from discord.ext import commands

import config
import channel_permissions as cp
from discord.ext.commands import has_permissions
import markov as mk
import server_toggle as st
from config import MAX_MESSAGE_LENGTH
from markov import REFLEXIVE_TAG, INCLUSIVE_TAG, NAMES

DEFAULT_NAME = 'MarkovBot'
DESCRIPTION = "Bot that creates stuff based off of Markov chains."
MAX_MARKOV_ATTEMPTS = 10
MAX_NICKNAME_LENGTH = 30
MAX_NUM_NAMES = 10


def has_post_permission(guildid, channelid):
    """Checks whether the bot can post in that channel."""
    guild_perms = cp.get_guild(guildid)
    try:
        for blacklist_channel in guild_perms[cp.BLACKLIST_KEY]:
            if channelid == blacklist_channel:
                return False
    except KeyError:
        pass

    if cp.WHITELIST_KEY in guild_perms.keys():
        if guild_perms[cp.WHITELIST_KEY]:
            try:
                for whitelist_channel in guild_perms[cp.WHITELIST_KEY]:
                    if channelid == whitelist_channel:
                        break
                else:
                    return False
            except KeyError:
                pass
    return True


def remove_mentions(msg, current_guild):
    user_tags = set([c for c in msg.split(' ') if c[0:2] == '<@'])
    for user_tag in user_tags:
        id = int(re.sub('\D', '', user_tag))
        username = current_guild.get_member(id)
        if username is not None:
            username = username.display_name
            msg = msg.replace(user_tag, '@' + username)
        elif user_tag in msg:
            msg = msg.replace(user_tag, "@UNKNOWN_USER")
    return msg


class MarkovBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=["$"], description=DESCRIPTION)
        self.default_nick = DEFAULT_NAME
        self.simulator_queue = []
        self.doing_dm = False
        self.topic = ""
        self.total_simulation_messages = 0
        self.simulation_on = asyncio.Event()
        self.add_command(self.do)
        self.add_command(self.domulti)
        self.add_command(self.do10)
        self.add_command(self.list)
        self.add_command(self.toggle)
        self.add_command(self.togglesim)
        self.add_command(self.random_link)
        self.add_command(self.listchannels)
        self.add_command(self.addblacklist)
        self.add_command(self.addwhitelist)
        self.add_command(self.setsimulator)
        self.add_command(self.removesimulator)
        self.add_command(self.removeblacklist)
        self.add_command(self.removewhitelist)
        self.loop.create_task(self.update_simulator())

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
        if has_post_permission(ctx.guild.id, ctx.channel.id):
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

            msg = remove_mentions(msg, current_guild)

            if person == INCLUSIVE_TAG:
                nick = ctx.guild.name.title()
            await bot_self.edit(nick=nick)
            await ctx.send(msg)

    @commands.command()
    async def domulti(self, ctx, num=1, person=REFLEXIVE_TAG, root=None):
        if has_post_permission(ctx.guild.id, ctx.channel.id):
            if type(num) != int:
                await ctx.send(f'{num} is not a number.')
            if num > 10:
                num = 10
            if num < 1:
                num = 1

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

            msg, nick = mk.generate_markov(person_ids, root, num=num)

            current_guild = ctx.guild
            bot_self = current_guild.me

            msg = remove_mentions(msg, current_guild)

            if person == INCLUSIVE_TAG:
                nick = ctx.guild.name.title()
            await bot_self.edit(nick=nick)
            await ctx.send(msg)

    @commands.command()
    async def do10(self, ctx, person=REFLEXIVE_TAG, root=None):
        if has_post_permission(ctx.guild.id, ctx.channel.id):
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

            msg, nick = mk.generate_markov(person_ids, root, num=10)

            current_guild = ctx.guild
            bot_self = current_guild.me

            msg = remove_mentions(msg, current_guild)

            if person == INCLUSIVE_TAG:
                nick = ctx.guild.name.title()
            await bot_self.edit(nick=nick)
            await ctx.send(msg)

    @commands.command()
    async def list(self, ctx, search=None):
        """Prints a list of everyone who has a Markov model."""
        if has_post_permission(ctx.guild.id, ctx.channel.id):
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

    @commands.command(aliases=['linkme', 'randlink', 'lonk'])
    async def random_link(self, ctx):
        """Returns a random link."""
        if ctx.guild.id == 529904258233925632:
            await ctx.send(mk.get_rand_link())

    @commands.command()
    async def toggle(self, ctx, server=None):
        """Lists/Toggles servers from which you want the bot to pull Markov chains."""
        if has_post_permission(ctx.guild.id, ctx.channel.id):
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

    @commands.command()
    @has_permissions(manage_guild=True)
    async def togglesim(self, ctx):
        if self.simulation_on.is_set():
            self.simulation_on.clear()
            await ctx.send("Simulation ended.")
        else:
            if not cp.get_channel(ctx.guild.id, cp.SIMULATION_KEY):
                await ctx.send("No channel set for simulation. "
                               "Please set the channel using `$setsim [channel mention]`")
            self.simulation_on.set()
            await ctx.send("Simulation started.")

    @commands.command()
    @has_permissions(manage_guild=True)
    async def listchannels(self, ctx):
        """Lists the channels in which the bot is white/blacklisted."""
        guild_perms = cp.get_guild(ctx.guild.id)
        await ctx.send(guild_perms)

    @commands.command()
    @has_permissions(manage_guild=True)
    async def addblacklist(self, ctx):
        """Adds a channel to the blacklist."""
        channel_mentions = ctx.message.channel_mentions

        if channel_mentions:
            out = ''
            for channel in channel_mentions:
                cp.add_channel(ctx.guild.id, channel.id, cp.BLACKLIST_KEY)
                out += f'{channel.name}, '
            await ctx.send(f"{out[:-2]} added to blacklist!")

    @commands.command()
    @has_permissions(manage_guild=True)
    async def addwhitelist(self, ctx):
        """Adds a channel to the whitelist."""
        channel_mentions = ctx.message.channel_mentions

        if channel_mentions:
            out = ''
            for channel in channel_mentions:
                cp.add_channel(ctx.guild.id, channel.id, cp.WHITELIST_KEY)
                out += f'{channel.name}, '
            await ctx.send(f"{out[:-2]} added to whitelist!")

    @commands.command(aliases=['removesim'])
    @has_permissions(manage_guild=True)
    async def removesimulator(self, ctx):
        """Removes an announcements channel."""
        cp.clear_channel(ctx.guild.id, cp.SIMULATION_KEY)
        await ctx.send(f"Removed simulation channel!")

    @commands.command()
    @has_permissions(manage_guild=True)
    async def removeblacklist(self, ctx):
        """Removes a blacklisted channel."""
        channel_mentions = ctx.message.channel_mentions

        if channel_mentions:
            out = ''
            for channel in channel_mentions:
                try:
                    cp.remove_channel(ctx.guild.id, channel.id, cp.BLACKLIST_KEY)
                    out += f'{channel.name}, '
                except ValueError:
                    pass
            if len(out) < 2:
                out = 'No channels were  '
            await ctx.send(f"{out[:-2]} removed from blacklist!")

    @commands.command()
    @has_permissions(manage_guild=True)
    async def removewhitelist(self, ctx):
        """Removes a whitelisted guild."""
        channel_mentions = ctx.message.channel_mentions

        if channel_mentions:
            out = ''
            for channel in channel_mentions:
                try:
                    cp.remove_channel(ctx.guild.id, channel.id, cp.WHITELIST_KEY)
                    out += f'{channel.name}, '
                except ValueError:
                    pass
            if len(out) < 2:
                out = 'No channels were  '
            await ctx.send(f"{out[:-2]} removed from whitelist!")

    @commands.command(aliases=['setsim'])
    @has_permissions(manage_guild=True)
    async def setsimulator(self, ctx):
        """Sets the default simulation channel."""
        channel_mentions = ctx.message.channel_mentions

        if channel_mentions:
            simulation_channel = channel_mentions[0]
            cp.set_channel(ctx.guild.id, simulation_channel.id, cp.SIMULATION_KEY)
            await ctx.send(f"{simulation_channel.name} set as simulation channel.")

    async def update_simulator(self):
        """Updates the htz simulator."""
        await self.wait_until_ready()
        while not self.is_closed():
            await self.simulation_on.wait()
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
            bot_channel = bot_guild.get_channel(cp.get_channel(config.DEFAULT_GUILD_ID, cp.SIMULATION_KEY))
            bot_self = bot_guild.me
            await bot_self.edit(nick=nick)
            await bot_channel.send(out)

            self.total_simulation_messages += 1
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

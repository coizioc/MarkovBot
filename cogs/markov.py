import re

from discord.ext import commands
from discord.ext.commands import has_permissions

from config import MAX_MESSAGE_LENGTH
from config import MAX_NUM_NAMES
from helpers import markov_helpers as mk
from helpers import server_toggle as st, channel_permissions as cp, simulation as sim
from helpers.markov_helpers import REFLEXIVE_TAG, INCLUSIVE_TAG, NAMES


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


class Markov():
    def __init__(self, bot):
        self.bot = bot
        self.simulation = sim.SimThread(bot)

    @commands.command(aliases=['mk'])
    async def do(self, ctx, person=REFLEXIVE_TAG, root=None):
        """Creates a Markov sentence based off of a user."""
        if has_post_permission(ctx.guild.id, ctx.channel.id):
            if person == REFLEXIVE_TAG:
                person = person.replace(REFLEXIVE_TAG, ctx.author.name)
            person_ids = await self.get_person_ids(ctx, person)
            if not person_ids:
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
            person_ids = await self.get_person_ids(ctx, person)
            if not person_ids:
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

            person_ids = await self.get_person_ids(ctx, person)
            if not person_ids:
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
        if self.simulation.simulation_on.is_set():
            self.simulation.simulation_on.clear()
            await ctx.send("Simulation ended.")
        else:
            if not cp.get_channel(ctx.guild.id, cp.SIMULATION_KEY):
                await ctx.send("No channel set for simulation. "
                               "Please set the channel using `$setsim [channel mention]`")
            self.simulation.simulation_on.set()
            await ctx.send("Simulation started.")

    @commands.command(aliases=['setsim'])
    @has_permissions(manage_guild=True)
    async def setsimulator(self, ctx):
        """Sets the default simulation channel."""
        channel_mentions = ctx.message.channel_mentions

        if channel_mentions:
            simulation_channel = channel_mentions[0]
            cp.set_channel(ctx.guild.id, simulation_channel.id, cp.SIMULATION_KEY)
            await ctx.send(f"{simulation_channel.name} set as simulation channel.")

    async def get_person_ids(self, ctx, person):
        try:
            return mk.parse_names(ctx, person)
        except mk.TooManyInputsError as e:
            error_msg = f'Too many inputs ({e.number}). Max is {MAX_NUM_NAMES}.'
            await ctx.send(error_msg)
            return None
        except mk.NameNotFoundError as e:
            error_msg = f'Name not found {e.name}.'
            await ctx.send(error_msg)
            return None
        except mk.AmbiguousInputError as e:
            error_msg = f'{e.name} maps to multiple people: {e.output}.'
            await ctx.send(error_msg)
            return None

    async def on_ready(self):
        await self.simulation.run()


def setup(bot):
    """Adds the cog to the bot."""
    bot.add_cog(Markov(bot))

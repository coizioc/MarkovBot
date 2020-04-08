import random

from discord.ext import commands

from consts import MAX_NUM_NAMES
from helpers import markov_helpers as mk
from helpers import mk_fanfic as mkff
from helpers import server_toggle as st, channel_permissions as cp, simulation as sim
from helpers.markov_helpers import REFLEXIVE_TAG


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


class Markov(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.simulation = sim.SimThread(bot)

    @commands.command(aliases=['mk'])
    async def do(self, ctx, person=REFLEXIVE_TAG, root=None):
        """Creates a Markov sentence based off of a user."""
        if has_post_permission(ctx.guild.id, ctx.channel.id):
            await mk.MarkovThread(ctx, person, root).run()

    @commands.command()
    async def domulti(self, ctx, num=1, person=REFLEXIVE_TAG, root=None):
        """Creates multiple Markov sentences (up to 10)."""
        if has_post_permission(ctx.guild.id, ctx.channel.id):
            if type(num) != int:
                await ctx.send(f'{num} is not a number.')
                return
            if num > 10:
                num = 10
            if num < 1:
                num = 1

            await mk.MarkovThread(ctx, person, root, num).run()

    @commands.command()
    async def do10(self, ctx, person=REFLEXIVE_TAG, root=None):
        """Creates 10 Markov sentences."""
        if has_post_permission(ctx.guild.id, ctx.channel.id):
            await mk.MarkovThread(ctx, person, root, num=10).run()

    @commands.command()
    async def list(self, ctx, search=None):
        """Prints a list of everyone who has a Markov model."""
        if has_post_permission(ctx.guild.id, ctx.channel.id):
            messages = mk.print_names(ctx, search)
            if len(messages) > 5:
                await ctx.send("List too long/too broad search. Please provide a more specific search.")
            elif len(messages) > 1:
                for msg in messages:
                    await ctx.author.send(msg)
            else:
                for msg in messages:
                    await ctx.send(msg)

    @commands.command(aliases=['sent'])
    async def sentiment(self, ctx, name):
        if has_post_permission(ctx.guild.id, ctx.channel.id):
            msg = await mk.get_sentiment_analysis(ctx, name)
            await ctx.send(msg)

    @commands.command(aliases=['linkme', 'randlink', 'lonk'])
    async def random_link(self, ctx):
        """Returns a random link."""
        if ctx.guild.id == 529904258233925632:
            await ctx.send(mk.get_rand_link())

    @commands.command()
    async def toggle(self, ctx, server=None):
        """Lists/Toggles servers you want the bot to pull from."""
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

    @commands.command(aliases=['ff'])
    async def fanfic(self, ctx, p1=None, p2=None, g1='m', g2='f'):
        out = mkff.generate_fanfic(p1, p2, g1, g2)
        await ctx.send(out)

    @commands.command()
    async def coiz(self, ctx):
        with open('coizirl.txt', 'r') as f:
            lines = f.read().splitlines()
        await ctx.send(random.choice(lines))

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


def setup(bot):
    """Adds the cog to the bot."""
    bot.add_cog(Markov(bot))

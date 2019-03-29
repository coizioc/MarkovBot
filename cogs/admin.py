from discord.ext import commands
from discord.ext.commands import has_permissions

from cogs.helpers import markov_helpers as mk, server_toggle as st, channel_permissions as cp

DEFAULT_NAME = 'MarkovBot'
DESCRIPTION = "Bot that creates stuff based off of Markov chains."


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


class Admin():
    def __init__(self, bot):
        self.bot = bot

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


def setup(bot):
    """Adds the cog to the bot."""
    bot.add_cog(Admin(bot))

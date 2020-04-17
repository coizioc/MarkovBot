"""Implements commands related to running a freemium-style text-based RPG."""
import asyncio
import math
import random

import discord
from discord.ext import commands


def calc_relationship(name1, name2=''):
    """Calculates the percent relationship between two people."""
    total = 0
    for name in [name1, name2]:
        for c in name:
            total += ord(c)
    percent = (total + 32) % 101
    return percent


class Other(commands.Cog):
    """Defines Other commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def snap(self, ctx, *args):
        """Determines whether you have been snapped by Thanos or not."""
        if len(args) > 0:
            name = ' '.join(args)
        else:
            name = ctx.author.nick if ctx.author.nick else ctx.author.name
        total = 0
        for c in name:
            total += ord(c)
        if total % 2 == 0:
            await ctx.send(f"{name.title()}, you were spared by Thanos.")
        else:
            await ctx.send(f'{name.title()}, you were slain by Thanos, for the good of the Universe.')

    @commands.command()
    async def ship(self, ctx, *args):
        """Ships two users together to determine their relationship."""
        if len(args) == 1:
            person1 = ctx.author.name.lower().replace(' ', '')
            person2 = args[0].lower().replace(' ', '')
        elif len(args) == 2:
            person1 = args[0].lower().replace(' ', '')
            person2 = args[1].lower().replace(' ', '')
        else:
            return

        percent = calc_relationship(person1, person2)
        out = f':heartpulse: __**MATCHMAKING**__ :heartpulse:\n' \
              f':small_red_triangle_down: *`{person1}`*\n' \
              f':small_red_triangle: *`{person2}`*\n\n' \
              f'**{percent}%** ​`'

        percent_bars = int(math.floor(percent / 10))
        for _ in range(percent_bars):
            out += '█'
        for _ in range(10 - percent_bars):
            out += ' ​'
        out += '`\n\n'

        descriptions = {
            9: 'Awful :sob:',
            19: 'Bad :cry:',
            29: 'Pretty low :frowning:',
            39: 'Not Too Great :confused:',
            49: 'Worse Than Average :neutral_face:',
            59: 'Barely :no_mouth:',
            68: 'Not Bad :slight_smile:',
            69: '( ͡° ͜ʖ ͡°)',
            79: 'Pretty Good :smiley:',
            89: 'Great :smile:',
            99: 'Amazing :heart_eyes:',
            100: 'PERFECT! :heart_exclamation:'
        }

        for max_value in descriptions.keys():
            if percent <= max_value:
                description_text = descriptions[max_value]
                break
        else:
            description_text = descriptions[100]
        out += description_text
        await ctx.send(out)

    @commands.command()
    async def shipall(self, ctx, word, bottom=None):
        """Compares a term against all users in the server."""
        out = ':heartpulse: __**MATCHMAKING**__ :heartpulse:\n'
        word = word.lower().replace(' ', '')
        relationships = []
        guild_members = ctx.guild.members
        for member in guild_members:
            percent = calc_relationship(word, member.name.lower().replace(' ', ''))
            relationships.append(tuple((percent, member)))
        if bottom is None:
            relationships = sorted(relationships, key=lambda x: x[0], reverse=True)
        else:
            relationships = sorted(relationships, key=lambda x: x[0])
        for i in range(10):
            out += f'**{i + 1}**: `{word}` :heart: `{relationships[i][1].name}`: {relationships[i][0]}%\n'
        await ctx.send(out)


def setup(bot):
    """Adds the cog to the bot."""
    bot.add_cog(Other(bot))

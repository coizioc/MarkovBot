import random

import markovify
from discord.ext import commands

import config
from config import MODELS_DIRECTORY, NAMES_FILE

USERID = '297481821472686081'
USERNAME = "Sprouts"

DEFAULT_NAME = 'MarkovBot'
DESCRIPTION = "Bot that keeps tracks of when reactions are added/removed."
MAX_MARKOV_ATTEMPTS = 10
MAX_MESSAGE_LENGTH = 1800
MAX_NICKNAME_LENGTH = 30
MAX_NUM_NAMES = 10

INCLUSIVE_TAG = 'all'
RANDOM_TAG = 'rand'
REFLEXIVE_TAG = 'me'

with open(NAMES_FILE, 'r', encoding='utf-8') as f:
    RAW_NAMES = f.read().splitlines()

NAMES = {}
for line in RAW_NAMES:
    id, name = line.split(';')
    NAMES[id] = name


class TooManyInputsError(Exception):
    """Error raised for too many inputs."""
    def __init__(self, number):
        self.number = number


class NameNotFoundError(Exception):
    """Error raised for input that refers to no user."""
    def __init__(self, name):
        self.name = name


class AmbiguousInputError(Exception):
    """Error raised for input that refers to multiple users"""
    def __init__(self, name, output):
        self.name = name
        self.output = output


def generate_markov(person_ids, root):
    """Generates a Markov sentence and nickname based off a list of Members and a given root."""
    nick = generate_nick(person_ids)
    try:
        models = generate_models(person_ids)
    except FileNotFoundError:
        return "File not found for person(s).", DEFAULT_NAME
    text_model = markovify.combine(models)

    for _ in range(MAX_MARKOV_ATTEMPTS):
        if root is None:
            output = text_model.make_sentence(tries=MAX_MARKOV_ATTEMPTS)
        else:
            output = text_model.make_sentence_with_start(
                root, tries=MAX_MARKOV_ATTEMPTS, strict=False)
        if output is not None:
            return output, nick.title()
    else:
        return 'Error: insufficient data for Markov chain.', DEFAULT_NAME


def generate_nick(person_ids):
    """Generates a nickname based off a list of Members."""
    nickname = ""
    for userid in person_ids:
        curr_nick = NAMES[userid]
        if len(nickname) + len(curr_nick) < MAX_NICKNAME_LENGTH:
            nickname += curr_nick + '+'

    names_in_nickname = nickname[:-1].split('+')

    # Add +n if the list of names was too long, otherwise, remove trailing +
    if len(names_in_nickname) < len(person_ids):
        nickname += str(len(person_ids) - len(names_in_nickname))
    else:
        nickname = nickname[:-1]

    return nickname


def generate_models(userids):
    """Generates a Markov model from a list of Member objects."""
    models = []
    for userid in userids:
        try:
            with open(f'{MODELS_DIRECTORY}{userid}.json', 'r', encoding='utf-8-sig') as json_file:
                models.append(markovify.Text.from_json(json_file.read()))
        except FileNotFoundError:
            raise FileNotFoundError()
    return models


class MarkovBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=["$"], description=DESCRIPTION)
        self.default_nick = DEFAULT_NAME
        self.add_command(self.do)
        self.add_command(self.list)

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
            person_ids = self.parse_names(ctx, person)
        except TooManyInputsError as e:
            error_msg = f'Too many inputs ({e.number}). Max is {MAX_NUM_NAMES}.'
            await ctx.send(error_msg)
            return
        except NameNotFoundError as e:
            error_msg = f'Name not found {e.name}.'
            await ctx.send(error_msg)
            return
        except AmbiguousInputError as e:
            error_msg = f'{e.name} maps to multiple people: {e.output}.'
            await ctx.send(error_msg)
            return

        msg, nick = generate_markov(person_ids, root)

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

    def parse_names(self, ctx, person):
        """Retrieves a string of names and converts them into a list of Member objects."""
        namelist = person.lower().split('+')
        num_names = len(namelist)
        if num_names > MAX_NUM_NAMES:
            raise TooManyInputsError(num_names)
        input_ids = []

        for name in namelist:
            current_name = []
            if name == RANDOM_TAG:
                input_ids.append(random.choice(list(NAMES.keys())))
            elif name == INCLUSIVE_TAG:
                input_ids.extend(random.sample(list(NAMES.keys()), 5))
            elif name == REFLEXIVE_TAG:
                input_ids.append(str(ctx.author.id))
            else:
                for userid in NAMES.keys():
                    if name.lower() == NAMES[userid].lower():
                        input_ids.append(userid)
                        break
                    if name.lower() in NAMES[userid].lower():
                        current_name.append(userid)
                else:
                    if not current_name:
                        raise NameNotFoundError(name)
                    elif len(current_name) == 1:
                        input_ids.append(current_name[0])
                    else:
                        raise AmbiguousInputError(name, [NAMES[userid] for userid in current_name])
        else:
            return input_ids

    def run(self):
        """Runs the bot with the token from the config file."""
        super().run(config.token, reconnect=True)


if __name__ == "__main__":
    bot = MarkovBot()
    bot.run()

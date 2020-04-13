import random
import requests
from threading import Thread

import markovify
import numpy as np
import ujson

from config import sentiment_token
import consts
from consts import MODELS_DIRECTORY, NAMES_FILE, USER_MODEL_FILE, LINKS_FILE, \
    MAX_NICKNAME_LENGTH, MAX_NUM_NAMES, MAX_MARKOV_ATTEMPTS
from helpers import server_toggle as st
from helpers.utility import remove_mentions

DEFAULT_NAME = 'MarkovBot'
DESCRIPTION = "Bot that keeps tracks of when reactions are added/removed."

INCLUSIVE_TAG = 'all'
RANDOM_TAG = 'rand'
REFLEXIVE_TAG = 'me'
BEGIN_TAG = 'BEGIN_LINE'
END_TAG = 'END_LINE'

with open(USER_MODEL_FILE, 'r', encoding='utf-8-sig') as f:
    USER_MODEL = markovify.Text.from_json(f.read())

try:
    with open(LINKS_FILE, 'r', encoding='utf-8-sig') as f:
        LINKS = f.read().splitlines()
except FileNotFoundError:
    LINKS = None


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


class MarkovThread(Thread):
    def __init__(self, ctx, name_str, root, num=1):
        Thread.__init__(self)
        self.ctx = ctx
        self.name_str = name_str
        self.person_ids = None
        self.root = root
        self.num = num

    async def run(self):
        self.person_ids = await get_person_ids(self.ctx, self.name_str)
        if not self.person_ids:
            return

        msg, nick = generate_markov(self.ctx, self.person_ids, self.root, self.num)

        bot_self = self.ctx.guild.me

        msg = remove_mentions(msg, self.ctx.guild)

        # await bot_self.edit(nick=nick)
        if self.num > 1:
            await self.ctx.send(f'**{nick}**:\n{msg}')
        else:
            await self.ctx.send(f'**{nick}**: {msg}')


async def get_person_ids(ctx, name_str):
    try:
        return parse_names(ctx, name_str)
    except TooManyInputsError as e:
        error_msg = f'Too many inputs ({e.number}). Max is {MAX_NUM_NAMES}.'
        await ctx.send(error_msg)
        return None
    except NameNotFoundError as e:
        error_msg = f'Name not found {e.name}.'
        await ctx.send(error_msg)
        return None
    except AmbiguousInputError as e:
        error_msg = f'{e.name} maps to multiple people: {e.output}.'
        await ctx.send(error_msg)
        return None


def get_rand_link():
    """Gets a random link from LINKS."""
    return random.choice(LINKS)


def generate_markov(ctx, person_ids, root, num=1):
    """Generates a Markov sentence and nickname based off a list of Members and a given root."""
    nick = generate_nick(ctx, person_ids)

    model = generate_model(ctx, person_ids)
    if not model:
        return "Unable to retrieve models for " + nick + ".", DEFAULT_NAME

    out = ""
    for _ in range(num):
        sentence = generate_sentence(model, root)
        if sentence:
            out += sentence + '\n'
    if out:
        return out, nick
    else:
        return "Insufficient data for Markov chain.", DEFAULT_NAME


def generate_sentence(model, root=None):
    """Generates a sentence from a text_model and returns the """
    for _ in range(MAX_MARKOV_ATTEMPTS):
        if root is None:
            output = model.make_sentence(tries=MAX_MARKOV_ATTEMPTS)
        else:
            output = model.make_sentence_with_start(
                root, tries=MAX_MARKOV_ATTEMPTS, strict=False)
        if output is not None:
            return output
    else:
        return None


def generate_nick(ctx, person_ids):
    """Generates a nickname based off a list of Members."""
    nickname = ""
    for userid in person_ids:
        user_member = ctx.guild.get_member(userid)
        curr_nick = user_member.nick if user_member.nick is not None else user_member.name
        if len(nickname) + len(curr_nick) < MAX_NICKNAME_LENGTH:
            nickname += curr_nick + '+'

    names_in_nickname = nickname[:-1].split('+')

    # Add +n if the list of names was too long, otherwise, remove trailing +
    if len(names_in_nickname) < len(person_ids):
        nickname += str(len(person_ids) - len(names_in_nickname))
    else:
        nickname = nickname[:-1]

    return nickname


def fill_simulator_queue():
    """Generates a list of userids to post in the htz simulator."""
    users = USER_MODEL.make_sentence().split(' ')
    return users


def get_wait_time(avg, stddev):
    """Gets the wait time between messages in the htz simulator."""
    wait_time = np.random.normal(avg, stddev)
    if wait_time < 1:
        wait_time = 1
    return wait_time


def generate_model(ctx, userids, user_servers=None):
    """Generates a Markov model from a list of Member objects."""
    models = []
    for userid in userids:
        # if not user_servers:
        #     user_servers = st.get_user_servers(userid)
        #     if not user_servers:
        #         continue
        # for server in user_servers:
        try:
            with open(f'{MODELS_DIRECTORY}{ctx.guild.id}/{userid}.json', 'r', encoding='utf-8-sig') as json_file:
                models.append(markovify.Text.from_json(json_file.read()))
        except FileNotFoundError:
            print(f'File not found for userid: {userid}, server: {ctx.guild.id}')
            pass
    if models:
        return markovify.combine(models)
    return None


def parse_names(ctx, person):
    """Retrieves a string of names and converts them into a list of userids."""
    namelist = person.lower().split('+')
    num_names = len(namelist)
    if num_names > MAX_NUM_NAMES:
        raise TooManyInputsError(num_names)
    input_ids = []

    for name in namelist:
        # Handle built-in tags.
        if name == RANDOM_TAG:
            input_ids.append(random.choice([member.id for member in ctx.guild.members]))
        elif name == INCLUSIVE_TAG:
            input_ids.extend(random.sample([member.id for member in ctx.guild.members], 5))
        elif name == REFLEXIVE_TAG:
            input_ids.append(ctx.author.id)

        # Otherwise, search for name in list of guild members.
        else:
            current_ids = []
            for member in ctx.guild.members:
                if member.nick and member.nick.lower() == name.lower():
                    input_ids.append(member.id)
                    break
                elif member.nick and name.lower() in member.nick.lower():
                    current_ids.append(member.id)
                elif member.name.lower() == name.lower():
                    input_ids.append(member.id)
                    break
                elif name.lower() in member.name.lower():
                    current_ids.append(member.id)
            # If exact match not found,
            else:
                if current_ids == []:
                    raise NameNotFoundError(name)
                elif len(current_ids) == 1:
                    input_ids.append(current_ids[0])
                else:
                    raise AmbiguousInputError(
                        name,
                        [ctx.guild.get_member(userid).name for userid in current_ids]
                    )
        
    return input_ids

def print_names(ctx, search=None):
    messages = []
    curr_message = ""
    for member in ctx.guild.members:
        member_name = member.nick if member.nick is not None else member.name
        if search and search.lower() not in member_name.lower():
                continue
        if len(curr_message) + len(member_name) >= consts.MAX_MESSAGE_LENGTH:
            messages.append(curr_message[:-2])
        curr_message += member_name + ', '
    else:
        messages.append(curr_message[:-2])
    return messages


async def get_sentiment_analysis(ctx, name_str=None):
    if name_str:
        userids = await get_person_ids(ctx, name_str)
        if not userids:
            return
    else:
        userids = [str(ctx.author.id)]
    userid = userids[0]

    try:
        with open(consts.SENTIMENT_ANALYSIS_JSON, 'r') as f:
            sentiment_cache = ujson.load(f)
    except FileNotFoundError:
        sentiment_cache = {}

    if userid not in sentiment_cache:
        user_model = generate_model([userid])
        if user_model is None:
            return "Unable to create Markov model of author."

        user_text = ""
        while len(user_text) < consts.MAX_SENTIMENT_TEXT_LENGTH:
            sentence = ""
            while not sentence:
                sentence = user_model.make_sentence()
            user_text += sentence + '\n'

        response = requests.post("https://japerk-text-processing.p.rapidapi.com/sentiment/",
                                 headers={
                                     "X-RapidAPI-Host": "japerk-text-processing.p.rapidapi.com",
                                     "X-RapidAPI-Key": sentiment_token,
                                     "Content-Type": "application/x-www-form-urlencoded"
                                 },
                                 data={
                                     "language": "english",
                                     "text": user_text
                                 }
                                 )
        sentiment_cache[userid] = response.json()
        with open(consts.SENTIMENT_ANALYSIS_JSON, 'w+') as f:
            ujson.dump(sentiment_cache, f)

    sentiment_data = sentiment_cache[userid]

    msg = f"__**{userid}'s Sentiment Analysis**__\n" \
          f"```Label: {sentiment_data['label']}\n\n" \
          f"Probabilities:\n" \
          f"neg: {sentiment_data['probability']['neg']}\n" \
          f"neutral: {sentiment_data['probability']['neutral']}\n" \
          f"pos: {sentiment_data['probability']['pos']}```"

    return msg

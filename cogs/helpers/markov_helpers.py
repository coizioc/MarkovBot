import random

import markovify
import numpy as np

import config
from cogs.helpers import server_toggle as st
from config import MODELS_DIRECTORY, NAMES_FILE, USER_MODEL_FILE, LINKS_FILE, \
    MAX_NICKNAME_LENGTH, MAX_NUM_NAMES, MAX_MARKOV_ATTEMPTS

DEFAULT_NAME = 'MarkovBot'
DESCRIPTION = "Bot that keeps tracks of when reactions are added/removed."

INCLUSIVE_TAG = 'all'
RANDOM_TAG = 'rand'
REFLEXIVE_TAG = 'me'
BEGIN_TAG = 'BEGIN_LINE'
END_TAG = 'END_LINE'

with open(NAMES_FILE, 'r', encoding='utf-8') as f:
    RAW_NAMES = f.read().splitlines()

NAMES = {}
for line in RAW_NAMES:
    id, name = line.split(';')
    NAMES[id] = name

with open(USER_MODEL_FILE, 'r', encoding='utf-8-sig') as f:
    USER_MODEL = markovify.Text.from_json(f.read())

with open(LINKS_FILE, 'r', encoding='utf-8-sig') as f:
    LINKS = f.read().splitlines()


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


def get_rand_link():
    """Gets a random link from LINKS."""
    return random.choice(LINKS)


def get_rand_name():
    """Gets a random name from NAMES."""
    return random.choice(list(NAMES.values()))


def get_name(name):
    """Gets a name from an userid."""
    if name in NAMES.keys():
        return NAMES[name]
    else:
        return None


def generate_markov(person_ids, root, num=1):
    """Generates a Markov sentence and nickname based off a list of Members and a given root."""
    nick = generate_nick(person_ids)

    model = generate_model(person_ids)
    if not model:
        return "No output.", DEFAULT_NAME

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


def fill_simulator_queue():
    """Generates a list of userids to post in the htz simulator."""
    users = USER_MODEL.make_sentence().split(' ')
    return users


def get_wait_time():
    """Gets the wait time between messages in the htz simulator."""
    wait_time = np.random.normal(config.POST_AVG, config.POST_STDDEV)
    if wait_time < 1:
        wait_time = 1
    return wait_time


def generate_model(userids):
    """Generates a Markov model from a list of Member objects."""
    models = []
    for userid in userids:
        user_servers = st.get_user_servers(userid)
        if not user_servers:
            continue
        for server in user_servers:
            try:
                with open(f'{MODELS_DIRECTORY}{server}/{userid}.json', 'r', encoding='utf-8-sig') as json_file:
                    models.append(markovify.Text.from_json(json_file.read()))
            except FileNotFoundError:
                print(f'userid: {userid}, server: {server}')
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

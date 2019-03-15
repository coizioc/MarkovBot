import markovify
import random

import server_toggle as st

from config import MODELS_DIRECTORY, NAMES_FILE

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

    models = generate_models(person_ids)
    if not models:
        return "No output.", DEFAULT_NAME
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
    return models


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
import re
import markovify
import ujson

import random

from config import SIMULATOR_GUILD
from consts import SERVERS_FILE, SERVER_JSON_DIRECTORY, LINKS_FILE


def get_serverid(filename):
    """
    Gets the serverid of a server from its filename.
    :param filename: Name of json file containing the server data.
    :return: The associated serverid of the server, or None if it is not found.
    """
    server_name = filename[:-5]
    with open(SERVERS_FILE, 'r', encoding='utf-8') as f:
        servers = f.read().splitlines()

    for line in servers:
        if server_name in line:
            return line.split(';')[0]
    else:
        with open(f'{SERVER_JSON_DIRECTORY}{filename}', 'r', encoding='utf-8-sig') as f:
            server_json = ujson.load(f)
        try:
            serverid = server_json['meta']['servers'][0]['id']
            servers.append(f'{serverid};{server_name}')
            with open(SERVERS_FILE, 'w+', encoding='utf-8') as f:
                f.write('\n'.join(servers))
            return str(serverid)
        except KeyError:
            return None


def is_mention(word: str):
    return word.startswith('<@') or word.startswith('<@!')

def get_user_tags(msg: str) -> set:
    user_tags = set()
    for line in msg.splitlines():
        user_tags.update([word for word in line.split() if is_mention(word)])
    return user_tags


def remove_mentions(msg, current_guild) -> str:
    """
    Removes mentions from a message.
    :param msg: str
    :param current_guild: Guild object
    :return: the message, with mentions removed.
    """
    user_tags = get_user_tags(msg)
    for user_tag in user_tags:
        userid = int(re.sub('\D', '', user_tag))
        username = current_guild.get_member(userid)
        if username is not None:
            username = username.display_name
            msg = msg.replace(user_tag, '@' + username)
        elif user_tag in msg:
            msg = msg.replace(user_tag, "@UNKNOWN_USER")
    return msg


def get_sim_model(serverid=None):
    """
    Gets the simulator model using the SIMULATOR_GUILD id given in config.py
    :return: the simulator Markov model.
    """
    with open(SERVERS_FILE, 'r', encoding='utf-8') as f:
        server_lines = f.read().splitlines()

    if not serverid:
        serverid = SIMULATOR_GUILD

    for line in server_lines:
        if str(serverid) in line:
            sim_guild_name = line.split(';')[1]
            break
    else:
        raise NameError(f"Server with id {SIMULATOR_GUILD} not found in servers.txt.")

    try:
        with open(f'{sim_guild_name}_sim_model.json', 'r', encoding='utf-8-sig') as f:
            sim_model = markovify.NewlineText.from_json(f.read())
            return sim_model
    except FileNotFoundError:
        return {}
        # raise FileNotFoundError(f'{sim_guild_name}_sim_model.json')


def get_link():
    """
    Returns a random link from the links file.
    :return: str representing the link's url.
    """
    try:
        with open(LINKS_FILE, 'r', encoding='utf-8') as f:
            links = f.read().splitlines()
        return random.choice(links)
    except FileNotFoundError:
        return None

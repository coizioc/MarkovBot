import ujson
import os

import consts
from consts import SERVERS_FILE, OPTIONS_DIRECTORY

with open(SERVERS_FILE, 'r', encoding='utf-8') as f:
    RAW_SERVERS = f.read().splitlines()

SERVERS = {}
for line in RAW_SERVERS:
    server_id, name = line.split(';')
    SERVERS[server_id] = name


def get_serverid(server):
    for serverid, name in SERVERS.items():
        if server == name:
            return serverid
    else:
        return None


def get_user_servers(userid):
    user_json = open_user_options(userid)

    if 'servers' in user_json.keys():
        return user_json['servers']
    else:
        return None


def is_server(server):
    return server in SERVERS.values()


def list_servers(userid):
    out = 'List of MarkovBot Servers:\n'
    user_servers = get_user_servers(userid)
    for server_id, name in SERVERS.items():
        if os.path.isfile(f'{consts.MODELS_DIRECTORY}{server_id}/{userid}.json'):
            if user_servers and server_id in user_servers:
                out += f'**{name}**\n'
            else:
                out += name + '\n'
    out += '**Bolded** servers have been toggled on. To toggle a specific server, type `$toggle <server>`.'
    return out


def open_user_options(userid):
    try:
        with open(f'{OPTIONS_DIRECTORY}{userid}.json', 'r', encoding='utf-8-sig') as f:
            user_json = ujson.load(f)
            return user_json
    except FileNotFoundError:
        return dict()


def save_user_options(userid, user_dict):
    with open(f'{OPTIONS_DIRECTORY}{userid}.json', 'w+', encoding='utf-8-sig') as f:
        ujson.dump(user_dict, f)


def toggle_server(userid, server):
    """Toggles whether a user wants a server to appear in their Markov results."""
    user_dict = open_user_options(userid)
    server_added = False
    serverid = get_serverid(server)
    if 'servers' not in user_dict.keys():
        user_dict['servers'] = []
    if serverid in user_dict['servers']:
        user_dict['servers'].remove(serverid)
    else:
        user_dict['servers'].append(serverid)
        server_added = True
    save_user_options(userid, user_dict)
    return server_added


def toggle_markov(userid):
    """Toggles whether a user wants to be in Markov chains."""
    user_dict = open_user_options(userid)
    markov_activated = False
    if user_dict['markov']:
        user_dict['markov'] = False
    else:
        user_dict['markov'] = True
        markov_activated = True
    save_user_options(userid, user_dict)
    return markov_activated

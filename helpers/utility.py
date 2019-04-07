import re
import ujson

from consts import SERVERS_FILE, SERVER_JSON_DIRECTORY


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


def remove_mentions(msg, current_guild):
    """
    Removes mentions from a message.
    :param msg: str
    :param current_guild: Guild object
    :return: the message, with mentions removed.
    """
    user_tags = set([c for c in msg.split(' ') if c[0:2] == '<@'])
    for user_tag in user_tags:
        userid = int(re.sub('\D', '', user_tag))
        username = current_guild.get_member(userid)
        if username is not None:
            username = username.display_name
            msg = msg.replace(user_tag, '@' + username)
        elif user_tag in msg:
            msg = msg.replace(user_tag, "@UNKNOWN_USER")
    return msg

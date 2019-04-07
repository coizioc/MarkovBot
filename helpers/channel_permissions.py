import ujson

from consts import CHANNEL_PERMISSIONS_JSON

WHITELIST_KEY = 'white'            # list containing all channels in a guild in which the bot can run commands.
BLACKLIST_KEY = 'black'            # list containing all channels in a guild in which the bot cannot run commands.
SIMULATION_KEY = 'sim'             # int representing the channelid of the channel where the simulation will go.


def add_channel(guildid, channelid, key):
    """Adds a channel to the file."""
    guildid = str(guildid)
    try:
        perms = get_file()
        guild_perms = perms[str(guildid)]
    except KeyError:
        perms[guildid] = {key: [channelid]}
        write(perms)
        return

    try:
        perms[guildid][key].append(channelid)
    except KeyError:
        perms[guildid][key] = [channelid]

    write(perms)


def clear_channel(guildid, key):
    """Removes a channel from the file."""
    guildid = str(guildid)
    try:
        perms = get_file()
        guild_perms = perms[str(guildid)]
    except KeyError:
        raise ValueError

    try:
        perms[guildid].pop(key, None)
        write(perms)
    except KeyError:
        raise ValueError
    except ValueError:
        raise ValueError


def get_channel(guildid, key):
    """Gets the channelid associated with the key."""
    guildid = str(guildid)
    try:
        channelid = get_file()[str(guildid)][key]
        if type(channelid) is int:
            return channelid
        else:
            raise ValueError
    except KeyError:
        return None


def get_file():
    """Opens the permissions file, or returns an empty dict if it does not exist."""
    try:
        with open(CHANNEL_PERMISSIONS_JSON, 'r') as f:
            return ujson.load(f)
    except FileNotFoundError:
        with open(CHANNEL_PERMISSIONS_JSON, 'w+') as f:
            ujson.dump({}, f)
        return {}


def get_guild(guildid):
    """Gets the white/blacklist for a guild, or raises a KeyError if it is not found."""
    try:
        return get_file()[str(guildid)]
    except KeyError:
        return {}


def remove_channel(guildid, channelid, key):
    """Removes a channel from the file."""
    guildid = str(guildid)
    try:
        perms = get_file()
        guild_perms = perms[str(guildid)]
    except KeyError:
        raise ValueError

    try:
        perms[guildid][key].remove(channelid)
        write(perms)
    except KeyError:
        raise ValueError
    except ValueError:
        raise ValueError


def set_channel(guildid, channelid, key):
    """Sets the channelid associated with the key."""
    guildid = str(guildid)
    try:
        perms = get_file()
        perms[guildid][key] = channelid
    except KeyError:
        perms[guildid] = {}
        perms[guildid][key] = channelid
    write(perms)


def write(permissions_dict):
    """Writes the permissions dict to a json file."""
    with open(CHANNEL_PERMISSIONS_JSON, 'w+') as f:
        ujson.dump(permissions_dict, f)

import datetime
import os
import re
import ujson

from discord import Embed

from config import SIMULATOR_CHANNEL
from consts import SERVERS_FILE, SERVER_JSON_DIRECTORY


def read_servers_file():
    with open(SERVERS_FILE, 'r+', encoding='utf-8') as f:
        server_file_lines = f.read().splitlines()
    servers = {}
    for line in server_file_lines:
        guildid, server_name = line.split(';')
        servers[guildid] = server_name
    return servers


def write_servers_file(servers_json):
    out = ''
    for guildid, server_name in servers_json.items():
        out += f'{guildid};{server_name}\n'

    with open(SERVERS_FILE, 'w+', encoding='utf-8') as f:
        f.write(out)


def init_server_json(ctx):
    server_json = {'meta': {}, 'data': {}}

    server_json['meta']['users'] = {}
    server_json['meta']['userindex'] = []
    server_json['meta']['servers'] = [{"name": ctx.guild.name, "id": ctx.guild.id, "type": "SERVER"}]
    server_json['meta']['channels'] = {}

    return server_json


def get_last_message_timecode(server_json, channelid):
    if channelid in server_json['data'].keys():
        latest_timestamp = 946684800
        for message in server_json['data'][channelid].values():
            curr_timecode = int(message['t']) // 1000
            if curr_timecode > latest_timestamp:
                latest_timestamp = curr_timecode
        return latest_timestamp
    else:
        return None


def get_message_json(message, author_index):
    message_json = {'u': author_index, 't': message.created_at.timestamp() * 1000, 'm': message.content}

    if message.edited_at:
        message_json['f'] = 1

    message_embeds = message.embeds
    if message_embeds:
        message_json['e'] = []
        for embed in message_embeds:
            if embed.url == Embed.Empty or embed.type == Embed.Empty:
                continue
            embed_json = {"url": embed.url, "type": embed.type}
            if embed_json['type'] == 'rich':
                if embed.title == Embed.Empty or embed.description == Embed.Empty:
                    continue
                embed_json['t'] = embed.title
                embed_json['d'] = embed.description
            message_json['e'].append(embed_json)

    message_links = re.findall('https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', message.content)
    if message_links:
        message_json['a'] = []
        for link in message_links:
            message_json['a'].append({"url": link})

    return message_json


async def setup_server(ctx):
    guildid = str(ctx.guild.id)
    servers = read_servers_file()
    try:
        server_name = servers[guildid]
        print('server found')
    except KeyError:
        servers[guildid] = ctx.guild.name.replace(';', ':')
        server_name = servers[guildid]
        print('server added to list of servers')

    write_servers_file(servers)

    server_filename = "".join(x for x in server_name if x.isalnum())

    try:
        with open(f'{SERVER_JSON_DIRECTORY}{server_filename}.json', 'r', encoding='utf-8-sig') as f:
            server_json = ujson.load(f)
    except FileNotFoundError:
        server_json = init_server_json(ctx)

    curr_channel_num = 1
    num_channels = len(ctx.guild.text_channels)
    for channel in ctx.guild.text_channels:
        if channel.id == SIMULATOR_CHANNEL:
            print('Skipping simulator channel...')
            continue
        if ctx.guild.me not in channel.members:
            print(f'Unable to scrape channel ({curr_channel_num}/{num_channels}) (Forbidden)...')
            curr_channel_num += 1
            continue

        channelid = str(channel.id)
        if channelid not in server_json['meta']['channels'].keys():
            channel_json = {"server": 0, "name": channel.name}
            server_json['meta']['channels'][channelid] = channel_json

        last_message_timestamp = get_last_message_timecode(server_json, channelid)
        if not last_message_timestamp:
            last_message_datetime = None
            server_json['data'][channelid] = {}
        else:
            last_message_datetime = datetime.datetime.fromtimestamp(last_message_timestamp)

        print(f'Scraping #{channel.name} ({curr_channel_num}/{num_channels}) after {last_message_datetime}...')

        async for message in channel.history(limit=None, after=last_message_datetime):
            message_author = message.author
            authorid = str(message_author.id)
            if authorid not in server_json['meta']['userindex']:
                user_json = {'name': message_author.name}
                server_json['meta']['userindex'].append(authorid)
                author_index = len(server_json['meta']['userindex']) - 1
                server_json['meta']['users'][authorid] = user_json
            else:
                author_index = server_json['meta']['userindex'].index(authorid)

            message_json = get_message_json(message, author_index)
            messageid = str(message.id)

            server_json['data'][channelid][messageid] = message_json
        curr_channel_num += 1
    print(f"Server saved to {server_filename}.json!")

    if not os.path.exists(SERVER_JSON_DIRECTORY):
        os.makedirs(SERVER_JSON_DIRECTORY)
    with open(f'{SERVER_JSON_DIRECTORY}{server_filename}.json', 'w+') as f:
        ujson.dump(server_json, f)

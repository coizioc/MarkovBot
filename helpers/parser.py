import os
import ujson
from datetime import datetime

import markovify

from consts import SERVER_JSON_DIRECTORY, MESSAGES_DIRECTORY, NAMES_FILE
from helpers.utility import get_serverid


def append_text(messages, serverid):
    print('writing users...')
    start_time = datetime.now()
    for userid, corpus in messages.items():
        if corpus:
            with open(f'{MESSAGES_DIRECTORY}{serverid}/{userid}.txt', 'a+', encoding='utf-8') as f:
                f.write(corpus)
    print(f"Wrote in {datetime.now() - start_time}")


def gen_simmodel(filename):
    with open(f'{SERVER_JSON_DIRECTORY}{filename}', 'r', encoding='utf-8-sig') as f:
        server_json = ujson.load(f)

    server_name = filename[:-5]
    userids = list(server_json['meta']['userindex'])

    out = ''
    for channel in server_json['data'].keys():
        for message in server_json['data'][channel].keys():
            out += userids[int(server_json['data'][channel][message]['u'])] + ' '
            if len(out) > 1000:
                out += '\n'
    sim_model = markovify.NewlineText(out)
    with open(f'{server_name}_sim_model.json', 'w+') as f:
        f.write(sim_model.to_json())
    print(f'{server_name}_sim_model.json successfully written!')


def init_message_files(serverid, userids):
    if not os.path.isdir(MESSAGES_DIRECTORY):
        os.mkdir(MESSAGES_DIRECTORY)
    if not os.path.isdir(f"{MESSAGES_DIRECTORY}{serverid}/"):
        os.mkdir(f'{MESSAGES_DIRECTORY}{serverid}/')

    for user_id in userids:
        with open(f'{MESSAGES_DIRECTORY}{serverid}/{user_id}.txt', 'w+', encoding='utf-8-sig') as f:
            f.write('')


def update_names(server_json):
    out = ""
    for userid in server_json['meta']['users']:
        out += f"{userid};{server_json['meta']['users'][userid]['name'].replace(';', ':')}\n"
    new_names = out.split('\n')
    with open(NAMES_FILE, 'r+', encoding='utf-8-sig') as f:
        old_names = f.read().splitlines()

    for name in new_names:
        if name not in old_names:
            old_names.append(name)

    with open(NAMES_FILE, 'w+', encoding='utf-8-sig') as f:
        f.write('\n'.join(old_names))


def parse_server(filename):
    with open(f'{SERVER_JSON_DIRECTORY}{filename}', 'r', encoding='utf-8-sig') as f:
        server_json = ujson.load(f)

    serverid = get_serverid(filename)
    if not serverid:
        raise NameError("Server not found.")

    # Initialize the files for each user.
    userids = list(server_json['meta']['userindex'])
    init_message_files(serverid, userids)

    update_names(server_json)

    channel_ids = list(server_json['data'].keys())
    num_channels = len(channel_ids)

    curr_channel_num = 1

    begin_time = datetime.now()

    messages = {}
    msg_in_messages = 0

    for channelid in channel_ids:
        print(f"Parsing channel {curr_channel_num}/{num_channels}...")
        message_ids = server_json["data"][channelid].keys()

        curr_message_no = 1
        num_messages = len(message_ids)
        for messageid in message_ids:
            if curr_message_no % 10000 == 0:
                print(f"Message {curr_message_no}/{num_messages}")
            try:
                message = server_json["data"][channelid][messageid]['m']
                user_index = server_json["data"][channelid][messageid]['u']
                userid = userids[int(user_index)]
                if userid not in messages.keys():
                    messages[userid] = ''
                messages[userid] += f'{message}\n'
                msg_in_messages += 1
                if msg_in_messages >= 100000:
                    append_text(messages, serverid)
                    messages = {}
                    msg_in_messages = 0
            except KeyError:
                print(f'keyerror: {messageid}')
                pass
            curr_message_no += 1
        curr_channel_num += 1

    print(f'Parse time: {datetime.now() - begin_time}')
    append_text(messages, serverid)


def count_replies(filename):
    serverid = get_serverid(filename)
    if not serverid:
        raise NameError("Server not found.")

    with open(filename, 'r', encoding='utf-8-sig') as f:
        server_json = ujson.load(f)

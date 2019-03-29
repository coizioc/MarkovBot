import ujson

from config import MESSAGES_DIRECTORY, NAMES_FILE, SERVERS_FILE

from datetime import datetime


def get_serverid(filename):
    server_name = filename[:-5]
    with open(SERVERS_FILE, 'r', encoding='utf-8-sig') as f:
        servers = f.read().splitlines()

    for line in servers:
        if server_name in line:
            return line.split(';')[0]
    else:
        return None


def update_names(server_json):
    out = ""
    for userid in server_json['meta']['users']:
        out += f"{userid};{server_json['meta']['users'][userid]['name']}\n"
    new_names = out.split('\n')
    with open(NAMES_FILE, 'r', encoding='utf-8-sig') as f:
        old_names = f.read().splitlines()

    for name in new_names:
        if name not in old_names:
            old_names.append(name)

    with open(NAMES_FILE, 'w+', encoding='utf-8-sig') as f:
        f.write('\n'.join(old_names))


def append_text(messages, serverid):
    for userid, corpus in messages.items():
        if corpus:
            with open(f'{MESSAGES_DIRECTORY}{serverid}/{userid}.txt', 'a+') as f:
                f.write(corpus)


def parse_server(filename):
    serverid = get_serverid(filename)
    if not serverid:
        raise NameError("Server not found.")

    with open(filename, 'r', encoding='utf-8-sig') as f:
        server_json = ujson.load(f)

    # Initialize the files for each user.
    userids = list(server_json['meta']['userindex'])
    for user_id in userids:
        with open(f'{MESSAGES_DIRECTORY}{serverid}/{user_id}.txt', 'w+', encoding='utf-8-sig') as f:
            f.write('')

    update_names(server_json)

    channel_ids = list(server_json['data'].keys())
    num_channels = len(channel_ids)

    curr_channel_num = 1
    curr_message_no = 1

    begin_time = datetime.now()

    print(begin_time)

    messages = {}
    msg_in_messages = 0

    for channelid in channel_ids:
        print(f"Parsing channel {curr_channel_num}/{num_channels}...")
        message_ids = server_json["data"][channelid].keys()
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
        curr_message_no = 1
        curr_channel_num += 1

    print(f'Parse time: {datetime.now() - begin_time}')
    begin_time = datetime.now()
    print('writing users...')
    append_text(messages, serverid)

    print(f'Write time: {datetime.now() - begin_time}')


def count_replies(filename):
    serverid = get_serverid(filename)
    if not serverid:
        raise NameError("Server not found.")

    with open(filename, 'r', encoding='utf-8-sig') as f:
        server_json = ujson.load(f)


if __name__ == '__main__':
    file = 'htz.json'
    parse_server(file)

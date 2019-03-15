import ujson

from config import MESSAGES_DIRECTORY

SERVER_ID = '529904258233925632'

with open('tt4_main.json', 'r', encoding='utf-8-sig') as f:
    DATA = ujson.load(f)

channel_ids = list(DATA['data'].keys())
num_channels = len(channel_ids)

userids = list(DATA['meta']['userindex'])

out = ""
for userid in DATA['meta']['users']:
    out += f"{userid};{DATA['meta']['users'][userid]['name']}\n"
new_names = out.split('\n')
with open('names.txt', 'r', encoding='utf-8-sig') as f:
    old_names = f.read().splitlines()

for name in new_names:
    if name not in old_names:
        old_names.append(name)

with open('names.txt', 'w+', encoding='utf-8-sig') as f:
    f.write('\n'.join(old_names))

i = 1
j = 1
for channelid in channel_ids:
    print(f"Parsing channel {i}/{num_channels}..." )
    message_ids = DATA["data"][channelid].keys()
    num_messages = len(message_ids)
    for messageid in message_ids:
        if j % 1000 == 0:
            print(f"Message {j}/{num_messages}")
        try:
            message = DATA["data"][channelid][messageid]['m']
            user_index = DATA["data"][channelid][messageid]['u']
            with open(f'{MESSAGES_DIRECTORY}{SERVER_ID}/{userids[int(user_index)]}.txt', 'a+') as f:
                f.write(message + "\n")
        except KeyError:
            print(f'keyerror: {messageid}')
            pass
        j += 1
    j = 1
    i += 1

if __name__ == '__main__':
    server_json = 'tt4_main.json'

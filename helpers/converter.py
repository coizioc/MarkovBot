import os
import re

import markovify

from consts import MESSAGES_DIRECTORY, MODELS_DIRECTORY, POST_SEPARATOR
from helpers.utility import get_serverid


class Post(markovify.Text):
    def sentence_split(self, text):
        return re.split(rf"\s*{POST_SEPARATOR}\s*", text)


def convert_server(filename=None, serverid=None):
    if not filename and not serverid:
        return
    if not serverid:
        serverid = get_serverid(filename)
        if not serverid:
            raise NameError("Server not found.")

    server_messages_dir = f'{MESSAGES_DIRECTORY}{serverid}/'
    server_model_dir = f'{MODELS_DIRECTORY}{serverid}/'
    if not os.path.isdir(server_messages_dir):
        print(f'serverid {serverid} not found in messages.')
        return
    print("Converting server " + serverid)

    if not os.path.exists(MODELS_DIRECTORY):
        os.mkdir(MODELS_DIRECTORY)
    if not os.path.exists(server_model_dir):
        os.mkdir(server_model_dir)
    for user_file in os.listdir(server_messages_dir):
        if not user_file.endswith('.txt'):
            continue
        userid = user_file[:-4]
        print(f' * Convering user {userid}')
        with open(f'{server_messages_dir}{userid}.txt', 'r', encoding='utf-8-sig') as message_fp:
            data = message_fp.read()
            if not data.isspace():
                try:
                    model = Post(data)
                    with open(f'{server_model_dir}{userid}.json', 'w+', encoding='utf-8-sig') as model_fp:
                        model_fp.write(model.to_json())
                except KeyError as e:
                    print(e)
                    print("error with user's json")
                    continue

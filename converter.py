import markovify
import os

from config import MESSAGES_DIRECTORY, MODELS_DIRECTORY


def convert_servers():
    for serverid in os.listdir(MESSAGES_DIRECTORY):
        print("Converting server " + serverid)
        server_dir = f'{MODELS_DIRECTORY}{serverid}'
        if not os.path.exists(server_dir):
            os.mkdir(server_dir)
        for user_file in os.listdir(f'{MESSAGES_DIRECTORY}{serverid}'):
            if not user_file.endswith('.txt'):
                continue
            userid = user_file[:-4]
            print(f'* Convering user {userid}')
            with open(f'{MESSAGES_DIRECTORY}{serverid}/{user_file}', 'r', encoding='utf-8-sig') as f:
                data = f.read()
            if not data.isspace():
                model = markovify.NewlineText(data)
                with open(f'{server_dir}/{userid}.json', 'w+', encoding='utf-8-sig') as f:
                    f.write(model.to_json())


if __name__ == '__main__':
    convert_servers()

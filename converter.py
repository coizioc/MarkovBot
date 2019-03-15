import markovify
import os

from config import MESSAGES_DIRECTORY, MODELS_DIRECTORY

SERVER_ID = '529904258233925632'

for user_file in os.listdir(f'{MESSAGES_DIRECTORY}{SERVER_ID}/'):
    if not user_file.endswith('.txt'):
        continue
    userid = user_file[:-4]
    print(userid)
    with open(f'{MESSAGES_DIRECTORY}{SERVER_ID}/{user_file}', 'r', encoding='utf-8-sig') as f:
        data = f.read()
    if not data.isspace():
        model = markovify.NewlineText(data)
        with open(f'{MODELS_DIRECTORY}{SERVER_ID}/{userid}.json', 'w+', encoding='utf-8-sig') as f:
            f.write(model.to_json())
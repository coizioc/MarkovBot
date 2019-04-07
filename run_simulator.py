import argparse
import asyncio
import ujson

import markovify
import numpy as np
from discord.ext import commands

import config
import consts
from helpers.markov_helpers import get_wait_time
from helpers.utility import remove_mentions, get_sim_model

try:
    with open('bots.json', 'r', encoding='utf-8-sig') as f:
        BOTS = ujson.load(f)
except FileNotFoundError:
    BOTS = None

SIM_MODEL = get_sim_model()

POST_AVG = 25
POST_STDDEV = 10
NAMES_IN_MSG = []


def find_names(msg):
    """Finds names in a message."""
    for userid in BOTS.keys():
        for name in BOTS[userid]['names']:
            if name in msg:
                NAMES_IN_MSG.append(userid)
                break


class MarkovSimulator(commands.Bot):
    def __init__(self, args):
        super().__init__(command_prefix="mk!", description="hi dere")
        self.token = config.sim_token
        self.topic = None
        self.queue = []
        if args.post_avg:
            self.avg = args.post_avg
        else:
            self.avg = POST_AVG
        if args.post_stddev:
            self.stddev = args.post_stddev
        else:
            self.stddev = POST_STDDEV

    def run(self):
        """Runs the bot with the token from the config file."""
        super().run(self.token, reconnect=True)

    def open_model(self, userid):
        with open(f'{consts.MODELS_DIRECTORY}{config.SIMULATOR_GUILD}/{userid}.json', 'r', encoding='utf-8-sig') as f:
            model = markovify.Text.from_json(f.read())
        return model

    def fill_queue(self):
        out = ''
        while not out:
            out = SIM_MODEL.make_sentence()
        self.queue = out.split(' ')

    def get_model(self, userid):
        try:
            with open(f'models/465791490526937088/{userid}.json', 'r', encoding='utf-8-sig') as f:
                model = markovify.Text.from_json(f.read())
            return model
        except FileNotFoundError:
            return None

    async def on_ready(self):
        bot_guild = self.get_guild(config.SIMULATOR_GUILD)
        bot_channel = bot_guild.get_channel(config.SIMULATOR_CHANNEL)
        print(f'Running bot on guild: {bot_guild}\nchannel: {bot_channel}')
        while True:
            next_user_member = None
            # Pop next poster from queue
            if not self.queue:
                self.fill_queue()
            curr_userid = self.queue.pop(0)
            next_user_member = bot_guild.get_member(int(curr_userid))
            if not next_user_member:
                continue

            model = self.get_model(curr_userid)
            if not model:
                continue

            for userid in NAMES_IN_MSG:
                self.queue.insert(np.random.randint(0, 2), userid)

            for _ in range(3):
                if self.topic:
                    try:
                        msg = model.make_sentence_with_start(self.topic)
                        if msg:
                            # If topic, remove topic from sentence.
                            msg = msg.split(' ', 1)[1]
                            break
                    except KeyError:
                        msg = model.make_sentence()
                        if msg:
                            break
            else:
                msg = model.make_sentence()

            if msg:
                self.topic = msg.split(' ')[-1]
                find_names(msg)
                msg = remove_mentions(msg, bot_guild)
                nick = next_user_member.nick
                if not nick:
                    nick = next_user_member.name
                msg = f'**{nick}**: {msg}'

                await bot_channel.send(msg)

            wait_time = get_wait_time(self.avg, self.stddev)
            await asyncio.sleep(wait_time)


if __name__ == '__main__':
    # TODO add setup code
    parser = argparse.ArgumentParser(description='Server simulator for MarkovBot.')
    # parser.add_argument('--setup', dest='do_setup', action='store_true',
    #                     help="Boots the simulator in setup mode.")
    parser.add_argument('--avg', dest='post_avg', type=int, nargs=1,
                        help=f"The average time between posts (default: {POST_AVG})")
    parser.add_argument('--stddev', dest='post_stddev', type=int, nargs=1,
                        help=f"The average standard deviation between posts (default {POST_STDDEV})")
    args = parser.parse_args()

    MarkovSimulator(args).run()

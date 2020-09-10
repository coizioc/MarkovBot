import argparse
import asyncio
import random
import ujson

import markovify
from discord.ext import commands
from discord import Embed
from discord.errors import HTTPException

import config
import consts
import helpers.setup_helpers as setuph
from helpers.markov_helpers import get_wait_time
from helpers.utility import remove_mentions, get_sim_model, get_link

try:
    with open('bots.json', 'r', encoding='utf-8-sig') as f:
        BOTS = ujson.load(f)
except FileNotFoundError:
    BOTS = None

SIM_MODEL = get_sim_model()

DEBUG_POST_AVG = 25
DEBUG_POST_STDDEV = 10
DEBUG_EMBED_RATE = 0.9

POST_AVG = 1800
POST_STDDEV = 900
EMBED_RATE = 0.04
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
        super().__init__(command_prefix="mk$", description="Simulator for MarkovBot.")
        self.token = config.sim_token
        self.do_setup = args.do_setup
        self.debug_vals = args.debug_vals
        if not args.do_setup:
            self.topic = None
            self.queue = []

            if args.post_avg:
                self.avg = args.post_avg
            else:
                self.avg = DEBUG_POST_AVG if self.debug_vals else POST_AVG
            if args.post_stddev:
                self.stddev = args.post_stddev
            else:
                self.stddev = DEBUG_POST_STDDEV if self.debug_vals else POST_STDDEV
            if args.embed:
                if args.embed > 1 or args.embed < 0:
                    print("Embed rate must be between 0 and 1.")
                    exit()
                self.embed_rate = args.embed
            else:
                self.embed_rate = DEBUG_EMBED_RATE if self.debug_vals else EMBED_RATE

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
            with open(f'models/{config.SIMULATOR_GUILD}/{userid}.json', 'r', encoding='utf-8-sig') as f:
                model = markovify.Text.from_json(f.read())
            return model
        except FileNotFoundError:
            return None

    async def on_ready(self):
        if self.debug_vals:
            bot_guild = self.get_guild(config.DEBUG_SIMULATOR_GUILD)
            bot_channel = bot_guild.get_channel(config.DEBUG_SIMULATOR_CHANNEL)
        else:
            bot_guild = self.get_guild(config.SIMULATOR_GUILD)
            bot_channel = bot_guild.get_channel(config.SIMULATOR_CHANNEL)
        print(f'Running bot on guild: {bot_guild}\nchannel: {bot_channel}')
        if self.do_setup:
            await setuph.setup_server(bot_channel)
        else:
            await self.do_sim(bot_guild, bot_channel)

    async def do_sim(self, bot_guild, bot_channel):
        while True:
            next_user_member = None
            # Pop next poster from queue
            if not self.queue:
                self.fill_queue()
            curr_userid = self.queue.pop(0)
            if curr_userid == '':
                print(self.queue)
                raise ValueError()
            if curr_userid in config.IGNORE_USERS:
                continue
            next_user_member = bot_guild.get_member(int(curr_userid))
            if not next_user_member:
                continue

            model = self.get_model(curr_userid)
            if not model:
                continue

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
                
                msg = remove_mentions(msg, bot_guild)
                nick = next_user_member.nick
                if not nick:
                    nick = next_user_member.name

                # Add image
                if random.random() < self.embed_rate:
                    e = Embed()
                    while True:
                        link = get_link()
                        if link is None or 'discordapp' in link:
                            break
                    if link is not None:
                        e.set_image(url=link)
                    else:
                        e = None
                else:
                    e = None

                try:
                    webhook_avatar = await next_user_member.avatar_url.read()
                    webhook = await bot_channel.create_webhook(name=nick, avatar=webhook_avatar)
                    try:
                        await webhook.send(msg, embed=e)
                        print(nick, ':', msg)
                    except HTTPException:
                        pass
                    await webhook.delete()
                except Exception:
                    continue

            wait_time = get_wait_time(self.avg, self.stddev)
            await asyncio.sleep(wait_time)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Server simulator for MarkovBot.')
    parser.add_argument('--debug', dest='debug_vals', action='store_true',
                        help="Set debug values for post_avg, post_stddev, and embed rate.")
    parser.add_argument('--update', dest='do_setup', action='store_true',
                        help="Updates/Creates the server json for the simulator server.")
    parser.add_argument('--avg', dest='post_avg', type=int, nargs=1,
                        help=f"The average time between posts (default: {POST_AVG})")
    parser.add_argument('--stddev', dest='post_stddev', type=int, nargs=1,
                        help=f"The average standard deviation between posts (default {POST_STDDEV})")
    parser.add_argument('--embed', dest='embed', type=float, nargs=1,
                        help=f"Percent of posts that will contain images (default {EMBED_RATE})")
    args = parser.parse_args()

    MarkovSimulator(args).run()

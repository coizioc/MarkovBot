import asyncio
import ujson
from threading import Thread

import markovify
import numpy as np
from discord.ext import commands

import config
from helpers.markov_helpers import get_wait_time
from helpers.utility import remove_mentions

with open('bots.json', 'r', encoding='utf-8-sig') as f:
    BOTS = ujson.load(f)

with open('htz_user_model.json', 'r', encoding='utf-8-sig') as f:
    USER_MODEL = markovify.NewlineText.from_json(f.read())


FINISH_POST_SIGNAL = asyncio.Event()
NAMES_IN_MSG = []


class QueueThread(Thread):
    def __init__(self, bots):
        Thread.__init__(self)
        self.queue = []
        self.bot_threads = bots

    async def run(self):
        while True:
            # Pop next poster from queue
            if not self.queue:
                self.fill_queue()
            curr_userid = self.queue.pop(0)
            curr_bot = self.get_bot(curr_userid)
            if not curr_bot:
                continue

            curr_bot.bot.post_signal.set()
            await FINISH_POST_SIGNAL.wait()
            FINISH_POST_SIGNAL.clear()
            for userid in NAMES_IN_MSG:
                self.queue.insert(np.random.randint(0, 2), userid)

            wait_time = get_wait_time()
            await asyncio.sleep(wait_time)

    def fill_queue(self):
        self.queue = USER_MODEL.make_sentence().split(' ')

    def get_bot(self, userid):
        for bot_thread in self.bot_threads:
            if bot_thread.userid == userid:
                return bot_thread
        else:
            return None


class BotThread(Thread):
    def __init__(self, userid: str, token: str, names: list):
        Thread.__init__(self)
        self.userid = userid
        self.bot = MarkovBot(userid, token, names)


class MarkovBot(commands.Bot):
    topic = None

    def __init__(self, userid, token, names):
        super().__init__(command_prefix="mk!", description="hi dere")
        self.token = token
        self.model: markovify.Text = self.open_model(userid)
        self.names = names
        self.post_signal = asyncio.Event()

    def open_model(self, userid):
        with open(f'{config.MODELS_DIRECTORY}{config.HTZ_GUILD}/{userid}.json', 'r', encoding='utf-8-sig') as f:
            model = markovify.Text.from_json(f.read())
        return model

    async def on_ready(self):
        bot_guild = self.get_guild(config.DEFAULT_GUILD_ID)
        bot_channel = bot_guild.get_channel(config.SIMULATOR_CHANNEL)
        while True:
            await self.post_signal.wait()

            for _ in range(3):
                if self.topic:
                    try:
                        msg = self.model.make_sentence_with_start(self.topic)
                        if msg:
                            # If topic, remove topic from sentence.
                            msg = msg.split(' ', 1)[1]
                            break
                    except KeyError:
                        msg = self.model.make_sentence()
                        if msg:
                            break
            else:
                msg = self.model.make_sentence()

            if msg:
                self.topic = msg.split(' ')[-1]
                find_names(msg)
                msg = remove_mentions(msg, bot_guild)

                await bot_channel.send(msg)

            self.post_signal.clear()
            FINISH_POST_SIGNAL.set()


def find_names(msg):
    """Finds names in """
    for userid in BOTS.keys():
        for name in BOTS[userid]['names']:
            if name in msg:
                NAMES_IN_MSG.append(userid)
                break


def print_links():
    for userid in BOTS.keys():
        if BOTS[userid]['client']:
            print(f"{BOTS[userid]['names'][0]}: "
                  f"https://discordapp.com/oauth2/authorize?client_id={BOTS[userid]['client']}&scope=bot&permissions=0")


if __name__ == '__main__':
    bots = []
    loop = asyncio.get_event_loop()
    for userid in BOTS.keys():
        if BOTS[userid]['token']:
            bots.append(BotThread(userid, BOTS[userid]['token'], BOTS[userid]['names']))
    for bot_thread in bots:
        loop.create_task(bot_thread.bot.start(bot_thread.bot.token))
    loop.create_task(QueueThread(bots).run())
    try:
        loop.run_forever()
    finally:
        loop.stop()

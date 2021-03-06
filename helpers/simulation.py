import asyncio
import random
import re
from threading import Thread

import config
from helpers import channel_permissions as cp
from helpers import markov_helpers as mk
from helpers.utility import remove_mentions


class SimThread(Thread):
    def __init__(self, bot, topic=""):
        """ Constructor for SimThread. """
        Thread.__init__(self)
        self.bot = bot
        self.sim_queue = []
        self.topic = topic
        self.total_simulation_messages = 0
        self.simulation_on = asyncio.Event()

    async def run(self):
        await self.bot.wait_until_ready()
        bot_guild = self.bot.get_guild(config.SIMULATOR_GUILD)
        bot_channel = bot_guild.get_channel(cp.get_channel(config.SIMULATOR_CHANNEL, cp.SIMULATION_KEY))
        bot_self = bot_guild.me
        print(f'Guild: {bot_guild.id}, Channel: {bot_channel.id}, Bot: {bot_self.id}')
        while not self.bot.is_closed():
            await self.simulation_on.wait()
            # Fills the queue if empty, otherwise pops the first element
            user_model = None
            next_user = None
            next_user_member = None
            out = None
            try:
                while not out:
                    while not user_model:
                        if not self.sim_queue:
                            self.sim_queue = mk.fill_simulator_queue()
                        next_user = self.sim_queue.pop(0)
                        if next_user in config.IGNORE_USERS:
                            continue
                        print(next_user)
                        next_user_member = bot_guild.get_member(int(next_user))
                        if not next_user_member:
                            continue

                        # Generates the model for the user and generates a sentence for that user.
                        user_model = mk.generate_model([next_user], user_servers=[config.SIMULATOR_GUILD])

                    for _ in range(3):
                        out = mk.generate_sentence(user_model, root=self.topic)
                        if out:
                            out = out.split(' ', 1)[1]
                            break
                    else:
                        out = mk.generate_sentence(user_model)

                    if not out:
                        continue

                    for userid, name in mk.NAMES.items():
                        if name in out:
                            self.sim_queue.insert(random.randint(0, 2), userid)

                    mentions = set([c for c in out[0].split(' ') if c[0:2] == '<@'])
                    for mention in mentions:
                        self.sim_queue.insert(random.randint(0, 1), mention[2:])

                    # Topic is last word of out, stripped of non-alphanumeric characters.
                    self.topic = out.split()[-1]
                    re.sub(r'\W+', '', self.topic)
            except Exception as e:
                print(e)
                with open('debug.txt', 'a+') as f:
                    f.write(str(e))
            
            try:
                # Posts that message to the SIMULATOR_CHANNEL

                nick = next_user_member.nick
                if not nick:
                    nick = next_user_member.name
                out = remove_mentions(out, bot_guild)

                webhook_avatar = await next_user_member.avatar_url.read()
                webhook = await bot_channel.create_webhook(name=nick, avatar=webhook_avatar)
                await webhook.send(out)
                await webhook.delete()
            except Exception as e:
                print(e)
                with open('debug.txt', 'a+') as f:
                    f.write(str(e))

            self.total_simulation_messages += 1
            if self.total_simulation_messages % 20 == 0:
                self.topic = None

            # Generate wait time and wait.
            wait_time = mk.get_wait_time()
            await asyncio.sleep(wait_time)


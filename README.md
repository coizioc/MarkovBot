# MarkovBot

MarkovBot is a Discord bot that uses server messages to create Markov chains.

## Setup

In order to run the bot, you'll need to have a JSON for the server you want to model. Specifically, the JSON's from [this Discord history tracker](https://dht.chylex.com/)[^1]. Once you have the JSON file, put it into the `/server_json` directory.

Then, create a file in the directory you are hosting the bot titled `servers.txt`. This is a semicolon-delimited list with the format `guildid;json_filename`. For example, if you wanted to add `/server_json/test.json` to the bot, I would need to add the line `1001;test.json`.

After that, run the `gen_models.py` file. If you do not specify a file(s) using the `--file` option, you will be prompted to give a filename. This will both separate all the messages into different files based on the user and convert those messages to a Markov model. Finally, if you wish to use this file as the basis for your simulation, use the `-s` flag to create a simulation model for that server.

Finally, you will need to create a `config.py` file. The format for this file is as follows:

```python
token = "BOT_TOKEN_STR"             # token used to run the bot using bot.py
sim_token = "SIM_BOT_TOKEN_STR"     # Can be the same as token; token used to run the bot using run_simulator.py

SIMULATOR_GUILD = 0                 # guildid of the server you want the bot to post the simulator in.
SIMULATOR_CHANNEL = 0               # channelid of the channel you want the bot to post the simulator in.

IGNORE_USERS = []                   # list of userids (int). The simulator will not post messages from these users.
```

Finally, you can run the bot using `bot.py` or the simulator using `run_simulator.py`.

## Usage

To run the bot, simply run `bot.py`. This will allow users to run the following commands

* `$mk [user (default:me)] [root]`: Creates a Markov chain for the user with an optional root. You can concatenate users (up to 5) using the + operator, e.g. `$do me+you`.
* `$domulti [num] [user (default:me)] [root]`: Generates num Markov chains for a user, up to 10.
* `$do10 [user (default:me}] [root]`: Same as `$domulti 10 [user] [root]`.

To run the simulator, run `run_simulator.py`. You can also run it using the following options:

* `--avg [num]`: Set the average time between posts.
* `--stddev [num]`: Set the standard deviation of time between posts.

The bot will start posting in the guild and channel set in `config.py`.

[^1]: In the future, I plan to allow for creation of the JSON file without needing to use an external program.
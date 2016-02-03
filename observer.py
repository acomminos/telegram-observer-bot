#!/usr/bin/env python2
#
# Copyright (C) 2016  Andrew Comminos <andrew@comminos.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import telegram
import sqlite3
import re
import subprocess
import sys
import os
import signal
from markov.database import MarkovDatabase
from markov.config import observer_token, talker_tokens

parser = argparse.ArgumentParser(description="Observe and construct markov chains of users' Telegram conversations.")
parser.add_argument("--parallel-chat", type=int, help="An optional chat ID to mirror users' messages into.")
parser.add_argument("--database",
                    default="observer.db",
                    nargs=1,
                    help="The path to the SQLite database used to store the generated chains. Default is observer.db.")

args = parser.parse_args()
bot = telegram.Bot(token=observer_token)
db = MarkovDatabase(args.database)

# Spawn talkers
talkers = {}
for username, token in talker_tokens.iteritems():
    child_args = ["python", os.path.join(sys.path[0], "talker.py"), token, username]
    if args.parallel_chat:
        child_args += ["--parallel-chat", str(args.parallel_chat)]
    talkers[username] = subprocess.Popen(child_args)

next_update = 0
while True:
    try:
        updates = bot.getUpdates(next_update)
    except telegram.error.TelegramError as err:
        print err
        print "Error received, will try again in 5 seconds."
        time.sleep(5)
        continue

    for update in updates:
        next_update = update.update_id + 1

        message = update.message
        if not message or not message.text or not message.from_user:
            continue

        if message.forward_from:
            continue

        # Don't record messages with queries to bots.
        if re.search(r'@[\w_]+?bot', message.text) is not None:
            continue

        db.add_message(message.from_user, message.text)

        username = message.from_user.username
        if message.chat_id != args.parallel_chat and username in talkers.keys():
            # Notify bot that its targeted user has talked.
            talkers[username].send_signal(signal.SIGUSR1)

db.close()

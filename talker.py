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
import random

parser = argparse.ArgumentParser(description="Construct and send messages based on observed markov chains.")
parser.add_argument("token", help="The bot's token.")
parser.add_argument("user", type=int, help="The ID of the user to simulate.")
parser.add_argument("command", default="talk", help="The command to trigger user simulation; default is 'talk'.")
parser.add_argument("--database",
                    default="observer.db",
                    nargs=1,
                    help="The path to the SQLite database used to load the generated chains. Default is observer.db.")

args = parser.parse_args()
bot = telegram.Bot(token=args.token)
conn = sqlite3.connect(args.database)

me = bot.getMe()
user = args.user
command = "/" + args.command + "@" + me.username

cur = conn.cursor()
next_update = 0
while True:
    for update in bot.getUpdates(next_update):
        next_update = update.update_id + 1
        message = update.message
        if not message or not message.text or not message.text == command:
            continue
        generated = []
        last_word = None
        while True:
            # For some reason, we can't select NULL columns using None.
            if last_word:
                options = cur.execute("SELECT word FROM chains WHERE (user_id=? AND last_word=?)",
                                      (user, str(last_word))).fetchall()
            else:
                options = cur.execute("SELECT word FROM chains WHERE (user_id=? AND last_word IS NULL)",
                                      (user,)).fetchall()

            if len(options) == 0:
                bot.sendMessage(message.chat.id, "Insufficient data for user.", reply_to_message_id=message.message_id)
                continue

            word, = random.choice(options)
            if word:
                generated.append(word)
                last_word = word
            else:
                break

        bot.sendMessage(message.chat.id, " ".join(generated), reply_to_message_id=message.message_id)


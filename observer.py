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

parser = argparse.ArgumentParser(description="Observe and construct markov chains of users' Telegram conversations.")
parser.add_argument("token", help="The bot's token.")
parser.add_argument("--database",
                    default="observer.db",
                    nargs=1,
                    help="The path to the SQLite database used to store the generated chains. Default is observer.db.")

args = parser.parse_args()
bot = telegram.Bot(token=args.token)
conn = sqlite3.connect(args.database)

# Set up chains table.
# word is NULL if this is node represents the end of a message.
# last_word is NULL if the given word starts a new message.
# While space inefficient, letting multiple rows serve as a frequency weight
# is rather nice and simple.
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS chains (
               user_id INTEGER NOT NULL,
               word TEXT,
               last_word TEXT)""")

next_update = 0
while True:
    for update in bot.getUpdates(next_update):
        next_update = update.update_id + 1

        message = update.message
        if not message or not message.text or not message.from_user:
            continue

        uid = message.from_user.id
        text = message.text

        # FIXME(acomminos): very naive, does not incorporate punctuation nor case.
        words = text.split(' ')
        if len(words) == 0:
            continue

        last_word = None
        # We append a "None" entry to the end in order to commit the terminating word.
        for word in text.split(' ') + [None]:
            cur.execute("""INSERT INTO chains VALUES (?,?,?)""", (uid, word, last_word))
            last_word = word

        conn.commit()

conn.close()

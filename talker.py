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
import time
import sys
from markov.database import MarkovDatabase

# Delay to wait before reattempting.
RETRY_DELAY = 5

parser = argparse.ArgumentParser(description="Construct and send messages based on observed markov chains.")
parser.add_argument("token", help="The bot's token.")
parser.add_argument("user", help="The username of the user to simulate.")
parser.add_argument("--command", default="talk", help="The command to trigger user simulation; default is 'talk'.")
parser.add_argument("--monospace", action="store_true", default=False, help="Use monospace text for messages- beep boop!")
parser.add_argument("--database",
                    default="observer.db",
                    nargs=1,
                    help="The path to the SQLite database used to load the generated chains. Default is observer.db.")

args = parser.parse_args()
bot = telegram.Bot(token=args.token)
db = MarkovDatabase(args.database)

me = bot.getMe()
command = "/%s" % args.command

# Fetch user ID from the database.
user, first_name, last_name = db.get_user_details(args.user)

def format_word(word):
    """Reformats a given word for display to the user, removing @
    symbols in particular."""
    # Strip @ symbols to prevent users from being notified.
    if word.startswith("@") and len(word) > 1:
        return word[1:]
    return word

def should_respond(message):
    """Returns True if the bot should respond to the given message."""
    return ("@" + me.username) in message or message.startswith(command)

next_update = 0
while True:
    try:
        updates = bot.getUpdates(next_update)
    except telegram.error.TelegramError as err:
        print err
        print "Error received, will try again in %d seconds." % RETRY_DELAY
        time.sleep(RETRY_DELAY)
        continue

    for update in updates:
        next_update = update.update_id + 1
        message = update.message
        if not message or not message.text or not should_respond(message.text):
            continue

        generated = " ".join(format_word(w) for w in db.generate_message(user))
        if args.monospace:
            generated = "`" + generated + "`"

        try:
            bot.sendMessage(message.chat.id, generated, parse_mode="Markdown")
        except telegram.error.TelegramError as err:
            print err
            print "Failed to send message, likely overloaded."
            time.sleep(RETRY_DELAY)

db.close()

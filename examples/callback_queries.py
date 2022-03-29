#!/usr/bin/python
import os
import sys
import logging
from typing import Optional

import df_engine.conditions as cnd
from df_engine.core import Context, Actor
from df_engine.core.keywords import TRANSITIONS, RESPONSE, GLOBAL

from telebot import types, logger
from telebot.util import content_type_media

from dff_telegram_connector.basic_connector import DffBot
from dff_telegram_connector.utils import set_state, get_user_id, get_initial_context


formatter = logging.Formatter(
    "[%(asctime)s] %(thread)d {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s", "%m-%d %H:%M:%S"
)
ch = logging.StreamHandler(sys.stdout)
logger.handlers = []
logger.addHandler(ch)
logger.setLevel(logging.INFO)
ch.setFormatter(formatter)

connector = dict()
# Optionally, you can use database connection implementations from the dff ecosystem
# from dff_db_connector import SqlConnector
# connector = SqlConnector("SOME_URI")

bot = DffBot(os.getenv("BOT_TOKEN", "SOMETOKEN"), threaded=False)

plot = {
    GLOBAL: {TRANSITIONS: {("general", "keyboard"): bot.cnd.message_handler(commands=["start", "restart"])}},
    "root": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {
                ("general", "keyboard"): cnd.true(),
            },
        },
        "fallback": {RESPONSE: "Finishing test"},
    },
    "general": {
        "keyboard": {
            RESPONSE: {
                "message": "What's 2 + 2?",
                "markup": {0: {"text": "4", "callback_data": "4"}, 1: {"text": "5", "callback_data": "5"}},
            },
            TRANSITIONS: {
                ("general", "success"): bot.cnd.callback_query_handler(func=lambda call: call.data == "4"),
                ("general", "fail"): bot.cnd.callback_query_handler(func=lambda call: call.data == "5"),
            },
        },
        "success": {RESPONSE: {"message": "Success!", "markup": None}, TRANSITIONS: {("root", "fallback"): cnd.true()}},
        "fail": {
            RESPONSE: {"message": "Incorrect answer, try again", "markup": None},
            TRANSITIONS: {("general", "keyboard"): cnd.true()},
        },
    },
}


actor = Actor(plot, start_label=("root", "start"), fallback_label=("root", "fallback"))


def get_markup(data: Optional[dict]):
    if not data:
        return None
    markup = types.InlineKeyboardMarkup(row_width=2)
    for key, item in data.items():
        markup.add(types.InlineKeyboardButton(**item))
    return markup


# if you need to work with callback queries or other types
# of queries, you can stack decorators upon the main handler
@bot.callback_query_handler(func=lambda call: True)
@bot.message_handler(func=lambda msg: True, content_types=content_type_media)
def handler(update):

    # retrieve or create a context for the user
    user_id = get_user_id(update)
    context: Context = connector.get(user_id, get_initial_context(user_id))

    # add newly received user data to the context
    context = set_state(context, update)

    # apply the actor
    context = actor(context)

    # save the context
    connector[user_id] = context

    response = context.last_response
    if isinstance(response, str):
        bot.send_message(update.from_user.id, response)
    elif isinstance(response, dict):
        bot.send_message(update.from_user.id, response["message"], reply_markup=get_markup(response["markup"]))


if __name__ == "__main__":
    bot.infinity_polling()

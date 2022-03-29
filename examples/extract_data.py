#!/usr/bin/python
import os
import sys
import logging

from df_engine.core.keywords import RESPONSE, TRANSITIONS, GLOBAL
from df_engine.core import Context, Actor
from df_engine import conditions as cnd

from telebot import types, logger
from telebot.util import content_type_media

from dff_telegram_connector.basic_connector import DffBot, get_user_id, get_initial_context
from dff_telegram_connector.utils import set_state


formatter = logging.Formatter(
    "[%(asctime)s] %(thread)d {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s", "%m-%d %H:%M:%S"
)
ch = logging.StreamHandler(sys.stdout)
logger.handlers = []
logger.addHandler(ch)
logger.setLevel(logging.INFO)
ch.setFormatter(formatter)

connector = dict()
# Optionally, you can use database connection implementations from the dff ecosystem.
# from dff_db_connector import SqlConnector
# connector = SqlConnector("SOME_URI")

bot = DffBot(os.getenv("BOT_TOKEN", "SOMETOKEN"), threaded=False)

plot = {
    GLOBAL: {TRANSITIONS: {("docs", "ask_doc"): bot.cnd_handler(commands=["start"])}},
    "root": {
        "start": {RESPONSE: "", TRANSITIONS: {("docs", "ask_doc"): cnd.true()}},
        "fallback": {RESPONSE: "Returned to fallback node, restarting", TRANSITIONS: {("root", "start"): cnd.true()}},
    },
    "docs": {
        "ask_doc": {
            RESPONSE: "Send me a plaintext doc",
            TRANSITIONS: {
                ("docs", "thank", 1.1): bot.cnd.message_handler(content_types=["document"]),
                ("docs", "repeat", 0.9): cnd.true(),
            },
        },
        "thank": {RESPONSE: "Got the doc, thanks", TRANSITIONS: {("root", "fallback"): cnd.true()}},
        "repeat": {
            RESPONSE: "I cannot find the doc. please, try again",
            TRANSITIONS: {
                ("docs", "thank", 1.1): bot.cnd.message_handler(content_types=["document"]),
                ("docs", "repeat", 0.9): cnd.true(),
            },
        },
    },
}

actor = Actor(plot, start_label=("root", "start"), fallback_label=("root", "fallback"))

# While most of the time you will be using only one handler to iterate over your plot,
# you can always create a separate function that will take care of additional tasks.
def extract_data(message):
    """A function to extract data with"""
    if not message.document:
        return
    file_id = message.document.file_id
    file = bot.get_file(file_id)
    bot.download_file(file.file_path)


@bot.message_handler(func=lambda msg: True, content_types=content_type_media)
def handler(update):
    user_id = get_user_id(update)
    context: Context = connector.get(user_id, get_initial_context(user_id))
    context = set_state(context, update)

    # Extract data if present
    if isinstance(update, types.Message):
        extract_data(update)

    context = actor(context)

    connector[user_id] = context

    response = context.last_response
    if isinstance(response, str):
        bot.send_message(update.from_user.id, response)
    # optionally provide conditions to use other response methods
    # elif isinstance(response, bytes):
    #     bot.send_document(update.from_user.id, response)


if __name__ == "__main__":
    bot.infinity_polling()

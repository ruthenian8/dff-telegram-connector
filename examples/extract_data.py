#!/usr/bin/env python3
import os
import sys

from df_engine.core.keywords import RESPONSE, TRANSITIONS, GLOBAL
from df_engine.core import Context, Actor
from df_engine import conditions as cnd

from telebot import types
from telebot.util import content_type_media

from df_telegram_connector.connector import TelegramConnector
from df_telegram_connector.utils import set_state, get_user_id, get_initial_context


connector = dict()
# Optionally, you can use database connection implementations from the dff ecosystem.
# from dff_db_connector import SqlConnector
# connector = SqlConnector("SOME_URI")

bot = TelegramConnector(os.getenv("BOT_TOKEN", "SOMETOKEN"), threaded=False)

script = {
    GLOBAL: {TRANSITIONS: {("docs", "ask_doc"): bot.cnd.message_handler(commands=["start"])}},
    "root": {
        "start": {RESPONSE: "", TRANSITIONS: {("docs", "ask_doc"): cnd.true()}},
        "fallback": {
            RESPONSE: "Final node reached, send any message to restart.",
            TRANSITIONS: {("docs", "ask_doc"): cnd.true()},
        },
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
            RESPONSE: "I cannot find the doc. Please, try again.",
            TRANSITIONS: {
                ("docs", "thank", 1.1): bot.cnd.message_handler(content_types=["document"]),
                ("docs", "repeat", 0.9): cnd.true(),
            },
        },
    },
}

actor = Actor(script, start_label=("root", "start"), fallback_label=("root", "fallback"))

# While most of the time you will be using only one handler to iterate over your script,
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

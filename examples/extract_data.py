#!/usr/bin/python
import os
import sys

from df_engine.core.keywords import RESPONSE, TRANSITIONS, GLOBAL
from df_engine.core import Context, Actor
from df_engine import conditions as cnd

from telebot import types

from dff_telegram_connector.basic_connector import DffBot, get_chat_plus_user_id, content_type_media, logger


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
    chat_plus_user = get_chat_plus_user_id(update)
    context: Context = connector.get(chat_plus_user, Context(id=chat_plus_user))

    context.add_request(update.text if (hasattr(update, "text") and update.text) else "data")
    context.misc["update"] = update  # this step is required for cnd_handler conditions to work

    # Extract data if present
    if isinstance(update, types.Message):
        extract_data(update)

    context = actor(context)
    context.clear(hold_last_n_indexes=3)

    connector[chat_plus_user] = context

    response = context.last_response
    if isinstance(response, str):
        bot.send_message(update.chat.id, response)
    # optionally provide conditions to use other response methods
    # elif isinstance(response, bytes):
    #     bot.send_document(update.chat.id, response)


if __name__ == "__main__":
    bot.infinity_polling()

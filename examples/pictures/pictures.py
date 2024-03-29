#!/usr/bin/env python3
import os
import sys
from typing import NamedTuple
from copy import copy

from df_engine.core.keywords import RESPONSE, TRANSITIONS, GLOBAL
from df_engine.core import Context, Actor
from df_engine import conditions as cnd

from telebot import types
from telebot.util import content_type_media

from dff_telegram_connector.basic_connector import DFFBot, get_user_id, get_initial_context
from dff_telegram_connector.utils import set_state


connector = dict()
# Optionally, you can use database connection implementations from the dff ecosystem.
# from dff_db_connector import SqlConnector
# connector = SqlConnector("SOME_URI")


def doc_is_photo(message):
    return message.document and message.document.mime_type == "image/jpeg"


bot = DFFBot(os.getenv("BOT_TOKEN", "SOMETOKEN"), threaded=False)

script = {
    GLOBAL: {TRANSITIONS: {("pics", "ask_picture"): bot.cnd.message_handler(commands=["start"])}},
    "root": {
        "start": {RESPONSE: "", TRANSITIONS: {("pics", "ask_picture"): cnd.true()}},
        "fallback": {
            RESPONSE: "Final node reached, send any message to restart.",
            TRANSITIONS: {("pics", "ask_picture"): cnd.true()},
        },
    },
    "pics": {
        "ask_picture": {
            RESPONSE: "Send me a picture",
            TRANSITIONS: {
                ("pics", "thank", 1.1): cnd.any(
                    [
                        bot.cnd.message_handler(content_types=["photo"]),
                        bot.cnd.message_handler(func=doc_is_photo, content_types=["document"]),
                    ]
                ),
                ("pics", "repeat", 0.9): cnd.true(),
            },
        },
        "thank": {
            RESPONSE: dict(
                text="Nice! Here is my picture:",
                picture=os.path.join(os.path.dirname(os.path.realpath(__file__)), "kitten.jpg"),
            ),
            TRANSITIONS: {("root", "fallback"): cnd.true()},
        },
        "repeat": {
            RESPONSE: "I cannot find the picture. Please, try again.",
            TRANSITIONS: {
                ("pics", "thank", 1.1): cnd.any(
                    [
                        bot.cnd.message_handler(content_types=["photo"]),
                        bot.cnd.message_handler(func=doc_is_photo, content_types=["document"]),
                    ]
                ),
                ("pics", "repeat", 0.9): cnd.true(),
            },
        },
    },
}

actor = Actor(script, start_label=("root", "start"), fallback_label=("root", "fallback"))

# While most of the time you will be using only one handler to iterate over your script,
# you can always create a separate function that will take care of additional tasks.
def extract_data(message):
    """A function to extract data with"""
    photo = message.photo or message.document
    if not photo:
        return
    file = bot.get_file(photo.file_id)
    result = bot.download_file(file.file_path)
    with open(photo.file_name, "wb+") as new_file:
        new_file.write(result)


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
    elif isinstance(response, dict):
        bot.send_message(update.from_user.id, response.get("text"))
        with open(response.get("picture"), "rb") as file:
            bot.send_photo(update.from_user.id, file)


if __name__ == "__main__":
    bot.infinity_polling()

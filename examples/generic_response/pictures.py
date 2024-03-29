#!/usr/bin/env python3
import os
import sys

import df_engine.conditions as cnd
from df_engine.core import Context, Actor
from df_engine.core.keywords import TRANSITIONS, RESPONSE, GLOBAL

from telebot.util import content_type_media
from telebot import types

from dff_telegram_connector.basic_connector import DFFBot

from df_generics import Response, Image, Attachments


def doc_is_photo(message: types.Message):
    return message.document and message.document.mime_type == "image/jpeg"


my_image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "kitten.jpg")

connector = dict()

bot = DFFBot(os.getenv("BOT_TOKEN", "SOMETOKEN"), db_connector=connector, threaded=False)

script = {
    GLOBAL: {TRANSITIONS: {("pics", "ask_picture"): bot.cnd.message_handler(commands=["start"])}},
    "root": {
        "start": {RESPONSE: Response(text=""), TRANSITIONS: {("pics", "ask_picture"): cnd.true()}},
        "fallback": {
            RESPONSE: Response(text="Final node reached, send any message to restart."),
            TRANSITIONS: {("pics", "ask_picture"): cnd.true()},
        },
    },
    "pics": {
        "ask_picture": {
            RESPONSE: Response(text="Send me a picture"),
            TRANSITIONS: {
                ("pics", "send_one", 1.1): cnd.any(
                    [
                        bot.cnd.message_handler(content_types=["photo"]),
                        bot.cnd.message_handler(func=doc_is_photo, content_types=["document"]),
                    ]
                ),
                ("pics", "send_many", 1.0): bot.cnd.message_handler(content_types=["sticker"]),
                ("pics", "repeat", 0.9): cnd.true(),
            },
        },
        "send_one": {
            RESPONSE: Response(text="Here's my picture!", image=Image(source=my_image_path)),
            TRANSITIONS: {("root", "fallback"): cnd.true()},
        },
        "send_many": {
            RESPONSE: Response(
                text="Look at my pictures",
                attachments=Attachments(files=[Image(source=my_image_path)] * 2),
            ),
            TRANSITIONS: {("root", "fallback"): cnd.true()},
        },
        "repeat": {
            RESPONSE: "I cannot find the picture. Please, try again.",
            TRANSITIONS: {
                ("pics", "send_one", 1.1): cnd.any(
                    [
                        bot.cnd.message_handler(content_types=["photo"]),
                        bot.cnd.message_handler(func=doc_is_photo, content_types=["document"]),
                    ]
                ),
                ("pics", "send_many", 1.0): bot.cnd.message_handler(content_types=["sticker"]),
                ("pics", "repeat", 0.9): cnd.true(),
            },
        },
    },
}

actor = Actor(script, start_label=("root", "start"), fallback_label=("root", "fallback"))


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
def handler(update, data: dict):
    context = data["context"]

    if isinstance(update, types.Message):
        extract_data(update)

    context = actor(context)
    response = context.last_response

    # use the universal method that adapts different types to Telegram format
    bot.send_response(update.from_user.id, response)

    data["context"] = context


if __name__ == "__main__":
    if "BOT_TOKEN" not in os.environ:
        print("BOT_TOKEN variable needs to be set to continue")
        sys.exit(1)

    bot.infinity_polling()

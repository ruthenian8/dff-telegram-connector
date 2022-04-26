#!/usr/bin/env python3
import os

import df_engine.conditions as cnd
from df_engine.core import Context, Actor
from df_engine.core.keywords import TRANSITIONS, RESPONSE, GLOBAL

from telebot.util import content_type_media

from dff_telegram_connector.basic_connector import DFFBot
from dff_telegram_connector.types import TelegramUI, TelegramButton

from dff_generics import Response, Keyboard, Button

connector = dict()

bot = DFFBot(os.getenv("BOT_TOKEN", "SOMETOKEN"), db_connector=connector, threaded=False)


plot = {
    GLOBAL: {TRANSITIONS: {("general", "keyboard"): bot.cnd.message_handler(commands=["start", "restart"])}},
    "root": {
        "start": {
            RESPONSE: Response(text="Finishing test"),
            TRANSITIONS: {
                ("general", "keyboard"): cnd.true(),
            },
        },
        "fallback": {RESPONSE: Response(text="Finishing test")},
    },
    # The reply below uses generic classes.
    # When creating a UI, you can use the generic Keyboard class.
    # It does not have all the options that are available in Telegram, so default options will be applied
    "general": {
        "keyboard": {
            RESPONSE: Response(
                **{
                    "text": "Starting test! What's 6 * 8?",
                    "ui": Keyboard(
                        buttons=[
                            Button(text="48", payload="48"),
                            Button(text="49", payload="49"),
                        ]
                    ),
                }
            ),
            TRANSITIONS: {
                ("general", "success"): bot.cnd.callback_query_handler(func=lambda call: call.data == "48"),
                ("general", "native_keyboard"): bot.cnd.callback_query_handler(func=lambda call: call.data == "49"),
            },
        },
        # otherwise, you can use the native TelegramUI class, that has more settings
        "native_keyboard": {
            RESPONSE: Response(
                **{
                    "text": "Question: What's 2 + 2?",
                    "ui": TelegramUI(
                        buttons=[
                            TelegramButton(text="5", payload="5"),
                            TelegramButton(text="4", payload="4"),
                            TelegramButton(text="2", payload="2"),
                            TelegramButton(text="6", payload="6"),
                        ],
                        row_width=4,
                    ),
                }
            ),
            TRANSITIONS: {
                ("general", "success"): bot.cnd.callback_query_handler(func=lambda call: call.data == "4"),
                ("general", "fail"): bot.cnd.callback_query_handler(func=lambda call: call.data == "5"),
            },
        },
        "success": {RESPONSE: Response(text="Success!"), TRANSITIONS: {("root", "fallback"): cnd.true()}},
        "fail": {
            RESPONSE: Response(text="Incorrect answer, try again"),
            TRANSITIONS: {("general", "keyboard"): cnd.true()},
        },
    },
}


actor = Actor(plot, start_label=("root", "start"), fallback_label=("root", "fallback"))


@bot.callback_query_handler(func=lambda call: True)
@bot.message_handler(func=lambda message: True, content_types=content_type_media)
def dialog_handler(update, data: dict):
    context = data["context"]

    context = actor(context)
    response = context.last_response

    # use the universal method that adapts different types to Telegram format
    bot.send_response(update.from_user.id, response)

    data["context"] = context


if __name__ == "__main__":
    bot.infinity_polling()

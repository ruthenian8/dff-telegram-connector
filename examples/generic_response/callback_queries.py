#!/usr/bin/env python3
import os
import sys

import df_engine.conditions as cnd
from df_engine.core import Context, Actor
from df_engine.core.keywords import TRANSITIONS, RESPONSE

from telebot.util import content_type_media
from telebot import types

from df_telegram_connector.connector import TelegramConnector
from df_telegram_connector.types import TelegramUI, TelegramButton
from df_telegram_connector.utils import set_state, get_user_id, get_initial_context

from df_generics import Response, Keyboard, Button

connector = dict()

bot = TelegramConnector(token=os.getenv("BOT_TOKEN", "SOMETOKEN"))


script = {
    "root": {
        "start": {
            RESPONSE: Response(text=""),
            TRANSITIONS: {
                ("general", "keyboard"): cnd.true(),
            },
        },
        "fallback": {
            RESPONSE: "Finishing test, send /restart command to restart",
            TRANSITIONS: {("general", "keyboard"): bot.cnd.message_handler(commands=["start", "restart"])},
        },
    },
    # The reply below uses generic classes.
    # When creating a UI, you can use the generic Keyboard class.
    # It does not include all the options that are available in Telegram, so an InlineKeyboard will be created by default.
    "general": {
        "keyboard": {
            RESPONSE: Response(
                **{
                    "text": "Starting test! What's 9 + 10?",
                    "ui": Keyboard(
                        buttons=[
                            Button(text="19", payload="19"),
                            Button(text="21", payload="21"),
                        ]
                    ),
                }
            ),
            TRANSITIONS: {
                ("general", "native_keyboard"): bot.cnd.callback_query_handler(func=lambda call: call.data == "19"),
                ("general", "fail"): bot.cnd.callback_query_handler(func=lambda call: call.data == "21"),
            },
        },
        # Otherwise, you can use the local TelegramUI class, that has more settings
        # It can be used as an argument for the generic Response class.
        # You can either instantiate a telebot keyboard yourself and pass it to TelegramUI as `keyboard`
        # or just pass a list of buttons.
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
                        is_inline=False,
                        row_width=4,
                    ),
                }
            ),
            TRANSITIONS: {
                ("general", "success", 1.2): bot.cnd.message_handler(func=lambda msg: msg.text == "4"),
                ("general", "fail", 1.0): cnd.true(),
            },
        },
        # if you want to remove the reply keyboard, pass an instance of telebot's ReplyKeyboardRemove
        # to the TelegramUI class.
        "success": {
            RESPONSE: Response(**{"text": "Success!", "ui": TelegramUI(keyboard=types.ReplyKeyboardRemove())}),
            TRANSITIONS: {("root", "fallback"): cnd.true()},
        },
        "fail": {
            RESPONSE: Response(
                **{
                    "text": "Incorrect answer, type anything to try again",
                    "ui": TelegramUI(keyboard=types.ReplyKeyboardRemove()),
                }
            ),
            TRANSITIONS: {("general", "keyboard"): cnd.true()},
        },
    },
}


actor = Actor(script, start_label=("root", "start"), fallback_label=("root", "fallback"))


@bot.callback_query_handler(func=lambda call: True)
@bot.message_handler(func=lambda message: True, content_types=content_type_media)
def dialog_handler(update):
    # retrieve or create a context for the user
    user_id = get_user_id(update)
    context: Context = connector.get(user_id, get_initial_context(user_id))
    # add newly received user data to the context
    context = set_state(context, update)  # this step is required for cnd.%_handler conditions to work

    # apply the actor
    updated_context = actor(context)

    # get and send a generic response
    response = updated_context.last_response
    bot.send_response(update.from_user.id, response)

    # save the context
    connector[user_id] = updated_context


if __name__ == "__main__":
    if "BOT_TOKEN" not in os.environ:
        print("BOT_TOKEN variable needs to be set to continue")
        sys.exit(1)

    bot.infinity_polling()

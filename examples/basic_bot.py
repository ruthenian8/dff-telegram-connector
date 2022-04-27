#!/usr/bin/env python3
import os
import sys

import df_engine.conditions as cnd
from df_engine.core import Context, Actor
from df_engine.core.keywords import TRANSITIONS, RESPONSE, GLOBAL

from telebot import types
from telebot.util import content_type_media

from dff_telegram_connector.basic_connector import DFFBot
from dff_telegram_connector.utils import set_state, get_user_id, get_initial_context


connector = dict()
# Optionally, you can use database connection implementations from the dff ecosystem.
# from dff_db_connector import SqlConnector
# connector = SqlConnector("SOME_URI")

bot = DFFBot(os.getenv("BOT_TOKEN", "SOMETOKEN"), threaded=False)

script: dict
"""
| The following example demonstrates that you can use any TeleBot condition inside your script.
| To achieve this, DFFBot provides a cnd namespace with telebot handler equivalents. 
| Thus, the Actor chooses the next node depending on whether the bot was sent a file, a particular command, etc.

"""
script = {
    GLOBAL: {
        TRANSITIONS: {
            ("root", "start", 2): bot.cnd.message_handler(commands=["start"]),
            ("root", "image", 2): bot.cnd.message_handler(content_types=["photo", "sticker"]),
            ("animals", "have_pets", 2): bot.cnd.message_handler(commands=["pets"]),
            ("animals", "like_animals", 2): bot.cnd.message_handler(commands=["animals"]),
        }
    },
    "root": {
        "start": {
            RESPONSE: "Hi",
            TRANSITIONS: {
                ("small_talk", "ask_some_questions"): cnd.exact_match("hi"),
            },
        },
        "fallback": {RESPONSE: "Oops"},
        "image": {RESPONSE: "Nice image", TRANSITIONS: {("root", "start"): cnd.true()}},
    },
    "animals": {
        "have_pets": {RESPONSE: "do you have pets?", TRANSITIONS: {"what_animal": cnd.exact_match("yes")}},
        "like_animals": {RESPONSE: "do you like it?", TRANSITIONS: {"what_animal": cnd.exact_match("yes")}},
        "what_animal": {
            RESPONSE: "what animals do you have?",
            TRANSITIONS: {"ask_about_color": cnd.exact_match("bird"), "ask_about_breed": cnd.exact_match("dog")},
        },
        "ask_about_color": {RESPONSE: "what color is it"},
        "ask_about_breed": {
            RESPONSE: "what is this breed?",
            TRANSITIONS: {
                "ask_about_breed": cnd.exact_match("pereat"),
                "tell_fact_about_breed": cnd.exact_match("bulldog"),
                "ask_about_training": cnd.exact_match("i do not known"),
            },
        },
        "tell_fact_about_breed": {
            RESPONSE: "Bulldogs appeared in England as specialized bull-baiting dogs. ",
        },
        "ask_about_training": {RESPONSE: "Do you train your dog? "},
    },
    "small_talk": {
        "ask_some_questions": {
            RESPONSE: "how are you",
            TRANSITIONS: {
                "ask_talk_about": cnd.exact_match("fine"),
                ("animals", "like_animals"): cnd.exact_match("let's talk about animals"),
            },
        },
        "ask_talk_about": {
            RESPONSE: "what do you want to talk about",
            TRANSITIONS: {
                ("animals", "like_animals"): cnd.exact_match("dog"),
            },
        },
    },
}

actor = Actor(script, start_label=("root", "start"), fallback_label=("root", "fallback"))


# The content_type parameter is set to the `content_type_media` constant, so that the bot can reply to images, stickers, etc.
@bot.message_handler(func=lambda message: True, content_types=content_type_media)
def dialog_handler(update):
    """
    | Standard handler that replies with df_engine's :py:class:`~df_engine.core.Actor` responses.

    | Since the logic of processing Telegram updates will be wholly handled by the :py:class:`~df_engine.core.Actor`,
    | only one handler is sufficient to run the bot.
    | If you need to need to process other updates in addition to messages,
    | just stack the corresponding handler decorators on top of the function.

    | The suggested way of extending the functionality is to expand the if-statement below.
    | In doing so you will be able to send an arbitrary number of messages or files to the user
    | depending on the type of response produced by the :py:class:`~df_engine.core.Actor`.
    | For instance, when it returns a :py:class:`dict`, the keys can be mapped to different messaging methods.

    Parameters
    -----------

    update: :py:class:`~telebot.types.JsonDeserializeable`
        Any Telegram update. What types you process depends on the decorators you stack upon the handler.

    """
    # retrieve or create a context for the user
    user_id = get_user_id(update)
    context: Context = connector.get(user_id, get_initial_context(user_id))
    # add newly received user data to the context
    context = set_state(context, update)  # this step is required for cnd.%_handler conditions to work

    # apply the actor
    updated_context = actor(context)

    response = updated_context.last_response
    if isinstance(response, str):
        bot.send_message(update.from_user.id, response)
    # optionally provide conditions to use other response methods
    # elif isinstance(response, bytes):
    #     bot.send_document(update.from_user.id, response)

    # save the context
    connector[user_id] = updated_context


if __name__ == "__main__":
    if "BOT_TOKEN" not in os.environ:
        print("BOT_TOKEN variable needs to be set to continue")
        sys.exit(1)

    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("Stopping bot")
        sys.exit(0)

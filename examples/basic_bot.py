#!/usr/bin/python
import os
import sys
import logging

import df_engine.conditions as cnd
from df_engine.core import Context, Actor
from df_engine.core.keywords import TRANSITIONS, RESPONSE, GLOBAL

from telebot import types, logger

from dff_telegram_connector.basic_connector import DffBot, get_chat_plus_user_id, content_type_media


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

plot: dict
"""
| The following example demonstrates that you can use any TeleBot condition inside your plot.
| To achieve this, DffBot provides a cnd namespace with telebot handler equivalents. 
| Thus, you can choose, which node to go to based on whether you've been sent a file or a particular command, etc.

"""
plot = {
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

actor = Actor(plot, start_label=("root", "start"), fallback_label=("root", "fallback"))


@bot.message_handler(func=lambda message: True, content_types=content_type_media)
def dialog_handler(update):
    """
    Standard handler that processes dff responses.
    """
    # retrieve or create a context for the user
    chat_plus_user = get_chat_plus_user_id(update)
    context: Context = connector.get(chat_plus_user, Context(id=chat_plus_user))

    # add newly received user data to the context
    context.add_request(update.text if (hasattr(update, "text") and update.text) else "data")
    context.misc["update"] = update  # this step is required for cnd_handler conditions to work

    # apply the actor
    context = actor(context)
    context.clear(hold_last_n_indexes=3)

    # save the context
    connector[chat_plus_user] = context

    response = context.last_response
    if isinstance(response, str):
        bot.send_message(update.chat.id, response)
    # optionally provide conditions to use other response methods
    # elif isinstance(response, bytes):
    #     bot.send_document(update.chat.id, response)


if __name__ == "__main__":
    if "BOT_TOKEN" not in os.environ:
        print("BOT_TOKEN variable needs to be set to continue")
        sys.exit(1)

    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("Stopping bot")
        sys.exit(0)

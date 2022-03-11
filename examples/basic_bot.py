#!/usr/bin/python
import sys
import os

from df_engine.core.keywords import RESPONSE, TRANSITIONS
from df_engine.core import Context, Actor
import df_engine.conditions as cnd
from telebot import TeleBot

from dff_telegram_connector.dff_telegram_connector import set_dff_handler

plot = {
    "root": {
        "start": {
            RESPONSE: "Hi",
            TRANSITIONS: {
                ("small_talk", "ask_some_questions"): cnd.exact_match("hi"),
                ("animals", "have_pets"): cnd.exact_match("i like animals"),
                ("animals", "like_animals"): cnd.exact_match("let's talk about animals"),
                ("news", "what_news"): cnd.exact_match("let's talk about news"),
            },
        },
        "fallback": {RESPONSE: "Oops"},
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
    "news": {
        "what_news": {
            RESPONSE: "what kind of news do you prefer?",
            TRANSITIONS: {
                "ask_about_science": cnd.exact_match("science"),
                "ask_about_sport": cnd.exact_match("sport"),
            },
        },
        "ask_about_science": {
            RESPONSE: "i got news about science, do you want to hear?",
            TRANSITIONS: {
                "science_news": cnd.exact_match("yes"),
                ("small_talk", "ask_some_questions"): cnd.exact_match("let's change the topic"),
            },
        },
        "science_news": {
            RESPONSE: "This is science news",
            TRANSITIONS: {
                "what_news": cnd.exact_match("ok"),
                ("small_talk", "ask_some_questions"): cnd.exact_match("let's change the topic"),
            },
        },
        "ask_about_sport": {
            RESPONSE: "i got news about sport, do you want to hear?",
            TRANSITIONS: {
                "sport_news": cnd.exact_match("yes"),
                ("small_talk", "ask_some_questions"): cnd.exact_match("let's change the topic"),
            },
        },
        "sport_news": {
            RESPONSE: "This is sport news",
            TRANSITIONS: {
                "what_news": cnd.exact_match("ok"),
                ("small_talk", "ask_some_questions"): cnd.exact_match("let's change the topic"),
            },
        },
    },
    "small_talk": {
        "ask_some_questions": {
            RESPONSE: "how are you",
            TRANSITIONS: {
                "ask_talk_about": cnd.exact_match("fine"),
                ("animals", "like_animals"): cnd.exact_match("let's talk about animals"),
                ("news", "what_news"): cnd.exact_match("let's talk about news"),
            },
        },
        "ask_talk_about": {
            RESPONSE: "what do you want to talk about",
            TRANSITIONS: {
                ("animals", "like_animals"): cnd.exact_match("dog"),
                ("news", "what_news"): cnd.exact_match("let's talk about news"),
            },
        },
    },
}

actor = Actor(plot, start_label=("root", "start"), fallback_label=("root", "fallback"))

if __name__ == "__main__":
    if "BOT_TOKEN" not in os.environ:
        print("BOT_TOKEN variable needs to be set to continue")
        sys.exit(1)

    default_bot = TeleBot(os.environ["BOT_TOKEN"])
    bot = set_dff_handler(bot=default_bot, actor=actor)
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("Stopping bot")
        sys.exit(0)

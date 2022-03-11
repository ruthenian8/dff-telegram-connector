import pytest
from telebot import types
from telebot import TeleBot


def test_stub(bot_instance):
    assert isinstance(bot_instance, TeleBot)


# def test_start(bot_instance, start_message):
#     reply = bot_instance.start_handler(start_message)
#     assert reply.text == "Welcome! Enjoy the conversation."


# def test_dialog(bot_instance, dialog_message):
#     reply = bot_instance.dialog_handler(dialog_message)
#     assert reply.text == "Hi"


# def test_document(bot_instance, doc_message):
#     reply = bot_instance.any_handler(doc_message)
#     assert reply.text == "I have trouble understanding media. Please, write me something."

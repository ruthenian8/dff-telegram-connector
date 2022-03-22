import sys
import os
from pathlib import Path

import pytest
from telebot import types
from telebot import TeleBot

from dff_telegram_connector.dff_handler import set_dff_handler

# sys.path.insert(0, "../")
# from examples.basic_bot import actor

# for variable in ["BOT_TOKEN", "TEST_CHAT"]:
#     if variable not in os.environ:
#         raise AssertionError(f"{variable} variable needs to be set to continue")


# @pytest.fixture(scope="session")
# def temp_file(tmpdir_factory):
#     filename = tmpdir_factory.mktemp("data").join("file.txt")
#     Path(filename).touch()
#     yield str(filename)


# @pytest.fixture(scope="session")
# def actor_instance():
#     yield actor


# @pytest.fixture(scope="session")
# def bot_and_factory(actor_instance):
#     default_bot = TeleBot(os.environ["BOT_TOKEN"])
#     bot = set_dff_handler(bot=default_bot, actor=actor_instance)
#     yield bot, set_dff_handler


# def create_text_message(text: str):
#     params = {"text": text}
#     chat = types.User(os.environ["TEST_CHAT"], False, "test")
#     return types.Message(1, chat, None, chat, "text", params, "")


# @pytest.fixture(scope="session")
# def start_message():
#     yield create_text_message("/start")


# @pytest.fixture(scope="session")
# def dialog_message():
#     yield create_text_message("Hello")


# @pytest.fixture(scope="session")
# def doc_message(temp_file):
#     file_content = open(temp_file, "rb")
#     params = {"document": file_content}
#     chat = types.User(os.environ["TEST_CHAT"], False, "test")
#     msg = types.Message(1, None, None, chat, "document", params, "")
#     yield msg

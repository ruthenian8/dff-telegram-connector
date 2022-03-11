import sys
import os
from pathlib import Path

import pytest
from telebot import types
from telebot import TeleBot

from dff_telegram_connector.dff_telegram_connector import set_dff_handler

sys.path.insert(0, "../")
from examples.basic_bot import actor

# if "BOT_TOKEN" not in os.environ:
#     raise AssertionError("BOT_TOKEN variable needs to be set to continue")


@pytest.fixture(scope="session")
def temp_file(tmpdir_factory):
    filename = tmpdir_factory.mktemp("data").join("file.txt")
    Path(filename).touch()
    yield str(filename)


@pytest.fixture(scope="session")
def actor_instance():
    yield actor


@pytest.fixture(scope="session")
def bot_instance(actor_instance):
    default_bot = TeleBot("")
    bot = set_dff_handler(bot=default_bot, actor=actor_instance)
    yield bot


def create_text_message(text: str):
    params = {"text": text}
    chat = types.User(11, False, "test")
    return types.Message(1, None, None, chat, "text", params, "")


@pytest.fixture(scope="session")
def start_message():
    yield create_text_message("/start")


@pytest.fixture(scope="session")
def dialog_message():
    yield create_text_message("Hello")


@pytest.fixture(scope="session")
def doc_message(temp_file):
    file_content = open(temp_file, "rb")
    params = {"document": file_content}
    chat = types.User(11, False, "test")
    msg = types.Message(1, None, None, chat, "document", params, "")
    yield msg

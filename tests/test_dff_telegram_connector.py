import pytest
import sys

from telebot import types
from telebot import TeleBot
from df_engine.core.context import Context

sys.path.insert(0, "../")

from examples.basic_bot import bot as basic_bot
from examples.middleware import bot as wired_bot


def test_inheritance():
    assert isinstance(basic_bot, TeleBot)
    assert isinstance(wired_bot, TeleBot)

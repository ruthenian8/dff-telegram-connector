import pytest
import sys

from telebot import types
from telebot import TeleBot
from df_engine.core.context import Context

sys.path.insert(0, "../")
from examples.basic_bot import bot


def test_stub():
    assert isinstance(bot, TeleBot)

import pytest
import sys

from telebot import types
from telebot import TeleBot
from df_engine.core.context import Context

sys.path.insert(0, "../")

from dff_telegram_connector.basic_connector import DatabaseMiddleware
from examples.basic_bot import bot as basic_bot
from examples.middleware import bot as wired_bot


def test_inheritance():
    assert isinstance(basic_bot, TeleBot)
    assert isinstance(wired_bot, TeleBot)


def create_text_message(text: str):
    params = {"text": text}
    chat = types.User("1", False, "test")
    return types.Message(1, chat, None, chat, "text", params, "")


def create_query(data: str):
    chat = types.User("1", False, "test")
    return types.CallbackQuery(1, chat, data, chat)


@pytest.mark.parametrize(
    "message,expected", [(create_text_message("Hello"), True), (create_text_message("Goodbye"), False)]
)
def test_message_handling(message, expected, actor_instance):
    condition = basic_bot.cnd.message_handler(func=lambda msg: msg.text == "Hello")
    context = Context(id=123)
    context.misc["TELEGRAM_CONNECTOR"] = {"keep_flag": True, "data": message}
    assert condition(context, actor_instance) == expected
    wrong_type = create_query("some data")
    context.misc["TELEGRAM_CONNECTOR"]["data"] = wrong_type
    assert condition(context, actor_instance) == False


@pytest.mark.parametrize("query,expected", [(create_query("4"), True), (create_query("5"), False)])
def test_query_handling(query, expected, actor_instance):
    condition = basic_bot.cnd.callback_query_handler(func=lambda call: call.data == "4")
    context = Context(id=123)
    context.misc["TELEGRAM_CONNECTOR"] = {"keep_flag": True, "data": query}
    assert condition(context, actor_instance) == expected
    wrong_type = create_text_message("some text")
    context.misc["TELEGRAM_CONNECTOR"]["data"] = wrong_type
    assert condition(context, actor_instance) == False


@pytest.mark.parametrize("update", [create_text_message("some message"), create_query("some query")])
def test_middleware(update):
    connector = dict()
    data = dict()
    middleware = DatabaseMiddleware(connector)
    middleware.pre_process(update, data)
    assert "context" in data
    assert isinstance(data["context"], Context)
    middleware.post_process(update, data)
    assert len(connector) == 1
    assert update.from_user.id in connector

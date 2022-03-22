"""Alternative connector implementation module"""
from functools import wraps
from typing import List, Optional, Callable, Union, Any
from collections.abc import MutableMapping

from telebot import types
from telebot import TeleBot
from telebot.custom_filters import AdvancedCustomFilter

from df_engine.core import Context, Actor
from df_engine.core.types import ConditionType


class BaseMiddleware:
    """
    Base class for middleware.
    Your middlewares should be inherited from this class.
    """

    def __init__(self):
        pass

    def pre_process(self, message, data):
        raise NotImplementedError

    def post_process(self, message, data, exception):
        raise NotImplementedError


class DffTeleBot(TeleBot):
    def __init__(self, *args, actor: Actor, db_connector: MutableMapping, **kwargs) -> None:
        TeleBot.__init__(self, *args, use_class_middlewares=True, **kwargs)
        self._actor = actor
        self._connector = db_connector
        self.add_custom_filter(LabelFilter(self))
        self.add_custom_filter(ConditionFilter(self))
        self.setup_middleware(ContextMiddleware(self._connector))

    def get_start_context(self, id: str):
        return Context(id=id, labels={0: self.actor.start_label[:2]})

    def apply_actor(self, func: Callable, *args, **kwargs):
        @wraps(func)
        def wrapper(message, data):
            message.context = self._actor(message.context)
            return func(message, data, *args, **kwargs)

        return wrapper

    @staticmethod
    def get_chat_plus_user_id(message: types.Message):
        return str(message.chat.id) + str(message.from_user.id)


class ContextMiddleware(BaseMiddleware):
    def __init__(self, db_connector: MutableMapping) -> None:
        self.update_types = "message"
        self._connector = db_connector

    def pre_process(self, message: types.Message, data: Any):
        chat_plus_user = DffTeleBot.get_chat_plus_user_id(message)
        message.context = self._connector.get(chat_plus_user, self.bot.get_start_context(id=chat_plus_user))
        message.context.add_request(message.text)

    def post_process(self, message: types.Message, data: Any, exception=None):
        if exception:
            print(exception)
        chat_plus_user = DffTeleBot.get_chat_plus_user_id(message)
        self._connector[chat_plus_user] = message.context


class LabelFilter(AdvancedCustomFilter):
    def __init__(self, bot: DffTeleBot) -> None:
        if not isinstance(bot, DffTeleBot):
            raise TypeError(f"The filter can only be applied to instances of `DffTeleBot`, not {type(bot)}")
        self.bot = bot

    key = "labels"

    def check(self, message: Union[types.Message, types.CallbackQuery], labels: Union[tuple, List[tuple]]):
        if labels == ("*",):
            return True

        if isinstance(message, types.CallbackQuery):
            message = message.message

        context = message.context

        # if hasattr(message, "context"):
        # context = message.context
        # else:
        #     chat_plus_user = self.bot.get_chat_plus_user_id(message)
        #     context = self.bot._connector.get(chat_plus_user, self.bot.get_start_context(id=chat_plus_user))

        label = context.last_label[:2] if context.last_label else self.bot._actor.start_label[:2]

        if isinstance(labels, list):
            for lab in labels:
                if lab == label:
                    return True
                return False

        return labels == label


class ConditionFilter(AdvancedCustomFilter):
    def __init__(self, bot: DffTeleBot) -> None:
        if not isinstance(bot, DffTeleBot):
            raise TypeError(f"The filter can only be applied to instances of `DffTeleBot`, not {type(bot)}")
        self.bot = bot

    key = "conditions"

    def check(
        self, message: Union[types.Message, types.CallbackQuery], conditions: Union[ConditionType, List[ConditionType]]
    ):

        if isinstance(message, types.CallbackQuery):
            message = message.message

        context = message.context

        # if hasattr(message, "context"):
        # context = message.context
        # else:
        #     chat_plus_user = self.bot.get_chat_plus_user_id(message)
        #     context = self.bot._connector.get(chat_plus_user, self.bot.get_start_context(id=chat_plus_user))
        #     context.add_request(message.text)

        actor = self.bot._actor

        if isinstance(conditions, list):
            for condition in conditions:
                if condition(context, actor):
                    return True
            return False

        return conditions(context, actor)

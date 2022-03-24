"""Draft connector implementation module"""
from typing import MutableMapping, Any
from functools import partialmethod

from telebot import types, TeleBot, logger
from telebot.handler_backends import BaseMiddleware
from telebot.util import update_types, content_type_media

from df_engine.core import Context, Actor


class DffBot(TeleBot):
    def __init__(self, *args, db_connector: MutableMapping = None, **kwargs):
        use_middleware = db_connector is not None
        super().__init__(*args, use_class_middlewares=use_middleware, **kwargs)
        self._connector = db_connector
        self.cnd = CndNamespace(self)
        if use_middleware:
            self.setup_middleware(DatabaseMiddleware(self._connector))


class CndNamespace:
    def __init__(self, bot: DffBot):
        self.bot = bot

    def handler(
        self, target_type: type, commands=None, regexp=None, func=None, content_types=None, chat_types=None, **kwargs
    ):

        handler = self.bot._build_handler_dict(
            None,
            False,
            commands=commands,
            regexp=regexp,
            func=func,
            content_types=content_types,
            chat_types=chat_types,
            **kwargs
        )

        def condition(ctx: Context, actor: Actor, *args, **kwargs):
            update = ctx.misc.get("update")
            if not update or not isinstance(update, target_type):
                return False
            test_result = self.bot._test_message_handler(handler, update)
            return test_result

        return condition

    message_handler = edited_message_handler = partialmethod(handler, target_type=types.Message)

    channel_post_handler = edited_channel_post_handler = partialmethod(handler, target_type=types.Message)

    inline_handler = partialmethod(handler, types.InlineQuery)

    chosen_inline_handler = partialmethod(handler, types.ChosenInlineResult)

    callback_query_handler = partialmethod(handler, types.CallbackQuery)

    shipping_query_handler = partialmethod(handler, types.ShippingQuery)

    pre_checkout_query_handler = partialmethod(handler, types.PreCheckoutQuery)

    poll_handler = partialmethod(handler, target_type=types.Poll)

    poll_answer_handler = partialmethod(handler, target_type=types.PollAnswer)

    chat_member_handler = my_chat_member_handler = partialmethod(handler, target_type=types.ChatMemberUpdated)

    chat_join_request_handler = partialmethod(handler, types.ChatJoinRequest)


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, db_connector: MutableMapping) -> None:
        self.update_types = update_types
        self._connector = db_connector

    def pre_process(self, update, data: dict):
        chat_plus_user = get_chat_plus_user_id(update)
        context = self._connector.get(chat_plus_user, Context(id=chat_plus_user))

        context.add_request(update.text if (hasattr(update, "text") and update.text) else "data")
        context.misc["update"] = update
        data["context"] = context

    def post_process(self, update, data: dict, exception=None):
        if exception:
            print(exception)
        chat_plus_user = get_chat_plus_user_id(update)
        data["context"].clear(hold_last_n_indexes=3)
        self._connector[chat_plus_user] = data["context"]


def get_chat_plus_user_id(message: types.Message) -> str:
    return str(message.from_user.id)

"""
basic_connector
-----------------

| Basic connector module provides the :py:class:`~dff_telegram_connector.basic_connector.DFFBot` class.
| It inherits from the :py:class:`~telebot.TeleBot` class from the :py:mod:`~pytelegrambotapi` library.
| Using it, you can put Telegram update handlers inside your plot and condition your transitions on them.

"""
from pathlib import Path
from typing import MutableMapping, Any, Union
from pydantic import BaseModel

from telebot import types, TeleBot, logger
from telebot.handler_backends import BaseMiddleware
from telebot.util import update_types

from df_engine.core import Context, Actor

from .utils import get_initial_context, get_user_id, set_state, partialmethod
from .types import TelegramResponse, TelegramResource


class DFFBot(TeleBot):
    """

    Parameters
    -----------

    db_connector: :py:class:`~typing.MutableMapping`
        | Any object that implements the :py:class:`dict` interface, e. g. setting, getting and deleting items.
        | Note that this argument is keyword-only.

        | In the release version you will be able to use the dff-db-connector library that adapts many kinds of
        | database connectors to this interface.

    """

    def __init__(self, *args, db_connector: MutableMapping = None, **kwargs):
        use_middleware = db_connector is not None
        super().__init__(*args, use_class_middlewares=use_middleware, **kwargs)
        self._connector = db_connector
        self.cnd = CndNamespace(self)
        if use_middleware:
            self.setup_middleware(DatabaseMiddleware(self._connector))

    def send_response(self, user_id: Union[str, int], *, response: BaseModel, gallery_type: type = None):
        AdapterType = TelegramResponse[gallery_type] if gallery_type else TelegramResponse
        adapted_response: TelegramResponse = AdapterType.parse_obj(response)
        if gallery_type:
            self.send_media_group(adapted_response.gallery.to_local())
        media_fields = [
            adapted_response.image,
            adapted_response.audio,
            adapted_response.video,
            adapted_response.document,
        ]

        field: TelegramResource
        for field in media_fields:

            bot_method = getattr(self, field._bot_method)

            if not isinstance(field.media, Path):
                bot_method(user_id, field.media)
                continue
            if Path.exists(field.media):
                with open(field.media, "rb") as file:
                    bot_method(user_id, file)

        self.send_message(user_id, adapted_response.text, reply_markup=adapted_response.ui.keyboard)


class CndNamespace:
    """
    This class includes methods that produce df_engine conditions based on pytelegrambotapi updates.

    It is included to the :py:class:`~dff_telegram_connector.basic_connector.DFFBot` as :py:attr:`cnd` attribute.
    This helps us avoid overriding the original methods.

    To set a condition in your plot, stick to the signature of the original :py:class:`~telebot.TeleBot` methods.
    E. g. the result of

    .. code-block:: python

        bot.cnd.message_handler(func=lambda msg: True)

    in your :py:class:`~df_engine.core.Plot` will always be `True`, unless the new update is not a message.

    """

    def __init__(self, bot: DFFBot):
        self.bot = bot

    def handler(
        self, target_type: type, commands=None, regexp=None, func=None, content_types=None, chat_types=None, **kwargs
    ):
        """
        | Generic handler method that serves as a base for other methods.
        | We advise against invoking it directly.

        """

        update_handler = self.bot._build_handler_dict(
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
            update = ctx.misc.get("TELEGRAM_CONNECTOR", {}).get("data")
            if not update or not isinstance(update, target_type):
                return False
            test_result = self.bot._test_message_handler(update_handler, update)
            return test_result

        return condition

    message_handler = partialmethod(handler, target_type=types.Message)

    edited_message_handler = partialmethod(handler, target_type=types.Message)

    channel_post_handler = partialmethod(handler, target_type=types.Message)

    edited_channel_post_handler = partialmethod(handler, target_type=types.Message)

    inline_handler = partialmethod(handler, target_type=types.InlineQuery)

    chosen_inline_handler = partialmethod(handler, target_type=types.ChosenInlineResult)

    callback_query_handler = partialmethod(handler, target_type=types.CallbackQuery)

    shipping_query_handler = partialmethod(handler, target_type=types.ShippingQuery)

    pre_checkout_query_handler = partialmethod(handler, target_type=types.PreCheckoutQuery)

    poll_handler = partialmethod(handler, target_type=types.Poll)

    poll_answer_handler = partialmethod(handler, target_type=types.PollAnswer)

    chat_member_handler = partialmethod(handler, target_type=types.ChatMemberUpdated)

    my_chat_member_handler = partialmethod(handler, target_type=types.ChatMemberUpdated)

    chat_join_request_handler = partialmethod(handler, target_type=types.ChatJoinRequest)


class DatabaseMiddleware(BaseMiddleware):
    """
    | DatabaseMiddleware is an optional extension to the :py:class:`~dff_telegram_connector.basic_connector.DFFBot`.
    | It encapsulates the context retrieval and context saving operations.
    | The context is passed to the decorated handler function with the :py:obj:`data` variable,
    | as suggested by the pytelegrambotapi documentation.

    """

    def __init__(self, db_connector: MutableMapping) -> None:
        self.update_types = update_types
        self._connector = db_connector

    def pre_process(self, update, data: dict):
        user_id = get_user_id(update)
        context = self._connector.get(user_id, get_initial_context(user_id))
        context = set_state(context, update)

        data["context"] = context

    def post_process(self, update, data: dict, exception=None):
        if exception:
            print(exception)

        user_id = get_user_id(update)
        self._connector[user_id] = data["context"]

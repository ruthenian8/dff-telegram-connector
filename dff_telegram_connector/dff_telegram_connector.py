"""Main module"""
import os
from typing import Optional
from collections.abc import MutableMapping

from telebot import TeleBot
from telebot import types

from df_engine.core import Context, Actor


def set_dff_handler(
    bot: TeleBot, actor: Actor, context_storage: Optional[MutableMapping] = None, reject_media: bool = True
) -> TeleBot:

    if not context_storage:
        context_storage = dict()

    def get_or_create_context(uid: str) -> Context:
        try:
            context = context_storage[uid]
        except KeyError:
            context = None
        if context is None or (context.last_label and [*context.last_label] == ["root", "fallback"]):
            context = Context(id=uid)
            context_storage[uid] = context

        return context

    @bot.message_handler(commands=["start"])
    def start_handler(message: types.Message) -> types.Message:
        """
        Handler for the initial command.
        """
        return bot.send_message(message.chat.id, "Welcome! Enjoy the conversation.")

    @bot.message_handler(content_types=["text"])
    def dialog_handler(message: types.Message) -> types.Message:
        """
        Standard handler that processes dff responses.
        """
        uid = str(message.from_user.id)
        ctx: Context = get_or_create_context(uid)
        ctx.add_request(message.text)
        ctx = actor(ctx)
        ctx.clear(hold_last_n_indexes=3)
        context_storage[uid] = ctx
        return bot.send_message(message.chat.id, ctx.last_response)

    if reject_media:

        @bot.message_handler(lambda msg: msg.content_type != "text")
        def any_handler(message: types.Message) -> types.Message:
            """
            In case you want your bot to ignore anything but text messages,
            leave this function untouched. Replace with alternative handlers otherwise.
            """
            return bot.send_message(
                message.chat.id, "I have trouble understanding media. " "Please, write me something."
            )

    return bot

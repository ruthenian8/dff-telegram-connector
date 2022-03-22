"""Draft connector implementation module"""
import os
import sys
from typing import Optional
from collections.abc import MutableMapping

from telebot import TeleBot
from telebot import types

from df_engine.core import Context, Actor

DEFAULT_CONDITIONS: dict = {"commands": ["start"], "content_types": ["text"]}


def set_dff_handler(
    bot: TeleBot, actor: Actor, context_storage: Optional[MutableMapping] = None, conditions: dict = DEFAULT_CONDITIONS
) -> TeleBot:

    if not context_storage:
        context_storage = dict()

    def get_or_create_context(uid: str) -> Context:
        context = context_storage.get(uid, Context(id=uid))

        if context.last_label and [*context.last_label] != ["root", "fallback"]:
            return context

        flow, node = actor.start_label[:2]
        response = actor.plot[flow][node].run_response(context, actor)

        context.add_label((flow, node))
        context.add_response(response)

        return context

    def dialog_handler(message: types.Message, bot: TeleBot = bot) -> types.Message:
        """
        Standard handler that processes dff responses.
        """
        uid = str(message.from_user.id)
        context: Context = get_or_create_context(uid)

        if len(context.requests) == 0:
            context.add_request("start")
        else:
            context.add_request(message.text)
            context = actor(context)
            context.clear(hold_last_n_indexes=3)

        context_storage[uid] = context
        return bot.send_message(message.chat.id, context.last_response)

    [bot.message_handler(**{key: val})(dialog_handler) for key, val in conditions.items()]

    set_dff_handler.get_or_create_context = get_or_create_context
    set_dff_handler.dialog_handler = dialog_handler

    return bot

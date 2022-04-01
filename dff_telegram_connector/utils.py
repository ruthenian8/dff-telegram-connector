from functools import wraps
from typing import Callable

from telebot import types
from df_engine.core import Context


def set_state(ctx: Context, update: types.JsonDeserializable):
    """
    Updates a context with information from a new Telegram update (event) and returns this context.

    Parameters
    -----------

    ctx: :py:class:`~Context`
        Dialog Flow Engine context
    update: :py:class:`~types.JsonDeserializable`
        Any Telegram update, e. g. a message, a callback query or any other event

    """
    ctx.add_request(update.text if (hasattr(update, "text") and update.text) else "data")
    ctx.misc["TELEGRAM_CONNECTOR"]["data"] = update
    return ctx


def get_user_id(update: types.JsonDeserializable) -> str:
    """Extracts user ID from an update instance AND casts it to a string"""
    assert hasattr(update, "from_user"), f"Received an invalid update object: {str(type(update))}"
    return str(update.from_user.id)


def get_initial_context(user_id: str):
    """
    Initialize a context with module-specific parameters.

    Parameters
    -----------

    user_id: str
        ID of the user from the update instance.

    """
    ctx = Context(id=user_id)
    ctx.misc.update({"TELEGRAM_CONNECTOR": {"keep_flag": True, "data": None}})
    assert "TELEGRAM_CONNECTOR" in ctx.misc
    return ctx


def partialmethod(func: Callable, **part_kwargs):
    """
    This function replaces the partialmethod implementation from functools.
    In contrast with the original class-based approach, it decorates the function, so we can use docstrings.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        return func(self, *args, **part_kwargs, **kwargs)

    wrapper.__doc__ = f"""
    Creates a df_engine condition, triggered by update type {str(list(part_kwargs.values()))}. 
    The signature is equal with the :py:class:`telebot.Telebot` method of the same name.
    """

    return wrapper

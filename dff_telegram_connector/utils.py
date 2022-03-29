from telebot import types

from df_engine.core import Context


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

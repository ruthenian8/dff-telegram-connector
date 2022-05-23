from functools import partial
from typing import Any

from telebot import types, logger

from df_engine.core import Context, Actor
from df_runner import AbsRequestProvider, Runner

from .connector import TelegramConnector
from .utils import get_user_id, set_state, get_initial_context

flask_imported: bool
try:
    from flask import Flask, request, abort

    flask_imported = True
except ImportError:
    flask_imported = False
    Flask = Any
    request, abort = None, None


class BaseRequestProvider(AbsRequestProvider):
    def __init__(self, bot: TelegramConnector):
        self.bot = bot

    def handle_update(self, update: types.Update, runner: Runner):
        if update.update_id > self.bot.last_update_id:
            self.bot.last_update_id = update.update_id

        update_fields = update.__dict__.copy()
        update_fields.pop("update_id")
        inner_update = next(filter(lambda val: val is not None, list(update_fields.values())))

        ctx_id = get_user_id(inner_update)
        ctx_update_callable = partial(set_state, update=inner_update)
        ctx: Context = runner.request_handler(
            ctx_id=ctx_id, ctx_update=ctx_update_callable, init_ctx=get_initial_context(ctx_id)
        )
        self.bot.send_response(ctx_id, ctx.last_response)

    def run(self, runner: Runner):
        raise NotImplementedError


class PollingRequestProvider(BaseRequestProvider):
    """
    | Class for compatibility with df_runner. Retrieves updates by polling.
    | Multi-threaded polling is currently not supported, but will be implemented in the future.
    """

    def __init__(self, bot: TelegramConnector, interval=3, allowed_updates=None, timeout=20, long_polling_timeout=20):
        super().__init__(bot=bot)
        self.interval = interval
        self.allowed_updates = allowed_updates
        self.timeout = timeout
        self.long_polling_timeout = long_polling_timeout

    def run(self, runner: Runner):
        self.bot._TeleBot__stop_polling.clear()
        logger.info("started polling")
        self.bot.get_updates(offset=-1)

        while not self.bot._TeleBot__stop_polling.wait(self.interval):
            try:
                updates = self.bot.get_updates(
                    offset=(self.bot.last_update_id + 1),
                    allowed_updates=self.allowed_updates,
                    timeout=self.timeout,
                    long_polling_timeout=self.long_polling_timeout,
                )
                for update in updates:
                    self.handle_update(update, runner=runner)

            except Exception as e:
                print(e)
                self.bot._TeleBot__stop_polling.set()
                break


class FlaskRequestProvider(BaseRequestProvider):
    """Class for compatibility with df_runner. Retrieves updates from post json requests."""

    def __init__(
        self,
        bot: TelegramConnector,
        app: Flask,
        host: str = "localhost",
        port: int = 8443,
        endpoint: str = "/dff-bot",
        full_uri: str = None,
    ):
        if not flask_imported:
            raise ModuleNotFoundError("Flask is not installed")

        super().__init__(bot=bot)
        self.app: Flask = app
        self.host: str = host
        self.port: int = port
        self.endpoint: str = endpoint
        self.full_uri: str = full_uri or "".join([f"https://{host}:{port}", endpoint])

    def run(self, runner: Runner):
        def handle_updates():
            if not request.headers.get("content-type") == "application/json":
                abort(403)

            json_string = request.get_data().decode("utf-8")
            update = types.Update.de_json(json_string)
            self.handle_update(update, runner=runner)
            return ""

        self.app.route(self.endpoint, methods=["POST"])(handle_updates)
        self.bot.remove_webhook()
        self.bot.set_webhook(self.full_uri)

        self.app.run(host=self.host, port=self.port)

from telebot import types, logger

from df_engine.core import Context, Actor
from df_runner import AbsRequestProvider, Runner

from .connector import TelegramConnector
from .utils import get_user_id, set_state, get_initial_context

try:
    from flask import Flask, request, abort
except ImportError:
    Flask, request, abort = None, None, None


class PollingRequestProvider(AbsRequestProvider):
    """
    Class for compatibility with df_runner. Retrieves updates by polling.
    """

    def __init__(self, bot: TelegramConnector, interval=3, allowed_updates=None, timeout=20, long_polling_timeout=20):
        self.bot = bot
        self.interval = interval
        self.allowed_updates = allowed_updates
        self.timeout = timeout
        self.long_polling_timeout = long_polling_timeout

    def run(self, runner: Runner):
        if self.set_state not in runner._pre_annotators:
            runner._pre_annotators.append(self.set_state)

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
                    if update.update_id > self.bot.last_update_id:
                        self.bot.last_update_id = update.update_id
                    _, inner_update = next(
                        filter(
                            lambda key_val: key_val[0] != "update_id" and key_val[1] is not None,
                            list(update.__dict__.items()),
                        )
                    )
                    ctx_id = get_user_id(inner_update)
                    ctx: Context = runner.request_handler(ctx_id, inner_update, get_initial_context(ctx_id))
                    self.bot.send_response(ctx_id, ctx.last_response)
            except Exception as e:
                print(e)
                self.bot._TeleBot__stop_polling.set()
                break

    @staticmethod
    def set_state(ctx: Context, actor: Actor):
        return set_state(ctx, ctx.last_request)


class FlaskRequestProvider(AbsRequestProvider):
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
        if Flask is None or request is None or abort is None:
            raise ModuleNotFoundError("Flask is not installed")

        self.bot = bot
        self.app = app
        self.host = host
        self.port = port
        self.endpoint = endpoint
        self.full_uri = full_uri or "".join([f"https://{host}:{port}", endpoint])

    def run(self, runner: Runner):
        if self.set_state not in runner._pre_annotators:
            runner._pre_annotators.append(self.set_state)

        def handle_updates():
            if not request.headers.get("content-type") == "application/json":
                abort(403)
            json_string = request.get_data().decode("utf-8")
            update = types.Update.de_json(json_string)
            if update.update_id > self.bot.last_update_id:
                self.bot.last_update_id = update.update_id
            _, inner_update = next(
                filter(
                    lambda key_val: key_val[0] != "update_id" and key_val[1] is not None,
                    list(update.__dict__.items()),
                )
            )
            ctx_id = get_user_id(inner_update)
            ctx: Context = runner.request_handler(ctx_id, inner_update)
            self.bot.send_response(id, ctx.last_response)
            return ""

        self.app.route(self.endpoint, methods=["POST"])(handle_updates)
        self.bot.remove_webhook()
        self.bot.set_webhook(self.full_uri)

        self.app.run(host=self.host, port=self.port)

    @staticmethod
    def set_state(ctx: Context, actor: Actor):
        return set_state(ctx, ctx.last_request)

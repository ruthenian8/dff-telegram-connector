from df_runner import Runner

from dff_telegram_connector.request_provider import PollingRequestProvider, FlaskRequestProvider

from basic_bot import bot, actor

# provider = PollingRequestProvider(bot=bot)

from flask import Flask
app = Flask(__name__)
provider = FlaskRequestProvider(bot=bot, app=app)

runner = Runner(actor=actor, db=dict(), request_provider=provider)

if __name__ == "__main__":
    runner.start()


# Dff Telegram Connector

[Dff Telegram Connector](https://github.com/ruthenian8/dff-telegram-connector) is an extension to the [Dialogflow Engine](https://github.com/deepmipt/dialog_flow_engine), a minimalistic open-source engine for conversational services.

[Dff Telegram Connector](https://github.com/ruthenian8/dff-telegram-connector) is an adapter module that integrates `df_engine` and [pytelegrambotapi](https://github.com/eternnoir/pyTelegramBotAPI) library, a popular Python implementation of the Telegram Bot API. In combination, these two components make the development of conversational services for Telegram straightforward and intuitive.

In this module, we introduce support for pytelegrambotapi-style conditions which can process different kinds of updates that your service may receive from Telegram. Not only `messages`, but also `callback queries` and many more. All of those can now be handled by `df_engine's` `Actor` that will transition to the right part of the `Plot` depending on the conditions you choose.

Working examples can be found in the [examples directory](https://github.com/ruthenian8/dff-telegram-connector/tree/main/examples).

<!-- [![Documentation Status](https://dff-telegram-connector.readthedocs.io/en/stable/?badge=stable)](https://readthedocs.org/projects/dff-telegram-connector/badge/?version=stable) -->
<!-- [![Coverage Status](https://coveralls.io/repos/github/ruthenian8/dff-telegram-connector/badge.svg?branch=main)](https://coveralls.io/github/deepmipt/dialog_flow_engine?branch=main) -->
[![Codestyle](https://github.com/ruthenian8/dff-telegram-connector/workflows/codestyle/badge.svg)](https://github.com/ruthenian8/dff-telegram-connector)
[![Tests](https://github.com/ruthenian8/dff-telegram-connector/workflows/test_coverage/badge.svg)](https://github.com/ruthenian8/dff-telegram-connector)
[![License Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/ruthenian8/dff-telegram-connector/blob/main/LICENSE)
![Python 3.6, 3.7, 3.8, 3.9](https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8%20%7C%203.9-green.svg)
<!-- [![PyPI](https://img.shields.io/pypi/v/dff-telegram-connector)](https://pypi.org/project/dff-telegram-connector/)
[![Downloads](https://pepy.tech/badge/dff-telegram-connector)](https://pepy.tech/project/dff-telegram-connector) -->

# Quick Start
## Installation
```bash
pip install dff-telegram-connector
```

## Basic example
```python
import os

from df_engine.core.keywords import GLOBAL, TRANSITIONS, RESPONSE
from df_engine.core import Context, Actor

from dff_telegram_connector.basic_connector import DffBot

db_connector=dict()

bot = DffBot(os.getenv("BOT_TOKEN"), db_connector=db_connector)

# create dialog plot
plot = {
    GLOBAL: {
        TRANSITIONS: {
            ("flow", "node_hi"): bot.cnd.message_handler(commands=["start"]), 
            ("flow", "node_ok"): bot.cnd.message_handler(commands=["finish"])
        }
    },
    "flow": {
        "node_hi": {RESPONSE: "Hi!!!"},
        "node_bye": {RESPONSE: "Bye!!!"},
    },
}

actor = Actor(plot, start_label=("root", "start"), fallback_label=("root", "fallback"))


@bot.message_handler(func=lambda message: True)
def dialog_handler(update, data: dict):
    # retrieve the saved context or create a new one
    context = data["context"]

    context = actor(context)
    response = context.last_response

    if isinstance(response, str):
        bot.send_message(update.from_user.id, response)
    # write some conditions to choose an alternative response method

    # update the `context` key in `data` to save changes to the state
    data["context"] = context


if __name__ == "__main__":
    bot.infinity_polling()
```

To get some of the more advanced examples, take a look at [examples](https://github.com/ruthenian8/dff-telegram-connector/tree/main/examples) on GitHub.

# Contributing to the Dialog Flow Engine

Please refer to [CONTRIBUTING.md](https://github.com/deepmipt/dialog_flow_engine/blob/dev/CONTRIBUTING.md).
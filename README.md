
# Dff Telegram Connector

[Dff Telegram Connector](https://github.com/ruthenian8/df-telegram-connector) is an extension to the [Dialogflow Engine](https://github.com/deepmipt/dialog_flow_engine), a minimalistic open-source engine for conversational services.

[Dff Telegram Connector](https://github.com/ruthenian8/df-telegram-connector) is an adapter module that integrates `df_engine` and [pytelegrambotapi](https://github.com/eternnoir/pyTelegramBotAPI) library, a popular Python implementation of the Telegram Bot API. In combination, these two components make the development of conversational services for Telegram straightforward and intuitive: while `pytelegrambotapi` provides an interface to build FSM-based bots, its capabilities in this domain are somewhat limited. In contrast, combining `df_engine` with `pytelegrambotapi` offers a comprehensive way to define a Finite State Machine and wire it up with your bot. (For more information, see the [Dialogflow Engine](https://github.com/deepmipt/dialog_flow_engine) documentation.)

`DFFBot` class that we use inherits from `TeleBot`, which is why all the `TeleBot` methods are still available. You can use this class exactly like you've been using `TeleBot`, but with a number of small differences. 

Inside the `cnd` subspace of the new class you will find some factory methods that create `df_engine`-style FSM transitions based on the updates that your service receives from Telegram: not only `messages`, but also `callback queries` and many more. All of those can now be handled by `df_engine's` `Actor` that will transition to the right part of the `Plot` depending on the conditions you choose. 

For instance, the following construction in your `Script` will ensure that the `Actor` transitions to the start node on each use of the "/start" command:

```python
TRANSITIONS: {("root", "start"): bot.cnd.message_handler(commands=["start"])}
```

As one can see from the example above, the name and signature of the method match those of the `TeleBot`.`message_handler` method, which is why you don't have to learn new things to make use of this feature.

Full examples of working bots can be found in the [examples directory](https://github.com/ruthenian8/df-telegram-connector/tree/main/examples).

<!-- [![Documentation Status](https://df-telegram-connector.readthedocs.io/en/stable/?badge=stable)](https://readthedocs.org/projects/df-telegram-connector/badge/?version=stable) -->
<!-- [![Coverage Status](https://coveralls.io/repos/github/ruthenian8/df-telegram-connector/badge.svg?branch=main)](https://coveralls.io/github/deepmipt/dialog_flow_engine?branch=main) -->
[![Codestyle](https://github.com/ruthenian8/df-telegram-connector/workflows/codestyle/badge.svg)](https://github.com/ruthenian8/df-telegram-connector)
[![Tests](https://github.com/ruthenian8/df-telegram-connector/workflows/test_coverage/badge.svg)](https://github.com/ruthenian8/df-telegram-connector)
[![License Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/ruthenian8/df-telegram-connector/blob/main/LICENSE)
![Python 3.6, 3.7, 3.8, 3.9](https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8%20%7C%203.9-green.svg)
<!-- [![PyPI](https://img.shields.io/pypi/v/df-telegram-connector)](https://pypi.org/project/df-telegram-connector/)
[![Downloads](https://pepy.tech/badge/df-telegram-connector)](https://pepy.tech/project/df-telegram-connector) -->

# Quickstart
## Installation
```bash
pip install df-telegram-connector
```

## Basic example
```python
import os

from df_engine.core.keywords import GLOBAL, TRANSITIONS, RESPONSE
from df_engine.core import Context, Actor

from df_telegram_connector.connector import DffBot

db_connector=dict()

bot = DffBot(os.getenv("BOT_TOKEN"), db_connector=db_connector)

# create a dialog plot (FSM prototype)
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
    # possibly, add some conditions to choose an alternative response method

    # update the `context` key in the `data` variable to save the new state
    data["context"] = context


if __name__ == "__main__":
    bot.infinity_polling()
```

To get some of the more advanced examples, take a look at [examples](https://github.com/ruthenian8/df-telegram-connector/tree/main/examples) on GitHub.

# Contributing to the Dialog Flow Engine

Please refer to [CONTRIBUTING.md](https://github.com/deepmipt/dialog_flow_engine/blob/dev/CONTRIBUTING.md).
"This script ensures that example scripts can successfully compile and are ready to run"
import sys

import pytest

sys.path.insert(0, "../")


def test_basics():
    from examples.basics.basic_bot import bot, actor

    assert bot
    assert actor
    from examples.basics.pictures import bot, actor

    assert bot
    assert actor
    from examples.basics.commands_and_buttons import bot, actor

    assert bot
    assert actor


def test_generics():
    from examples.generic_response.callback_queries import bot, actor

    assert bot
    assert actor
    from examples.generic_response.pictures import bot, actor

    assert bot
    assert actor


def test_runner():
    from examples.df_runner.flask import bot, provider, runner

    assert bot
    assert provider
    assert runner
    from examples.df_runner.polling import bot, provider, runner

    assert bot
    assert provider
    assert runner

import sys
import os

import pytest

sys.path.insert(0, "../")
from examples.basic_bot import bot, actor

for variable in ["BOT_TOKEN"]:
    if variable not in os.environ:
        raise AssertionError(f"{variable} variable needs to be set to continue")


@pytest.fixture(scope="session")
def actor_instance():
    yield actor

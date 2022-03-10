import pytest

from dff_telegram_connector.dff_telegram_connector import main


def test_main():
    assert main() is None

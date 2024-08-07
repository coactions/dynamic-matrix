"""Tests for github action."""

import sys
from subprocess import run


def test_foo() -> None:
    """Sample test."""
    run([sys.executable, "entrypoint.py"], check=True, shell=False)  # noqa: S603

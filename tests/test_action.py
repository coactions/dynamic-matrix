"""Tests for github action."""

import json
import os
import sys
import tempfile
from subprocess import run

import pytest


@pytest.mark.parametrize(
    ("passed_env", "expected"),
    [
        pytest.param(
            {
                "INPUT_DEFAULT_PYTHON": "3.8",
                "INPUT_LINUX": "full",
                "INPUT_MACOS": "minmax",
                "INPUT_MAX_PYTHON": "3.8",
                "INPUT_MIN_PYTHON": "3.8",
                "INPUT_OTHER_NAMES": "z\nall-linux-arm64:tox -e py38-unit;tox -e py310-integration",
                "INPUT_PLATFORMS": "linux-arm64:ubuntu-24.04-arm64-2core",
                "INPUT_SKIP_EXPLODE": "1",
                "INPUT_WINDOWS": "minmax",
            },
            {
                "matrix": {
                    "include": [
                        {
                            "command": "tox -e py38-unit",
                            "command2": "tox -e py310-integration",
                            "name": "all-linux-arm64",
                            "os": "ubuntu-24.04-arm64-2core",
                            "python_version": "3.8\n3.10",
                        },
                        {
                            "command": "tox -e z",
                            "name": "z",
                            "os": "ubuntu-24.04",
                            "python_version": "3.8",
                        },
                    ],
                },
            },
            id="1",
        ),
    ],
)
def test_action(passed_env: dict[str, str], expected: dict[str, str]) -> None:
    """Sample test."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        env = {
            **os.environ.copy(),
            **passed_env,
            "TEST_GITHUB_OUTPUT_JSON": temp_file.name,
        }

        result = run(
            [sys.executable, "entrypoint.py"],
            text=True,
            shell=False,
            check=True,
            capture_output=True,
            env=env,
        )
        assert result.returncode == 0
        temp_file.seek(0)
        effective = temp_file.read().decode("utf-8")
        data = json.loads(effective)
        assert isinstance(data, dict), data
        assert len(data) == 1
        assert "matrix" in data
        assert data == expected, result
        # TestCase().assertDictEqual(data, expected)

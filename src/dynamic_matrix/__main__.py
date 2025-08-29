#!env python3
"""Action body."""

import json
import os
import re
from pathlib import Path
from typing import Any

from actions_toolkit import core

KNOWN_PYTHONS = ("3.7", "3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14-dev")
PYTHON_REDIRECTS = {
    "3.14": "3.14-dev",  # Remove once GHA allows 3.14 as a valid version
}
PLATFORM_MAP = {
    "linux": "ubuntu-24.04",
    "macos": "macos-13",
    "windows": "windows-latest",
}
IMPLICIT_PLATFORM = "linux"
IMPLICIT_MIN_PYTHON = "3.8"
IMPLICIT_MAX_PYTHON = "3.14"
IMPLICIT_DEFAULT_PYTHON = "3.9"
IMPLICIT_SKIP_EXPLODE = "0"


def sort_human(data: list[str]) -> list[str]:
    """Sort a list using human logic, so 'py39' comes before 'py311'."""

    def convert(text: str) -> str | float:
        return float(text) if text.isdigit() else text

    def alphanumeric(key: str) -> list[str | float]:
        return [convert(c) for c in re.split(r"([-+]?\d*\\.?\d*)", key)]

    data.sort(key=alphanumeric)
    return data


def add_job(result: dict[str, dict[str, str]], name: str, data: dict[str, str]) -> None:
    """Add a new job to the list of generated jobs."""
    if name in result:
        core.set_failed(
            f"Action failed as it tried add an already a job with duplicate name {name}: {result[name]} already present while trying to add {data}",
        )
    result[name] = data


def get_platforms() -> list[str]:
    """Retrieve effective list of platforms."""
    platforms = []
    for v in core.get_input("platforms", required=False).split(","):
        platform, run_on = v.split(":") if ":" in v else (v, None)
        if not platform:
            continue
        if run_on:
            core.debug(
                f"Add platform '{platform}' with run_on={run_on} to known platforms",
            )
            PLATFORM_MAP[platform] = run_on
        platforms.append(platform)
    return platforms


def produce_output(output: dict[str, Any]) -> None:
    """Produce the output."""
    if "TEST_GITHUB_OUTPUT_JSON" in os.environ:
        with Path(os.environ["TEST_GITHUB_OUTPUT_JSON"]).open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(output, f)
    for key, value in output.items():
        core.set_output(key, value)


# loop list staring with given item
# pylint: disable=too-many-locals,too-many-branches,too-many-statements
def main() -> None:  # noqa: C901,PLR0912,PLR0915
    """Execute main function."""
    # print all env vars starting with INPUT_
    for k, v in os.environ.items():
        if k.startswith("INPUT_"):
            core.info(f"Env var {k}={v}")
    try:
        # ignore empty lines
        other_names = [
            x for x in core.get_input("other_names", required=False).split("\n") if x
        ]
        platforms = get_platforms()
        core.info(f"Effective platforms: {platforms}")
        core.info(f"Platform map: {PLATFORM_MAP}")

        min_python = core.get_input("min_python") or IMPLICIT_MIN_PYTHON
        max_python = core.get_input("max_python") or IMPLICIT_MAX_PYTHON
        default_python = core.get_input("default_python") or IMPLICIT_DEFAULT_PYTHON
        skip_explode = int(core.get_input("skip_explode") or IMPLICIT_SKIP_EXPLODE)
        strategies = {}

        for platform in PLATFORM_MAP:
            strategies[platform] = core.get_input(platform, required=False)

        core.debug(f"Testing strategy: {strategies}")

        result: dict[str, dict[str, str]] = {}
        if max_python == "3.14":
            python_names = KNOWN_PYTHONS[KNOWN_PYTHONS.index(min_python) :]
        else:
            python_names = KNOWN_PYTHONS[
                KNOWN_PYTHONS.index(min_python) : (KNOWN_PYTHONS.index(max_python) + 1)
            ]
        python_flavours = len(python_names)

        def sort_key(s: str) -> tuple[int, str]:
            """Sorts longer strings first."""
            return -len(s), s

        # we put longer names first in order to pick the most specific platforms
        platform_names_sorted = sorted(PLATFORM_MAP.keys(), key=sort_key)
        core.info(f"Known platforms sorted: {platform_names_sorted}")

        for line in other_names:
            # line can look like:
            # - name
            # - name:command1;command2
            # - name:command:runner=ubuntu-20.04
            segments = line.split(":")
            name = segments[0]
            commands = [f"tox -e {name}"]  # implicit commands if not provided
            args = {}
            if len(segments) > 1 and segments[1]:
                commands = segments[1].split(";")
            if len(segments) > 2:  # noqa: PLR2004
                # we have arguments foo=bar;baz=qux
                try:
                    args = dict(x.split("=") for x in segments[2].split(";"))
                except ValueError:
                    core.set_failed(
                        f"Action failed due to optional args not having the expected format 'a=b;c=d', value being '{segments[2]}'",
                    )

            # Check for using correct python version for other_names like py310-devel.
            pythons: list[str] = [
                f"{py_version[0]}.{py_version[1:]}"
                for py_version in re.findall(r"py(\d+)", line)
            ]
            if not pythons:
                pythons.append(default_python)
            if "runner" not in args:
                for platform_name in platform_names_sorted:
                    if platform_name in name:
                        break
                else:
                    platform_name = "linux"  # implicit platform (os) to use
                args["runner"] = PLATFORM_MAP[platform_name]

            data = {
                # we expose all args in the output
                **args,
                "name": name,
                "command": commands[0],
                # versions compatible with actions/setup-python action
                "python_version": "\n".join(
                    [
                        PYTHON_REDIRECTS.get(env_python, env_python)
                        for env_python in pythons
                    ],
                ),
                # versions compatible with astral-sh/setup-uv action
                "uv_python_version": "\n".join(pythons),
                "os": args["runner"],
            }
            for index, command in enumerate(commands[1:]):
                data[f"command{index + 2}"] = command
            add_job(
                result,
                name,
                data,
            )

        if not skip_explode:
            for platform in platforms:
                for i, python in enumerate(python_names):
                    py_name = re.sub(r"\D", "", python.strip("."))
                    suffix = "" if platform == IMPLICIT_PLATFORM else f"-{platform}"
                    if strategies[platform] == "minmax" and (
                        i not in (0, python_flavours - 1)
                    ):
                        continue

                    add_job(
                        result,
                        f"py{py_name}{suffix}",
                        {
                            "python_version": python,
                            "os": PLATFORM_MAP.get(platform, platform),
                            "command": f"tox -e py{py_name}",
                        },
                    )

        core.info(f"Generated {len(result)} matrix entries.")
        names = sort_human(list(result.keys()))
        core.info(f"Job names: {', '.join(names)}")
        matrix_include = []
        matrix_include = [
            dict(sorted(dict(result[name], name=name).items())) for name in names
        ]
        core.info(
            f"Matrix jobs ordered by their name: {json.dumps(matrix_include, indent=2)}",
        )
        output = {"matrix": {"include": matrix_include}}
        produce_output(output)

    # pylint: disable=broad-exception-caught
    except Exception as exc:  # noqa: BLE001
        core.set_failed(f"Action failed due to {exc}")


if __name__ == "__main__":
    main()

#!env python3
# """Action body."""
import json
import os
import re

from actions_toolkit import core

KNOWN_PYTHONS = ("3.7", "3.8", "3.9", "3.10", "3.11", "3.12", "3.13-dev")
PYTHON_REDIRECTS = {
    "3.13": "3.13-dev" # Remove once GHA allows 3.13 as a valid version
}
PLATFORM_MAP = {
    "linux": "ubuntu-24.04",
    "macos": "macos-13",
    "windows": "windows-latest",
}
IMPLICIT_PLATFORM = "linux"
IMPLICIT_MIN_PYTHON = "3.8"
IMPLICIT_MAX_PYTHON = "3.12"
IMPLICIT_DEFAULT_PYTHON = "3.9"
IMPLICIT_SKIP_EXPLODE = "0"

# loop list staring with given item
def main() -> None:
    """Main."""
    # print all env vars starting with INPUT_
    for k, v in os.environ.items():
        if k.startswith("INPUT_"):
            core.info(f"Env var {k}={v}")
    try:
        other_names = core.get_input("other_names", required=False).split("\n")
        platforms = core.get_input("platforms", required=False).split(",")
        min_python = core.get_input("min_python") or IMPLICIT_MIN_PYTHON
        max_python = core.get_input("max_python") or IMPLICIT_MAX_PYTHON
        default_python = core.get_input("default_python") or IMPLICIT_DEFAULT_PYTHON
        skip_explode = int(core.get_input("skip_explode") or IMPLICIT_SKIP_EXPLODE)
        strategies = {}
        for platform in PLATFORM_MAP:
            strategies[platform] = core.get_input(platform, required=False)

        core.debug(f"Testing strategy: {strategies}")

        result = []
        try:
            if max_python == "3.13":
                python_names = KNOWN_PYTHONS[KNOWN_PYTHONS.index(min_python) :]
            else:
                python_names = KNOWN_PYTHONS[
                    KNOWN_PYTHONS.index(min_python) : (KNOWN_PYTHONS.index(max_python) + 1)
                ]
        except Exception as e:
            core.debug(e)
            python_names = ()
        python_flavours = len(python_names)
        core.debug("...")
        for env in other_names:
            env_python = default_python
            # Check for using correct python version for other_names like py310-devel.
            match = re.search(r"py(\d+)", env)
            if match:
                py_version = match.groups()[0]
                env_python = f"{py_version[0]}.{py_version[1:]}"
            result.append(
                {
                    "name": env,
                    "passed_name": env,
                    "python_version": PYTHON_REDIRECTS.get(env_python, env_python),
                    "os": PLATFORM_MAP["linux"],
                }
            )

        if not skip_explode:
            for platform in platforms:
                for i, python in enumerate(python_names):
                    py_name = re.sub(r"[^0-9]", "", python.strip("."))
                    if platform == IMPLICIT_PLATFORM:
                        suffix = ""
                    else:
                        suffix = f"-{platform}"

                    if strategies[platform] == "minmax" and (
                        i not in (0, python_flavours - 1)
                    ):
                        continue

                    result.append(
                        {
                            "name": f"py{py_name}{suffix}",
                            "python_version": python,
                            "os": PLATFORM_MAP.get(platform, platform),
                            "passed_name": f"py{py_name}",
                        }
                    )

        core.info(f"Generated {len(result)} matrix entries.")
        names = [k["name"] for k in result]
        core.info(f"Job names: {', '.join(names)}")
        core.info(f"matrix: {json.dumps(result, indent=2)}")

        core.set_output("matrix", {"include": result})

    except Exception as exc:
        core.set_failed(f"Action failed due to {exc}")


if __name__ == "__main__":
    # only used for local testing, emulating use from github actions
    if os.getenv("GITHUB_ACTIONS") is None:
        os.environ["INPUT_DEFAULT_PYTHON"] = "3.10"
        os.environ["INPUT_LINUX"] = "full"
        os.environ["INPUT_MACOS"] = "minmax"
        os.environ["INPUT_MAX_PYTHON"] = "3.13"
        os.environ["INPUT_MIN_PYTHON"] = "3.8"
        os.environ["INPUT_OTHER_NAMES"] = "lint\npkg\npy313-devel"
        os.environ["INPUT_PLATFORMS"] = "linux,macos"  # macos and windows
        os.environ["INPUT_SKIP_EXPLODE"] = "0"
        os.environ["INPUT_WINDOWS"] = "minmax"
    main()

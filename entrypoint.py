#!env python3
# """Action body."""
import os
import json
import re
from actions_toolkit import core

KNOWN_PYTHONS = ("3.7", "3.8", "3.9", "3.10", "3.11", "3.12-dev")
PLATFORM_MAP = {
    "linux": "ubuntu-22.04",
    "macos": "macos-12",
    "windows": "windows-latest",
}
IMPLICIT_PLATFORM = "linux"


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
        min_python = core.get_input("min_python", required=True)
        max_python = core.get_input("max_python", required=True)
        def_python = core.get_input("def_python", required=True)
        strategies = {}
        for platform in PLATFORM_MAP:
            strategies[platform] = core.get_input(platform, required=False)

        core.debug(f"Testing strategy: {strategies}")

        result = []
        if max_python == "3.12":
            python_names = KNOWN_PYTHONS[KNOWN_PYTHONS.index(min_python) :]
        else:
            python_names = KNOWN_PYTHONS[KNOWN_PYTHONS.index(min_python) : (KNOWN_PYTHONS.index(max_python)+1)]
        python_flavours = len(python_names)
        for env in other_names:
            result.append(
                {
                    "name": env,
                    "passed_name": env,
                    "python_version": def_python,
                    "os": PLATFORM_MAP["linux"],
                }
            )

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
                        "os": PLATFORM_MAP[platform],
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
        os.environ["INPUT_OTHER_NAMES"] = "lint\npkg"
        os.environ["INPUT_MIN_PYTHON"] = "3.8"
        os.environ["INPUT_MAX_PYTHON"] = "3.12"
        os.environ["INPUT_DEF_PYTHON"] = "3.9"
        os.environ["INPUT_PLATFORMS"] = "linux,macos"  # macos and windows
        os.environ["INPUT_LINUX"] = "full"
        os.environ["INPUT_MACOS"] = "minmax"
        os.environ["INPUT_WINDOWS"] = "minmax"

    main()

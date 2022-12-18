# matrix

Github Action that returns a dynamic test matrix. Currently supports projects
using:

* `python` and `tox`

## Supported arguments, all being optional:

* `min_python` - Minimal version of python to be tested against.
* `other_names`- A list of other tox environments to include in the matrix. We
  plan to read them from `tox_envs` field in `tox.ini`.
* `platforms` - Default to `linux` only but can be `linux`, `windows`, `macos`
   or a combination of them (comma separated).
* `linux`: matrix expansion strategy for Linux, `full` or `minmax`.
* `windows`: matrix expansion strategy for Windows, `full` or `minmax`.
* `macos`: matrix expansion strategy for MacOS, `full` or `minmax`.

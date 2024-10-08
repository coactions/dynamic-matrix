# matrix

GitHub Action that returns a dynamic test matrix. Currently, it supports
projects using:

- `python` and `tox`

## Supported optional arguments:

- `min_python` - Minimal version of python to be tested against, default is `"3.8"`. The maximum value is currently `"3.14"`
- `other_names`- A list of other tox environments to include in the matrix. We
  plan to read them from [envlist](https://tox.wiki/en/latest/config.html#envlist) field in `tox.ini`.
- `platforms` - Default to `linux` only but can be `linux`, `windows`, `macos`
  or a combination of them (comma separated).
- `linux`: matrix expansion strategy for Linux, `full` or `minmax`.
- `windows`: matrix expansion strategy for Windows, `full` or `minmax`.
- `macos`: matrix expansion strategy for MacOS, `full` or `minmax`.
- `skip_explode`: pass 1 if you want to avoid generating implicit pyXY jobs.

## Upgrading action from v2 to v3

The returned tox environment name from returned `passed_name` was replaced by
`command` which would now contain the full command to be executed like
`tox -e py39`.

```yaml
# old v2 syntax:
- run: tox -e ${{ matrix.passed_env }}
# new v3 syntax:
- run: ${{ matrix.command }}
```

## Returned values

This action returns a list of actions to be executed, each of them containing
the following fields:

- `name` of the job to run

- `command`, and optional `command2`, `command3`, ... which are the commands
  to be executed using `run: ` step.

- `python_version` is a string compatible with the expected format used by
  [actions/setup-python](https://github.com/actions/setup-python) github action,
  like `3.12` or `3.11\n3.12` when multiple python versions are to be installed.

- `os` the name of an github runner, should be passed to `runs_on: `

## Examples

Simple workflow using coactions/dynamic-matrix

```yaml
# .github/workflows/tox.yml (your workflow file)
---
jobs:
  pre: # <-- this runs before your real matrix job
    name: pre
    runs-on: ubuntu-24.04
    outputs:
      matrix: ${{ steps.generate_matrix.outputs.matrix }}
    steps:
      - name: Determine matrix
        id: generate_matrix
        uses: coactions/dynamic-matrix@v3
        with:
          other_names: |
            lint
            pkg
            py39-all:tox -f py39

  build:
    name: ${{ matrix.name }}
    runs-on: ${{ matrix.os || 'ubuntu-24.04' }}
    needs: pre
    strategy: # this the magic part, entire matrix comes from pre job!
      matrix: ${{ fromJson(needs.pre.outputs.matrix) }}

    steps: # common steps used to test with tox
      - uses: actions/checkout@main
        with:
          fetch-depth: 0

      - name: Set up python ${{ matrix.python_version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python_version }}

      - name: Install tox
        run: |
          python -m pip install -U pip
          pip install tox

      - run: ${{ matrix.command }}
```

## Q&A

### Which projects using tox would benefit from this GitHub Action?

If your tox [envlist](https://tox.wiki/en/latest/config.html#envlist) is simple, like `lint,packaging,py{36,37,38,39}` you are among the best candidates to make use of it as that is the primary usage case it covers. If you use environments combining multiple factors, you will need to specify them in `other_names` argument.

### Why this action does not just load <tt>envlist</tt> values?

We plan to add support for this in the future but it might not be
as simple as one would assume. For historical reasons, `envlist` does very often already include Python versions instead of generic `py` entry or
they are outdated. The repository code is not available at the
time this action runs.

### Why only Linux testing is enabled by default?

Linux runners are the fastest ones and many Python projects do not need to support platforms like Windows or macOS. That is why the default platform contains only lines. Still, you can enable all of them by specifying `platforms: linux,windows,macos` in the action arguments.

### Why Windows and MacOS matrix expansion strategy is different than the Linux one?

The defaults for macOS and Windows are `minmax` while for Linux is `full`. This limit resource usage low while still providing a good level of testing. If your pythons are `py38,py39,py310,py311` unless you specify `windows: full` you will see only two Windows based jobs in the generated matrix: py38 and py311.

### Why is <tt>other_names</tt> a multiline string instead of being a comma-separated one?

We wanted to allow users to chain (group) multiple tox environments in a single command like `tox run -e lint,packaging`, and this means that we needed to allow users to use commas as part of a valid name, without
splitting on it.

### How to use custom test commands for some jobs.

In v3 we allow users to add entries like `py39-all:tox -f py39` inside `other-names`. This would be translated into returning the job name `py39-all` and the command `tox -f py39`.

This is especially useful as it allows users to make use of labels (`-m`) and factor filtering (`-f`) to select groups of tox environments instead of just using the environments (`-e`) selector.

This allows running other test frameworks instead of tox.

### Generating multiple test commands for the same job

In some cases, you might want to have separate test steps inside the same
job, as this makes it easier to debug them. As GHA does not have any support
for step looping, you are forced to manually add several steps if you want
to use this feature.

Use `;` as a separator inside the other_names to achieve this:

```yaml
# Return two commands instead of one for `all-tests` job
uses: coactions/dynamic-matrix@v3
with:
  other_names: |
    all-tests:tox -e unit;tox -e integration
  # ^ job-name ':' 1st command ';' 2nd command ...
---
# Inside matrix job:
steps:
  - run: "${{ matrix.command }}"
  # Execute second command *if* it does exist
  - run: "${{ matrix.command2 }}"
    if: "${{ matrix.command2 || false }}"
```

### How to use custom test commands for some jobs.

In v3 we allow users to add entries like `py39-all:tox -f py39` inside `other-names`. This would translated into returning the job name `py39-all` and the command `tox -f py39`.

This is especially useful as it allows users to make use of labels (`-m`) and factor filtering (`-f`) to select groups of tox environments instead of just using the environments (`-e`) selector.

This allows running other test frameworks instead of tox.

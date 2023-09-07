# matrix

GitHub Action that returns a dynamic test matrix. Currently it supports
projects using:

- `python` and `tox`

## Supported optional arguments:

- `min_python` - Minimal version of python to be tested against, default is `"3.8"`. The maximum value is currently `"3.12"`
- `other_names`- A list of other tox environments to include in the matrix. We
  plan to read them from [envlist](https://tox.wiki/en/latest/config.html#envlist) field in `tox.ini`.
- `platforms` - Default to `linux` only but can be `linux`, `windows`, `macos`
  or a combination of them (comma separated).
- `linux`: matrix expansion strategy for Linux, `full` or `minmax`.
- `windows`: matrix expansion strategy for Windows, `full` or `minmax`.
- `macos`: matrix expansion strategy for MacOS, `full` or `minmax`.

## Examples

<details><summary>Simple workflow using coactions/dynamic-matrix</summary><p>

```yaml
# .github/workflows/tox.yml (your workflow file)
---
jobs:
  pre: # <-- this runs before your real matrix job
    name: pre
    runs-on: ubuntu-22.04
    outputs:
      matrix: ${{ steps.generate_matrix.outputs.matrix }}
    steps:
      - name: Determine matrix
        id: generate_matrix
        uses: coactions/dynamic-matrix@v1
        with:
          other_names: |
            lint
            pkg

  build:
    name: ${{ matrix.name }}
    runs-on: ${{ matrix.os || 'ubuntu-22.04' }}
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

      - run: tox run -e ${{ matrix.passed_name }}
```

</p></details>

## Q&A

<details><summary>Which projects using tox would benefit from this GitHub Action?</summary><p>

If your tox [envlist](https://tox.wiki/en/latest/config.html#envlist) is simple, like `lint,packaging,py{36,37,38,39}` you are among the best candidates to make use of it as that is the primary usage case it covers. If you use environments combining multiple factors, you will need to specify them in `other_names` argument.

</p></details>

<details><summary>Why this action does not just load <tt>envlist</tt> values?</summary><p>

We plan to add support for this in the future but it might not be
as simple as one would assume. For historical reasons `envlist` do very often already include python versions instead of generic `py` entry or
they are outdated. The repository code is not available at the
time this action runs.

</p></details>

<details><summary>Why only Linux testing is enabled by default?</summary><p>

Linux runners are the fastest ones and many Python projects do not need to support platforms like Windows or macOS. That is why the default platform contains only lines. Still, you can enable all of them by specifying `platforms: linux,windows,macos` in the action arguments.

</p></details>

<details><summary>Why Windows and MacOS matrix expansion strategy is different than Linux one?</summary><p>

The defaults for macOS and Windows are `minmax` while for Linux is `full`. This limit resource usage low while still providing a good level of testing. If your pythons are `py38,py39,py310,py311` unless you specify `windows: full` you will see only two Windows based jobs in the generated matrix: py38 and py311.

</p></details>

<details><summary>What is the difference between <tt>name</tt> and <tt>passed_name</tt> in generated matrix?</summary><p>

`name` is aimed to be the job name displayed in GHA, while `passed_name` is the tox environment name. We did not name it `tox_env` because we plan to add support for other testing frameworks, which might use different
terminology.

</p></details>

<details><summary>Why is <tt>other_names</tt> a multiline string instead of being comma separated?</summary><p>

We wanted to allow users to chain (group) multiple tox environments in a single command like `tox run -e lint,packaging`, and this means that we
needed to allow users to use commas as part of a valid name, without
splitting on it.

</p></details>

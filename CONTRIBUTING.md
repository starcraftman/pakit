# Contribting Guidelines

## Issues

- First specify python version you are using, i.e. `python --version`
- Clearly state the steps to reproduce your bug.
- If there are relevant error messages in the log or console,
append at end in a code block (three back ticks).

## PRs

- All code should be runnable on python >= 2.7.
- All new code should be covered by tests. Coverage should not drop.
- Your code should comply with `flake8` & `pylint`.
- You can run all tests including `flake8`, `pylint` & `py.test` with `tox`.
- You can check coverage with `tox -e coverage`.

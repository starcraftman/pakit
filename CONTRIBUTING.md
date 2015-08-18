# Contribting Guidelines

## Issues

- Please specify the python version you are using.
- Clearly specify steps to reproduce.
- If there are relevant error messages in the log or console, append at end.

## PRs

- Any new code should be covered by tests, ideally coverage never drops substantially.
- Your code should comply with flake8 & pylint.
- You can check all this by just using `tox`.
- New code should ideally be runnable on python >= 2.7 . Though I don't currently
test for this I've been careful to make it easy.

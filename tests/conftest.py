from pytest import fixture

from marc_lint.linter import MarcLint


@fixture
def linter():
    """Fresh MarcLint instance for each test."""
    return MarcLint()

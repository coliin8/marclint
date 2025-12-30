"""MARC Linting library for Python."""

__version__ = "0.0.1"

from .linter import MarcLint
from .warning import MarcWarning

__all__ = ["MarcLint", "MarcWarning"]

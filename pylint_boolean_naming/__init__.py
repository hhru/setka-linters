"""Register checker to enforce variable naming for boolean variables.

This module is used to register the checker to enforce the naming of boolean,
the prefix names are configurable, default being 'is', 'has', 'can'.
"""

# Standard Library
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # External Party
    from pylint.lint import PyLinter


def register(linter: "PyLinter") -> None:
    """Register the checker to enforce the naming of boolean variables."""
    from .checker import BooleanNamingChecker

    linter.register_checker(BooleanNamingChecker(linter))
"""Command-line interface package for clippy-code."""

from .first_time_setup import run_first_time_setup, should_run_setup
from .main import main
from .oneshot import run_one_shot
from .repl import run_interactive

__all__ = ["main", "run_one_shot", "run_interactive", "run_first_time_setup", "should_run_setup"]

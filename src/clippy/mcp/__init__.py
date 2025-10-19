"""MCP (Model Context Protocol) integration for clippy-code."""

from .config import Config, load_config
from .manager import Manager

__all__ = ["Manager", "Config", "load_config"]

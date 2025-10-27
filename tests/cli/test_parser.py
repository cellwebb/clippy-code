"""Tests for the CLI argument parser."""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from clippy.cli.parser import create_parser


def _parse(args: Sequence[str]):
    return create_parser().parse_args(args)


def test_parser_defaults() -> None:
    parsed = _parse([])

    assert parsed.prompt == []
    assert parsed.yes is False
    assert parsed.model is None
    assert parsed.base_url is None
    assert parsed.config is None
    assert parsed.verbose is False


@pytest.mark.parametrize(
    "args, expected_prompt",
    [
        (["fix", "bug"], ["fix", "bug"]),
        (["single"], ["single"]),
    ],
)
def test_parser_collects_prompt(args: list[str], expected_prompt: list[str]) -> None:
    parsed = _parse(args)
    assert parsed.prompt == expected_prompt


def test_parser_supports_flags() -> None:
    parsed = _parse(["-y"])

    assert parsed.yes is True


def test_parser_accepts_configuration_options() -> None:
    parsed = _parse(
        [
            "--model",
            "gpt-5",
            "--base-url",
            "https://api.example.com/v1",
            "--config",
            "permissions.yaml",
            "--verbose",
        ]
    )

    assert parsed.model == "gpt-5"
    assert parsed.base_url == "https://api.example.com/v1"
    assert parsed.config == "permissions.yaml"
    assert parsed.verbose is True

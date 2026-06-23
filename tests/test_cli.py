"""smoke tests for the cli using typer's runner. these do not call a real model."""

import pytest

typer = pytest.importorskip("typer")
from typer.testing import CliRunner  # noqa: E402

from agent.cli import app  # noqa: E402

runner = CliRunner()


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "personal-aiagent" in result.stdout


def test_tools_command_lists_tools():
    result = runner.invoke(app, ["tools"])
    assert result.exit_code == 0
    assert "calculator" in result.stdout


def test_formats_command():
    result = runner.invoke(app, ["formats"])
    assert result.exit_code == 0
    assert "json" in result.stdout


def test_personas_command():
    result = runner.invoke(app, ["personas"])
    assert result.exit_code == 0
    assert "skeptic" in result.stdout


def test_cost_command():
    result = runner.invoke(app, ["cost", "hello there, what is up", "--model", "gpt-4o"])
    assert result.exit_code == 0
    assert "gpt-4o" in result.stdout


def test_config_command():
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "provider" in result.stdout

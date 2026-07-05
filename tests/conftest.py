"""Shared pytest fixtures for the pySET test suite."""

import pytest

from pyset.modules.misc.models import AppConfig
from pyset.view_model_app import ViewModelApp


@pytest.fixture(autouse=True)
def _isolated_from_real_environment(tmp_path, monkeypatch):
    """Keeps tests deterministic regardless of the developer's own shell/.env setup.

    AppConfig reads PYSET_ADMIN_SECRET from the environment and from a `.env` file in the working
    directory, and both take precedence over whatever a fixture passes explicitly. Without this,
    a developer who has set up `.env`/the env var for their own local server run would see fixtures
    like `secret='top-secret'` silently overridden when running the test suite.
    """
    monkeypatch.delenv('PYSET_ADMIN_SECRET', raising=False)
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def app_config() -> AppConfig:
    """Small, deterministic configuration for unit tests (no penalty delay, small session cap)."""
    return AppConfig(
        service_id='pySET-test',
        version='0.0.0-test',
        max_sessions=5,
        session_name_max_chars=36,
        max_players=4,
        player_name_max_chars=12,
        penalty_timeout_seconds=0,
        secret='top-secret',
    )


@pytest.fixture
def vm(app_config: AppConfig) -> ViewModelApp:
    """A ViewModelApp wired with the test config, exercised without going through Flask."""
    return ViewModelApp(app_config, scheme='http://', subdomain='localhost')

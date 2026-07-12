#!/usr/bin/env python3
"""Created on Wed Jan 25 11:17:51 2023.

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

import importlib.metadata

from pydantic import AliasChoices, BaseModel, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


class AIDifficultyConfig(BaseModel):
    """Min/max thinking time (milliseconds) an AI player waits before answering, per difficulty."""

    easy: tuple[int, int] = (10000, 15000)
    normal: tuple[int, int] = (7000, 10000)
    hard: tuple[int, int] = (3000, 5000)


class AppConfig(BaseSettings):
    """Application configuration, loaded primarily from ``config.json``.

    The ``secret`` field may additionally be supplied via the ``PYSET_ADMIN_SECRET`` environment
    variable, or a ``.env`` file in the working directory -- either of which takes precedence over
    ``config.json`` (see :meth:`settings_customise_sources`), so the real value never has to sit in
    plaintext in a file that gets committed.

    Field aliases mirror the exact SCREAMING_SNAKE_CASE keys used in ``config.json`` (and consumed
    verbatim by the Vue frontend via the ``get_config`` endpoint), while the Python-facing attribute
    names stay ``snake_case``.
    """

    model_config = SettingsConfigDict(populate_by_name=True, env_file='.env', env_file_encoding='utf-8', extra='ignore')

    service_id: str = 'pySET'
    # Single source of truth is pyproject.toml's [project] version -- config.json should not
    # (and no longer does) carry its own copy that can drift out of sync on a version bump.
    version: str = Field(default_factory=lambda: importlib.metadata.version('pyset'))
    app_version: str = '0.0.0'
    logging_level: int | str = 'INFO'
    max_sessions: int = Field(default=10, alias='MAX_SESSIONS')
    session_name_max_chars: int = Field(default=36, alias='SESSION_NAME_MAX_CHARS')
    session_ttl_seconds: int = Field(default=1800, alias='SESSION_TTL_SECONDS')
    max_players: int = Field(default=4, alias='MAX_PLAYERS')
    player_name_max_chars: int = Field(default=12, alias='PLAYER_NAME_MAX_CHARS')
    submit_timeout_seconds: int = Field(default=10, alias='SUBMIT_TIMEOUT_SECONDS')
    penalty_timeout_seconds: int = Field(default=20, alias='PENALTY_TIMEOUT_SECONDS')
    ai: AIDifficultyConfig = Field(default_factory=AIDifficultyConfig)
    secret: str = Field(default='', validation_alias=AliasChoices('secret', 'PYSET_ADMIN_SECRET'))

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Lets the environment / ``.env`` file override values loaded from ``config.json``.

        Pydantic-settings' default precedence favors constructor arguments (i.e. ``config.json``)
        over the environment, which is the opposite of what we want here.

        Returns:
            tuple[PydanticBaseSettingsSource, ...]: Sources in priority order, highest first.
        """
        return env_settings, dotenv_settings, init_settings, file_secret_settings

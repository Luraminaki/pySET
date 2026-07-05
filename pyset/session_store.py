#!/usr/bin/env python3
"""Created on Wed Jan 25 11:17:51 2023.

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

import contextlib
import enum
import logging
import threading
import time
from collections.abc import Callable, Generator

from pydantic import BaseModel, ConfigDict, Field, SkipValidation

from pyset.modules.game.game import Game
from pyset.modules.misc.models import AppConfig


class GameSession(BaseModel):
    """A single running :class:`~pyset.modules.game.game.Game` plus its session bookkeeping.

    ``lock`` serializes access to this specific session's mutable state (the ``Game``/``Grid``/
    ``Player`` objects reachable through ``game``) so that concurrent requests against *different*
    sessions can run in parallel, while requests against the *same* session still serialize
    safely. It isn't session data -- it's excluded from serialization.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    game: Game
    game_secret: str = ''
    created: int
    last_accessed: int
    ttl: int
    lock: SkipValidation[threading.Lock] = Field(default_factory=threading.Lock, exclude=True, repr=False)


class LogEvent(enum.StrEnum):
    """Human-readable tags used in log lines (not part of the wire contract)."""

    DATA_RECEIVED = 'DATA_RECEIVED'
    DELETING_GAME = 'DELETING_GAME'
    DELETING_GAME_TTL_REACHED = 'DELETING_GAME_TTL_REACHED'
    ORDER_66 = 'ORDER_66'


class SessionStore:
    """Thread-safe storage for the running :class:`GameSession` objects, keyed by game id.

    Two-tier locking: an internal table lock guards structural changes to the session table
    itself (insert/delete/replace/iterate); each ``GameSession``'s own lock (acquired via
    :meth:`locked`) guards that session's gameplay state. Requests against different sessions can
    therefore proceed concurrently, while requests against the same session still serialize.
    """

    def __init__(self, config: AppConfig, logger: logging.Logger):
        """Initializes the SessionStore.

        Args:
            config (AppConfig): Application configuration. `max_sessions` and
                `session_ttl_seconds` are read live off this object on every call (not snapshotted
                here), so changing them on the config takes effect immediately.
            logger (logging.Logger): Logger used for session lifecycle events.
        """
        self._sessions: dict[str, GameSession] = {}
        self._table_lock = threading.Lock()
        self._config: AppConfig = config
        self._logger = logger

    def __len__(self) -> int:
        """Returns the number of currently tracked sessions.

        Returns:
            int: Session count.
        """
        return len(self._sessions)

    def is_full(self) -> bool:
        """Checks whether the table has reached its configured capacity.

        Returns:
            bool: True if at capacity, False otherwise.
        """
        return len(self._sessions) >= self._config.max_sessions

    def get(self, game_id: str) -> GameSession | None:
        """Thread-safe lookup of a session by id.

        Args:
            game_id (str): Session to look up.

        Returns:
            GameSession | None: The session, or None if it doesn't (or no longer) exist.
        """
        with self._table_lock:
            return self._sessions.get(game_id)

    def items(self) -> list[tuple[str, GameSession]]:
        """Thread-safe snapshot of every (game_id, session) pair currently tracked.

        Unlike ``dict.items()``, this returns a copy rather than a live view, so it's safe to
        iterate without holding any lock (and without racing a concurrent insert/delete).

        Returns:
            list[tuple[str, GameSession]]: The snapshot.
        """
        with self._table_lock:
            return list(self._sessions.items())

    def create_if_missing(self, game_id: str, factory: Callable[[], GameSession]) -> None:
        """Atomically creates a session if (and only if) one doesn't already exist for `game_id`.

        `factory` runs while the table lock is held, so it's only ever invoked once per `game_id`
        even under concurrent calls -- keep it fast (it's just building a fresh Game/Grid here).

        Args:
            game_id (str): Session to create.
            factory (Callable[[], GameSession]): Builds the session; only called if needed.
        """
        with self._table_lock:
            if game_id not in self._sessions:
                self._sessions[game_id] = factory()

    def clear(self) -> None:
        """Removes every tracked session.

        Any request already past :meth:`locked` for an individual session (i.e. already holding
        that session's own lock) simply finishes on its own, now-orphaned ``GameSession`` -- its
        result won't be visible here anymore, which is fine for a rare admin wipe.
        """
        with self._table_lock:
            self._sessions = {}

    def evict_inactive(self) -> None:
        """Evicts sessions that have been inactive for longer than their TTL."""
        if self.is_full():
            now = int(time.time())
            with self._table_lock:
                inactive_games = [
                    game_id
                    for game_id, session in self._sessions.items()
                    if (now - session.last_accessed) >= self._config.session_ttl_seconds
                ]

                for game_id in inactive_games:
                    last_accessed = time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.localtime(self._sessions[game_id].last_accessed)
                    )
                    self._logger.info(
                        '%s: %s -- last_accessed: %s', LogEvent.DELETING_GAME_TTL_REACHED.value, game_id, last_accessed
                    )
                    del self._sessions[game_id]

    @contextlib.contextmanager
    def locked(self, game_id: str) -> Generator[GameSession | None]:
        """Thread-safe, exclusive access to one session's mutable game state.

        Looks the session up -- it may have been removed concurrently by :meth:`clear` or
        :meth:`evict_inactive`, in which case this yields None -- and, if found, holds that
        session's own lock for the duration of the ``with`` block. A concurrent call against the
        *same* session waits; calls against other sessions are unaffected.

        Args:
            game_id (str): Session to access.

        Yields:
            GameSession | None: The locked session, or None if it doesn't (or no longer) exist.
        """
        session = self.get(game_id)
        if session is None:
            yield None
            return

        with session.lock:
            yield session

    @staticmethod
    def touch(session: GameSession) -> None:
        """Bumps a session's last-accessed timestamp.

        Args:
            session (GameSession): Session to update. Caller must already hold ``session.lock``
                (see :meth:`locked`).
        """
        session.last_accessed = int(time.time())

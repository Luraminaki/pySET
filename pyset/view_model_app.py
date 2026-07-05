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
from collections.abc import Iterator

from pydantic import BaseModel, ConfigDict, Field, SkipValidation, ValidationError

from pyset.modules.game.game import Game, GameState
from pyset.modules.game.set import Grid
from pyset.modules.misc.helpers import StatusFunction
from pyset.modules.misc.models import AppConfig
from pyset.modules.web.app_factory import export
from pyset.modules.web.models import (
    AddPlayerRequest,
    ApiError,
    ApiResponse,
    ApplyPenaltyRequest,
    BaseGameRequest,
    ChangeGameStateRequest,
    DeleteRunningGamesRequest,
    GameGridResponse,
    GameStateResponse,
    HintsResponse,
    PlayersInfosResponse,
    PublicConfigResponse,
    RemovePlayerRequest,
    ResetGameRequest,
    RunningGameInfo,
    RunningGamesResponse,
    SanityCheckFailure,
    SanityCheckSuccess,
    StatusEnumResponse,
    SubmitSetRequest,
    SubmitSetResponse,
    VersionResponse,
)

__version__ = '0.1.0'


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


class ViewModelApp:
    """Bridges the Flask API (see :mod:`pyset.modules.web.app_factory`) and the game engine."""

    def __init__(self, conf: AppConfig, scheme: str, subdomain: str):
        """Initializes the ViewModelApp.

        Args:
            conf (AppConfig): Application configuration.
            scheme (str): URL scheme (e.g. 'http://').
            subdomain (str): Subdomain/host the app is served from.
        """
        self.scheme = scheme
        self.subdomain = subdomain

        self.config = conf
        self.config.app_version = __version__

        self.logger = logging.getLogger('View_Model_App')

        self.logger.info('%s version %s', self.__class__.__name__, __version__)

        self.set_games: dict[str, GameSession] = {}
        # Guards structural changes to `set_games` itself -- insert, delete, full replace, and
        # iteration. It does NOT guard gameplay state within a session; that's each GameSession's
        # own `lock` (see `_session_lock`), so requests against different sessions don't block
        # each other.
        self._table_lock = threading.Lock()

    ################################################
    #              PRIVATE  FUNCTIONS              #
    ################################################

    def _get_session(self, game_id: str) -> GameSession | None:
        """Thread-safe lookup of a session by id.

        Args:
            game_id (str): Session to look up.

        Returns:
            GameSession | None: The session, or None if it doesn't (or no longer) exist.
        """
        with self._table_lock:
            return self.set_games.get(game_id)

    @contextlib.contextmanager
    def _session_lock(self, game_id: str) -> Iterator[GameSession | None]:
        """Thread-safe, exclusive access to one session's mutable game state.

        Looks the session up -- it may have been removed concurrently by ``delete_running_games``
        or the TTL sweep, in which case this yields None -- and, if found, holds that session's own
        lock for the duration of the ``with`` block. A concurrent request against the *same*
        session waits; requests against other sessions are unaffected.

        Args:
            game_id (str): Session to access.

        Yields:
            GameSession | None: The locked session, or None if it doesn't (or no longer) exist.
        """
        session = self._get_session(game_id)
        if session is None:
            yield None
            return

        with session.lock:
            yield session

    def _clean_inactive_games(self) -> None:
        """Evicts sessions that have been inactive for longer than their TTL."""
        if len(self.set_games) >= self.config.max_sessions:
            now = int(time.time())
            with self._table_lock:
                inactive_games = [
                    game_id
                    for game_id, session in self.set_games.items()
                    if (now - session.last_accessed) >= self.config.session_ttl_seconds
                ]

                for game_id in inactive_games:
                    last_accessed = time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.localtime(self.set_games[game_id].last_accessed)
                    )
                    self.logger.info(
                        '%s: %s -- last_accessed: %s', LogEvent.DELETING_GAME_TTL_REACHED.value, game_id, last_accessed
                    )
                    del self.set_games[game_id]

    def _sanity_check[ReqT: BaseModel](
        self,
        request_model: type[ReqT],
        params: bytes | str | None,
        *,
        ignore_empty_game_id: bool = False,
        ignore_empty_game_secret: bool = False,
        ignore_missing_game: bool = False,
        check_max_sessions: bool = False,
    ) -> SanityCheckSuccess[ReqT] | SanityCheckFailure:
        """Parses and validates an incoming request payload against a session.

        Args:
            request_model (type[ReqT]): Pydantic model the raw payload is parsed into.
            params (bytes | str | None): Raw JSON payload.
            ignore_empty_game_id (bool, optional): Skip the "game_id must be set" check. Defaults to False.
            ignore_empty_game_secret (bool, optional): Skip the "game_secret must match" check. Defaults to False.
            ignore_missing_game (bool, optional): Skip the "game must exist" check. Defaults to False.
            check_max_sessions (bool, optional): Reject once the session table is full. Only meaningful
                for requests that are about to create a new session (i.e. combined with
                `ignore_missing_game=True`) -- otherwise a missing game already fails above with
                `GAME_ID_DOES_NOT_EXIST` regardless of this flag. Defaults to False.

        Returns:
            SanityCheckSuccess[ReqT] | SanityCheckFailure: The parsed request on success, or the
            error code on failure.
        """
        try:
            data = request_model.model_validate_json(params or '{}')
        except ValidationError as err:
            self.logger.error('%s: %r -- %s', ApiError.PARAMS_ERROR.value, params, err)
            return SanityCheckFailure(error=ApiError.PARAMS_ERROR)

        self.logger.info('%s: %r', LogEvent.DATA_RECEIVED.value, data)

        game_id = ''
        game_secret = ''
        if isinstance(data, BaseGameRequest):
            game_id = data.game_id[: self.config.session_name_max_chars]
            game_secret = data.game_secret[: self.config.session_name_max_chars]

        if not ignore_empty_game_id and game_id == '':
            return SanityCheckFailure(error=ApiError.INVALID_GAME_ID)

        session = self._get_session(game_id)

        if not ignore_missing_game and session is None:
            return SanityCheckFailure(error=ApiError.GAME_ID_DOES_NOT_EXIST)

        if not ignore_empty_game_secret and session is not None and session.game_secret != game_secret:
            return SanityCheckFailure(error=ApiError.INVALID_SECRET)

        if check_max_sessions and len(self.set_games) >= self.config.max_sessions and session is None:
            return SanityCheckFailure(error=ApiError.MAX_SESSIONS_REACHED)

        return SanityCheckSuccess(game_id=game_id, game_secret=game_secret, request=data)

    def _update_game_ttl(self, session: GameSession) -> None:
        """Bumps a session's last-accessed timestamp.

        Args:
            session (GameSession): Session to update. Caller must already hold ``session.lock``
                (see ``_session_lock``).
        """
        session.last_accessed = int(time.time())

    ################################################
    #                  BASIC  API                  #
    ################################################

    @export
    def get_version(self) -> VersionResponse:
        """Returns the service version.

        Returns:
            VersionResponse: Service version.
        """
        return VersionResponse(status=StatusFunction.SUCCESS.name, version=self.config.version)

    @export
    def get_config(self) -> PublicConfigResponse:
        """Returns the public (secret-free) application configuration, flat, no envelope.

        Returns:
            PublicConfigResponse: Public configuration.
        """
        return PublicConfigResponse(self.config.model_dump(by_alias=True, exclude={'secret'}))

    @export
    def get_status_enum(self) -> StatusEnumResponse:
        """Returns the {name: name} mapping of every :class:`StatusFunction` value.

        Returns:
            StatusEnumResponse: The status enum, dumped as a name-to-name mapping.
        """
        return StatusEnumResponse({status.name: status.name for status in StatusFunction})

    @export
    def get_running_games(self) -> RunningGamesResponse:
        """Returns the list of currently running game sessions.

        Returns:
            RunningGamesResponse: Running sessions summary.
        """
        self._clean_inactive_games()

        with self._table_lock:
            games = [
                RunningGameInfo(game_id=game_id, has_secret=session.game_secret != '')
                for game_id, session in self.set_games.items()
            ]

        return RunningGamesResponse(status=StatusFunction.SUCCESS.name, games=games)

    @export
    def init_set_game(self, params: bytes | str | None = None) -> ApiResponse:
        """Creates a new game session (or is a no-op if it already exists).

        Args:
            params (bytes | str | None, optional): Raw JSON payload. Defaults to None.

        Returns:
            ApiResponse: Outcome of the operation.
        """
        sanity_check = self._sanity_check(BaseGameRequest, params, ignore_missing_game=True, check_max_sessions=True)
        if isinstance(sanity_check, SanityCheckFailure):
            return ApiResponse(status=StatusFunction.ERROR.name, error=sanity_check.error)

        game_id = sanity_check.game_id
        game_secret = sanity_check.game_secret

        with self._table_lock:
            if game_id not in self.set_games:
                now = int(time.time())
                game = Game(Grid())
                game.set_penalty_time(self.config.penalty_timeout_seconds)
                game.set_max_player(self.config.max_players)
                self.set_games[game_id] = GameSession(
                    game=game,
                    game_secret=game_secret,
                    created=now,
                    last_accessed=now,
                    ttl=self.config.session_ttl_seconds,
                )

        return ApiResponse(status=StatusFunction.SUCCESS.name)

    @export
    def delete_running_games(self, params: bytes | str | None = None) -> ApiResponse:
        """Wipes every running game session. Requires the admin secret.

        Args:
            params (bytes | str | None, optional): Raw JSON payload. Defaults to None.

        Returns:
            ApiResponse: Outcome of the operation.
        """
        self._clean_inactive_games()

        sanity_check = self._sanity_check(
            DeleteRunningGamesRequest,
            params,
            ignore_empty_game_id=True,
            ignore_empty_game_secret=True,
            ignore_missing_game=True,
        )
        if isinstance(sanity_check, SanityCheckFailure):
            return ApiResponse(status=StatusFunction.ERROR.name, error=sanity_check.error)

        secret = sanity_check.request.secret

        if secret == '':
            return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.PARAMS_ERROR)

        if secret != self.config.secret:
            return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.NOT_ALLOWED)

        # Any request already past this point for an individual session (i.e. already holding that
        # session's lock) simply finishes on its own, now-orphaned GameSession -- its result won't
        # be visible in `set_games` anymore, which is fine for a rare admin wipe.
        with self._table_lock:
            self.set_games = {}
        self.logger.info('%s: Lord Vader will be pleased', LogEvent.ORDER_66.value)

        return ApiResponse(status=StatusFunction.SUCCESS.name)

    ################################################
    #                 PLAYER  API                  #
    ################################################

    @export
    def remove_player(self, params: bytes | str | None = None) -> ApiResponse:
        """Removes a player from a game session.

        Args:
            params (bytes | str | None, optional): Raw JSON payload. Defaults to None.

        Returns:
            ApiResponse: Outcome of the operation.
        """
        sanity_check = self._sanity_check(RemovePlayerRequest, params)
        if isinstance(sanity_check, SanityCheckFailure):
            return ApiResponse(status=StatusFunction.ERROR.name, error=sanity_check.error)

        with self._session_lock(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            game = session.game

            if game.get_game_state() == GameState.RUNNING.name:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.NOT_ALLOWED)

            result = game.remove_player(player_name=sanity_check.request.name)

            self._update_game_ttl(session)
            return PlayersInfosResponse(
                status=StatusFunction.SUCCESS.name if result.status else StatusFunction.ERROR.name,
                players_stats=[player.get_stats() for player in game.get_players()],
                game_state=game.get_game_state(),
                error=result.error,
            )

    @export
    def add_player(self, params: bytes | str | None = None) -> ApiResponse:
        """Adds a player to a game session.

        Args:
            params (bytes | str | None, optional): Raw JSON payload. Defaults to None.

        Returns:
            ApiResponse: Outcome of the operation.
        """
        sanity_check = self._sanity_check(AddPlayerRequest, params)
        if isinstance(sanity_check, SanityCheckFailure):
            return ApiResponse(status=StatusFunction.ERROR.name, error=sanity_check.error)

        with self._session_lock(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            game = session.game

            if game.get_game_state() == GameState.RUNNING.name:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.NOT_ALLOWED)

            player_name = sanity_check.request.name[: self.config.player_name_max_chars]
            player_color = sanity_check.request.color

            if len(player_name) <= 2:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.INVALID_PLAYER_NAME)

            result = game.add_player(player_name=player_name, player_color=player_color)

            self._update_game_ttl(session)
            return PlayersInfosResponse(
                status=StatusFunction.SUCCESS.name if result.status else StatusFunction.ERROR.name,
                players_stats=[player.get_stats() for player in game.get_players()],
                game_state=game.get_game_state(),
                error=result.error,
            )

    @export
    def get_players_infos(self, params: bytes | str | None = None) -> ApiResponse:
        """Returns the roster and state of a game session.

        Args:
            params (bytes | str | None, optional): Raw JSON payload. Defaults to None.

        Returns:
            ApiResponse: Outcome of the operation.
        """
        sanity_check = self._sanity_check(BaseGameRequest, params)
        if isinstance(sanity_check, SanityCheckFailure):
            return ApiResponse(status=StatusFunction.ERROR.name, error=sanity_check.error)

        with self._session_lock(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            game = session.game

            self._update_game_ttl(session)
            return PlayersInfosResponse(
                status=StatusFunction.SUCCESS.name,
                players_stats=[player.get_stats() for player in game.get_players()],
                game_state=game.get_game_state(),
            )

    @export
    def submit_set(self, params: bytes | str | None = None) -> ApiResponse:
        """Submits a candidate set on behalf of a player.

        Args:
            params (bytes | str | None, optional): Raw JSON payload. Defaults to None.

        Returns:
            ApiResponse: Outcome of the operation.
        """
        sanity_check = self._sanity_check(SubmitSetRequest, params)
        if isinstance(sanity_check, SanityCheckFailure):
            return ApiResponse(status=StatusFunction.ERROR.name, error=sanity_check.error)

        with self._session_lock(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            game = session.game

            player_name = sanity_check.request.player_name
            cards_set = sanity_check.request.cards_set

            cards_displayed = game.grid.get_displayed_cards()
            if not all(card in cards_displayed for card in cards_set):
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.CARDS_NOT_FOUND)

            result = game.submit_set_from_player_name(player_name, cards_set)
            game.update_game(enable_pause=False)

            self._update_game_ttl(session)
            return SubmitSetResponse(
                status=StatusFunction.SUCCESS.name,
                is_valid=result.status,
                set=result.cards_set,
                player_name=player_name,
                game_state=game.get_game_state(),
                error=result.error,
            )

    @export
    def apply_penalty(self, params: bytes | str | None = None) -> ApiResponse:
        """Applies a penalty to a player.

        Args:
            params (bytes | str | None, optional): Raw JSON payload. Defaults to None.

        Returns:
            ApiResponse: Outcome of the operation.
        """
        sanity_check = self._sanity_check(ApplyPenaltyRequest, params)
        if isinstance(sanity_check, SanityCheckFailure):
            return ApiResponse(status=StatusFunction.ERROR.name, error=sanity_check.error)

        with self._session_lock(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            game = session.game
            result = game.apply_penalty_from_player_name(sanity_check.request.player_name)

            self._update_game_ttl(session)
            return GameStateResponse(
                status=StatusFunction.SUCCESS.name if result.status else StatusFunction.ERROR.name,
                game_state=game.get_game_state(),
            )

    ################################################
    #                  GAME  API                   #
    ################################################

    @export
    def change_game_state(self, params: bytes | str | None = None) -> ApiResponse:
        """Starts, resumes or pauses a game session.

        Args:
            params (bytes | str | None, optional): Raw JSON payload. Defaults to None.

        Returns:
            ApiResponse: Outcome of the operation.
        """
        sanity_check = self._sanity_check(ChangeGameStateRequest, params)
        if isinstance(sanity_check, SanityCheckFailure):
            return ApiResponse(status=StatusFunction.ERROR.name, error=sanity_check.error)

        with self._session_lock(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            game = session.game

            if not game.get_players():
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.PLAYER_NOT_FOUND)

            if game.is_game_ended():
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.NOT_ALLOWED)

            game.update_game(sanity_check.request.enable_pause)
            self.logger.info('Game is now: %s', game.get_game_state())
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug('Grid Layout:\n%s', game.grid.grid_as_str())

            self._update_game_ttl(session)
            return GameGridResponse(
                status=StatusFunction.SUCCESS.name,
                grid=game.grid.arrange_cards_to_grid(),
                draw_pile=game.grid.get_number_cards_left_in_deck(),
                game_state=game.get_game_state(),
            )

    @export
    def reset_game(self, params: bytes | str | None = None) -> ApiResponse:
        """Resets a game session, optionally keeping the current roster.

        Args:
            params (bytes | str | None, optional): Raw JSON payload. Defaults to None.

        Returns:
            ApiResponse: Outcome of the operation.
        """
        sanity_check = self._sanity_check(ResetGameRequest, params)
        if isinstance(sanity_check, SanityCheckFailure):
            return ApiResponse(status=StatusFunction.ERROR.name, error=sanity_check.error)

        with self._session_lock(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            hard_reset = sanity_check.request.hard
            old_game = session.game

            new_game = Game(Grid())
            new_game.set_penalty_time(self.config.penalty_timeout_seconds)
            new_game.set_max_player(self.config.max_players)
            session.game = new_game

            # hard_reset defaults to True, i.e. the common case -- only bother snapshotting and
            # rebuilding the roster when a soft reset actually needs it.
            if not hard_reset:
                for player in old_game.get_players():
                    stats = player.get_stats()
                    new_game.add_player(
                        player_name=stats.name,
                        player_color=stats.color,
                        is_ai=stats.is_ai,
                        difficulty=stats.difficulty,
                    )

            self._update_game_ttl(session)
            return GameStateResponse(status=StatusFunction.SUCCESS.name, game_state=new_game.get_game_state())

    @export
    def get_game(self, params: bytes | str | None = None) -> ApiResponse:
        """Returns the current grid and draw pile of a game session.

        Args:
            params (bytes | str | None, optional): Raw JSON payload. Defaults to None.

        Returns:
            ApiResponse: Outcome of the operation.
        """
        sanity_check = self._sanity_check(BaseGameRequest, params)
        if isinstance(sanity_check, SanityCheckFailure):
            return ApiResponse(status=StatusFunction.ERROR.name, error=sanity_check.error)

        with self._session_lock(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            game = session.game

            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug('Grid Layout:\n%s', game.grid.grid_as_str())

            self._update_game_ttl(session)
            return GameGridResponse(
                status=StatusFunction.SUCCESS.name,
                grid=game.grid.arrange_cards_to_grid(),
                draw_pile=game.grid.get_number_cards_left_in_deck(),
                game_state=game.get_game_state(),
            )

    @export
    def get_game_state(self, params: bytes | str | None = None) -> ApiResponse:
        """Returns the current state of a game session.

        Args:
            params (bytes | str | None, optional): Raw JSON payload. Defaults to None.

        Returns:
            ApiResponse: Outcome of the operation.
        """
        sanity_check = self._sanity_check(BaseGameRequest, params)
        if isinstance(sanity_check, SanityCheckFailure):
            return ApiResponse(status=StatusFunction.ERROR.name, error=sanity_check.error)

        with self._session_lock(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            self._update_game_ttl(session)
            return GameStateResponse(status=StatusFunction.SUCCESS.name, game_state=session.game.get_game_state())

    @export
    def get_hints(self, params: bytes | str | None = None) -> ApiResponse:
        """Returns every valid set currently on the grid of a game session.

        Args:
            params (bytes | str | None, optional): Raw JSON payload. Defaults to None.

        Returns:
            ApiResponse: Outcome of the operation.
        """
        sanity_check = self._sanity_check(BaseGameRequest, params)
        if isinstance(sanity_check, SanityCheckFailure):
            return ApiResponse(status=StatusFunction.ERROR.name, error=sanity_check.error)

        with self._session_lock(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            game = session.game
            self._update_game_ttl(session)
            return HintsResponse(
                status=StatusFunction.SUCCESS.name,
                sets=game.grid.get_unique_sets_on_grid(),
                game_state=game.get_game_state(),
            )

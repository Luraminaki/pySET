#!/usr/bin/env python3
"""Created on Wed Jan 25 11:17:51 2023.

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

import logging
import time

from pydantic import BaseModel, ValidationError

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
from pyset.session_store import GameSession, LogEvent, SessionStore

__version__ = '0.1.0'


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

        self.sessions = SessionStore(config=conf, logger=self.logger)

    ################################################
    #              PRIVATE  FUNCTIONS              #
    ################################################

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

        session = self.sessions.get(game_id)

        if not ignore_missing_game and session is None:
            return SanityCheckFailure(error=ApiError.GAME_ID_DOES_NOT_EXIST)

        if not ignore_empty_game_secret and session is not None and session.game_secret != game_secret:
            return SanityCheckFailure(error=ApiError.INVALID_SECRET)

        if check_max_sessions and self.sessions.is_full() and session is None:
            return SanityCheckFailure(error=ApiError.MAX_SESSIONS_REACHED)

        return SanityCheckSuccess(game_id=game_id, game_secret=game_secret, request=data)

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
        self.sessions.evict_inactive()

        games = [
            RunningGameInfo(game_id=game_id, has_secret=session.game_secret != '')
            for game_id, session in self.sessions.items()
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

        def build_session() -> GameSession:
            now = int(time.time())
            game = Game(Grid())
            _ = game.set_penalty_time(self.config.penalty_timeout_seconds)
            _ = game.set_max_player(self.config.max_players)
            return GameSession(
                game=game, game_secret=game_secret, created=now, last_accessed=now, ttl=self.config.session_ttl_seconds
            )

        self.sessions.create_if_missing(game_id, build_session)

        return ApiResponse(status=StatusFunction.SUCCESS.name)

    @export
    def delete_running_games(self, params: bytes | str | None = None) -> ApiResponse:
        """Wipes every running game session. Requires the admin secret.

        Args:
            params (bytes | str | None, optional): Raw JSON payload. Defaults to None.

        Returns:
            ApiResponse: Outcome of the operation.
        """
        self.sessions.evict_inactive()

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

        self.sessions.clear()
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

        with self.sessions.locked(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            game = session.game

            if game.get_game_state() == GameState.RUNNING.name:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.NOT_ALLOWED)

            result = game.remove_player(player_name=sanity_check.request.name)

            SessionStore.touch(session)
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

        with self.sessions.locked(sanity_check.game_id) as session:
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

            SessionStore.touch(session)
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

        with self.sessions.locked(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            game = session.game

            SessionStore.touch(session)
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

        with self.sessions.locked(sanity_check.game_id) as session:
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

            SessionStore.touch(session)
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

        with self.sessions.locked(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            game = session.game
            result = game.apply_penalty_from_player_name(sanity_check.request.player_name)

            SessionStore.touch(session)
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

        with self.sessions.locked(sanity_check.game_id) as session:
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

            SessionStore.touch(session)
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

        with self.sessions.locked(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            hard_reset = sanity_check.request.hard
            old_game = session.game

            new_game = Game(Grid())
            _ = new_game.set_penalty_time(self.config.penalty_timeout_seconds)
            _ = new_game.set_max_player(self.config.max_players)
            session.game = new_game

            # hard_reset defaults to True, i.e. the common case -- only bother snapshotting and
            # rebuilding the roster when a soft reset actually needs it.
            if not hard_reset:
                for player in old_game.get_players():
                    stats = player.get_stats()
                    _ = new_game.add_player(
                        player_name=stats.name,
                        player_color=stats.color,
                        is_ai=stats.is_ai,
                        difficulty=stats.difficulty,
                    )

            SessionStore.touch(session)
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

        with self.sessions.locked(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            game = session.game

            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug('Grid Layout:\n%s', game.grid.grid_as_str())

            SessionStore.touch(session)
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

        with self.sessions.locked(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            SessionStore.touch(session)
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

        with self.sessions.locked(sanity_check.game_id) as session:
            if session is None:
                return ApiResponse(status=StatusFunction.ERROR.name, error=ApiError.GAME_ID_DOES_NOT_EXIST)

            game = session.game
            SessionStore.touch(session)
            return HintsResponse(
                status=StatusFunction.SUCCESS.name,
                sets=game.grid.get_unique_sets_on_grid(),
                game_state=game.get_game_state(),
            )

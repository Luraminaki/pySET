#!/usr/bin/env python3
"""Created on Wed Jan 25 11:17:51 2023.

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

import enum

from pydantic import BaseModel, ConfigDict, Field, RootModel

from pyset.modules.game.models import PlayerStats


class ApiError(enum.StrEnum):
    """Stable error codes returned to the client in the ``error`` field of a response.

    Values are part of the wire contract: the frontend string-matches ``CARDS_NOT_FOUND``
    (``TurnControl.vue``), so none of these values may change even if renamed on the Python side.
    """

    PARAMS_ERROR = 'PARAMS_ERROR'
    MAX_SESSIONS_REACHED = 'MAX_SESSIONS_REACHED'
    INVALID_GAME_ID = 'INVALID_GAME_ID'
    GAME_ID_ALREADY_EXISTS = 'GAME_ID_ALREADY_EXISTS'
    GAME_ID_DOES_NOT_EXIST = 'GAME_ID_DOES_NOT_EXIST'
    NOT_ALLOWED = 'NOT_ALLOWED'
    INVALID_PLAYER_NAME = 'INVALID_PLAYER_NAME'
    PLAYER_NOT_FOUND = 'PLAYER_NOT_FOUND'
    SET_NOT_FOUND = 'SET_NOT_FOUND'
    CARDS_NOT_FOUND = 'CARDS_NOT_FOUND'
    INVALID_SECRET = 'INVALID_SECRET'
    INTERNAL_ERROR = 'INTERNAL_ERROR'


#
# REQUESTS
#


class BaseGameRequest(BaseModel):
    """Common payload shape shared by every session-scoped endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    game_id: str = Field(default='', alias='gameID')
    game_secret: str = Field(default='', alias='gameSecret')


class DeleteRunningGamesRequest(BaseModel):
    """Payload for the admin ``delete_running_games`` endpoint."""

    secret: str = ''


class AddPlayerRequest(BaseGameRequest):
    """Payload for ``add_player``."""

    name: str = ''
    color: str = '#000000'


class RemovePlayerRequest(BaseGameRequest):
    """Payload for ``remove_player``."""

    name: str = ''


class SubmitSetRequest(BaseGameRequest):
    """Payload for ``submit_set``."""

    model_config = ConfigDict(populate_by_name=True)

    player_name: str = Field(default='', alias='playerName')
    cards_set: list[int] = Field(default_factory=list, alias='set')


class ApplyPenaltyRequest(BaseGameRequest):
    """Payload for ``apply_penalty``."""

    model_config = ConfigDict(populate_by_name=True)

    player_name: str = Field(default='', alias='playerName')


class ChangeGameStateRequest(BaseGameRequest):
    """Payload for ``change_game_state``."""

    model_config = ConfigDict(populate_by_name=True)

    enable_pause: bool = Field(default=False, alias='enablePause')


class ResetGameRequest(BaseGameRequest):
    """Payload for ``reset_game``."""

    hard: bool = True


#
# RESPONSES
#


class ApiResponse(BaseModel):
    """Common response envelope: every endpoint (except ``get_config``) returns at least this."""

    status: str
    error: str = ''


class VersionResponse(ApiResponse):
    """Response for ``get_version``."""

    version: str = ''


class RunningGameInfo(BaseModel):
    """Public summary of a single running game session."""

    game_id: str
    has_secret: bool


class RunningGamesResponse(ApiResponse):
    """Response for ``get_running_games``."""

    games: list[RunningGameInfo] = []


class PlayersInfosResponse(ApiResponse):
    """Response for ``get_players_infos``, and the shape returned by add/remove player."""

    players_stats: list[PlayerStats] = []
    game_state: str = ''


class SubmitSetResponse(ApiResponse):
    """Response for ``submit_set``."""

    is_valid: bool = False
    set: list[int] = []
    player_name: str = ''
    game_state: str = ''


class ApplyPenaltyResponse(ApiResponse):
    """Response for ``apply_penalty``."""

    game_state: str = ''


class GameGridResponse(ApiResponse):
    """Response shape shared by ``change_game_state`` and ``get_game``."""

    grid: list[list[int]] = []
    draw_pile: int = 0
    game_state: str = ''


class GameStateResponse(ApiResponse):
    """Response for ``get_game_state`` and ``reset_game``."""

    game_state: str = ''


class HintsResponse(ApiResponse):
    """Response for ``get_hints``."""

    sets: list[list[int]] = []
    game_state: str = ''


class StatusEnumResponse(RootModel[dict[str, str]]):
    """Response for ``get_status_enum``: a dynamic {name: name} mapping, not a fixed field set."""


class PublicConfigResponse(RootModel[dict[str, object]]):
    """Secret-free view of :class:`pyset.modules.misc.models.AppConfig`, returned flat (no envelope)."""


#
# INTERNAL SANITY-CHECK RESULT
#


class SanityCheckSuccess[ReqT: BaseModel](BaseModel):
    """Successful outcome of :meth:`ViewModelApp._sanity_check`, carrying the parsed request."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    game_id: str = ''
    game_secret: str = ''
    request: ReqT


class SanityCheckFailure(BaseModel):
    """Failed outcome of :meth:`ViewModelApp._sanity_check`."""

    error: ApiError

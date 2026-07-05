#!/usr/bin/env python3
"""Created on Wed Jan 25 11:17:51 2023.

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

import json
import logging
import typing
from functools import wraps

from flask_classful import FlaskView, route
from pydantic import BaseModel
from werkzeug.datastructures import FileStorage, ImmutableMultiDict

from flask import Response, render_template, request
from pyset.modules.web.models import ApiError, ApiResponse

logger = logging.getLogger(__name__)

# Flask runs with threaded=True (see server_app.py). Thread-safety for ViewModelApp.set_games and
# the Game/Grid/Player state within each session is handled inside ViewModelApp itself (a table
# lock for set_games structure, a per-GameSession lock for that session's gameplay state) -- see
# ViewModelApp._session_lock -- so requests against different sessions can run concurrently here.


class AppView(FlaskView):
    """Flask-Classful view exposing every ``@export``-decorated method of ``api_class``."""

    route_base = ''
    route_prefix = ''
    default_methods = ['POST', 'GET', 'PUT', 'DELETE']
    # Holds the single ViewModelApp instance set by server_app.create_app(); typed loosely to
    # avoid a circular import with view_model_app.py, which itself imports from this module.
    api_class: typing.ClassVar[typing.Any] = None


class TemplateView(FlaskView):
    """Flask-Classful view serving the frontend's static templates."""

    route_base = ''
    route_prefix = ''
    default_methods = ['GET']

    @route('/')
    def index(self) -> str:
        """Serves the frontend's entry point.

        Returns:
            str: Rendered ``index.html``.
        """
        return render_template('index.html')

    def not_found(self) -> str:
        """Serves the 404 page.

        Returns:
            str: Rendered ``404.html``.
        """
        return render_template('404.html')


def export(func: typing.Callable[..., typing.Any], req: str = '') -> typing.Callable[..., typing.Any]:
    """Exposes a method from the ``AppView.api_class`` class to the client.

    https://stackoverflow.com/questions/33134609

    Currently supported return types are: ``str``, ``flask.Response``, ``pydantic.BaseModel``,
    ``dict``, ``list``. ``TypeError`` is raised if none of these is returned.

    Example:
        @export
        def send_greetings(self, payload: BaseModel | None=None) -> str:
            return f"Hello world! {payload}"

    Args:
        func (typing.Callable[..., typing.Any]): The function to be executed.
        req (str, optional): The request type, either 'form', 'data' or 'files' (only supported
            ones). Defaults to ''.

    Returns:
        typing.Callable[..., typing.Any]: The original, undecorated function (the decorated
        wrapper is registered directly on ``AppView``).
    """

    def decorator(func: typing.Callable[..., typing.Any]) -> typing.Callable[..., typing.Any]:
        """Wraps an API function so its result is serialized for Flask.

        https://www.geeksforgeeks.org/python-functools-wraps-function/

        Args:
            func (typing.Callable[..., typing.Any]): API function to decorate.

        Returns:
            typing.Callable[..., typing.Any]: Wrapped function.
        """

        @wraps(func)
        def wrapper(*args: typing.Any, **kwargs: typing.Any) -> str | Response:
            """Executes `func` against the current Flask request and serializes its result.

            Returns:
                str | Response: JSON-serialized payload, or a raw str/Response passthrough.

            Raises:
                TypeError: If `func` returned a type that isn't serializable.
            """
            if request.args:
                logger.warning(
                    '%s -- Reached with URL params %s -- (Not supported)', request.endpoint, dict(request.args)
                )

            func_resp: typing.Any
            try:
                func_resp = request_strategy(func, req)
            except Exception:
                logger.exception('%s -- Request handling failed', request.endpoint)
                func_resp = ApiResponse(status='ERROR', error=ApiError.INTERNAL_ERROR)

            if isinstance(func_resp, (str, Response)):
                return func_resp
            if isinstance(func_resp, BaseModel):
                return Response(func_resp.model_dump_json(by_alias=True), mimetype='application/json')
            if isinstance(func_resp, (dict, list)):
                return Response(json.dumps(func_resp), mimetype='application/json')
            raise TypeError
            # END WRAPPER

        setattr(AppView, func.__name__, wrapper)
        return func
        # END DECORATOR

    return decorator(func)


def request_strategy(
    func: typing.Callable[..., typing.Any],
    req: bytes | str | ImmutableMultiDict[str, str] | ImmutableMultiDict[str, FileStorage] = '',
) -> typing.Any:
    """Calls the ``AppView.api_class`` method with whichever payload the current request carries.

    Args:
        func (typing.Callable[..., typing.Any]): The function to be executed.
        req (bytes | str | ImmutableMultiDict[str, str] | ImmutableMultiDict[str, FileStorage], optional):
            The request type, either 'form', 'data' or 'files' (only supported ones). Defaults to ''.

    Returns:
        typing.Any: Result of the ``AppView.api_class`` method (``func``).
    """
    if req == 'form' or request.form:
        return func(AppView.api_class, json.dumps(request.form))
    if req == 'data' or request.data:
        return func(AppView.api_class, request.data)
    if req == 'files' or request.files:
        return func(AppView.api_class, request.files)

    return func(AppView.api_class)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 11:17:51 2023

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

#===================================================================================================
import json
import typing
import inspect
from functools import wraps

from werkzeug.datastructures import ImmutableMultiDict, FileStorage
from flask_classful import FlaskView, route
from flask import  Response, render_template, request
#===================================================================================================


__version__ = '0.1.0'


class AppView(FlaskView):
    route_base = ''
    route_prefix = ''
    default_methods = ['POST', 'GET', 'PUT', 'DELETE']
    api_class: typing.Type = None


class TemplateView(FlaskView):
    route_base = ''
    route_prefix = ''
    default_methods = ['GET']

    @route('/')
    def index(self):
        return render_template('index.html')


    def not_found(self):
        return render_template('404.html')


def export(func: typing.Callable[..., typing.Optional[typing.Any]]=None, req: str='') -> typing.Callable[..., typing.Optional[typing.Any]]:
    """
    https://stackoverflow.com/questions/33134609

    Exposes a method from the AppView.api_class class to the client.
    Currently supported types returned are: str, flask.Response, dict, list.
    TypeError is raised if no return type specified.

    Example:

    @export
    def send_greetings(self, payload: dict=None) -> str:
        return str(f"Hello world! {payload.get('name', '')}")

    Args:
        func (typing.Callable[..., typing.Optional[typing.Any]]): The function to be executed. Defaults to None.
        req (bytes | str | ImmutableMultiDict[str, str] | ImmutableMultiDict[str, FileStorage], optional): The request type which can be either 'form', 'data' or 'files' (only supported ones). Defaults to ''.
    Returns:
        typing.Callable[..., typing.Optional[typing.Any]]: decorator(func).
    """
    def decorator(func: typing.Callable[..., typing.Optional[typing.Any]]) -> typing.Callable[..., typing.Optional[typing.Any]]:
        """
        https://www.geeksforgeeks.org/python-functools-wraps-function/

        Args:
            func (typing.Callable[..., typing.Optional[typing.Any]]): API function to decorate.

        Returns:
            typing.Callable[..., typing.Optional[typing.Any]]: Wrapped function.
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> str | Response:
            if request.args:
                print(f"{request.endpoint} -- Reached with URL params {dict(request.args)} -- (Not supported)")

            try:
                func_resp = request_strategy(func, req)
            except Exception as err:
                print(f"{request.endpoint} -- ERROR -- {repr(err)}")
                func_resp = { 'status': 'ERROR', 'error': repr(err) }

            if isinstance(func_resp, (str, Response)):
                return func_resp
            if isinstance(func_resp, (dict, list)):
                return json.dumps(func_resp)
            raise TypeError
            # END WRAPPER

        setattr(AppView, func.__name__, wrapper)
        return func
        # END DECORATOR


    curr_func = inspect.currentframe().f_code.co_name
    try:
        return decorator(func)

    except Exception as err_01:
        try:
            print(f"{curr_func} -- Something went wrong when trying to wrap function {func.__name__} : {repr(err_01)}")

        except Exception as err_02:
            print(f"{curr_func} -- Wrapping function triggered exception {repr(err_01)}, and trying to retrieve function name triggered exception {repr(err_02)}")

    raise RuntimeError


def request_strategy(func: typing.Callable[..., typing.Optional[typing.Any]]=None, req: bytes | str | ImmutableMultiDict[str, str] | ImmutableMultiDict[str, FileStorage]='') -> str | Response | dict | list:
    """
    Function that returns the result of the AppView.api_class method called depending on the flask.request made.

    Args:
        func (typing.Callable[..., typing.Optional[typing.Any]], optional): The function to be executed. Defaults to None.
        req (bytes | str | ImmutableMultiDict[str, str] | ImmutableMultiDict[str, FileStorage], optional): The request type which can be either 'form', 'data' or 'files' (only supported ones). Defaults to ''.

    Returns:
        str | Response | dict | list: Result of the AppView.api_class method (func)
    """
    if req == 'form' or request.form:
        return func(AppView.api_class, json.dumps(request.form))
    if req == 'data' or request.data:
        return func(AppView.api_class, request.data)
    if req == 'files' or request.files:
        return func(AppView.api_class, request.files)

    return func(AppView.api_class)

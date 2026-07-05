#!/usr/bin/env python3
"""Created on Wed Jan 25 11:17:51 2023.

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

import argparse
import json
import logging
import os
from pathlib import Path

from flask_cors import CORS

from flask import Flask
from pyset.modules.misc.logging_utils import configure_launcher_logging
from pyset.modules.misc.models import AppConfig
from pyset.modules.web.app_factory import AppView, TemplateView
from pyset.view_model_app import ViewModelApp as ViewModel

logger = logging.getLogger()


def create_app(config: str = 'config.json', scheme: str = 'https://', subdomain: str = 'localhost') -> Flask:
    """Builds and configures the Flask application.

    See :class:`pyset.modules.misc.models.AppConfig` for how the admin secret can be supplied via the
    environment / a ``.env`` file instead of ``config.json``.

    Args:
        config (str, optional): Path to the JSON configuration file. Defaults to 'config.json'.
        scheme (str, optional): URL scheme (e.g. 'http://'). Defaults to 'https://'.
        subdomain (str, optional): Subdomain/host the app is served from. Defaults to 'localhost'.

    Returns:
        Flask: The configured Flask application.
    """
    conf_file = Path(config).expanduser()
    with conf_file.open('r', encoding='utf-8') as f:
        conf = AppConfig.model_validate(json.load(f))

    configure_launcher_logging(logger, log_file_stem=conf.service_id)
    logger.setLevel(conf.logging_level)

    dist_path = Path(__file__).absolute().parent.parent / 'flask' / 'dist'
    if not dist_path.exists():
        raise Exception(f"WebApp generation failed or was not initiated -- Sources not found: {dist_path.as_posix()}")

    app = Flask(
        __name__, static_folder=dist_path.as_posix(), template_folder=dist_path.as_posix(), static_url_path='/'
    )
    app.secret_key = os.urandom(32).hex()
    app.register_error_handler(404, TemplateView.not_found)

    _ = CORS(app)

    TemplateView.register(app)
    AppView.api_class = ViewModel(conf, scheme, subdomain)
    AppView.register(app, route_prefix='/api/app')

    return app


if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser()
    _ = parser.add_argument('-c', '--configuration', help='Configuration file location', required=True)
    args = parser.parse_args()

    APP = create_app(args.configuration, scheme='http://', subdomain='0.0.0.0')
    APP.run(host='0.0.0.0', port=10000, threaded=True)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 11:17:51 2023

@author: Luraminaki
@rules: https://en.wikipedia.org/wiki/Set_(card_game)#Games
"""

#===================================================================================================
import os
import sys
import json
import argparse
import logging
import logreset
from pathlib import Path

from flask_cors import CORS
from flask import Flask
from view_model_app import ViewModelApp as ViewModel

#pylint: disable=wrong-import-position, wrong-import-order
from modules.web.app_factory import AppView, TemplateView
#pylint: enable=wrong-import-position, wrong-import-order
#=======================================================================


logreset.reset_logging()

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def create_app(config: str='config.json', scheme: str='https://', subdomain: str='localhost') -> Flask:
    conf_file = Path(config).expanduser()
    with conf_file.open('r', encoding='utf-8') as f:
        conf = json.load(f)

    try:
        level = conf['logging_level']
    except KeyError:
        level = logging.INFO

    logging.basicConfig(
        level=level,
            format="[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
    logger.setLevel(level)

    app = Flask(__name__, static_folder='flask/.output/public/', template_folder='flask/.output/public/', static_url_path='/')
    app.secret_key = os.urandom(32).hex()
    app.register_error_handler(404, TemplateView.not_found)

    CORS(app)

    TemplateView.register(app)
    AppView.api_class = ViewModel(conf, scheme, subdomain)
    AppView.register(app, route_prefix='/api/app')

    return app


if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--configuration', help='Configuration file location', required=True)
    args = parser.parse_args()

    APP = create_app(args.configuration, scheme='http://', subdomain='0.0.0.0')
    APP.run(host='0.0.0.0', port=10000, threaded=True)

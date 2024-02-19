#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py

loglevel = "info"
accesslog = errorlog = "-"
capture_output = False

wsgi_app = "server_app:create_app('../config.json', scheme='http://', subdomain='0.0.0.0')"
bind = "0.0.0.0:10000"

chdir = "./flask/"

workers = 1
threads = 1

daemon = False

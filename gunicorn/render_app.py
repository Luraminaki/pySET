#!/usr/bin/env python3
"""Gunicorn configuration used for the render.com-hosted deployment.

https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py
"""

loglevel = 'info'
accesslog = errorlog = '-'
capture_output = False

wsgi_app = "pyset.server_app:create_app('../config.json', scheme='http://', subdomain='0.0.0.0')"
bind = '0.0.0.0:10000'

chdir = './flask/'

workers = 1
threads = 1

daemon = False

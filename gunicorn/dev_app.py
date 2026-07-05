#!/usr/bin/env python3
"""Gunicorn configuration for local development (auto-reload, debug logging).

https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py
"""

loglevel = 'debug'
accesslog = errorlog = '-'
capture_output = False

wsgi_app = "pyset.server_app:create_app('../config.json', scheme='http://', subdomain='0.0.0.0')"
bind = '0.0.0.0:10000'

chdir = './flask/'

workers = 1
threads = 1

# TLS configuration
# certfile = './gunicorn/cert.pem'
# keyfile = './gunicorn/key.pem'

# Restart workers when code changes (development only!)
reload = True

daemon = False

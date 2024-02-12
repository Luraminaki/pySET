#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py

loglevel = "debug"
accesslog = errorlog = "-"
capture_output = False

wsgi_app = "server_app:create_app('config.json', scheme='http://', subdomain='localhost')"
bind = "localhost:5000"

chdir = "./flask/"

workers = 1
threads = 1

# TLS configuration
# certfile = './gunicorn/cert.pem'
# keyfile = './gunicorn/key.pem'

# Restart workers when code changes (development only!)
reload = True

daemon = False

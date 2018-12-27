#!-*- encoding: utf-8 -*-
import os
import logging

from flask import Flask

from distsuper.common import tools

app = Flask(__name__)


def load_interface(_module_name):
    if _module_name == 'agent':
        from . import agent_api
        daemon_log = "logs/distsuperagent/uwsgi.log"
    elif _module_name == 'server':
        from . import server_api
        daemon_log = "logs/distsuperd/uwsgi.log"
    else:
        daemon_log = ""

    if daemon_log:
        tools.get_logger("interface", daemon_log, level=logging.INFO)
        tools.get_logger("client", daemon_log, level=logging.INFO)
        tools.get_logger("diff", "logs/diff.log", level=logging.INFO)


load_interface(os.environ.get('DISTSUPER_MODULE_NAME'))

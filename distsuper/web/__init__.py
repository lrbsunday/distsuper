#!-*- encoding: utf-8 -*-
import os
import logging

from flask import Flask

from distsuper.common import tools

tools.get_logger("interface", None, level=logging.INFO)
tools.get_logger("client", "None", level=logging.INFO)
tools.get_logger("diff", "logs/diff.log", level=logging.INFO)
app = Flask(__name__)


def load_interface(_module_name):
    if _module_name == 'agent':
        from . import agent_api
    elif _module_name == 'server':
        from . import server_api


load_interface(os.environ.get('DISTSUPER_MODULE_NAME'))

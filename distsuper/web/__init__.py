#!-*- encoding: utf-8 -*-
import os
from flask import Flask

app = Flask(__name__)


def load_interface(_module_name):
    if _module_name == 'agent':
        from . import agent_api
    elif _module_name == 'server':
        from . import server_api


load_interface(os.environ.get('DISTSUPER_MODULE_NAME'))

#!-*- encoding: utf-8 -*-
import logging

from distsuper.common import handlers, tools, exceptions
from distsuper.main.local import local_start, local_stop, get_status, local_restart
from distsuper import CONFIG
from . import app

logger = tools.get_logger('agent', CONFIG.COMMON.agent_log_file_path,
                          level=logging.INFO)


@app.route('/check', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def check(_):
    return {}


@app.route('/start', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def start(request_info):
    if 'program_id' not in request_info:
        raise exceptions.LackParamException("请求参数缺少program_id")
    if 'machine' not in request_info:
        raise exceptions.LackParamException("请求参数缺少machine")

    program_id = request_info['program_id']
    machine = request_info['machine']
    local_start(program_id, machine)

    return {}


@app.route('/stop', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def stop(request_info):
    if 'program_id' not in request_info:
        raise exceptions.LackParamException("请求参数缺少program_id")

    program_id = request_info['program_id']
    local_stop(program_id)

    return {}


@app.route('/restart', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def restart(request_info):
    if 'program_id' not in request_info:
        raise exceptions.LackParamException("请求参数缺少program_id")

    program_id = request_info['program_id']
    local_restart(program_id)

    return {}


@app.route('/status', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def _status(request_info):
    if 'program_id' not in request_info:
        raise exceptions.LackParamException("请求参数缺少program_id")

    program_id = request_info['program_id']
    status = get_status(program_id)

    return {"status": status}

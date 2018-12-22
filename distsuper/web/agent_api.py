#!-*- encoding: utf-8 -*-
from distsuper.common import handlers, exceptions
from distsuper.main.local import local_start, local_stop, get_status
from . import app


@app.route('/check', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def check(_):
    return {}


@app.route('/start', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def start(request_info):
    if 'program_id' not in request_info:
        raise exceptions.LackParamException("请求参数缺少program_id")

    program_id = request_info['program_id']
    pid = local_start(program_id)

    return {"pid": pid}


@app.route('/stop', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def stop(request_info):
    if 'program_id' not in request_info:
        raise exceptions.LackParamException("请求参数缺少program_id")

    program_id = request_info['program_id']
    local_stop(program_id)

    return {}


@app.route('/status', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def _status(request_info):
    if 'program_id' not in request_info:
        raise exceptions.LackParamException("请求参数缺少program_id")

    program_id = request_info['program_id']
    status = get_status(program_id)

    return {"status": status}

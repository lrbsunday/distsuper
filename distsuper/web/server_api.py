#!-*- encoding: utf-8 -*-
import logging

from distsuper.common import handlers, tools, exceptions
from distsuper.main.operate_db import create_program, stop_program, \
    start_program
from distsuper import CONFIG
from . import app

logger = tools.get_logger('server', CONFIG.COMMON.server_log_file_path,
                          level=logging.INFO)


@app.route('/check', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def check(_):
    return {}


@app.route('/create', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def create(request_info):
    if 'program_name' not in request_info:
        raise exceptions.LackParamException("请求参数缺少program_name")
    if 'command' not in request_info:
        raise exceptions.LackParamException("请求参数缺少command")
    if 'machines' not in request_info:
        raise exceptions.LackParamException("请求参数缺少machines")
    directory = request_info.get('directory')
    environment = request_info.get('environment')
    auto_start = request_info.get('auto_start', True)
    auto_restart = request_info.get('auto_restart', True)
    touch_timeout = request_info.get('touch_timeout', 10 * 365 * 24 * 3600)
    max_fail_count = request_info.get('max_fail_count', 1)
    stdout_logfile = request_info.get('stdout_logfile', '')
    stderr_logfile = request_info.get('stderr_logfile', '')
    source = request_info.get('source', 'api')
    program_name = request_info['program_name']
    command = request_info['command']
    machines = request_info['machines']
    if not machines:
        raise exceptions.ParamValueException("machines不能为空")
    if not command:
        raise exceptions.ParamValueException("command不能为空")
    if not program_name:
        raise exceptions.ParamValueException("program_name不能为空")

    program_id = create_program(program_name, command, machines,
                                directory, environment,
                                auto_start, auto_restart, touch_timeout,
                                max_fail_count, source,
                                stdout_logfile, stderr_logfile)

    return {'program_id': program_id}


@app.route('/start', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def start(request_info):
    if request_info.get('program_id') is None and \
            request_info.get('program_name') is None:
        raise exceptions.LackParamException("请求参数缺少program_id/program_name")

    if request_info.get('program_id') is not None:
        program_id = str(request_info['program_id'])
        if '#' in program_id:
            try:
                _, program_id = program_id.split('#')
            except ValueError:
                raise exceptions.ParamValueException("program_id格式不正确")
        try:
            program_id = int(program_id)
        except ValueError:
            raise exceptions.ParamValueException("program_id格式不正确")
        start_program(program_id=program_id)

    if request_info.get('program_name') is not None:
        start_program(program_name=request_info['program_name'])

    return {}


@app.route('/stop', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def stop(request_info):
    if request_info.get('program_id') is None and \
            request_info.get('program_name') is None:
        raise exceptions.LackParamException("请求参数缺少program_id/program_name")

    if request_info.get('program_id') is not None:
        program_id = str(request_info['program_id'])
        if '#' in program_id:
            try:
                _, program_id = program_id.split('#')
            except ValueError:
                raise exceptions.ParamValueException("program_id格式不正确")
        try:
            program_id = int(program_id)
        except ValueError:
            raise exceptions.ParamValueException("program_id格式不正确")
        stop_program(program_id=program_id)

    if request_info.get('program_name') is not None:
        stop_program(program_name=request_info['program_name'])

    return {}

#!-*- encoding: utf-8 -*-
from playhouse.shortcuts import model_to_dict

from distsuper.common import handlers, exceptions
from distsuper.main import operate
from distsuper.api import agent
from . import app


def get_best_machine(machines):
    return machines.split(";")[0]


# todo
"""
并发性：uwsgi的多个线程同时启停一个进程怎么办？
        相同dpid的操作排队执行
原子性：操作到一半时uwsg重启或服务器宕机怎么办？
        数据库中创建一条记录 => 远程启动 => 修改启动状态
        若中间任何一个环节终端，客户端会收到未知异常，表示内部状态未知，需要查询确定
        要保证服务内部状态一致，即不能出现远程已启动，但数据库中是已停止的状态
        通过touchdb接口保证最终一致性
"""


@app.route('/check', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def check(_):
    return {}


@app.route('/touch', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def touch(request_info):
    return {}


@app.route('/create', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def create(request_info):
    if 'program_name' not in request_info:
        raise exceptions.LackParamException("请求参数缺少program_name")
    if 'command' not in request_info:
        raise exceptions.LackParamException("请求参数缺少command")
    program_name = request_info['program_name']
    command = request_info['command']
    directory = request_info.get('directory')
    environment = request_info.get('environment')
    auto_start = request_info.get('auto_start', True)
    auto_restart = request_info.get('auto_restart', True)
    touch_timeout = request_info.get('touch_timeout', 10 * 365 * 24 * 3600)
    max_fail_count = request_info.get('max_fail_count', 1)
    stdout_logfile = request_info.get('stdout_logfile', '')
    stderr_logfile = request_info.get('stderr_logfile', '')
    machines = request_info.get('machines', "localhost")
    if not machines:
        raise exceptions.ParamValueException("machines不能为空")
    if not command:
        raise exceptions.ParamValueException("command不能为空")
    if not program_name:
        raise exceptions.ParamValueException("program_name不能为空")

    program_id = operate.create_program(program_name, command, machines,
                                        directory, environment,
                                        auto_start, auto_restart,
                                        touch_timeout, max_fail_count,
                                        stdout_logfile, stderr_logfile)

    machine = get_best_machine(machines)
    info = agent.start_process(program_id, machine)

    if info:
        operate.start_program(info, program_id=program_id)
        return program_id
    else:
        raise exceptions.StartException()


@app.route('/start', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def start(request_info):
    program_id = request_info.get('program_id')
    program_name = request_info.get('program_name')

    if program_id is None and program_name is None:
        raise exceptions.LackParamException("请求参数缺少program_id/program_name")

    if program_id is not None:
        program_id = str(program_id)
        try:
            program_id = int(program_id)
        except ValueError:
            raise exceptions.ParamValueException("program_id格式不正确")

    program = operate.get_program(program_id=program_id,
                                  program_name=program_name,
                                  status=0)
    machine = get_best_machine(program.machines)
    info = agent.start_process(program_id, machine)

    if info:
        operate.start_program(info, program_id=program_id)
        return program_id
    else:
        raise exceptions.StartException()


@app.route('/stop', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def stop(request_info):
    program_id = request_info.get('program_id')
    program_name = request_info.get('program_name')

    if program_id is None and program_name is None:
        raise exceptions.LackParamException("请求参数缺少program_id/program_name")

    # 修改数据库
    if program_id is not None:
        program_id = str(program_id)
        try:
            program_id = int(program_id)
        except ValueError:
            raise exceptions.ParamValueException("program_id格式不正确")

    program = operate.get_program(program_id=program_id,
                                  program_name=program_name,
                                  status=1)
    operate.stop_program(program_id=program_id)


@app.route('/status', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def stop(request_info):
    program_id = request_info.get('program_id')
    program_name = request_info.get('program_name')

    if program_id or program_name:
        program = get_program(program_id=program_id, program_name=program_name)
        return model_to_dict(program, recurse=False)
    else:
        programs = get_program(program_id=program_id, program_name=program_name)
        return [model_to_dict(program, recurse=False)
                for program in programs]

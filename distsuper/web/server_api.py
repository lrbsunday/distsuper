#!-*- encoding: utf-8 -*-
from playhouse.shortcuts import model_to_dict

from distsuper.common import handlers, exceptions
from distsuper.main import operate
from distsuper.api import agent
from . import app


def get_best_machine(machines):
    machines = machines.split(";")
    machines = [machine.strip()
                for machine in machines
                if machine.strip()]
    return machines[0] if machines else "127.0.0.1"


def start(program):
    machine = get_best_machine(program.machines)

    operate.lock(program.id)
    pid = agent.start_process(program.id, machine)

    if pid:
        operate.start_program(machine, pid, program_id=program.id)
        operate.unlock(program.id)
        return program.id

    operate.unlock(program.id)
    raise exceptions.StartException()


def stop(program):
    machine = program.machine

    operate.lock(program.id)
    ret = agent.stop_process(program.id, machine)

    if ret:
        operate.stop_program(program_id=program.id)
        operate.unlock(program.id)
        return program.id

    operate.unlock(program.id)
    raise exceptions.StopException()


# todo
"""
并发性：uwsgi的多个线程同时启停一个进程怎么办？
        相同dpid的操作排队执行
        为减小延迟，队列长度设为2，一个用户使用，一个后台使用
原子性：操作到一半时uwsgi重启或服务器宕机怎么办？
        数据库中创建一条记录 => 远程启动 => 修改启动状态
        若中间任何一个环节中断，客户端会收到未知异常，表示内部状态未知，需要查询确定状态
        要保证服务内部状态一致，即不能出现远程已启动，但数据库中是已停止的状态
        通过touchdb接口保证最终一致性
        
不可能出现的情况：
    数据库里的进程已停止，且实际进程运行中
"""


@app.route('/check', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def check(_):
    return {}


@app.route('/touch', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def touch(request_info):
    # todo
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

    program = operate.create_program(program_name, command, machines,
                                     directory, environment,
                                     auto_start, auto_restart,
                                     touch_timeout, max_fail_count,
                                     stdout_logfile, stderr_logfile)
    return start(program)


@app.route('/start', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def start(request_info):
    program_id = request_info.get('program_id')
    program_name = request_info.get('program_name')

    if program_id is None and program_name is None:
        raise exceptions.LackParamException("参数program_id和program_name至少存在一个")

    if program_id is not None:
        try:
            program_id = int(program_id)
        except ValueError:
            raise exceptions.ParamValueException("program_id格式不正确")

    program = operate.get_program(program_id=program_id,
                                  program_name=program_name,
                                  status=0,
                                  lock=0)
    return start(program)


@app.route('/stop', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def stop(request_info):
    program_id = request_info.get('program_id')
    program_name = request_info.get('program_name')

    if program_id is None and program_name is None:
        raise exceptions.LackParamException("参数program_id和program_name至少存在一个")

    if program_id is not None:
        try:
            program_id = int(program_id)
        except ValueError:
            raise exceptions.ParamValueException("program_id格式不正确")

    program = operate.get_program(program_id=program_id,
                                  program_name=program_name,
                                  status=1,
                                  lock=0)
    return stop(program)


@app.route('/restart', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def restart(request_info):
    program_id = request_info.get('program_id')
    program_name = request_info.get('program_name')

    if program_id is None and program_name is None:
        raise exceptions.LackParamException("参数program_id和program_name至少存在一个")

    if program_id is not None:
        try:
            program_id = int(program_id)
        except ValueError:
            raise exceptions.ParamValueException("program_id格式不正确")

    program = operate.get_program(program_id=program_id,
                                  program_name=program_name,
                                  status=1,
                                  lock=0)
    return stop(program) and start(program)


@app.route('/status', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def status(request_info):
    program_id = request_info.get('program_id')
    program_name = request_info.get('program_name')
    _status = request_info.get('status')

    if program_id or program_name:
        program = operate.get_program(program_id=program_id,
                                      program_name=program_name,
                                      status=_status)
        return model_to_dict(program, recurse=False)
    else:
        programs = operate.get_program()
        return [model_to_dict(program, recurse=False)
                for program in programs]

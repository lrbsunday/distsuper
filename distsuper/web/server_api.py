#!-*- encoding: utf-8 -*-
import logging

from playhouse.shortcuts import model_to_dict

from distsuper.common import handlers, exceptions, tools
from distsuper.main import operate
from distsuper.common.constant import STATUS
from distsuper.api import agent
from . import app

logger = logging.getLogger("interface.server")


def get_best_machine(machines):
    machines = machines.split(";")
    machines = [machine.strip()
                for machine in machines
                if machine.strip()]
    return machines[0] if machines else "127.0.0.1"


CAN_CREATE_STATUS = (STATUS.STOPPED, STATUS.FATAL, STATUS.UNKNOWN)
CAN_START_STATUS = (STATUS.STOPPED, STATUS.EXITED, STATUS.FATAL, STATUS.UNKNOWN)
CAN_STOP_STATUS = (STATUS.RUNNING, STATUS.EXITED, STATUS.FATAL, STATUS.UNKNOWN)


def create_process(program_id, program_name, command, machines,
                   directory, environment,
                   auto_start, auto_restart, touch_timeout,
                   max_fail_count,
                   stdout_logfile, stderr_logfile):
    try:
        program = operate.get_program(program_name=program_name)
    except exceptions.ProgramNotExistInDB:
        return operate.create_program(program_id, program_name,
                                      command, machines,
                                      directory, environment,
                                      auto_start, auto_restart, touch_timeout,
                                      max_fail_count,
                                      stdout_logfile, stderr_logfile)

    if program.status not in CAN_CREATE_STATUS:
        msg = "程序%s所处状态，无法重新创建" % program_name
        logger.error(msg)
        raise exceptions.AlreadExistsException(msg)

    if operate.update_program(program.id,
                              id=program_id,
                              command=command,
                              machines=machines,
                              directory=directory,
                              environment=environment,
                              auto_start=auto_start,
                              auto_restart=auto_restart,
                              touch_timeout=touch_timeout,
                              max_fail_count=max_fail_count,
                              stdout_logfile=stdout_logfile,
                              stderr_logfile=stderr_logfile,
                              machine="",
                              status=STATUS.STOPPED,
                              fail_count=0,
                              timeout_timestamp=0x7FFFFFFF):
        return operate.get_program(program_id=program_id)
    else:
        logger.error("程序创建失败")
        raise exceptions.CreateException()


def start_process(program_id):
    program = operate.get_program(program_id=program_id)
    if program.status == STATUS.RUNNING:
        logger.warning("程序%s运行中，无需重复启动" % program.id)
        raise exceptions.AlreadyStartException()

    if program.status not in CAN_START_STATUS:
        logger.warning("程序%s所处状态无法启动" % program.name)
        raise exceptions.StartException()

    machine = get_best_machine(program.machines)

    if not operate.change_status(program.id,
                                 CAN_START_STATUS,
                                 STATUS.STARTING):
        logger.error("程序%s修改状态失败" % program.id)
        raise exceptions.StartException()

    ret = agent.start_process(program.id, machine)
    if not ret:
        logger.error("程序%s启动失败" % program.id)
        operate.change_status(program.id, STATUS.STARTING, STATUS.STOPPED)
        raise exceptions.StartException()

    fields = dict(machine=machine,
                  fail_count=0,
                  timeout_timestamp=0x7fffffff)
    if operate.update_program(program_id=program.id, **fields):
        ret = operate.change_status(program.id, STATUS.STARTING, STATUS.RUNNING)
    else:
        logger.error("程序%s更新数据库失败" % program.id)
        ret = operate.change_status(program.id, STATUS.STARTING, STATUS.STOPPED)

    if not ret:
        logger.error("程序%s修改状态失败" % program.id)
        raise exceptions.StartException()

    return program.id


def stop_process(program_id):
    program = operate.get_program(program_id=program_id)
    if program.status == STATUS.STOPPED:
        logger.warning("程序%s已停止，无需重复停止" % program.id)
        raise exceptions.AlreadyStopException()

    if program.status not in CAN_STOP_STATUS:
        logger.warning("程序%s不是运行状态，无法停止" % program.name)
        raise exceptions.StopException()

    machine = program.machine

    if not operate.change_status(program.id,
                                 CAN_STOP_STATUS,
                                 STATUS.STOPPING):
        logger.error("程序%s修改状态失败" % program.id)
        raise exceptions.StopException()

    ret = agent.stop_process(program.id, machine)
    if not ret:
        logger.error("程序%s停止失败" % program.id)
        operate.change_status(program.id, STATUS.STOPPING, STATUS.RUNNING)
        raise exceptions.StopException()

    ret = operate.change_status(program.id, STATUS.STOPPING, STATUS.STOPPED)
    if not ret:
        logger.error("程序%s修改状态失败" % program.id)
        raise exceptions.StopException()

    return program.id


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

    program_id = tools.gen_uuid()
    logger.info(program_id)
    program = create_process(program_id, program_name, command, machines,
                             directory, environment,
                             auto_start, auto_restart, touch_timeout,
                             max_fail_count,
                             stdout_logfile, stderr_logfile)
    logger.info(program.id)

    if program.auto_start:
        start_process(program.id)

    return {
        "program_id": program.id
    }


@app.route('/start', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def start(request_info):
    program_id = request_info.get('program_id')
    program_name = request_info.get('program_name')

    if program_id is None and program_name is None:
        raise exceptions.LackParamException("参数program_id和program_name至少存在一个")

    program = operate.get_program(program_id=program_id,
                                  program_name=program_name)

    return {
        "program_id": start_process(program.id)
    }


@app.route('/stop', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def stop(request_info):
    program_id = request_info.get('program_id')
    program_name = request_info.get('program_name')

    if program_id is None and program_name is None:
        raise exceptions.LackParamException("参数program_id和program_name至少存在一个")

    program = operate.get_program(program_id=program_id,
                                  program_name=program_name)

    return {
        "program_id": stop_process(program.id)
    }


@app.route('/restart', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def restart(request_info):
    program_id = request_info.get('program_id')
    program_name = request_info.get('program_name')

    if program_id is None and program_name is None:
        raise exceptions.LackParamException("参数program_id和program_name至少存在一个")

    program = operate.get_program(program_id=program_id,
                                  program_name=program_name)
    if program.status in CAN_STOP_STATUS:
        stop_process(program.id) and start_process(program.id)
    elif program.status in CAN_START_STATUS:
        start_process(program.id)
    else:
        raise exceptions.RestartException()

    return {
        "program_id": program.id
    }


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
        programs = operate.get_programs()
        return [model_to_dict(program, recurse=False)
                for program in programs]

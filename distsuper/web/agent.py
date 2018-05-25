import os
import subprocess
import logging
import time

from peewee import DoesNotExist

from distsuper.common import handlers, tools, exceptions
from distsuper.web.common import processwrapper
from distsuper.models.models import Process
from distsuper import CONFIG
from . import app

logger = tools.get_logger('agent', CONFIG.AGENT.log_file_path,
                          level=logging.INFO)


@app.route('/check', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def check(_):
    return {}


@app.route('/start', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def start(request_info):
    if 'program_name' not in request_info:
        raise exceptions.LackParamException("请求参数缺少program_name")
    if 'machine' not in request_info:
        raise exceptions.LackParamException("请求参数缺少machine")

    program_name = request_info['program_name']
    machine = request_info['machine']
    local_start(program_name, machine)

    return {}


@app.route('/stop', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def stop(request_info):
    if 'program_name' not in request_info:
        raise exceptions.LackParamException("请求参数缺少program_name")

    program_name = request_info['program_name']
    local_stop(program_name)

    return {}


@app.route('/status', methods=['GET', 'POST'])
@handlers.request_pre_handler()
def _status(request_info):
    if 'program_name' not in request_info:
        raise exceptions.LackParamException("请求参数缺少program_name")

    program_name = request_info['program_name']
    status = get_status(program_name)

    return {"status": status}


# noinspection PyUnusedLocal
def sigdefault(process, info, *args):
    logger.info(args)
    program_name = info['program_name']
    logger.info("进程%s收到信号，即将退出" % program_name)
    process.terminate()


# noinspection PyUnusedLocal
def sigterm(process, info, *args):
    process.terminate()
    program_name = info['program_name']
    r = Process.update(pstatus=0,
                       update_time=tools.get_now_time()) \
        .where(Process.name == program_name,
               Process.pstatus << (1, 2)) \
        .execute()
    if r == 1:
        logger.info("进程%s手动被SIG_TERM信号杀死" % (program_name,))
    else:
        info['stop_flag'] = True


# noinspection PyUnusedLocal
def fail(args, retcode, info):
    if 'stop_flag' in info:
        return
    program_name = info['program_name']
    r = Process.update(pstatus=0,
                       fail_count=Process.fail_count + 1,
                       update_time=tools.get_now_time()) \
        .where(Process.name == program_name,
               Process.pstatus << (1, 2)) \
        .execute()
    if r == 1:
        logger.info("进程%s执行失败，退出状态码%s" % (program_name, retcode))


# noinspection PyUnusedLocal
def success(args, retcode, info):
    program_name = info['program_name']
    r = Process.update(pstatus=5,
                       update_time=tools.get_now_time()) \
        .where(Process.name == program_name,
               Process.pstatus << (1, 2)) \
        .execute()
    logger.info("进程%s执行成功，退出状态码%s" % (program_name, retcode))
    if r == 0:
        logger.warning("进程%s状态更新失败" % program_name)


# noinspection PyUnusedLocal
def start_success(args, info):
    program_name = info['program_name']
    machine = info['machine']
    pid = info['pid']
    retcode = Process.update(pstatus=2,
                             fail_count=0,
                             machine=machine,
                             pid=pid,
                             update_time=tools.get_now_time()) \
        .where(Process.name == program_name,
               Process.pstatus == 1) \
        .execute()
    if retcode == 1:
        msg = "进程%s启动成功" % program_name
        logger.info(msg)
    else:
        msg = "进程%s启动失败，或状态改变导致数据库冲突，无法修改状态" % program_name
        logger.error(msg)
        raise exceptions.DBConflictException(msg)


def local_start(program_name, machine):
    try:
        process = Process.select().where(Process.name == program_name).get()
    except DoesNotExist:
        msg = "找不到进程%s的配置数据，无法启动" % program_name
        logger.warning(msg)
        raise exceptions.NoConfigException(msg)

    if process.pstatus == 0:
        pass
    if process.pstatus == 1:
        msg = "进程%s启动中，忽略本次请求" % program_name
        logger.warning(msg)
        raise exceptions.ProcessStatusException(msg)
    if process.pstatus == 2:
        msg = "进程%s已启动，忽略本次请求" % program_name
        raise exceptions.ProcessStatusException(msg)
    if process.pstatus == 3:
        msg = "进程%s停止中，忽略本次请求" % program_name
        raise exceptions.ProcessStatusException(msg)

    retcode = Process.update(pstatus=1,
                             machine=machine,
                             timeout_timestamp=(int(time.time())
                                                + Process.touch_timeout),
                             update_time=tools.get_now_time()) \
        .where(Process.name == program_name,
               Process.pstatus == 0) \
        .execute()
    if retcode == 1:
        logger.info("进程%s启动中..." % program_name)
    else:
        msg = "进程%s启动时，状态改变导致数据库冲突，无法修改状态" % program_name
        logger.warning(msg)
        raise exceptions.DBConflictException(msg)

    command = process.command
    touch_timeout = process.touch_timeout
    callbacks = {
        'success': success,
        'fail': fail,
        'sigdefault': sigdefault,
        'sigterm': sigterm,
        'start_success': start_success
    }
    info = {
        'machine': machine,
        'program_name': program_name,
        'touch_timeout': touch_timeout,
        'stdout_logfile': '.logs/test.log'
    }
    processwrapper.create_subprocess(command, info, callbacks)

    # 需要连续运行一段时间，才能确定是启动成功


def local_stop(program_name):
    try:
        process = Process.select().where(Process.name == program_name).get()
    except DoesNotExist:
        msg = "找不到进程%s的配置数据，无法启动" % program_name
        logger.warning(msg)
        raise exceptions.NoConfigException(msg)

    if process.pstatus == 0:
        msg = "进程%s已停止，忽略本次请求" % program_name
        logger.warning(msg)
        raise exceptions.ProcessStatusException(msg)
    if process.pstatus == 1:
        msg = "进程%s启动中，忽略本次请求" % program_name
        logger.warning(msg)
        raise exceptions.ProcessStatusException(msg)
    if process.pstatus == 2:
        pass
    if process.pstatus == 3:
        msg = "进程%s停止中，忽略本次请求" % program_name
        raise exceptions.ProcessStatusException(msg)

    retcode = Process.update(pstatus=3,
                             update_time=tools.get_now_time()) \
        .where(Process.name == program_name,
               Process.pstatus == 2) \
        .execute()
    if retcode == 1:
        logger.info("进程%s停止中..." % program_name)
    else:
        msg = "进程%s停止时，状态改变导致数据库冲突，无法修改状态" % program_name
        logger.warning(msg)
        raise exceptions.DBConflictException(msg)

    if process.pid == 0:
        msg = "进程%s的pid不合法，停止失败" % program_name
        logger.warning(msg)
        raise exceptions.ProcessStatusException(msg)

    args = ['kill', str(process.pid)]
    subprocess.Popen(args).wait()

    retcode = Process.update(cstatus=0,
                             pstatus=0,
                             machine='',
                             pid=-1,
                             update_time=tools.get_now_time()) \
        .where(Process.name == program_name,
               Process.pstatus == 3) \
        .execute()
    if retcode == 1:
        logger.info("进程%s停止成功" % program_name)
    else:
        msg = "进程%s停止成功，但状态改变导致数据库冲突，无法修改状态" % program_name
        logger.warning(msg)
        raise exceptions.DBConflictException(msg)


def get_status(program_name):
    try:
        process = Process.select().where(Process.name == program_name).get()
    except DoesNotExist:
        return False

    pid = process.pid
    for line in os.popen("ps aux|awk '{print $2}'|grep %s" % pid):
        if line.strip() == str(pid):
            return True
    return False

#!-*- encoding: utf-8 -*-
import os
import re
import json
import subprocess
import time
import logging

from peewee import DoesNotExist

from distsuper.common import exceptions
from distsuper.common.constant import STATUS
from distsuper.models.models import Process
from distsuper.scripts.common import get_pid

logger = logging.getLogger("interface.agent")


def local_start(program_id, wait=3):
    try:
        process = Process.select().where(Process.id == program_id).get()
    except DoesNotExist:
        msg = "找不到进程%s的配置数据，无法启动" % program_id
        logger.warning(msg)
        raise exceptions.NoConfigException(msg)

    if process.status == STATUS.RUNNING:
        msg = "进程%s已启动，忽略本次请求" % process.name
        logger.warning(msg)
        raise exceptions.AlreadyStartException()

    command = process.command
    directory = process.directory
    environment = process.environment
    touch_timeout = process.touch_timeout
    stdout_logfile = process.stdout_logfile
    stderr_logfile = process.stderr_logfile
    info = {
        'program_id': process.id,
        'program_name': process.name,
        'directory': directory,
        'environment': environment,
        'touch_timeout': touch_timeout,
        'stdout_logfile': stdout_logfile,
        'stderr_logfile': stderr_logfile,
    }

    args = json.dumps(command)
    info = json.dumps(info)

    p = subprocess.Popen(['dswrapper', args, info],
                         stdout=subprocess.PIPE)
    p.wait()

    if p.returncode != 0:
        logger.warning("进程%s启动失败" % process.name)
        raise exceptions.StartException()

    if not check_start_status(program_id, wait):
        logger.warning("进程%s启动失败" % process.name)
        raise exceptions.StartException()

    return True


def local_stop(program_id, wait_timeout=10):
    try:
        process = Process.select().where(Process.id == program_id).get()
    except DoesNotExist:
        msg = "找不到进程%s的配置数据，无法启动" % program_id
        logger.warning(msg)
        raise exceptions.NoConfigException(msg)

    if process.status == STATUS.STOPPED:
        msg = "进程%s已停止，忽略本次请求" % process.name
        logger.warning(msg)
        raise exceptions.AlreadyStopException()

    pid = get_pid(program_id)
    if pid == 0:
        logger.warning("要停止的进程不存在，忽略")
        return True

    args = ['kill', str(pid)]
    subprocess.Popen(args).wait()

    if not wait_until_stop_done(program_id, wait_timeout):
        logger.warning("进程%s停止失败" % process.name)
        raise exceptions.StopException()

    return True


def get_status(program_id):
    try:
        process = Process.select().where(Process.id == program_id).get()
    except DoesNotExist:
        return False

    if process.status == STATUS.STOPPED:
        return False

    return check_process(program_id)


def check_process(program_id):
    pid = get_pid(program_id)

    check_process_command = """ ps aux | 
                                awk '{print $2}' |
                                grep -E '^%s$'""" % pid
    check_process_command = check_process_command.replace("\n", "")
    check_process_command = re.sub(r" +", " ", check_process_command)
    for line in os.popen(check_process_command):
        if line.strip() == str(pid):
            return True
    return False


def check_start_status(program_id, wait):
    time.sleep(wait)
    return check_process(program_id)


def wait_until_stop_done(program_id, wait_timeout):
    while True:
        if not check_process(program_id):
            return True

        if wait_timeout <= 0:
            return False

        wait_timeout -= 1
        time.sleep(1)

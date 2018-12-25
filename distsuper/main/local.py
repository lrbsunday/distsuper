#!-*- encoding: utf-8 -*-
import os
import json
import subprocess
import time
import logging

from peewee import DoesNotExist

from distsuper.common import exceptions
from distsuper.models.models import Process

logger = logging.getLogger('agent')


def local_start(program_id, wait=3):
    try:
        process = Process.select().where(Process.id == program_id).get()
    except DoesNotExist:
        msg = "找不到进程%s的配置数据，无法启动" % program_id
        logger.warning(msg)
        raise exceptions.NoConfigException(msg)

    if process.status == 1:
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

    pid = int(p.stdout.readline())
    if not check_start_status(pid, wait):
        logger.warning("进程%s启动失败" % process.name)
        raise exceptions.StartException()

    return pid


def local_stop(program_id, wait_timeout=10):
    try:
        process = Process.select().where(Process.id == program_id).get()
    except DoesNotExist:
        msg = "找不到进程%s的配置数据，无法启动" % program_id
        logger.warning(msg)
        raise exceptions.NoConfigException(msg)

    if process.status == 0:
        msg = "进程%s已停止，忽略本次请求" % process.name
        logger.warning(msg)
        raise exceptions.AlreadyStopException()

    args = ['kill', str(process.pid)]
    subprocess.Popen(args).wait()

    if not wait_until_stop_done(process.pid, wait_timeout):
        logger.warning("进程%s停止失败" % process.name)
        raise exceptions.StopException()

    return True


def get_status(program_id):
    try:
        process = Process.select().where(Process.id == program_id).get()
    except DoesNotExist:
        return False

    if process.status == 0:
        return False

    pid = process.pid
    return check_pid(pid)


def check_pid(pid):
    for line in os.popen("ps aux|awk '{print $2}'|grep -E '^%s$'" % pid):
        if line.strip() == str(pid):
            return True
    return False


def check_start_status(pid, wait):
    time.sleep(wait)
    return check_pid(pid)


def wait_until_stop_done(pid, wait_timeout):
    while True:
        time.sleep(1)
        if not check_pid(pid):
            return True

        wait_timeout -= 1
        if wait_timeout <= 0:
            return False

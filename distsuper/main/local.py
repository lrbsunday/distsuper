#!-*- encoding: utf-8 -*-
import os
import json
import subprocess
import time
import logging

from peewee import DoesNotExist

from distsuper.common import exceptions, tools
from distsuper.models.models import Process
from distsuper import CONFIG

logger = tools.get_logger('agent', CONFIG.COMMON.agent_log_file_path,
                          level=logging.INFO)


def local_start(program_id, machine):
    try:
        process = Process.select().where(Process.id == program_id).get()
    except DoesNotExist:
        msg = "找不到进程%s的配置数据，无法启动" % program_id
        logger.warning(msg)
        raise exceptions.NoConfigException(msg)

    if process.pstatus == 0:
        pass
    if process.pstatus == 1:
        msg = "进程%s启动中，忽略本次请求" % program_id
        logger.warning(msg)
        raise exceptions.ProcessStatusException(msg)
    if process.pstatus == 2:
        msg = "进程%s已启动，忽略本次请求" % program_id
        raise exceptions.ProcessStatusException(msg)
    if process.pstatus == 3:
        msg = "进程%s停止中，忽略本次请求" % program_id
        raise exceptions.ProcessStatusException(msg)

    fields = dict(machine=machine,
                  pid=0,
                  pstatus=1,

                  # fail_count=0,  # 需要连续运行一段时间，才能确定是启动成功
                  timeout_timestamp=(int(time.time()) + Process.touch_timeout),

                  config_updated=0,
                  update_time=tools.get_now_time())
    retcode = Process.update(**fields) \
        .where(Process.id == program_id,
               Process.config_hash == process.config_hash,
               Process.pstatus == 0) \
        .execute()
    if retcode == 1:
        logger.info("进程%s启动中..." % program_id)
    else:
        msg = "进程%s启动时，状态改变导致数据库冲突，无法修改状态" % program_id
        logger.warning(msg)
        raise exceptions.DBConflictException(msg)

    command = process.command
    directory = process.directory
    environment = process.environment
    touch_timeout = process.touch_timeout
    stdout_logfile = process.stdout_logfile
    stderr_logfile = process.stderr_logfile
    info = {
        'machine': machine,
        'program_id': process.id,
        'program_name': process.name,
        'directory': directory,
        'environment': environment,
        'touch_timeout': touch_timeout,
        'stdout_logfile': stdout_logfile,
        'stderr_logfile': stderr_logfile,
    }
    # processwrapper.create_subprocess(command, info)

    args = json.dumps(command)
    info = json.dumps(info)
    subprocess.Popen(['dswrapper', args, info])


def local_stop(program_id):
    try:
        process = Process.select().where(Process.id == program_id).get()
    except DoesNotExist:
        msg = "找不到进程%s的配置数据，无法启动" % program_id
        logger.warning(msg)
        raise exceptions.NoConfigException(msg)

    if process.pstatus == 0:
        msg = "进程%s已停止，忽略本次请求" % program_id
        logger.warning(msg)
        raise exceptions.ProcessStatusException(msg)
    if process.pstatus == 1:
        msg = "进程%s启动中，忽略本次请求" % program_id
        logger.warning(msg)
        raise exceptions.ProcessStatusException(msg)
    if process.pstatus == 2:
        pass
    if process.pstatus == 3:
        msg = "进程%s停止中，忽略本次请求" % program_id
        raise exceptions.ProcessStatusException(msg)

    fields = dict(pstatus=3,

                  config_updated=0,
                  update_time=tools.get_now_time())
    retcode = Process.update(**fields) \
        .where(Process.id == program_id,
               Process.config_hash == process.config_hash,
               Process.pstatus == 2) \
        .execute()
    if retcode == 1:
        logger.info("进程%s停止中..." % program_id)
    else:
        msg = "进程%s停止时，状态改变导致数据库冲突，无法修改状态" % program_id
        logger.warning(msg)
        raise exceptions.DBConflictException(msg)

    if process.pid == 0:
        msg = "进程%s的pid不合法，停止失败" % program_id
        logger.warning(msg)
        raise exceptions.ProcessStatusException(msg)

    args = ['kill', str(process.pid)]
    subprocess.Popen(args).wait()

    fields = dict(cstatus=0,

                  pstatus=0,
                  machine='',
                  pid=0,

                  update_time=tools.get_now_time())
    retcode = Process.update(**fields) \
        .where(Process.id == program_id,
               Process.pstatus == 3) \
        .execute()
    if retcode == 1:
        logger.info("进程%s停止成功" % program_id)
    else:
        msg = "进程%s停止成功，但状态改变导致数据库冲突，无法修改状态" % program_id
        logger.warning(msg)
        raise exceptions.DBConflictException(msg)


def local_restart(program_id):
    try:
        process = Process.select().where(Process.id == program_id).get()
    except DoesNotExist:
        msg = "找不到进程%s的配置数据，无法重启" % program_id
        logger.warning(msg)
        raise exceptions.NoConfigException(msg)

    if process.pstatus == 0:
        msg = "进程%s已停止，忽略本次请求" % program_id
        logger.warning(msg)
        raise exceptions.ProcessStatusException(msg)

    args = ['kill', str(process.pid)]
    subprocess.Popen(args).wait()


def get_status(program_id):
    try:
        process = Process.select().where(Process.id == program_id).get()
    except DoesNotExist:
        return False

    pid = process.pid
    for line in os.popen("ps aux|awk '{print $2}'|grep %s" % pid):
        if line.strip() == str(pid):
            return True
    return False

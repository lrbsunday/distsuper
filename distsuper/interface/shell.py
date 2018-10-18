#!-*- encoding: utf-8 -*-
import logging
import time

from distsuper.models.models import Process
from . import api


# todo 取消直接数据库查询
# 1. 回调通知进程状态
# 2. get_status_by_shell走API接口
def start_process_by_shell(program_id, wait=False):
    ret = api.start_process(program_id)
    if ret is None:
        logging.warning("进程%s已启动，请不要重复操作")
        return True

    if not ret:
        logging.warning("进程%s启动失败" % program_id)
        return False

    if wait:
        return wait_until_start_done(program_id)

    return True


def stop_process_by_shell(program_id, wait=False):
    ret = api.stop_process(program_id)
    if ret is None:
        logging.warning("进程%s已停止，请不要重复操作")
        return True

    if not ret:
        logging.warning("进程%s停止失败" % program_id)
        return False

    if wait:
        return wait_until_stop_done(program_id)

    return True


def restart_process_by_shell(program_id, wait=False):
    ret = api.restart_process(program_id=program_id)
    if not ret:
        logging.warning("进程%s重启失败" % program_id)
        return False

    return True


def get_status_by_shell():
    processes = Process.select() \
        .order_by(Process.cstatus, Process.pstatus)

    results = []
    for process in processes:
        name = "%s#%s" % (process.name, process.id)
        status = caculate_status(process.pstatus)
        started = True if status in ('RUNNING', 'STOPPING') else False
        machine = 'machine:' + process.machine if started else ''
        pid = 'pid:' + str(process.pid) if started else ''
        start_time = process.create_time.strftime(
            "%Y-%m-%dT%H:%M:%S") if started else ''

        results.append([name, status, machine, pid, start_time])

    if results:
        templates = []
        for i in range(5):
            max_length = max(len(result[i]) for result in results)
            templates.append("%{}s".format(max_length))

        for result in results:
            print('\t'.join([template % field
                             for field, template in zip(result, templates)]))


def caculate_status(pstatus):
    if pstatus == 0:
        return 'STOP'
    elif pstatus == 1:
        return 'STARTING'
    elif pstatus == 2:
        return 'RUNNING'
    elif pstatus == 3:
        return 'STOPPING'
    elif pstatus == 4:
        return 'FAILED'
    elif pstatus == 5:
        return 'SUCCEED'
    else:
        return 'UNKNOWN'


def wait_until_start_done(program_id):
    while True:
        time.sleep(1)

        process = Process.select().where(
            Process.id == program_id).get()

        if process.pstatus in (2, 5):
            logging.info("进程%s启动成功" % program_id)
            return True
        if process.pstatus == 4:
            logging.warning("进程%s启动失败" % program_id)
            return False
        if process.pstatus in (0, 1, 3):
            logging.info("等待进程%s启动" % program_id)


def wait_until_stop_done(program_id):
    while True:
        time.sleep(1)

        process = Process.select().where(
            Process.id == program_id).get()

        if process.pstatus in (0, 5):
            logging.info("进程%s停止成功" % program_id)
            return True
        if process.pstatus == 4:
            logging.info("进程%s停止失败" % program_id)
            return False
        if process.pstatus in (1, 2, 3):
            logging.info("等待进程%s停止" % program_id)

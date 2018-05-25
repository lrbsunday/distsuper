import logging
import time

from peewee import DoesNotExist

from distsuper.common import tools
from distsuper.models.models import Process


def wait_until_start_done(program_name):
    while True:
        time.sleep(1)

        try:
            process = Process.select().where(Process.name == program_name).get()
        except DoesNotExist:
            logging.info("等待进程%s启动" % program_name)
        else:
            if process.pstatus in (2, 5):
                logging.info("进程%s启动成功" % program_name)
                return True
            if process.pstatus == 4:
                logging.warning("进程%s启动失败" % program_name)
                return False
            if process.pstatus in (0, 1, 3):
                logging.info("等待进程%s启动" % program_name)


def start_process_by_shell(program_name,
                           wait=False):
    ret_code = Process.update(cstatus=1,
                              machine='',
                              pstatus=0,
                              pid=-1,
                              fail_count=0,
                              timeout_timestamp=0x7FFFFFFF,
                              update_time=tools.get_now_time()) \
        .where(Process.name == program_name,
               Process.pstatus << (0, 4, 5)) \
        .execute()
    if ret_code == 1:
        logging.info("程序%s启动中..." % program_name)
    else:
        logging.error("程序%s的配置不存在或进程状态不合法" % program_name)
        return False

    if wait:
        return wait_until_start_done(program_name)

    return True


def wait_until_stop_done(program_name):
    while True:
        time.sleep(1)

        try:
            process = Process.select().where(Process.name == program_name).get()
        except DoesNotExist:
            logging.info("进程%s停止成功" % program_name)
            return True
        else:
            if process.pstatus in (0, 5):
                logging.info("进程%s停止成功" % program_name)
                return True
            if process.pstatus == 4:
                logging.info("进程%s停止失败" % program_name)
                return False
            if process.pstatus in (1, 2, 3):
                logging.info("等待进程%s停止" % program_name)


def stop_process_by_shell(program_name,
                          wait=False):
    ret_code = Process.update(cstatus=0,
                              update_time=tools.get_now_time()) \
        .where(Process.name == program_name,
               Process.pstatus == 2) \
        .execute()
    if ret_code == 1:
        logging.info("程序%s停止中..." % program_name)
    else:
        logging.error("程序%s的配置不存在或进程状态不合法" % program_name)
        return False

    if wait:
        return wait_until_stop_done(program_name)

    return True


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


def get_status_by_shell():
    processes = Process.select() \
        .order_by(Process.cstatus, Process.pstatus)

    results = []
    for process in processes:
        name = process.name
        status = caculate_status(process.pstatus)
        started = True if status in ('RUNNING', 'STOPPING') else False
        machine = 'machine:' + process.machine if started else ''
        pid = 'pid:' + str(process.pid) if started else ''
        start_time = process.create_time.strftime(
            "%Y-%m-%dT%H:%M:%S") if started else ''

        results.append([name, status, machine, pid, start_time])

    templates = []
    for i in range(5):
        max_length = max(len(result[i]) for result in results)
        templates.append("%{}s".format(max_length))

    for result in results:
        print('\t'.join([template % field
                         for field, template in zip(result, templates)]))

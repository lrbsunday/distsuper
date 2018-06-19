#!-*- encoding: utf-8 -*-
import time
import datetime
import logging
import random
from datetime import timedelta

from distsuper.common import tools
from distsuper.main.remote import remote_start, remote_stop, remote_status
from distsuper.models.models import Process


def diff():
    while True:
        try:
            # 正在运行的
            processes = Process.select() \
                .where(Process.cstatus == 1,
                       Process.pstatus == 2)
            for process in processes:
                diff_one(process)

            # 正在启动的
            processes = Process.select() \
                .where(Process.cstatus == 1,
                       Process.pstatus == 1)
            for process in processes:
                diff_one(process)

            # 正在停止的
            processes = Process.select() \
                .where(Process.cstatus == 0,
                       Process.pstatus == 3)
            for process in processes:
                diff_one(process)

            # 应该停止的
            processes = Process.select() \
                .where(Process.cstatus == 0,
                       Process.pstatus == 2)
            for process in processes:
                diff_one(process)

            # 应该启动的
            processes = Process.select() \
                .where(Process.cstatus == 1,
                       Process.pstatus == 0)
            for process in processes:
                diff_one(process)

            # 配置已更新的
            # processes = Process.select() \
            #     .where(Process.config_updated == 1)
            # for process in processes:
            #     diff_one(process)

            time.sleep(1)
        except Exception as e:
            logging.exception("some exception is happened")
            raise Exception(e)


def get_best_machine(process):
    """ 随机挑一台可用机器
    :param process:
    :return:
    """
    if process.machines:
        machines = process.machines.split(",")
        return random.choice(machines)
    else:
        return "localhost"


def diff_one(process):
    """ 同步process之间的状态
    :return:
    """
    cstatus = process.cstatus
    pstatus = process.pstatus
    now_timestamp = time.time()

    # 无需处理
    if cstatus == 1 and pstatus == 2:
        if process.timeout_timestamp < now_timestamp:
            if not remote_status(process.id, process.machine):
                retcode = Process.update(pstatus=0) \
                    .where(Process.id == process.id,
                           Process.pstatus == 2,
                           Process.cstatus == 1,
                           Process.timeout_timestamp < now_timestamp) \
                    .execute()
                if retcode == 1:
                    logging.info("重置已挂掉的进程%s" % process.name)
        return True
    if cstatus == 0 and pstatus == 0:
        return True

    # 超时后重试
    if pstatus == 1:
        if datetime.datetime.now() - process.update_time > \
                timedelta(seconds=60):
            logging.warning("%s启动超时，重试" % process.name)
            process.pstatus = 0
            process.update_time = tools.get_now_time()
            process.save()
            return False
        return True
    if pstatus == 3:
        if datetime.datetime.now() - process.update_time > \
                timedelta(seconds=60):
            logging.warning("%s停止超时，重试" % process.name)
            process.pstatus = 2
            process.update_time = tools.get_now_time()
            process.save()
            return False
        return True

    # 启动
    if cstatus == 1 and pstatus == 0:
        # 如果失败很多次，就不要启动了
        if process.max_fail_count is not None and \
                process.max_fail_count < process.fail_count:
            logging.warning("%s连续失败次数超过%s次，不再重试" % (
                process.name, process.max_fail_count))
            process.pstatus = 4
            process.update_time = tools.get_now_time()
            process.save()
            return False
        best_machine = get_best_machine(process)

        ret = remote_start(process.id, best_machine)
        if ret:
            logging.info("进程%s的启动请求已发出" % process.name)
            return True
        else:
            logging.error("进程%s启动失败" % process.name)
            return False

    # 停止
    if cstatus == 0 and pstatus == 2:
        ret = remote_stop(process.id, process.machine)
        if ret:
            logging.info("进程%s的停止请求已发出" % process.name)
            return True
        else:
            logging.error("进程%s停止失败" % process.name)
            return False

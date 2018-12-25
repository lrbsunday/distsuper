#!-*- encoding: utf-8 -*-
import time
import logging
from distsuper.api.server import start_process, stop_process
from distsuper.models.models import Process
from distsuper.common.tools import retry


@retry(sleep_time=3, logger=logging)
def diff():
    while True:
        # todo
        # 需要启动的
        # need_to_start()

        # 锁超时的
        # lock_timeout()

        # 休息
        time.sleep(5)


def need_to_start():
    """ autorestart=True而且长时间没有touchdb的
    :return:
    """
    processes = Process.select().where(
        Process.status == 1,
        Process.touch_timeout < int(time.time()),
        Process.lock == 0
    )
    for process in processes:
        start_process(program_id=process.id)


def lock_timeout():
    """ 长时间上锁，以数据库状态为准
    :return:
    """
    processes = Process.select().where(
        Process.lock == 1,
        Process.lock_time + 60 < int(time.time())
    )
    for process in processes:
        if process.status == 1:
            start_process(program_id=process.id)
        else:
            stop_process(program_id=process.id)

#!-*- encoding: utf-8 -*-
import time
import logging

from distsuper.api.server import restart_process
from distsuper.models.models import Process
from distsuper.common import tools
from distsuper.common.constant import STATUS

logger = logging.getLogger("diff")


@tools.retry(sleep_time=3)
def diff():
    while True:
        logger.info("diff")
        # 需要重新启动的
        need_to_restart()

        # 处于STARTING或STOPPING状态超过一定时间的
        need_to_reset_status()

        # 休息
        time.sleep(5)


def need_to_restart():
    """ auto_restart=True而且长时间没有touchdb的
    :return:
    """
    # 超时没有touch db的
    processes = Process.select().where(
        Process.status == STATUS.RUNNING,
        Process.auto_restart == 1,
        Process.timeout_timestamp < int(time.time())
    )
    for process in processes:
        if Process.update(status=STATUS.EXITED) \
                .where(Process.id == process.id,
                       Process.status == STATUS.RUNNING,
                       Process.auto_restart == 1,
                       Process.timeout_timestamp < int(time.time())) \
                .execute() == 1:
            logger.info("重启进程%s" % process.id)
            restart_process(program_id=process.id)

    # 处于exited状态的
    processes = Process.select().where(
        Process.status == STATUS.EXITED,
        Process.auto_restart == 1
    )
    for process in processes:
        if Process.update(status=STATUS.EXITED) \
                .where(Process.id == process.id,
                       Process.status == STATUS.EXITED,
                       Process.auto_restart == 1) \
                .execute() == 1:
            logger.info("重启进程%s" % process.id)
            restart_process(program_id=process.id)


def need_to_reset_status():
    cnt = Process.update(status=STATUS.RUNNING) \
        .where(Process.status == STATUS.STOPPING,
               Process.update_time + 60 < int(time.time())) \
        .execute()
    if cnt:
        logger.info("重置了%s个进程的状态为RUNNING" % cnt)

    cnt = Process.update(status=STATUS.STOPPED) \
        .where(Process.status == STATUS.STARTING,
               Process.update_time + 60 < int(time.time())) \
        .execute()
    if cnt:
        logger.info("重置了%s个进程的状态为STOPPED" % cnt)

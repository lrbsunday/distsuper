#!-*- encoding: utf-8 -*-
import sys
import logging

from distsuper import CONFIG
from distsuper.common import tools
from distsuper.models.models import Process
from distsuper.main.operate_db import create_or_update_program


def delete_expire_data(start_time):
    fields = dict(cstatus=0,
                  update_time=tools.get_now_time())
    Process.update(**fields) \
        .where(Process.update_time < start_time,
               Process.source == 'file').execute()


def load_config():
    start_time = tools.get_now_time()

    for section_name in CONFIG.programs:
        program_name = section_name.split(':')[1]
        command = CONFIG.config.get(section_name, 'command')
        if not command:
            logging.error("程序%s的启动命令不能为空" % section_name)
        auto_start = CONFIG.config.getboolean(section_name, 'auto_start',
                                              fallback=True)
        auto_restart = CONFIG.config.getboolean(section_name, 'auto_restart',
                                                fallback=True)
        machines = CONFIG.config.get(section_name, 'machines',
                                     fallback='')
        directory = CONFIG.config.get(section_name, 'directory',
                                      fallback=None)
        environment = CONFIG.config.get(section_name, 'environment',
                                        fallback=None)
        touch_timeout = CONFIG.config.getint(section_name, 'touch_timeout',
                                             fallback=10 * 365 * 24 * 3600)
        max_fail_count = CONFIG.config.getint(section_name, 'max_fail_count',
                                              fallback=3)
        stdout_logfile = CONFIG.config.get(section_name, 'stdout_logfile',
                                           fallback='')
        stderr_logfile = CONFIG.config.get(section_name, 'stderr_logfile',
                                           fallback='')
        create_or_update_program(program_name, command, machines,
                                 directory, environment,
                                 auto_start, auto_restart, touch_timeout,
                                 max_fail_count, 'file',
                                 stdout_logfile, stderr_logfile)

    delete_expire_data(start_time)

#!-*- encoding: utf-8 -*-
import os
import subprocess
import logging
import sys

import click

from distsuper.scripts.common import check_config
from distsuper.main.remote import remote_check
from distsuper import CONFIG


@click.group()
def main():
    check_config()


@main.command()
@click.option('--force', '-f', is_flag=True)
def start(force=False):
    if not force and os.path.exists(CONFIG.SERVERHTTP.pid_file_path):
        logging.warning("当前目录下存在pidfile，请确保server没有启动，"
                        "并删除pidfile后再试")
        sys.exit(-1)
    args = 'uwsgi --ini {}:server-http ' \
           '--mule=distsuper.main.diff:diff'.format(CONFIG.config_file_path) \
        .split()
    env = os.environ
    env.update({'DISTSUPER_MODULE_NAME': 'server'})
    ret = subprocess.Popen(args, env=env).wait()
    if ret == 0 and remote_check(CONFIG.COMMON.server, CONFIG.SERVERHTTP.port,
                                 'STARTING'):
        logging.info("server启动成功")
    else:
        logging.info("server启动失败")


@main.command()
@click.option('--force', '-f', is_flag=True)
def stop(force=False):
    if not force and not os.path.exists(CONFIG.SERVERHTTP.pid_file_path):
        logging.warning("找不到pidfile，请确保server已启动，"
                        "并在pidfile所在路径下执行该命令")
        sys.exit(-1)
    args = 'uwsgi --stop {}'.format(CONFIG.SERVERHTTP.pid_file_path).split()
    ret = subprocess.Popen(args).wait()
    if ret == 0 and not remote_check(CONFIG.COMMON.server,
                                     CONFIG.SERVERHTTP.port,
                                     'STOPPING'):
        logging.info("server停止成功")
    else:
        logging.info("server停止失败")


@main.command()
@click.option('--force', '-f', is_flag=True)
def restart(force=False):
    if not force and not os.path.exists(CONFIG.SERVERHTTP.pid_file_path):
        logging.warning("找不到pidfile，请确保server已启动，"
                        "并在pidfile所在路径下执行该命令")
        sys.exit(-1)
    args = 'uwsgi --reload {}'.format(CONFIG.SERVERHTTP.pid_file_path).split()
    ret = subprocess.Popen(args).wait()
    if ret == 0 and remote_check(CONFIG.COMMON.server, CONFIG.SERVERHTTP.port,
                                 'STARTING'):
        logging.info("server重启成功")
    else:
        logging.info("server重启失败")


if __name__ == '__main__':
    main()

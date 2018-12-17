#!-*- encoding: utf-8 -*-
import os
import sys
import logging

import click

from distsuper.scripts.common import check_config
from distsuper.interface import api

"""
distsuperctl start {id}
distsuperctl stop {id}
distsuperctl restart {id}
distsuperctl status
distsuperctl init db [--drop]  # 初始化数据库
distsuperctl init config  # 初始化配置文件
"""


@click.group()
def main():
    pass


@main.command()
@click.argument('program_id')
def start(program_id):
    if api.start_process(program_id=program_id):
        logging.info("进程启动成功")
    else:
        logging.info("进程启动失败")


@main.command()
@click.argument('program_id')
def stop(program_id):
    if api.stop_process(program_id=program_id):
        logging.info("进程停止成功")
    else:
        logging.info("进程停止失败")


@main.command()
@click.argument('program_id')
def restart(program_id):
    if api.restart_process(program_id=program_id):
        logging.info("进程重启成功")
    else:
        logging.info("进程重启失败")


@main.command()
def status():
    processes = api.get_process()

    results = []
    for process in processes:
        name = process["name"]
        _status = process["status"]
        machine = 'machine:' + process.machine if _status else ''
        pid = 'pid:' + str(process.pid) if _status == 1 else ''
        start_time = process.create_time.strftime(
            "%Y-%m-%dT%H:%M:%S") if _status == 1 else ''
        command = process["command"]

        results.append([str(process.id), name, _status,
                        machine, pid, start_time, command])

    if results:
        templates = []
        for i in range(7):
            max_length = max(len(result[i]) for result in results)
            templates.append("%{}s".format(max_length))

        for result in results:
            print('\t'.join([template % field
                             for field, template in
                             zip(result, templates)]))


@main.command()
@click.argument('obj',
                type=click.Choice(['db', 'config', 'all']))
@click.argument('path', default='.')
@click.option('--force', '-f', is_flag=True)
@click.option('--drop', '-d', is_flag=True)
def init(obj, path, force=False, drop=False):
    if obj == 'db':
        check_config()
        init_db(drop)
    elif obj == 'config':
        init_config(force, path)


def init_config(force, path):
    orig_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  os.path.pardir,
                                  'configure', 'distsuper.ini')
    dest_file_path = '%s/distsuper.ini' % path
    if os.path.exists(dest_file_path) and not force:
        logging.warning('distsuper.ini已存在, 如需覆盖请使用-f/--force选项')
        sys.exit(-1)
    else:
        os.system("cp -f %s %s" % (orig_file_path, dest_file_path))


def init_db(drop):
    from distsuper import CONFIG
    from distsuper.models import create_database, drop_database, database
    from distsuper.models.models import Process

    if drop:
        drop_database(CONFIG.DATABASE.db)

    create_database(CONFIG.DATABASE.db)
    database.create_tables([Process])


if __name__ == '__main__':
    main()

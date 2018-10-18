#!-*- encoding: utf-8 -*-
import os
import sys
import logging

import click

from distsuper.scripts.common import check_config


@click.group()
def main():
    pass


@main.command()
@click.argument('program_id')
def start(program_id):
    from distsuper.interface.shell import start_process_by_shell

    start_process_by_shell(program_id, wait=True)


@main.command()
@click.argument('program_id')
def stop(program_id):
    from distsuper.interface.shell import stop_process_by_shell

    stop_process_by_shell(program_id, wait=True)


@main.command()
@click.argument('program_id')
def restart(program_id):
    from distsuper.interface.shell import restart_process_by_shell

    restart_process_by_shell(program_id, wait=True)


@main.command()
def status():
    from distsuper.interface.shell import get_status_by_shell

    get_status_by_shell()


@main.command()
def load():
    from distsuper.main.load import load_config

    load_config()


@main.command()
@click.argument('obj',
                type=click.Choice(['db', 'config', 'all']))
@click.argument('path', default='.')
@click.option('--force', '-f', is_flag=True)
def init(obj, path, force=False):
    if obj == 'db':
        check_config()
        init_db()
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


def init_db():
    from distsuper import CONFIG
    from distsuper.models import create_database, drop_database
    drop_database(CONFIG.DB.db)
    create_database(CONFIG.DB.db)
    from distsuper.models import database
    from distsuper.models.models import Process
    database.drop_tables([Process], safe=True)
    database.create_tables([Process])


if __name__ == '__main__':
    main()

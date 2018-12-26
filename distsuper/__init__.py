#!-*- encoding: utf-8 -*-
import os
import sys
import configparser

from distsuper.common import tools

if sys.version_info.major == 2:
    # noinspection PyUnresolvedReferences
    reload(sys)
    # noinspection PyUnresolvedReferences
    sys.setdefaultencoding('utf-8')

config_file_path = './distsuper.ini'
if not os.path.exists(config_file_path):
    config_file_path = '/etc/distsuper.ini'

config = configparser.ConfigParser()
config.read(config_file_path, encoding='utf-8')


class CONFIG(object):
    config_file_path = config_file_path
    config = config
    programs = []

    class DATABASE(object):
        host = config.get('database', 'host', fallback='localhost')
        port = config.getint('database', 'port', fallback=3306)
        user = config.get('database', 'user', fallback='root')
        password = config.get('database', 'password', fallback='')
        db = config.get('database', 'db', fallback='')

    class DISTSUPERCTL(object):
        host = config.get('distsuperctl', 'host', fallback='localhost')
        port = config.get('distsuperctl', 'port', fallback='3378')

    class DISTSUPERAGENT(object):
        pid_file_path = config.get('distsuperagent', 'pidfile',
                                   fallback='./agent.pidfile')
        port = config.get('distsuperagent', 'http',
                          fallback=':3379').split(':')[-1]

    class DISTSUPERD(object):
        pid_file_path = config.get('distsuperd', 'pidfile',
                                   fallback='./agent.pidfile')
        port = config.get('distsuperd', 'http',
                          fallback=':3378').split(':')[-1]


for section in config.sections():
    if section.startswith("program:"):
        CONFIG.programs.append(section)

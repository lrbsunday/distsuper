import os
import logging
import configparser
from distsuper.common import tools

tools.get_logger(None, None, level=logging.INFO)
tools.get_logger('peewee', None, level=logging.DEBUG)

config_file_path = './distsuper.ini'
if not os.path.exists(config_file_path):
    config_file_path = '/etc/distsuper.ini'

config = configparser.ConfigParser()
config.read(config_file_path)


class COMMON(object):
    server = config.get('common', 'server', fallback='localhost')
    agent = config.get('common', 'agent', fallback='localhost')
    server_log_file_path = config.get('server', 'server_log_file_path',
                                      fallback='./logs/distsuper.server.log')
    agent_log_file_path = config.get('agent', 'agent_log_file_path',
                                     fallback='./logs/distsuper.agent.log')


class DB(object):
    host = config.get('db', 'host', fallback='localhost')
    port = config.getint('db', 'port', fallback=3306)
    user = config.get('db', 'user', fallback='root')
    password = config.get('db', 'password', fallback='')
    db = config.get('db', 'db', fallback='')


class AGENTHTTP(object):
    pid_file_path = config.get('agent-http', 'pidfile',
                               fallback='./agent.pidfile')
    port = config.get('agent-http', 'http',
                      fallback=':3379').split(':')[-1]


class SERVERHTTP(object):
    pid_file_path = config.get('server-http', 'pidfile',
                               fallback='./agent.pidfile')
    port = config.get('server-http', 'http',
                      fallback=':3378').split(':')[-1]


class CONFIG(object):
    config_file_path = config_file_path
    config = config
    programs = []

    COMMON = COMMON
    DB = DB
    AGENTHTTP = AGENTHTTP
    SERVERHTTP = SERVERHTTP


for section in config.sections():
    if section.startswith("program:"):
        CONFIG.programs.append(section)
import os
import logging
import configparser
from distsuper.common import tools

tools.get_logger(None, None, level=logging.INFO)

config_file_path = './distsuper.ini'
if not os.path.exists(config_file_path):
    config_file_path = '/etc/distsuper.ini'

config = configparser.ConfigParser()
config.read(config_file_path)


class DB(object):
    host = config.get('db', 'host', fallback='localhost')
    port = config.getint('db', 'port', fallback=3306)
    user = config.get('db', 'user', fallback='root')
    password = config.get('db', 'password', fallback='')
    db = config.get('db', 'db', fallback='')


class HTTP(object):
    pid_file_path = config.get('http', 'pidfile', fallback='./pidfile')


class AGENT(object):
    log_file_path = config.get('distsuperagent', 'log_file_path',
                               fallback='./logs/distsuperagent.log')


class CONFIG(object):
    config_file_path = config_file_path
    config = config
    programs = []
    groups = []
    DB = DB
    HTTP = HTTP
    AGENT = AGENT


for section in config.sections():
    if section.startswith("program:"):
        CONFIG.programs.append(section)
    if section.startswith("group:"):
        CONFIG.groups.append(section)

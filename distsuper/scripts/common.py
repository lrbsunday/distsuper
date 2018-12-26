#!-*- encoding: utf-8 -*-
import os
import re
import sys
from distsuper import CONFIG


def check_config():
    if os.path.exists(CONFIG.config_file_path):
        pass
    else:
        print("distsuper.ini不存在，请先执行distsuperctl init config初始化")
        sys.exit(-1)


def get_pid(program_id):
    get_pid_command = """ ps aux | 
                          grep dswrapper | 
                          grep %s | 
                          grep -v grep | 
                          awk '{print $2}' """ % program_id
    get_pid_command = get_pid_command.replace("\n", "")
    get_pid_command = re.sub(r" +", " ", get_pid_command)
    for pid in os.popen(get_pid_command):
        return int(pid.strip())
    return 0
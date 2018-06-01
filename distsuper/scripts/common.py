#!-*- encoding: utf-8 -*-
import os
import sys
from distsuper import CONFIG


def check_config():
    if os.path.exists(CONFIG.config_file_path):
        pass
    else:
        print("distsuper.ini不存在，请先执行distsuperctl init config初始化")
        sys.exit(-1)

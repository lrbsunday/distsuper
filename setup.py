#!-*- encoding: utf-8 -*-
import logging
import os
import ssl
from setuptools import setup, find_packages

# noinspection PyProtectedMember
ssl._create_default_https_context = ssl._create_unverified_context


# with open('requirements.txt') as fp:
#     requirements = fp.readlines()


def execute_commands(commands):
    for command in commands:
        command = command.strip()
        if not command:
            continue
        ret = os.system(command)
        if ret != 0:
            logging.warning(u"%s命令执行失败，退出码为%s" % (command, ret >> 16))
            raise Exception(u"%s命令执行失败，退出码为%s" % (command, ret >> 16))


if os.path.exists('dist'):
    execute_commands(["rm -rf dist"])

setup(
    name="distsuper",
    version="0.2.27",
    description=(
        '仿照supervisor的功能实现的一个分布式进程监控工具，支持跨机器的进程失效转移'
    ),
    packages=find_packages(exclude=[]),
    author='lrbsunday',
    author_email='272316131@qq.com',
    maintainer='lrbsunday',
    maintainer_email='272316131@qq.com',
    url='https://github.com/lrbsunday/distsuper',
    package_data={
        'distsuper.configure': ['distsuper.ini'],
    },
    entry_points={
        'console_scripts': [
            'distsuperctl = distsuper.scripts.distsuperctl:main',
            'distsuperd = distsuper.scripts.distsuperd:main',
            'distsuperagent = distsuper.scripts.distsuperagent:main',
            'dswrapper = distsuper.scripts.wrapper:main',
        ]
    },
    install_requires=['pymysql',
                      'requests',
                      'uwsgi',
                      'flask',
                      'peewee',
                      'click',
                      'configparser']
)

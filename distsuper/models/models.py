#!-*- encoding: utf-8 -*-
from peewee import *
from . import BaseModel


class Process(BaseModel):
    class Meta:
        db_table = "process"

    source = CharField(max_length=8,
                       help_text="配置来源：file/api，不能修改其他来源创建的program")
    name = CharField(max_length=128, unique=True,
                     help_text="进程名称")
    command = TextField(help_text="启动命令")
    directory = CharField(max_length=256, null=True,
                          help_text="启动路径")
    environment = CharField(max_length=256, null=True,
                            help_text="环境变量")
    machines = CharField(max_length=256,
                         help_text="失效转移的机器列表")
    auto_start = BooleanField(default=True,
                              help_text="是否自动启动")
    auto_restart = BooleanField(default=True,
                                help_text="是否自动重启")
    stdout_logfile = CharField(max_length=256,
                               default='',
                               help_text="标准输出文件")
    stderr_logfile = CharField(max_length=256,
                               default='',
                               help_text="标准错误文件")
    touch_timeout = IntegerField(default=10 * 365 * 24 * 3600,
                                 help_text="进程保活时间")
    max_fail_count = IntegerField(default=3, null=True,
                                  help_text="默认最大失败次数，失败第4次时将不会重试")
    cstatus = IntegerField(default=1,
                           help_text="0 不启动, 1 可启动")

    machine = CharField(max_length=128, default='',
                        help_text="运行在哪台机器上machine")
    pid = IntegerField(default=0,
                       help_text="进程ID")
    pstatus = IntegerField(default=0,
                           help_text="0 待启动, 1 启动中, 2 运行中, 3 停止中, "
                                     "4 失败结束, 5 成功结束")

    fail_count = IntegerField(default=0,
                              help_text="失败次数")
    timeout_timestamp = IntegerField(default=0x7FFFFFFF,
                                     help_text="超时时间")

    config_updated = IntegerField(default=1,
                                  help_text="表示配置有更新，0 表示配置无更新")
    config_hash = CharField(max_length=32, default='',
                            help_text="配置hash值，据此判断配置更新时是否需要重启，"
                                      "md5(command,machines,touch_timeout)")


class Test(BaseModel):
    class Meta:
        db_table = "test"

    name = CharField(max_length=128, unique=True)
    status = IntegerField(default=0)

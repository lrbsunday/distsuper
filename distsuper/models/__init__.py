#!-*- encoding: utf-8 -*-
from datetime import datetime

from peewee import *
import pymysql

from distsuper import CONFIG

# peewee3.0已经去除了RetryOperationalError
from peewee import MySQLDatabase as MySQLDB


database = MySQLDB(
    CONFIG.DB.db,
    host=CONFIG.DB.host,
    port=CONFIG.DB.port,
    user=CONFIG.DB.user,
    password=CONFIG.DB.password,
)


def get_conn():
    connection = pymysql.connect(host=CONFIG.DB.host,
                                 user=CONFIG.DB.user,
                                 password=CONFIG.DB.password,
                                 charset='utf8',
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection


def create_database(db):
    sql = """CREATE DATABASE IF NOT EXISTS %s 
            DEFAULT CHARSET utf8 COLLATE utf8_general_ci;""" % db
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(sql)


def drop_database(db):
    sql = """DROP DATABASE IF EXISTS %s""" % db
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(sql)


class BaseModel(Model):
    """模型基类，为每个模型补充创建时间，更新时间"""

    class Meta:
        database = database

    id = PrimaryKeyField()
    create_time = DateTimeField(index=True,
                                default=datetime.now)  # 创建时间
    update_time = DateTimeField(index=True,
                                default=datetime.now)  # 更新时间

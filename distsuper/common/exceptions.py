#!-*- encoding: utf-8 -*-
import json


class SimpleEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__str__'):
            return str(obj)
        else:
            return ''


class BaseExc(Exception):
    code = 0
    msg = ""
    dmsg = ""
    data = None

    def __init__(self, dmsg=None, data=None):
        if data is not None:
            self.data = data
        if dmsg is not None:
            self.dmsg = dmsg

    def __str__(self):
        r_dict = {
            "code": self.code,
            "msg": self.msg,
            "dmsg": self.dmsg
        }
        if self.data is not None:
            r_dict["data"] = self.data
        return json.dumps(r_dict, cls=SimpleEncoder, ensure_ascii=False)


class NoException(BaseExc):
    code = 200
    msg = "成功"


class AuthException(BaseExc):
    code = 300
    msg = "权限校验错误"


class NotLoginException(BaseExc):
    code = 301
    msg = "用户未登录"


class NoAuthException(BaseExc):
    code = 302
    msg = "用户无权限"


class ClientException(BaseExc):
    code = 400
    msg = "客户端未知错误"


class ResourceException(BaseExc):
    code = 401
    msg = "资源不存在"


class UniqueException(BaseExc):
    code = 402
    msg = "唯一键重复"


class ParamTypeException(BaseExc):
    code = 411
    msg = "参数类型不合法"


class ParamValueException(BaseExc):
    code = 412
    msg = "参数值不合法"


class LackParamException(BaseExc):
    code = 413
    msg = "参数不全"


class ServerException(BaseExc):
    code = 500
    msg = "服务端未知错误"


class MySQLDBException(BaseExc):
    code = 501
    msg = "mysql数据库未知异常"


class ProcessStatusException(BaseExc):
    code = 511
    msg = "进程状态不正确"


class DBConflictException(BaseExc):
    code = 512
    msg = "数据库状态冲突（乐观锁）"


class DBIntegrityException(BaseExc):
    code = 513
    msg = "数据库完整性错误, 请稍后重试"


class AlreadExistsException(BaseExc):
    code = 514
    msg = "数据记录已存在"


class DuplicateOperationException(BaseExc):
    code = 515
    msg = "重复操作"


class NoConfigException(BaseExc):
    code = 521
    msg = "配置不存在"


class NoGroupException(BaseExc):
    code = 522
    msg = "机器组不存在"


# 内部使用
class RetryException(BaseExc):
    pass

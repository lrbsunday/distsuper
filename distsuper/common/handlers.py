#!-*- encoding: utf-8 -*-
import functools
import time
import json
import uuid
import logging
import traceback

from flask import request
import peewee

from distsuper.common.tools import ComplexEncoder
from . import exceptions

logger = logging.getLogger('interface')


def get_request_info():
    request_info = dict()

    # url args
    args = request.args
    for key in args:
        request_info[key] = args[key]

    # raw data
    # noinspection PyBroadException
    try:
        data = request.get_json()
        if data is not None:
            request_info.update(data)
    except Exception:
        pass

    # form data
    form = request.form
    if form:
        for key in form:
            request_info[key] = form[key]

    return request_info


def request_pre_handler():
    def __request_pre_handler(func):
        @functools.wraps(func)
        def wrapper():
            start_time = time.time()
            api_name = func.__name__
            _uuid = str(uuid.uuid4())
            request_info = get_request_info()
            req_str = json.dumps(request_info, ensure_ascii=False)
            logger.info('%s(%s) - request: %s' % (_uuid, api_name, req_str))

            # noinspection PyBroadException
            try:
                r_dict = func(request_info)
            except peewee.PeeweeException:
                logger.info('%s(%s) - error: %s' % (_uuid, api_name,
                                                    traceback.format_exc()))
                res_str = str(exceptions.MySQLDBException())
            except exceptions.BaseExc as e:
                logger.info('%s(%s) - error: %s' % (_uuid, api_name, str(e)))
                res_str = str(e)
            except Exception:
                logger.info('%s(%s) - error: %s' % (_uuid, api_name,
                                                    traceback.format_exc()))
                res_str = str(exceptions.ServerException())
            else:
                res_str = json.dumps({"code": 200,
                                      "msg": "",
                                      "dmsg": "",
                                      "data": r_dict},
                                     cls=ComplexEncoder,
                                     ensure_ascii=False)

            waste_time = time.time() - start_time
            logger.info('%s(%s) - response(%.2f): %s' % (_uuid, api_name,
                                                         waste_time, res_str))
            return res_str, 200, {'Content-Type': 'application/json'}

        return wrapper

    return __request_pre_handler

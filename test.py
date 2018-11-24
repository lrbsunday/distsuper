# -*- coding: utf-8 -*-
# @Time    : 2018/8/17 上午10:10
# @Author  : WangJuan
# @File    : test_case.py
import allure
import pytest


@allure.feature('test_module_01')
def test_case_01():
    """
    用例描述：Test case 01
    """
    assert 0


@allure.feature('test_module_02')
def test_case_02():
    """
    用例描述：Test case 02
    """
    assert 0 == 0


@allure.feature('test_module_02')
def test_case_02():
    """
    用例描述：Test case 02
    """
    assert 0 == 0


@allure.feature('test_module_03')
def test_case_03():
    """
    用例描述：Test case 02
    """
    assert 1 == 1


if __name__ == '__main__':
    pytest.main(['-s', '-q'])

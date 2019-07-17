# !/usr/bin/env python
# encoding: utf-8

"""
file: spider.py
time: 2019/6/19 10:58
Author: twy
contact: 19983195362
des: 爬虫的常用工具，提供Redis实例封装，网页解析等功能
"""

import fake_useragent
import redis
import re
from lxml import etree


class Utils(object):

    def __init__(self, redis_con='localhost', redis_port=6379):
        self.root = ""
        _redis_pool = redis.ConnectionPool(host=redis_con, port=redis_port)
        self.redis_con = redis.StrictRedis(connection_pool=_redis_pool)

    def _get_xpath_root(self, html):
        self.root = etree.HTML(html)

    def parse_html_with_xpath(self, xpath):
        return self.root.xpath(xpath) if len(self.root.xpath(xpath)) > 1 else self.root.xpath(xpath)[0]

    @staticmethod
    def gen_random_ua(num=300):
        _ua = fake_useragent.FakeUserAgent()
        _ua_list = [_ua.random for i in range(num)]
        return _ua_list

    @staticmethod
    def regx_str(re_str, regx):
        return re.search(regx, re_str).group(1) if re_str and regx and re.search(regx, re_str) else None


utilsMixin = Utils
utils = Utils()

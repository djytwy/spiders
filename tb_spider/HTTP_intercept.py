# !/usr/bin/env python
# encoding: utf-8

"""
file: HTTP_intercept.py
time: 2019/6/19 13:31
Author: twy
contact: 19983195362
des: 拦截并篡改淘宝的判断自动化浏览器的js文件
"""

from mitmproxy import http, ctx

TARGET_URL = 'https://g.alicdn.com/secdev/sufei_data/3.7.1/index.js'
# 在js中设置webdriver为false
INJECT_TEXT = 'Object.defineProperties(navigator,{webdriver:{get:() => false}});'


def response(flow: http.HTTPFlow):
    if flow.request.url.startswith(TARGET_URL):
        flow.response.text = INJECT_TEXT + flow.response.text
        ctx.log.info('注入成功！')

    if 'um.js' in flow.request.url or '115.js' in flow.request.url:
        # 屏蔽检测
        ctx.log.info(flow.request.url)
        flow.response.text = flow.response.text + 'Object.defineProperties(navigator,{webdriver:{get:() => false}})'



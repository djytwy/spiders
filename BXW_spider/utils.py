# !user/bin/env 
# -*- coding: utf-8 -*-
# Author: twy

import random
import fake_useragent
import redis
from lxml import etree
from datetime import datetime as dt

class Utils(object):

    def __init__(self, burst, redis_class):
        try:
            """
            fake_useragent 可能会缓存不下来请求头
            """
            ua = fake_useragent.UserAgent()
            self.ua_list = [ua.random for i in range(300)]
        except Exception as e:
            self.ua_list = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 SE 2.X MetaSr 1.0",
                "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36 QIHU 360EE"
            ]
        self.cookies_pool = [
            "suid=4488859312; __admx_track_id=bvRi7-b_5hNR95FRxYkgzQ; __admx_track_id.sig=n3iY8rS_b02OZw4dpBWfh6VeTNA; __trackId=154588196450645; __uuid=115458819649530.a187a; _ga=GA1.2.1818966348.1545881966; agreedUserPrivacy=1; __chat_udid=ae091516-ee0b-4a34-96e2-539c81faa044; __s=f2cqnm56ml93p8vm56sbu7ui80; Hm_lvt_5a727f1b4acc5725516637e03b07d3d2=1553168304,1553220219,1553222217; __city=chongqing; __area2=tongwei; _gid=GA1.2.989251167.1553479553; _auth_redirect=http%3A%2F%2Fchongqing.baixing.com%2Fershoufang%2F%3Fsrc%3Dtopbar; __sense_session_pv=1; Hm_lpvt_5a727f1b4acc5725516637e03b07d3d2=1553517296; _gat=1"
        ]
        self.redis_con = redis.ConnectionPool(
            host="xxxxxxx", port=6379, db=12)
        self.r_db = redis.StrictRedis(connection_pool=self.redis_con)
        self.proxy_list = []
        self.burst = burst
        self.redis_class = redis_class
        self.now = dt.now()
        self.today = "{0}-{1}-{2}".format(self.now.year, self.now.month, self.now.day)

    def get_headers(self):
        headers = {
            "User-Agent": random.choice(self.ua_list)
        }
        return headers

    def get_cookies(self):
        cookie_str = random.choice(self.cookies_pool)
        cookies = {}
        for i in cookie_str.split(";"):
            each = i.split("=")
            cookies[each[0].replace(" ", "")] = each[1].replace(" ", "")
        return cookies

    @staticmethod
    def parse_html(html):
        return etree.HTML(html, etree.HTMLParser(encoding='utf-8'))

    def get_proxy(self, r, proxy=None):
        import json
        html = r.get("http://xxxxxxx/get_proxy_ip")
        new_proxy = {"requests":{"http": "http://{0}".format(json.loads(html.text)["ip"])},
                      "aiohttp":"http://{0}".format(json.loads(html.text)["ip"])}
        if proxy:
            self.proxy_list.remove(proxy)
        self.proxy_list.append(new_proxy)

    def check_proxy(self):
        import requests
        import time
        r = requests.session()
        if self.proxy_list:
            for each in self.proxy_list:
                try:
                    response = r.get("http://china.baixing.com/", proxies = each["requests"],timeout=10)
                    if response.status_code != 200:
                        print("切换代理！！！！")
                        self.get_proxy(r, each)
                except Exception as e:
                    print("切换代理！！！！")
                    self.get_proxy(r , each)
        else:
            for i in range(0, int((self.burst + 1)/5)):
                self.get_proxy(r)
        time.sleep(2)
        print("sleep {0} sec .....".format(2))

    def write_to_redis(self):
        """
        生成所有的求租求购的列表页数据第一页
        """
        with open("baixing_urls.txt", "r") as f:
            file = f.read()
            file = file.split(",")
            for i in file:
                i = i.replace("'", "").replace(" ", "")
                url = "http://{0}.baixing.com/qiufang/m178892/".format(i)
                url2 = "http://{0}.baixing.com/qiufang/m178893/".format(i)
                self.r_db.lpush(
                    "{0}:url_list".format(
                        self.redis_class), url)
                self.r_db.lpush(
                    "{0}:url_list".format(
                        self.redis_class), url2)

    def get_urls(self):
        url_list = self.r_db.lrange(
            "{0}:url_list".format(
                self.redis_class), 0, self.burst)
        self.r_db.ltrim(
            "{0}:url_list".format(
                self.redis_class), self.burst + 1, -1)
        re_url = []
        for i in url_list:
            if type(i) == bytes:
                re_url.append(i.decode())
            else:
                re_url.append(i)
        return re_url

    def add_data(self):
        if self.judge_write():
            self.del_yesterday_data()
            self.write_to_redis()

    def judge_write(self):
        t = "{0}-{1}-{2}".format(dt.today().year, dt.today().month, dt.today().day)
        return self.r_db.hset('{0}:flag'.format(self.redis_class), t, "crawled")

    def del_yesterday_data(self):
        self.r_db.delete("{0}:new_data".format(self.redis_class))
        self.r_db.delete("{0}:url_list".format(self.redis_class))

Mixin_utils = Utils
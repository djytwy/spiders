# !/usr/bin/env python
# encoding: utf-8

"""
file: http_aioget.py
time: 2019/6/19 14:47
Author: twy
contact: 19983195362
des: 获取图片的异步请求类
"""

import aiohttp
import asyncio
import random
import time
import json
from spider.utils import utilsMixin


class HttpAioget(utilsMixin):
    def __init__(self, burst=100):
        super().__init__()
        self.burst = burst
        self.headers_list = [{"User-Agent": random.choice(self.gen_random_ua())}]

    async def aioget(self, title_url):
        _title = list(title_url.keys())[0]
        _url = list(title_url.values())[0]
        async with aiohttp.ClientSession() as session:
            async with session.get(_url, headers=random.choice(self.headers_list)) as response:
                _img_data = await response.read()
                # crawled_url是一个用于去重的哈希
                self.redis_con.hset("crawled_url", _url, random.randint(0, 123456789))
                self.redis_con.hset("img_data_list", _title, _img_data)

    def _http_get(self, url_list):
        try:
            loop = asyncio.get_event_loop()
            task_list = [asyncio.ensure_future(self.aioget(url)) for url in url_list]
            loop.run_until_complete(asyncio.wait(task_list))
        except Exception as e:
            print(e)

    def run(self):
        print("http请求进程启动.......")
        while True:
            _to_crawl_list = self.redis_con.lrange("to_crawl_data", 0, self.burst)
            if _to_crawl_list:
                _url_list = []
                for each in _to_crawl_list:
                    _title_url = json.loads(each)
                    _title = list(_title_url.keys())[0]
                    _url = list(_title_url.values())[0]
                    if not self.redis_con.hget("crawled_url", _url):
                        _url_list.append({_title: _url})
                if self.redis_con.llen("to_crawl_data") > 1:
                    self.redis_con.ltrim("to_crawl_data", self.burst, -1)
                else:
                    _url = self.redis_con.delete("to_crawl_data")
                self._http_get(_url_list)
            print("http请求休眠5秒！！！！")
            time.sleep(5)


http_aioget = HttpAioget()

if __name__ == "__main__":
    h = HttpAioget()
    h.run()



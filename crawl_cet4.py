# encoding:utf-8
# !/usr/bin/env python
# author: djytwy
# date: 2020-04-19

'''
爬取CET4网站的验证码
使用python 3.7编写， 使用asyncio.run()
'''

import asyncio
import aiohttp
import time
import random
import redis
import fake_useragent
import threading
import re

class Tools:
    '''
    工具类，主要是Redis连接,ua
    '''
    def __init__(self,redis_host,redis_port):
        _redis_pool = redis.ConnectionPool(host=redis_host,port=redis_port)
        self.redis_con = redis.StrictRedis(connection_pool=_redis_pool)

    @staticmethod
    def gen_random_ua(num=300):
        _ua = fake_useragent.FakeUserAgent()
        _ua_list = [_ua.random for i in range(num)]
        return _ua_list


class CetSpider(Tools):
    '''
    爬虫类
    '''
    def __init__(self, burst, redis_host, redis_port, username_list):
        super().__init__(redis_host=redis_host, redis_port=redis_port)
        self.base_url = 'http://cache.neea.edu.cn/Imgs.do?c=CET&ik='
        self.username_list = username_list
        self.burst = burst
        self.header_list = [{"User-Agent": random.choice(self.gen_random_ua()),
                             'Referer': 'http://cet.neea.edu.cn/cet/'}]

    async def http_get(self, url, redis_key):
        """
        异步请求的方法，整个爬虫的控制端在redis所以最后数据都存Redis
        :param url:
        :param redis_key:
        :return:
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=random.choice(self.header_list)) as response:
                if response.status == 200:
                    _data = await response.read()
                    self.redis_con.lpush(redis_key, _data)

    def gen_url(self):
        """
        生成一级url
        :return:
        """
        _temp_url_list = [
            f'{self.base_url}{random.choice(self.username_list)}&t={random.random()}' for i in range(self.burst)]
        for i in _temp_url_list:
            self.redis_con.lpush('image_name_url_list', i)

    async def gen_image_url(self):
        """
        由一级url去生成二级url
        :return:
        """
        _crawl_urls = self.redis_con.lrange('image_name_url_list', 0, -1)
        self.redis_con.ltrim('image_name_url_list', 0, -1)
        task_list = [self.http_get(url=i.decode(), redis_key='image_url_list') for i in _crawl_urls]
        await asyncio.gather(*task_list)

    async def get_image_data(self):
        """
        由二级url获得图片的数据，存入Redis
        :return:
        """
        _crawl_urls = self.redis_con.lrange('image_url_list', 0, -1)
        self.redis_con.ltrim('image_url_list', 0, -1)
        task_list = [self.http_get(url=f'''http://cet.neea.edu.cn/imgs/{re.search(r'"(.*?)"',i.decode()).group(1)}.png''',
                                   redis_key='image_data_list') for i in _crawl_urls]
        await asyncio.gather(*task_list)

    def crawl_image_url(self):
        """
        爬取一轮之后休眠（下面的都是）
        :return:
        """
        while True:
            asyncio.run(self.gen_image_url())
            print('爬取图片链接线程休眠10秒....')
            time.sleep(10)

    def crawl_image(self):
        while True:
            asyncio.run(self.get_image_data())
            print('获取图片数据线程休眠10秒...')
            time.sleep(10)

    def start_gen_url(self):
        while True:
            self.gen_url()
            print('生成图片链接休眠10秒....')
            time.sleep(10)

    def save_image(self):
        """
        从Redis获取图片数据保存到本地
        :return:
        """
        while True:
            _image_data = self.redis_con.lrange('image_data_list', 0, -1)
            self.redis_con.ltrim('image_data_list', 0, -1)
            str_dic = ['a', 'b', 'c', 'd', 'e', 'f']
            for image in _image_data:
                with open(f'./images/{random.choice(str_dic)}{random.randint(0,10000000)}.png', 'wb') as f:
                    f.write(image)
            print('生成图片链接休眠10秒....')
            time.sleep(10)

    def run(self):
        _gen_image_url = threading.Thread(target=self.crawl_image_url)
        _gen_url = threading.Thread(target=self.start_gen_url)
        _gen_image_data = threading.Thread(target=self.crawl_image)
        _save_image = threading.Thread(target=self.save_image)
        _gen_image_url.start()
        _gen_url.start()
        _gen_image_data.start()
        _save_image.start()
        _gen_image_data.join()
        _save_image.join()
        _gen_image_url.join()
        _gen_url.join()


if __name__ == "__main__":
    username_list = ['372611122107828']
    s = CetSpider(redis_port=8888, redis_host='xxxx', burst=3, username_list=username_list)
    s.run()


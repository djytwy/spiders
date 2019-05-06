#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import redis
import asyncio
import aiohttp
import random
import re
from lxml import etree
import fake_useragent
import time


class Spider_58(object):
    """
    58同城的爬虫，若出现验证码则使用浏览器显示，然后人工输入，获取到改变了的cookies并重新设置进请求
    """
    def __init__(self):
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
        self.redis_con = redis.ConnectionPool(host="xxxxx", port=6379, db=12)
        self.r_db = redis.StrictRedis(connection_pool=self.redis_con)
        self.redis_class = "58"
        self.change_cookie = False
        self.cookies_pool = [
            "f=n; commontopbar_new_city_info=2%7C%E4%B8%8A%E6%B5%B7%7Csh; userid360_xml=D22CC785632D31027525A6084FD5335E; time_create=1556176801575; commontopbar_ipcity=cd%7C%E6%88%90%E9%83%BD%7C0; id58=c5/njVyZ0qAqX2HGAyQlAg==; wmda_uuid=bcb64a473057c252e44db5957546d796; wmda_new_uuid=1; wmda_visited_projects=%3B6333604277682; 58tj_uuid=9a82548d-8cdc-40d8-bfc7-12b5d524fed3; new_uv=1; als=0; xxzl_deviceid=nTJEQceHMJYfZXPrsp57h5CoHNWiaD958mj%2Bfrs5Cp1LkUv11%2F%2Fe2jfSyI6Sjx3c; JSESSIONID=24F6C1ADB25A360FB1965102F7A8DBB9; xzfzqtoken=g0yphhiwlkQiBsgXOCR3CDu2LCBW1EA6wWVGuFxDLKMYuZo3deea12niiQgGVR%2Fkin35brBb%2F%2FeSODvMgkQULA%3D%3D"
        ]
        self.error_url = None
        self.burst = 50
        self.sleep_time_min = 5
        self.sleep_time_max = 12

    def get_header(self):
        headers = {
            "User-Agent": random.choice(self.ua_list)
        }
        return headers

    async def get_html(self,url):
        async with aiohttp.ClientSession(cookies=self.get_cookies()) as session:
            async with session.get(url,headers=self.get_header()) as res:
                if res.status == 200 and not res.history:
                    html = await res.text()
                    self.save_logs(url)
                    self.save_data(url, html)
                else:
                    self.change_cookie = True
                    self.error_url = url
                    self.save_logs(url, True)

    def start_request(self):
        loop = asyncio.get_event_loop()
        tasks = [asyncio.ensure_future(self.get_html(url.decode())) for url in self.get_url_list()]
        loop.run_until_complete(asyncio.wait(tasks))

    def save_data(self, url, html):
        root = self.parse_html(html)
        if "key=" in url:
            url_list = root.xpath('//ul[@class="house-list-wrap"]/li/div[2]/h2/a/@href')
            for each in url_list:
                url_to_save = each.split("?")[0]
                if not self.r_db.hget("{0}:succ_logs".format(self.redis_class), url_to_save):
                    self.r_db.lpush("{0}:url_list".format(self.redis_class), url_to_save)
        else:
            self.save_detail(url, root, html)

    def save_detail(self, url, root, html):
        data = {}
        try:
            data['url'] = url
            data['title'] = root.xpath("//h1/text()")[0]
            data['city'] = re.search("-(.*?)58同城", root.xpath("//title/text()")[0]).group(1)
            data['desc'] = root.xpath('//p[@class="pic-desc-word"]/text()')[0]
            data['phone'] = root.xpath('//p[@class="phone-num"]/text()')[0]
            data['price'] = "{0}万".format(re.search("'MinPrice':'(\d+)'", html).group(1))
        except Exception as e:
            pass
        if 'phone' in data and not self.r_db.hget("{0}:phone_list".format(self.redis_class), data['phone']):
            self.r_db.lpush("{0}:new_data".format(self.redis_class), data)
            self.r_db.lpush("{0}:detail_msg".format(self.redis_class), data)
            self.r_db.hset("{0}:phone_list".format(self.redis_class), data['phone'], 200)
        else:
            self.r_db.lpush("{0}:err_msg".format(self.redis_class), data)

    def save_logs(self, url, redirect=False):
        from datetime import datetime as dt
        if redirect:
            self.r_db.hset("{0}:err_logs".format(self.redis_class), url,302)
            self.r_db.lpush("{0}:url_list".format(self.redis_class), url)
        elif not "key=" in url:
            today = str(dt.today()).split(" ")[0]
            self.r_db.hset("{0}:{1}".format(self.redis_class,today), url, 200)
            self.r_db.hset("{0}:succ_logs".format(self.redis_class), url,200)

    @staticmethod
    def parse_html(html):
        return etree.HTML(html,etree.HTMLParser(encoding="utf-8"))

    def get_url_list(self,once=False):
        from datetime import datetime as dt
        t = "{0}-{1}-{2}".format(dt.today().year, dt.today().month, dt.today().day)
        if once and not self.r_db.hget("{0}:flag".format(self.redis_class), t):
            self.r_db.delete("{0}:new_data".format(self.redis_class))
            url_list = self.r_db.lrange("{0}:url_list_base".format(self.redis_class), 0, -1)
            for each in url_list:
                each = each.decode()
                self.r_db.lpush("{0}:url_list".format(self.redis_class), each)
            self.r_db.hset("{0}:flag".format(self.redis_class), t, "flag")
        else:
            url_list = self.r_db.lrange("{0}:url_list".format(self.redis_class), 0, self.burst)
            self.r_db.ltrim("{0}:url_list".format(self.redis_class), self.burst+1, -1)
            if self.r_db.llen("{0}:url_list".format(self.redis_class)) <= 1:
                self.r_db.delete("{0}:url_list".format(self.redis_class))
                print("58数据已经获取完毕，程序即将结束。。。。")
                time.sleep(3)
                exit()
            return url_list

    def get_cookies(self):
        cookie_str = random.choice(self.cookies_pool)
        cookies = {}
        for i in cookie_str.split(";"):
            each = i.split("=")
            cookies[each[0].replace(" ", "")] = each[1].replace(" ", "")
        return cookies

    def del_ban(self):
        from selenium import webdriver

        driver = webdriver.Chrome()
        driver.get(self.error_url)
        cookies = driver.get_cookies()
        while True:
            try:
                now_cookie = driver.get_cookies()
                if cookies != now_cookie:
                    time.sleep(1)
                    driver.close()
                    cookie_str = ""
                    for i in now_cookie:
                        cookie_str += "{0}={1};".format(i["name"], i["value"])
                    self.cookies_pool = [cookie_str[0:-1]]
                    break
                time.sleep(1)
            except Exception as e:
                print("浏览器关闭")
                break
        self.error_url = None
        self.change_cookie = False

    def start(self):
        import time
        self.get_url_list(True)
        while True:
            if self.change_cookie:
                self.del_ban()
            elif self.r_db.exists("{0}:url_list".format(self.redis_class)):
                self.start_request()
            else:
                break
            sleep_time = random.randint(self.sleep_time_min, self.sleep_time_max)
            print("sleep {0} sec ......".format(sleep_time))
            time.sleep(sleep_time)

    def debug(self):
        self.r_db.delete("58:city_url_list")


if __name__ == "__main__":
    s = Spider_58()
    # s.debug()
    s.start()

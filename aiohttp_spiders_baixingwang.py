# !user/bin/env
# -*- coding: utf-8 -*-
# Author: twy

import redis
import asyncio
import aiohttp
import random
from lxml import etree
import fake_useragent


class Spider(object):
    """
    百姓网爬虫，需要人工干预来解决九宫格验证码问题
    burst:一次的并发请求数量
    change_cookie:用于判断是否需要启动浏览器过九宫格验证码
    sleep_time_min: 发送完burst数量的请求后休眠时间的最小值
    sleep_time_max: 发送完burst数量的请求后休眠时间的最大值
    error_url:跳验证码的url传给浏览器打开
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
        self.redis_con = redis.ConnectionPool(
            host="192.168.200.52", port=6379, db=12)
        self.r_db = redis.StrictRedis(connection_pool=self.redis_con)
        self.cookies_pool = [
            "suid=4488859312; __admx_track_id=bvRi7-b_5hNR95FRxYkgzQ; __admx_track_id.sig=n3iY8rS_b02OZw4dpBWfh6VeTNA; __trackId=154588196450645; __uuid=115458819649530.a187a; _ga=GA1.2.1818966348.1545881966; agreedUserPrivacy=1; __chat_udid=ae091516-ee0b-4a34-96e2-539c81faa044; __s=f2cqnm56ml93p8vm56sbu7ui80; Hm_lvt_5a727f1b4acc5725516637e03b07d3d2=1553168304,1553220219,1553222217; __city=chongqing; __area2=tongwei; _gid=GA1.2.989251167.1553479553; _auth_redirect=http%3A%2F%2Fchongqing.baixing.com%2Fershoufang%2F%3Fsrc%3Dtopbar; __sense_session_pv=1; Hm_lpvt_5a727f1b4acc5725516637e03b07d3d2=1553517296; _gat=1"
        ]
        self.redis_class = "BXW"
        self.change_cookie = False
        self.error_url = None
        self.burst = 100
        self.sleep_time_min = 5
        self.sleep_time_max = 12

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

    async def get_baixing(self, url):
        async with aiohttp.ClientSession(cookies=self.get_cookies()) as session:
            async with session.get(url, headers=self.get_headers()) as res:
                if "spider" in str(res.url):
                    self.change_cookie = True
                    self.error_url = url
                    self.save_logs(url, res.status, res.history[0].status)
                else:
                    html = await res.text()
                    self.save_logs(url, res.status)
                    self.save_data(url, html)

    def next_page(self, url, root):
        try:
            last_page_num = root.xpath(
                '//a[text()="下一页"]/../preceding-sibling::li[1]/a/text()')[0]
            for i in range(1, int(last_page_num)):
                if len(url.split("?")) < 3:
                    self.save_urls_redis("{0}?page={1}".format(url, i))
        except Exception as e:
            self.r_db.lpush("{0}:have_none_next".format(self.redis_class), url)

    def start_request(self, url_list):
        loop = asyncio.get_event_loop()
        tasks = [asyncio.ensure_future(self.get_baixing(i)) for i in url_list]
        loop.run_until_complete(asyncio.wait(tasks))

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

    def save_data(self, url, html):
        root = self.parse_html(html)
        url_list = root.xpath('//li[contains(@class,"listing-ad")]/a/@href')
        if url_list:
            self.next_page(url, root)
            [self.save_urls_redis(i, "detail_page") for i in url_list]
        else:
            self.save_detail(url, root)

    def save_urls_redis(self, url, page_type="list_page"):
        if not self.r_db.hget("{0}:succ_logs".format(self.redis_class), url) and page_type == "detail_page":
            self.r_db.lpush("{0}:url_list".format(self.redis_class), url)

    def save_detail(self, url, root):
        data = {}
        try:
            data['url'] = url.split("?")[0]
            if root.xpath("//meta[@name='description']/@content"):
                data['title'] = root.xpath(
                    "//meta[@name='description']/@content")[0]
            else:
                data['title'] = root.xpath("//h1/text()")[0]
            data['city'] = root.xpath(
                "/html/body/header/div[1]/div/div/a[1]/text()")[0]
            data['desc'] = root.xpath(
                '//section[@class="viewad-description"]/div[@class="viewad-text"]/text()')[0]
            data['phone'] = root.xpath(
                "//p[@id='mobileNumber']/strong/text()")[0]
        except Exception as e:
            pass
        if 'phone' in data and not self.r_db.hget("{0}:phone_list".format(self.redis_class), data['phone']):
            self.r_db.lpush("{0}:new_data".format(self.redis_class), data)
            self.r_db.lpush("{0}:detail_msg".format(self.redis_class), data)
            self.r_db.hset("{0}:phone_list".format(self.redis_class), data['phone'], 200)
        else:
            self.r_db.lpush("{0}:expired_msg".format(self.redis_class), data)

    def save_logs(self, url, status, status_history=200):
        from datetime import datetime as dt
        if status == 200 and status_history == 200:
            today = str(dt.today()).split(" ")[0]
            self.r_db.hset(
                "{0}:{1}".format(
                    self.redis_class,
                    today),
                url,
                status)
            self.r_db.hset(
                "{0}:succ_logs".format(
                    self.redis_class), url, status)
        else:
            self.r_db.hset(
                "{0}:err_logs".format(
                    self.redis_class),
                url,
                status_history)
            self.r_db.lpush("{0}:url_list".format(self.redis_class), url)

    @staticmethod
    def parse_html(html):
        return etree.HTML(html, etree.HTMLParser(encoding='utf-8'))

    def add_data(self):
        from datetime import datetime as dt
        t = "{0}-{1}-{2}".format(dt.today().year,
                                 dt.today().month, dt.today().day)
        if self.r_db.hset('{0}:flag'.format(self.redis_class), t, "flag"):
            self.r_db.delete("{0}:new_data".format(self.redis_class))
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

    def del_ban(self):
        from selenium import webdriver
        import time

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
        self.change_cookie = False
        self.error_url = None

    def debug(self):
        f_data = self.r_db.lrange("BXW:expired_msg", 0, -1)
        s_data = self.r_db.lrange('BXW:detail_msg', 0, -1)
        # for each in f_data:
        #     each = eval(each)
        #     self.r_db.hset("BXW:succ_logs", each["url"], 200)
        for each in s_data:
            each = eval(each)
            self.r_db.hset("BXW:phone_list", each["phone"], 200)
            # self.r_db.hset("BXW:succ_logs", each["url"], 200)

    def start(self):
        import time
        while True:
            url_list = self.get_urls()
            if url_list:
                self.start_request(url_list)
            else:
                break
            if self.change_cookie:
                self.del_ban()
            time_sleep = random.randint(
                self.sleep_time_min, self.sleep_time_max)
            print("sleep {0}...".format(time_sleep))
            time.sleep(time_sleep)
        print("over !")


def run():
    spider = Spider()
    spider.add_data()
    spider.start()
    # spider.debug()
    # excel = Write_Excel()
    # excel.write_to_excel('百姓网求租求购.xlsx')


if __name__ == "__main__":
    run()

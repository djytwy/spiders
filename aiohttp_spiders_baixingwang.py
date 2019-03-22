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

    def __init__(self):
        ua = fake_useragent.UserAgent()
        self.ua_list = [ua.random for i in range(200)]
        self.redis_con = redis.ConnectionPool(
            host="xxx.xxx.xxx.xxx", port=6379, db=12)
        self.r_db = redis.StrictRedis(connection_pool=self.redis_con)
        self.cookies_pool = [

        ]
        self.change_cookie = False
        self.error_url = None
        self.burst = 100

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

    async def get(self, url):
        async with aiohttp.ClientSession(cookies=self.get_cookies()) as session:
            async with session.get(url, headers=self.get_headers()) as res:
                if res.history:
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
            self.r_db.lpush("have_none_next", url)

    def asy_http(self, url_list):
        loop = asyncio.get_event_loop()
        tasks = [asyncio.ensure_future(self.get(i)) for i in url_list]
        loop.run_until_complete(asyncio.wait(tasks))

    def start(self):
        import time
        while True:
            url_list = self.get_100_urls()
            if url_list:
                self.asy_http(url_list)
            else:
                break
            if self.change_cookie:
                self.del_ban()
            time_sleep = random.randint(10, 60)
            print("sleep {0}...".format(time_sleep))
            time.sleep(time_sleep)
        print("over !")

    def get_100_urls(self):
        url_list = self.r_db.lrange("baixingwang_url", 1, self.burst)
        self.r_db.ltrim("baixingwang_url", self.burst + 1, -1)
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
            [self.save_urls_redis(i,"detail_page") for i in url_list]
        else:
            self.save_detail(url, root)

    def save_urls_redis(self, url, page_type="list_page"):
        if not self.r_db.hget("succ_logs", url) and page_type == "detail_page":
            self.r_db.lpush("baixingwang_url", url)

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
        if 'phone' in data:
            self.r_db.lpush("detail_msg", data)
        else:
            self.r_db.lpush("expired_msg", data)

    def save_logs(self, url, status, status_history=200):
        if status == 200 and status_history == 200:
            self.r_db.hset("succ_logs", url, status)
        else:
            self.r_db.hset("err_logs", url, status_history)
            self.r_db.lpush("baixingwang_url", url)

    @staticmethod
    def parse_html(html):
        return etree.HTML(html, etree.HTMLParser(encoding='utf-8'))

    def add_data(self):
        with open("baixing_urls.txt", "r") as f:
            file = f.read()
            file = file.split(",")
            for i in file:
                i = i.replace("'", "").replace(" ", "")
                url = "http://{0}.baixing.com/qiufang/m178892/".format(i)
                url2 = "http://{0}.baixing.com/qiufang/m178893/".format(i)
                self.r_db.lpush("baixingwang_url", url)
                self.r_db.lpush("baixingwang_url", url2)
        f.close()

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

    def temp(self):
        succ_msg = self.r_db.lrange("detail_msg", 0, -1)
        for each in succ_msg:
            each = eval(each)
            try:
                self.r_db.hset("succ_logs", each["url"], 200)
            except Exception as e:
                print(e)


class Write_Excel(Spider):
    def __init__(self):
        super().__init__()

    def get_data(self):
        return self.r_db.lrange("detail_msg", 0, -1)

    def write_to_excel(self):
        import openpyxl
        wb = openpyxl.load_workbook('百姓网求租求购.xlsx')
        sheet = wb.get_active_sheet()
        sheet["A1"] = "标题"
        sheet["B1"] = "描述"
        sheet["C1"] = "城市"
        sheet["D1"] = "网页链接"
        sheet["E1"] = "电话"
        data = self.get_data()
        for each in data:
            try:
                each = eval(each)
                sheet.append([each['title'], each['desc'],
                              each['city'], each['url'], each['phone']])
            except Exception as e:
                print(each)
        wb.save("ty.xlsx")

def run():
    spider = Spider()
    spider.add_data()
    spider.start()
    excel = Write_Excel()
    excel.write_to_excel()

if __name__ == "__main__":
    run()
    # spider.temp()

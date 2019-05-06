# !user/bin/env
# -*- coding: utf-8 -*-
# Author: twy

import time
import asyncio
import aiohttp
import re
from utils import Mixin_utils

class Spider(Mixin_utils):
    """
    百姓网求购、求租爬虫
    """

    def __init__(self, burst, redis_class, filter_type = "2", days='1'):
        super().__init__(burst - 1, redis_class)

        if burst % 5 != 0 or burst > 200:
            print("并发量必须是5的倍数！且小于200！")
            time.sleep(5)
            exit()
        self.filter_type = filter_type
        self.days = days
        self.redis_class = redis_class
        self.change_cookie = False
        self.error_url = None
        self.sleep_time_min = 5
        self.sleep_time_max = 12

    def next_page(self, url, root):
        try:
            last_page_num = root.xpath('//a[text()="下一页"]/../preceding-sibling::li[1]/a/text()')
            if last_page_num and len(url.split("?")) == 1:
                for i in range(1, int(last_page_num[0])):
                    self.save_url_to_redis("{0}?page={1}".format(url.split("?")[0], i))
        except Exception as e:
            self.r_db.lpush("{0}:have_none_next".format(self.redis_class), url)

    async def get_baixing(self, url, url_list):
        if not self.proxy_list:
            cookies = self.get_cookies()
        else:
            cookies = None
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(url, headers=self.get_headers(),
                                   proxy=self.proxy_list[int(url_list.index(url)/5)]["aiohttp"]) as res:
                # 被封了的情况：
                if "spider" in str(res.url):
                    self.change_cookie = True
                    self.error_url = url
                    self.save_logs(url, res.status, res.history[0].status)
                else:
                    html = await res.text()
                    if not ("m178893" in url or "m178892" in url):
                        self.save_logs(url, res.status)
                    self.save_data(url, html, res.history)

    def start_request(self, url_list):
        loop = asyncio.get_event_loop()
        tasks = [asyncio.ensure_future(self.get_baixing(i, url_list)) for i in url_list]
        loop.run_until_complete(asyncio.wait(tasks))

    def save_data(self, url, html, status=None):
        root = self.parse_html(html)
        if root == None or "Too Many Requests" in html or status:
            print("请求失败的URL：{0}".format(url))
        else:
            url_list = root.xpath('//ul/li[contains(@class,"listing-ad")]/div[@class="media-body"]/div[1]/a[1]') \
                       or root.xpath('//ul/li[contains(@class,"listing-ad")]/a')
            if url_list:
                self.next_page(url, root)
                for i in url_list :
                    if i.xpath('.//text()') and i.xpath('.//@href') and \
                            "搞定了" not in i.xpath('.//text()')[0] and not self.judge_url(i.xpath('.//@href')[0]):
                        self.save_url_to_redis(i.xpath('.//@href')[0])
            else:
                self.save_detail(url, root)


    def save_url_to_redis(self, url):
        self.r_db.lpush("{0}:url_list".format(self.redis_class), url)

    def parse_detail(self, url, root):
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
            data["time"] = root.xpath("//span[@data-toggle='tooltip']/@title")[0].replace(u"首次发布于：", "")
            data["class"] = root.xpath('//a[@class="meta-分类"]/text()')[0]
            data['phone'] = root.xpath(
                "//p[@id='mobileNumber']/strong/text()")[0]
        except Exception as e:
            pass
        return data

    def save_detail(self, url, root):
        data = self.parse_detail(url, root)
        if 'phone' in data :
            if self.is_save(data):
            # if not self.r_db.hget("{0}:phone_list".format(self.redis_class), data['phone']) and self.is_save(data["class"], data["time"]):
                self.r_db.lpush("{0}:new_data".format(self.redis_class), data)
                self.r_db.hset("{0}:phone_list".format(self.redis_class), data['phone'], 200)
                print("新鲜数据：{0}".format(data['url']))
                self.r_db.hset("{0}:all_msg".format(self.redis_class), data['url'], data)
            else:
                print("不符合标准的有效数据：{0}: {1} 链接：{2}".format(data["class"], data["time"], url))
        else:
            self.r_db.lpush("{0}:expired_msg".format(self.redis_class), data)
            print("过期数据：{0} ".format(url))

    def judge_url(self, url):
        return self.r_db.hget("{0}:succ_logs".format(self.redis_class), url)

    def is_save(self, data):
        if self.filter_type == "1":
            import datetime
            time_str = data["time"].replace("月","-").replace("年","-").replace("日","")
            time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            return (datetime.datetime.now() - time).days == int(self.days)
        else:
            return not self.r_db.hget("{0}:phone_list".format(self.redis_class), data['phone']) and \
                   ("2019" in data["time"] and data["class"] == "求购") or ( self.now.month - int(re.search(u'(\d+)月',
                    data["time"]).group(1)) == 0 and data["class"] == "求租" and "2019" in data["time"] )

    def save_logs(self, url, status, status_history=200):
        if status == 200 and status_history == 200:
            self.r_db.hset(
                "{0}:{1}".format(
                    self.redis_class,
                    self.today),
                url,
                status)
            self.r_db.hset(
                "{0}:succ_logs".format(
                    self.redis_class), url.split("?")[0], status)
        else:
            self.r_db.hset(
                "{0}:err_logs".format(
                    self.redis_class),
                url,
                status_history or status)
            print("出错的URL:{0}, 重新入库。。。。。".format(url))
            self.r_db.lpush("{0}:url_list".format(self.redis_class), url)

    def del_ban(self):
        """
        开启webdriver从而手动完成验证码
        :return:
        """
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

    def start_with_proxy(self):
        while True:
            self.check_proxy()
            url_list = self.get_urls()
            if url_list:
                self.start_request(url_list)
            else:
                print("符合标准的数据已经抓取完毕！程序将在3秒后关闭！")
                time.sleep(3)
                break
        print("over !")



def run():
    """
    Spider初始化有三个参数，第三个参数用于控制过滤方式
    :return:
    """
    filter_type = input("请选择过滤类型：\n 1.只根据时间过滤，可输入过滤的天数。\n 2.根据电话过滤，获得2019年的求购，和近一个月的求租\n ")
    if filter_type not in ("1","2"):
        print("请输入合理的选择：1或者2 !")
        time.sleep(3)
        exit()
    if filter_type == '1':
        days = input('请输入过滤的天数： ')
        if re.search('(\d+)',days):
            print("启动模式：{0}，往后的天数：{1}".format(filter_type,days))
            time.sleep(1)
            spider = Spider(50, "BXW", filter_type, days)
        else:
            print("请输入合理的整数天数 ！！！")
            time.sleep(3)
            exit()
            # 这一句是为了ide不报警告
            spider = Spider(50, "BXW")
    else:
        spider = Spider(50, "BXW")
    spider.add_data()
    spider.start_with_proxy()

if __name__ == "__main__":
    run()

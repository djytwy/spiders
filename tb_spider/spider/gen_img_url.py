# !/usr/bin/env python
# encoding: utf-8

"""
file: gen_img_url.py
time: 2019/6/19 11:34
Author: twy
contact: 19983195362
des: 网页信息的初步处理，主要调用gen_img_url生成要抓取的网页信息
"""

from spider.utils import utilsMixin
import json
import time


class ParseHtml(utilsMixin):

    def __init__(self):
        super().__init__()
        self._all_html = ""

    def parse_html(self) -> dict:
        """
        定制化网页解析，这块可能改变
        :return: 返回类型：{title: url,....}
        """
        title_ele_list = self.parse_html_with_xpath('//div[@class="row row-2 title"]/a')
        title_list = map(lambda each: each.xpath('string(.)').replace(' ', "").replace('\n', ""), title_ele_list)
        img_ele_list = self.parse_html_with_xpath('//img[@class="J_ItemPic img"]/@data-src')
        img_list = map(lambda each: f'http:{each}', img_ele_list)
        img_dic = dict(zip(title_list, img_list))
        return img_dic

    def gen_img_url(self):
        """
        往Redis中存入数据，to_crawl_data为列表，内部元素为json字符串
        """
        print("生成图片URL进程启动......")
        while True:
            self._all_html = self.redis_con.hgetall("tb_data")
            self.redis_con.delete("tb_data")
            for each in self._all_html:
                self._get_xpath_root(self._all_html[each].decode('utf-8', 'ignore'))
                _data = self.parse_html()
                for item in _data:
                    self.redis_con.lpush("to_crawl_data", json.dumps({item: _data[item]}))
            print("所有图片的URL生成完毕！休眠5秒等待动态网页....")
            time.sleep(5)
                
    # def gen_data(self):
    #     """
    #     程序入口，执行生成img的URL
    #     """
    #     while True:
    #         if self.redis_con.exists("tb_data"):
    #             self.gen_img_url()
    #             print("生成所有的img URL完毕！ 休眠10秒")
    #         else:
    #             print("暂无img URL 数据，休眠10秒")
    #         time.sleep(100)
            

parseHTML = ParseHtml()

if __name__ == "__main__":
    s = ParseHtml()
    s.gen_img_url()

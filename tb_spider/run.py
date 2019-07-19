# !/usr/bin/env python
# encoding: utf-8

"""
file: run.py.py
time: 2019/6/20 11:42
Author: twy
des: 淘宝爬虫的入口函数
"""

from multiprocessing import Process
from spider.gen_img_url import ParseHtml
from spider.http_aioget import http_aioget
from spider.save_img import write_img


class TBSpider(ParseHtml):
    """
    继承ParseHtml类，需要修改时，重写parse_html方法
    """
    def __init__(self):
        super().__init__()


p = TBSpider()


def http_get():
    http_aioget.run()


def write_image():
    write_img.run()


def gen_img_url():
    p.gen_img_url()


def run():
    """
    多进程爬取
    """
    process_list = []

    p_http_get = Process(target=http_get)
    p_http_get.start()
    process_list.append(p_http_get)

    p_write_img = Process(target=write_image)
    p_write_img.start()
    process_list.append(p_write_img)

    p_gen_img_url = Process(target=gen_img_url)
    p_gen_img_url.start()
    process_list.append(p_gen_img_url)

    for each in process_list:
        each.join()


if __name__ == "__main__":
    # t = TBSpider()
    # t.run()
    run()


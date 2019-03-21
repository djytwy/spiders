# coding:utf-8

import random
import asyncio
import aiohttp
import redis
from lxml import etree

ua_list = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
]

redis_con = redis.Redis("xxx.xxx.xxx.xxx",6379)

async def get(url):
    async with aiohttp.ClientSession() as session:
        headers = {
            "User-Agent":random.choice(ua_list),
            "Referer":"https://www.dyfc.net/resoldhome/esf/list?source=1"
        }
        async with session.get(url.decode(),headers=headers) as res:
            text = await res.text()
            return text

async def dyesf():
    url = redis_con.lpop("dyesf")
    text = await get(url)
    root = etree.HTML(text, etree.HTMLParser(encoding='utf-8'))
    value_list = root.xpath('//li[@class="item clearfix"]/div[1]/a/@href')
    for value in value_list:
        url = "https://www.dyfc.net{0}".format(value)
        redis_con.lpush("dyesf_url",url)


if __name__ == "__main__":
    for i in range(1,20):
        url = "https://www.dyfc.net/resoldhome/zf/list?source=1&way=226&sort=7&type=1&page={0}".format(i)
        redis_con.lpush("dyesf",url)
    loop = asyncio.get_event_loop()
    tasks = [ asyncio.ensure_future(dyesf()) for i in range(1,20)]
    loop.run_until_complete(asyncio.wait(tasks))



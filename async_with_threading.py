# !user/bin/env 
# -*- coding: utf-8 -*-
# Author: twy

import threading
import asyncio
from aiohttp import ClientSession


class async_with_threading(threading.Thread):
    def __init__(self):
        super().__init__()

    async def async_get(self, url, loop):
        async with ClientSession() as session:
            async with session.get(url) as response:
                print("{0}: from {}")


async def async_get(url, loop):
    async with ClientSession() as session:
        async with session.get(url) as response:
            print("{0}: from : {1}".format(await response.text(), id(loop)))


def thread_loop_task(loop):

    # 为子线程设置自己的事件循环
    asyncio.set_event_loop(loop)
    tasks = [ asyncio.ensure_future(async_get("http://localhost:3001/test/io_test/24",loop)) for i in range(100) ]
    loop.run_until_complete(asyncio.wait(tasks))


if __name__ == '__main__':

    # 创建一个事件循环thread_loop
    thread_loop = asyncio.new_event_loop()

    # 将thread_loop作为参数传递给子线程
    t = threading.Thread(target=thread_loop_task, args=(thread_loop,))
    # t.daemon = True
    t.start()

    main_loop = asyncio.get_event_loop()
    tasks = [ asyncio.ensure_future(async_get("http://localhost:3001/test/io_test/24",main_loop)) for i in range(100) ]
    main_loop.run_until_complete(asyncio.wait(tasks))
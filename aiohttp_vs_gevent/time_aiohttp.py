import asyncio
import aiohttp
import time


class Spider():

    def __init__(self, url):
        self.url = url

    async def request(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                print(html)

    def start(self):
        loop = asyncio.get_event_loop()
        tasks = [ asyncio.ensure_future(self.request(self.url)) for i in range(200) ]
        loop.run_until_complete(asyncio.wait(tasks))

    def test(self):
        start = time.time()
        self.start()
        end = time.time()
        print("use time : {0}".format(end-start))

if __name__ == "__main__":
    s = Spider("http://localhost:5000/")
    s.test()
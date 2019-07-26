# spiders
一些我写过的比较有意思的爬虫。
## BXW_spider:
爬百姓网求租、求购数据的爬虫，挂代理进行数据爬取，若代理失效，则自动切换，使用aiohttp进行并发爬取，每个代理ip承受5个并发。
并发量的控制提供redis来控制。

## 58同城：
爬取58同城的求租、求购的数据，使用的是seleium + aiohttp，若出现验证码才弹出浏览器。

## tb_spider:
使用puppeteer.js,作为浏览列表页和通过验证的方式，使用aiohttp作为图片的下载器，队列使用redis控制。

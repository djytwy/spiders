# spiders
some spiders demo
## BXW_spider:
爬百姓网求租、求购数据的爬虫，挂代理进行数据爬取，若代理失效，则自动切换，使用aiohttp进行并发爬取，每个代理ip承受5个并发。
并发量的控制提供redis来控制。
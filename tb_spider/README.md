淘宝爬虫

#### 软件架构
软件架构说明
分为TS（JS）端低速爬虫和python端高速爬虫两块

#### 安装
需要先安装node环境：[下载node](https://nodejs.org/zh-cn/) 

#### 安装教程
设置cnpm加速拉包的速度：[cnpm](https://npm.taobao.org/) 

安装[mitmproxy](https://mitmproxy.org/)

#### 使用说明
1. 执行```cnpm i```
2. 执行```pip install -r requirements.txt```
3. 启动mitmproxy: ```mitmdump -s HTTP_intercept.py```
4. 启动低速爬虫：```npm run start``` 
5. 启动高速爬虫：```python run.py```

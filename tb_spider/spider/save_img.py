# !/usr/bin/env python
# encoding: utf-8

"""
file: save_img.py
time: 2019/6/19 15:56
Author: twy
contact: 19983195362
des:
"""

from spider.utils import utilsMixin
import time


class WriteImg(utilsMixin):
    def __init__(self):
        super().__init__()

    def run(self):
        print("图片写入进程启动.......")
        while True:
            if self.redis_con.exists("img_data_list"):
                _img_dic = self.redis_con.hgetall("img_data_list")
                self.redis_con.delete("img_data_list")
                for each in _img_dic:
                    try:
                        file_name = each.decode('utf-8').replace('/', '').replace('|', '').replace('\\', '')\
                            .replace('<', "").replace('?', "").replace('*', "").replace(':', "").replace('>', "")
                        with open(f"./dist/{file_name}.jpg", "wb") as f:
                            f.write(_img_dic[each])
                            f.close()
                    except Exception as e:
                        print(e)
            print("图片写入休眠10秒，等待Redis写入图片......")
            time.sleep(10)


write_img = WriteImg()

if __name__ == "__main__":
    w = WriteImg()
    w.run()

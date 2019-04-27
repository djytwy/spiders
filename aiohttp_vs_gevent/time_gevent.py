from gevent import monkey
monkey.patch_all()
import gevent
import requests
import time

def r(url):
    s = requests.session()
    response = s.get(url)
    print(response.text)

def start():
    gevent.joinall([gevent.spawn(r, "http://localhost:5000/") for i in range(200) ])

def test():
    s = time.time()
    start()
    e = time.time()
    print("used time : {0}".format(e-s))

if __name__ == "__main__":
    test()
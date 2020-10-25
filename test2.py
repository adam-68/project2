import asyncio
import datetime
import chilkat
import dill
import multiprocessing
import httpx
import os
from tornado.httpclient import *
# from tornado.curl_httpclient import *

def blocking_io():
    # File operations (such as logging) can block the
    # event loop: run them in a thread pool.
    # with open('USER_INPUT_DATA/proxies.txt', 'rb') as f:
    #     return f.read(100)
    print("WHAT")

    
def cpu_bound():
    # CPU-bound operations will block the event loop:
    # in general it is preferable to run them in a
    # process pool.
    return sum(i * i for i in range(10 ** 7))

class whatt():
    def __init__(self):
        self.what = ""

    async def main(self, cert):
        # asyncio.set_event_loop(asyncio.new_event_loop())
        #
        # ## Options:
        #
        # # 1. Run in the default loop's executor:
        # # result = await loop.run_in_executor(
        # #     None, blocking_io)
        # # print('default thread pool', result)
        #
        # executor = ProcessPoolExecutor()
        # out = await asyncio.get_event_loop().run_in_executor(executor, blocking_io)  # This does not
        # print(out)
        # curl -U Kw3nS5:6gZ7Hh -x 88.218.48.42:8000 https://httpbin.org/ip --proxy-anyauth
        # curl -U Kw3nS5:6gZ7Hh -x http://proxy.ourdomain.net:80 --request
        # export http_proxy="http://Kw3nS5:6gZ7Hh@88.218.48.42:8000"
        # curl -x https://[customer-umct8d58-cc-PL-sessid-UILGQHR6-sesstime-30:9UfZa4U4@]pr.rubyproxies.com[:7777]/ https://httpbin.org/ip
        # proxies = "http://Kw3nS5:6gZ7Hh@88.218.48.42:8000"
        # proxies = httpx.Proxy(
        #     url="http://customer-umct8d58-cc-PL-sessid-UILGQHR6-sesstime-30:9UfZa4U4@pr.rubyproxies.com:7777",
        #     mode="FORWARD_ONLY"
        # )
        # proxies = httpx.Proxy(
        #     url="https://Kw3nS5:6gZ7Hh@88.218.48.42:8000",
        #     mode="FORWARD_ONLY"
        # )
        proxies = {
            "http://": "http://Kw3nS5:6gZ7Hh@88.218.48.42:8000",
            "https://": "http://Kw3nS5:6gZ7Hh@88.218.48.42:8000",
        }

        # http_client = HTTPClient()
        # print(datetime.datetime.now().strftime('[%H:%M:%S:%f]'))
        # print( os.system(f"curl -U {proxy[2]}:{proxy[3]} -x {proxy[0]}:{proxy[1]} https://httpbin.org/ip --proxy-anyauth"))
        client = httpx.AsyncClient(proxies="http://Kw3nS5:6gZ7Hh@88.218.48.42:8000")
        response = await client.get("https://httpbin.org/ip")
        print(response.text)


def what(proxy):
    new = whatt()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.get_event_loop().run_until_complete(new.main(proxy))


if __name__ == "__main__":
    # proxies = ["88.218.50.153:8000:EPnsGd:Eyvjd1", "88.218.49.213:8000:EPnsGd:Eyvjd1", "88.218.48.249:8000:EPnsGd:Eyvjd1", "88.218.49.197:8000:EPnsGd:Eyvjd1",
    #            "88.218.51.106:8000:EPnsGd:Eyvjd1", "88.218.48.26:8000:EPnsGd:Eyvjd1"]
    processe = []
    cert = ""
    # cert = chilkat.CkCert()
    # success = cert.LoadFromFile("client.pem")
    # print(cert.VerifySignature())
    # print(cert.authorityKeyId())
    # print(cert.ExportPublicKey())
    # print(cert.serialNumber())
    proxies = ["88.218.50.153:8000:EPnsGd:Eyvjd1"]
    for i in range(len(proxies)):
        proxy = proxies[i].split(':')
        p = multiprocessing.Process(target=what, args=(cert,))
        p.start()
        processe.append(p)

    for p in processe:
        p.join()
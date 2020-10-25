# coding=utf8
# from discord_webhook import DiscordWebhook, DiscordEmbed
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from multiprocessing import Process
from threading import Thread
# from async_class import AsyncClass
from bs4 import BeautifulSoup
import datetime
import re
import concurrent
import httpx
# import aiohttp
from tornado import httpclient
import requests_async
import json
import requests
import asyncio
import time


async def start(task, profile):
    start = time.time()
    print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}]"
          f" Loading bypass...")
    headers = {
        "Host": "sklep.sizeer.com",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/83.0.4103.106 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "same-origin",
        "Referer": "https://sklep.sizeer.com/profile",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
    }
    async with httpx.AsyncClient(proxies=task['proxy'], timeout=20.0) as client:
        # response = await client.get("https://sklep.sizeer.com/meskie/akcesoria?sort=price_asc&limit=60&page=1",
        #                             headers=headers)
        # loop = asyncio.new_event_loop()
        # self.product_url = "https://sklep.sizeer.com" + \
        #                    BeautifulSoup(response.text, "html.parser").find("a", {"class": "b-itemList_photoLink"})[
        #                        "href"]

        # print(self.product_url)
        # headers["Sec-Fetch-Site"] = "same-origin"
        # headers['Referer'] = "https://sklep.sizeer.com/meskie/buty/sneakersy"
        bypass_product_page = await client.get("https://sklep.sizeer.com/sizeer-skarpety-frote-2ppk-mix-7609-unisex-skarpetki-czarny-sisk7609", headers=headers)
        sizes = re.findall(r'EU: (.*?)"', bypass_product_page.text)
        sizes_ids = re.findall(r'data-value="(.*?)"', bypass_product_page.text)
        sizes_dict = {}
        for i in range(len(sizes)):
            sizes_dict[sizes[i].strip()] = sizes_ids[i]
        pid = sizes_dict[list(sizes_dict.keys())[0]]

        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}] Adding product to cart...")
        data = f"id={pid}&transport=&qty=1"
        headers = {
            "Host": "sklep.sizeer.com",
            "Connection": "keep-alive",
            "Content-Length": str(len(data)),
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/83.0.4103.106 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://sklep.sizeer.com",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://sklep.sizeer.com/sizeer-skarpety-frote-2ppk-mix-7609-unisex-skarpetki-czarny-sisk7609",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        cart_add = await client.post("https://sklep.sizeer.com/cart/pre-x-add",
                                     headers=headers, data=data)
        await asyncio.sleep(0)

        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}]"
              f" Successfully added to cart.")

        headers = {
            "Host": "sklep.sizeer.com",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/83.0.4103.106 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": "https://sklep.sizeer.com/sizeer-skarpety-frote-2ppk-mix-7609-unisex-skarpetki-czarny-sisk7609",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        cart_page = await client.get("https://sklep.sizeer.com/koszyk/lista", headers=headers)
        token = re.search(r'"cart_flow_list_step(.*?)" value="(.*?)"',
                                       cart_page.text).group().split('"')[-2]
        hash = re.search(r'data-item-hash="(.*?)"', cart_page.text).group().split('"')[-2]

        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}]"
              f" Filling delivery form...")
        # Pobranie
        # data = f"cart_flow_list_step%5B_token%5D={self.token}&" \
        #        f"cart_flow_list_step%5BtransportMethod%5D=43&" \
        #        f"cart_flow_list_step%5BpaymentGroup%5D=71&cart_flow_list_step%5Bcoupon%5D="
        # Blik
        data = f"cart_flow_list_step%5B_token%5D=Y{token}&" \
               f"cart_flow_list_step%5BtransportMethod%5D=43&" \
               f"cart_flow_list_step%5BpaymentGroup%5D=103&cart_flow_list_step%5Bcoupon%5D="

        headers = {
            "Host": "sklep.sizeer.com",
            "Connection": "keep-alive",
            "Content-Length": str(len(data)),
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/83.0.4103.106 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://sklep.sizeer.com",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://sklep.sizeer.com/koszyk/lista",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        order_info_req = await client.post("https://sklep.sizeer.com/koszyk/lista/zapisz?isAjax=1",
                                           headers=headers, data=data)

        headers = {
            "Host": "sklep.sizeer.com",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/83.0.4103.106 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
                      ",application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-User": "?1",
            "Referer": "https://sklep.sizeer.com/koszyk/lista",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        address_page = await client.get("https://sklep.sizeer.com/koszyk/adres", headers=headers)
        curr_token = re.search(r'name="cart_flow_address_step(.)_token(.)" value="(.*?)"', address_page.text)

        token = curr_token.group().split('"')[-2]
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}]"
              f" Filling address form...")

        data = f"cart_flow_address_step%5BaccountAddress%5D%5BfirstName%5D=gfds&cart_flow_address_step%5BaccountAddress%5D%5BlastName%5D=agfd&cart_flow_address_step%5BaccountAddress%5D%5Bemail%5D=afdasdf%40gmail.com&cart_flow_address_step%5BaccountAddress%5D%5BaddressType%5D=person&cart_flow_address_step%5BaccountAddress%5D%5Bcompany%5D=&cart_flow_address_step%5BaccountAddress%5D%5Bnip%5D=&cart_flow_address_step%5BaccountAddress%5D%5Bphone%5D=543-897-987&cart_flow_address_step%5BaccountAddress%5D%5Bstreet%5D=gsfads&cart_flow_address_step%5BaccountAddress%5D%5BhouseNumber%5D=34&cart_flow_address_step%5BaccountAddress%5D%5BapartmentNumber%5D=&cart_flow_address_step%5BaccountAddress%5D%5Bpostcode%5D=42-341&cart_flow_address_step%5BaccountAddress%5D%5Bcity%5D=hdfsd&cart_flow_address_step%5BsameTransportAddress%5D=1&cart_flow_address_step%5BtransportAddress%5D%5Bcompany%5D=&cart_flow_address_step%5BtransportAddress%5D%5BfirstName%5D=&cart_flow_address_step%5BtransportAddress%5D%5BlastName%5D=&cart_flow_address_step%5BtransportAddress%5D%5Bphone%5D=&cart_flow_address_step%5BtransportAddress%5D%5Bstreet%5D=&cart_flow_address_step%5BtransportAddress%5D%5BhouseNumber%5D=&cart_flow_address_step%5BtransportAddress%5D%5BapartmentNumber%5D=&cart_flow_address_step%5BtransportAddress%5D%5Bpostcode%5D=&cart_flow_address_step%5BtransportAddress%5D%5Bcity%5D=&cart_flow_address_step%5BsameBillingAddress%5D=1&cart_flow_address_step%5BbillingAddress%5D%5BfirstName%5D=&cart_flow_address_step%5BbillingAddress%5D%5BlastName%5D=&cart_flow_address_step%5BbillingAddress%5D%5BaddressType%5D=person&cart_flow_address_step%5BbillingAddress%5D%5Bcompany%5D=&cart_flow_address_step%5BbillingAddress%5D%5Bnip%5D=&cart_flow_address_step%5BbillingAddress%5D%5Bphone%5D=&cart_flow_address_step%5BbillingAddress%5D%5Bstreet%5D=&cart_flow_address_step%5BbillingAddress%5D%5BhouseNumber%5D=&cart_flow_address_step%5BbillingAddress%5D%5BapartmentNumber%5D=&cart_flow_address_step%5BbillingAddress%5D%5Bpostcode%5D=&cart_flow_address_step%5BbillingAddress%5D%5Bcity%5D=&cart_flow_address_step%5BconsentForm%5D%5Bconsent_1925%5D%5B%5D=1925&cart_flow_address_step%5BconsentForm%5D%5Bconsent_1760%5D%5B%5D=1760&cart_flow_address_step%5BconsentForm%5D%5Bconsent_1778%5D%5B%5D=1778&cart_flow_address_step%5BtransportAddress%5D%5BaddressType%5D=person&cart_flow_address_step%5BcustomerComment%5D=&cart_flow_address_step%5B_token%5D={token}"
        headers = {
            "Host": "sklep.sizeer.com",
            "Connection": "keep-alive",
            "Content-Length": str(len(data)),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.9",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/83.0.4103.106 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://sklep.sizeer.com",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-User": "?1",
            "Referer": "https://sklep.sizeer.com/koszyk/adres",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        send_address_req = await client.post("https://sklep.sizeer.com/koszyk/adres/zapisz", headers=headers,
                                             data=data)

        curr_token = re.search(r'name="cart_flow_summation_step(.)_token(.)" value="(.*?)"',
                               send_address_req.text).group().split('"')[-2]
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}]"
              f" Checking out... {time.time() - start}")
        data = f"cart_flow_summation_step%5B_token%5D={curr_token}"
        headers = {
            "Host": "sklep.sizeer.com",
            "Connection": "keep-alive",
            "Content-Length": str(len(data)),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.9",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/83.0.4103.106 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://sklep.sizeer.com",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-User": "?1",
            "Referer": "https://sklep.sizeer.com/koszyk/podsumowanie",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }


# async def main(tasks, profiles):
#     await asyncio.gather(*[start(tasks[i], profiles[0]) for i in range(len(tasks))])


def main(task, profile):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.get_event_loop().run_until_complete(start(task, profile))


if __name__ == "__main__":
    with open("USER_INPUT_DATA/tasks.json", "r") as f1, \
            open("USER_INPUT_DATA/proxies.txt", "r") as f2, \
            open("USER_INPUT_DATA/profiles.json", "r") as f3:
        tasks = json.load(f1)
        proxies = f2.read().split("\n")
        profiles = json.load(f3)
    processes = []

    with ThreadPoolExecutor(len(tasks)) as executor:
        futures = []

        for i in range(len(tasks)):
            proxy_list = proxies[i].split(":")
            proxy = f"http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}"
            tasks[i]["proxy"] = proxy
            task_data = [tasks[i], profiles[0]]
            futures.append(executor.submit(lambda p: main(*p), task_data))

        results = []
        for future in as_completed(futures):
            results.append(future)


    # for i in range(len(tasks)):
    #     proxy_list = proxies[i].split(":")
    #     proxy = f"http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}"
    #     tasks[i]["proxy"] = proxy


    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main(tasks, profiles))
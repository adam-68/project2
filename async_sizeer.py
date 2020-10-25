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


class SizeerBot:
    def __init__(self, task, profile):
        self.task = task
        self.product_url = "https://sklep.sizeer.com/sizeer-skarpety-frote-2ppk-mix-7609-unisex-skarpetki-czarny-sisk7609"
        self.path = ""
        self.title = ""
        self.image_url = ""
        self.cookies = ""
        self.profile = profile
        self.pid = "545638863"
        self.curr_sizes = []
        self.token = ""
        self.errors_num = 0
        self.hash = ""
        self.start = ""
        self.checkout_token = ""
        self.bypass = ""

    async def loginn(self):
        proxy_defaults = {
            'proxy_host': "88.218.50.153",
            'proxy_port': 8000,
            "proxy_username": "EPnsGd",
            "proxy_password": "Eyvjd1",
        }
        httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient',
                                             defaults=proxy_defaults)
        client = httpclient.AsyncHTTPClient()
        response = await client.get("https://sklep.sizeer.com/login")
        print(response.text)

    async def login(self):
        headers = {
            "Host": "sklep.sizeer.com",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/83.0.4103.106 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }

        try:
            print(f"{ datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Logging in...")
            # httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient',
            #                                      defaults=self.task['proxy_dict'])
            # self.client = httpclient.AsyncHTTPClient()
            login_page = await self.client.get("https://sklep.sizeer.com/login", headers=headers)
            await asyncio.sleep(0)
            self.token = re.search(r'"enp_customer_form_login(.*?)" value="(.*?)"',
                                   login_page.text).group().split('"')[-2]
            login_data = f"enp_customer_form_login%5Busername%5D={self.profile['email']}&" \
                         f"enp_customer_form_login%5Bpassword%5D={self.profile['password']}&" \
                         f"enp_customer_form_login%5B_remember_me%5D=1&" \
                         f"_submit=Zaloguj+si%C4%99&" \
                         f"enp_customer_form_login%5B_token%5D={self.token}"
            login_headers = {
                "Host": "sklep.sizeer.com",
                "Connection": "keep-alive",
                "Content-Length": str(len(login_data)),
                "cache-control": "max-age=0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                          "application/signed-exchange;v=b3;q=0.9",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/83.0.4103.106 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://sklep.sizeer.com",
                "Referer": "https://sklep.sizeer.com/login",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Dest": "document",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
            }
            login_check = await self.client.post("https://sklep.sizeer.com/login_check",headers=login_headers,data=login_data)
            await asyncio.sleep(0)
            while not json.loads(login_check.content)['loginSuccess']:
                await asyncio.sleep(.1)
                self.errors_num += 1
                if self.errors_num > 10:
                    self.errors_num = 0
                    await self.login()
                    return
                login_check = await self.client.post("https://sklep.sizeer.com/login_check",
                                                      headers=login_headers, data=login_data)
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Login: {error}."
                  f" Retrying...")
            await self.login()
            return

        if self.task['bypass'] == "enable":
            await self.load_bypass_product()
        else:
            await self.load_product()
        return

    def bs(self, html):
        return "https://sklep.sizeer.com" + \
                                   BeautifulSoup(html, "html.parser").find("a", {"class": "b-itemList_photoLink"})[
                                       "href"]

    async def load_bypass_product(self):
        self.start = time.time()
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}]"
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
        try:
            async with httpx.AsyncClient(proxies=self.task['proxy'], timeout=20.0) as client:
                response = await client.get("https://sklep.sizeer.com/meskie/akcesoria?sort=price_asc&limit=60&page=1",
                                            headers=headers)
                # loop = asyncio.new_event_loop()
                # self.product_url = "https://sklep.sizeer.com" + \
                #                    BeautifulSoup(response.text, "html.parser").find("a", {"class": "b-itemList_photoLink"})[
                #                        "href"]

                headers["Sec-Fetch-Site"] = "same-origin"
                headers['Referer'] = "https://sklep.sizeer.com/meskie/buty/sneakersy"
                bypass_product_page = await client.get(self.product_url, headers=headers)
                sizes = re.findall(r'EU: (.*?)"', bypass_product_page.text)
                sizes_ids = re.findall(r'data-value="(.*?)"', bypass_product_page.text)
                sizes_dict = {}
                for i in range(len(sizes)):
                    sizes_dict[sizes[i].strip()] = sizes_ids[i]
                self.pid = sizes_dict[list(sizes_dict.keys())[0]]
                return client
        except requests.exceptions.Timeout as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Bypass: {error}."
                  f" Retrying...")
            await self.load_bypass_product()
            return

    async def load_product(self):
        headers = {
            "Host": "sklep.sizeer.com",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/83.0.4103.106 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }

        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Waiting for product...")
        try:
            product_page = await self.client.get(self.product_url, headers=headers)
            await asyncio.sleep(0)
            while "Powiadom mnie" in product_page.text:
                await asyncio.sleep(.05)
                product_page = await self.client.get(self.product_url, headers=headers)
            product_page_text = product_page.text

            sizes = re.findall(r'EU: (.*?) &', product_page_text)
            sizes_ids = re.findall(r'data-value="(.*?)"', product_page_text)
            sizes_dict = {}
            self.image_url = "https://sklep.sizeer.com" + \
                             re.search(rf'/media/cache/(.*?){self.task["sku"]}(.*?)\.jpg', product_page_text).group()
            self.title = re.search(r'data-ga-name="(.*?)"', product_page_text).group().split('"')[-2]
            for i in range(len(sizes)):
                sizes_dict[sizes[i].strip()] = sizes_ids[i]

            if self.task['size'] in list(sizes_dict.keys()):
                self.pid = sizes_dict[self.task['size']]
            else:
                self.task['size'] = list(sizes_dict.keys())[0]
                self.pid = sizes_dict[self.task['size']]

        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Product page: {error}."
                  f" Retrying...")
            await self.load_product()
            return

        await self.add_to_basket()
        return

    async def add_to_basket(self, client):
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Adding product to cart...")
        data = f"id={self.pid}&transport=&qty=1"
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
            "Referer": self.product_url,
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }

        try:
            cart_add = await client.post("https://sklep.sizeer.com/cart/pre-x-add",
                                         headers=headers, data=data)
            await asyncio.sleep(0)
            while "Dodano pomyślnie produkt do koszyka" not in cart_add.text:
                await asyncio.sleep(.1)
                self.errors_num += 1
                if self.errors_num > 10:
                    self.errors_num = 0
                    if self.task['bypass'] == "enable":
                        await self.load_bypass_product()
                    else:
                        await self.load_product()
                    return
                cart_add = await self.client.post("https://sklep.sizeer.com/cart/pre-x-add",
                                                  headers=headers, data=data)

            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}]"
                  f" Successfully added to cart.")
            return client
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Carting: {error}. "
                  f"Retrying...")
            self.errors_num += 1
            if self.errors_num > 15:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    await self.load_bypass_product()
                else:
                    await self.load_product()
            else:
                await self.add_to_basket()
            return



        # if self.bypass == "done":
        #     await self.bypass_remove()
        #     await self.sum_order()
        #     return
        # else:
        #     await self.load_cart_page()
        #     return

    async def bypass_remove(self):
        data = f"hash={self.hash}"
        headers = {
            "Host": "sklep.sizeer.com",
            "Connection": "keep-alive",
            "Content-Length": str(len(data)),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/83.0.4103.106 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://sklep.sizeer.com",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": self.product_url,
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        try:
            async with httpx.AsyncClient(proxies=self.task['proxy'], cookies=self.cookies) as client:
                bypass_remove = await client.post("https://sklep.sizeer.com/ajax/cart/mini/remove",
                                                        headers=headers, data=data)
                while not json.loads(bypass_remove.content)["remove"]:
                    await asyncio.sleep(.1)
                    self.errors_num += 1
                    if self.errors_num > 10:
                        self.errors_num = 0
                        if self.task['bypass'] == "enable":
                            await self.load_bypass_product()
                        else:
                            await self.load_product()
                        return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Bypass remove: "
                  f"{error}. Retrying...")
            self.errors_num += 1
            if self.errors_num > 15:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    await self.load_bypass_product()
                else:
                    await self.load_product()
            else:
                await self.bypass_remove()
            return

        return

    async def load_cart_page(self, client):
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
            "Referer": self.product_url,
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }

        try:
            cart_page = await client.get("https://sklep.sizeer.com/koszyk/lista", headers=headers)
            while "Sposób płatności" not in cart_page.text:
                await asyncio.sleep(.1)
                if self.errors_num > 5:
                    self.errors_num = 0
                    if self.task['bypass'] == "enable":
                        await self.load_bypass_product()
                    else:
                        await self.load_product()
                    return
                cart_page = await client.get("https://sklep.sizeer.com/koszyk/lista", headers=headers)
            self.token = re.search(r'"cart_flow_list_step(.*?)" value="(.*?)"',
                                   cart_page.text).group().split('"')[-2]
            self.hash = re.search(r'data-item-hash="(.*?)"', cart_page.text).group().split('"')[-2]
            return client
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Cart page: {error}."
                  f" Retrying...")
            self.errors_num += 1
            if self.errors_num > 5:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    await self.load_bypass_product()
                else:
                    await self.load_product()
            else:
                await self.load_cart_page()
            return



    async def send_order_info(self, client):
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}]"
              f" Filling delivery form...")
        # Pobranie
        # data = f"cart_flow_list_step%5B_token%5D={self.token}&" \
        #        f"cart_flow_list_step%5BtransportMethod%5D=43&" \
        #        f"cart_flow_list_step%5BpaymentGroup%5D=71&cart_flow_list_step%5Bcoupon%5D="
        # Blik
        data = f"cart_flow_list_step%5B_token%5D=Y{self.token}&" \
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

        try:
            order_info_req = await client.post("https://sklep.sizeer.com/koszyk/lista/zapisz?isAjax=1",
                                               headers=headers, data=data)
            while order_info_req.text.split(":")[-1][:-1] != "true":
                await asyncio.sleep(.1)
                if self.errors_num > 5:
                    self.errors_num = 0
                    if self.task['bypass'] == "enable":
                        await self.load_bypass_product()
                    else:
                        await self.load_product()
                    return
                order_info_req = await client.post("https://sklep.sizeer.com/koszyk/lista/zapisz?isAjax=1",
                                                   headers=headers, data=data)
            return client
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Delivery: "
                  f"{error}. Retrying...")
            self.errors_num += 1
            if self.errors_num > 5:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    await self.load_bypass_product()
                else:
                    await self.load_product()
            else:
                await self.load_cart_page()
            return


    async def load_address_page(self, client):
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
        try:
            address_page = await client.get("https://sklep.sizeer.com/koszyk/adres", headers=headers)
            curr_token = re.search(r'name="cart_flow_address_step(.)_token(.)" value="(.*?)"', address_page.text)
            while not curr_token:
                await asyncio.sleep(.1)
                self.errors_num += 1
                if self.errors_num > 5:
                    self.errors_num = 0
                    await self.load_product()
                    return
                address_page = await client.get("https://sklep.sizeer.com/koszyk/adres", headers=headers)
                curr_token = re.search(r'name="cart_flow_address_step(.)_token(.)" value="(.*?)"',
                                       address_page.text)

            self.token = curr_token.group().split('"')[-2]
            return client
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Address page: {error}."
                  f" Retrying...")
            self.errors_num += 1
            if self.errors_num > 5:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    await self.load_bypass_product()
                else:
                    await self.load_product()
            else:
                await self.load_address_page()
            return


    async def send_address(self, client):
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}]"
              f" Filling address form...")

        # data = f"cart_flow_address_step%5BaccountAddress%5D%5BfirstName%5D={self.profile['first_name']}&" \
        #        f"cart_flow_address_step%5BaccountAddress%5D%5BlastName%5D={self.profile['last_name']}&" \
        #        f"cart_flow_address_step%5BaccountAddress%5D%5Bemail%5D={self.profile['email']}&" \
        #        f"cart_flow_address_step%5BaccountAddress%5D%5BaddressType%5D=person&" \
        #        f"cart_flow_address_step%5BaccountAddress%5D%5Bcompany%5D=&" \
        #        f"cart_flow_address_step%5BaccountAddress%5D%5Bnip%5D=&" \
        #        f"cart_flow_address_step%5BaccountAddress%5D%5Bphone%5D={self.profile['phone']}&" \
        #        f"cart_flow_address_step%5BaccountAddress%5D%5Bstreet%5D={self.profile['street']}&" \
        #        f"cart_flow_address_step%5BaccountAddress%5D%5BhouseNumber%5D={self.profile['house_number']}&" \
        #        f"cart_flow_address_step%5BaccountAddress%5D%5BapartmentNumber%5D=&" \
        #        f"cart_flow_address_step%5BaccountAddress%5D%5Bpostcode%5D={self.profile['post_code']}&" \
        #        f"cart_flow_address_step%5BaccountAddress%5D%5Bcity%5D={self.profile['city']}&" \
        #        f"cart_flow_address_step%5BsameTransportAddress%5D=1&" \
        #        f"cart_flow_address_step%5BtransportAddress%5D%5Bcompany%5D=&" \
        #        f"cart_flow_address_step%5BtransportAddress%5D%5BfirstName%5D=&" \
        #        f"cart_flow_address_step%5BtransportAddress%5D%5BlastName%5D=&" \
        #        f"cart_flow_address_step%5BtransportAddress%5D%5Bphone%5D=&" \
        #        f"cart_flow_address_step%5BtransportAddress%5D%5Bstreet%5D=&" \
        #        f"cart_flow_address_step%5BtransportAddress%5D%5BhouseNumber%5D=&" \
        #        f"cart_flow_address_step%5BtransportAddress%5D%5BapartmentNumber%5D=&" \
        #        f"cart_flow_address_step%5BtransportAddress%5D%5Bpostcode%5D=&" \
        #        f"cart_flow_address_step%5BtransportAddress%5D%5Bcity%5D=&" \
        #        f"cart_flow_address_step%5BsameBillingAddress%5D=1&" \
        #        f"cart_flow_address_step%5BbillingAddress%5D%5BfirstName%5D=&" \
        #        f"cart_flow_address_step%5BbillingAddress%5D%5BlastName%5D=&" \
        #        f"cart_flow_address_step%5BbillingAddress%5D%5BaddressType%5D=person&" \
        #        f"cart_flow_address_step%5BbillingAddress%5D%5Bcompany%5D=&" \
        #        f"cart_flow_address_step%5BbillingAddress%5D%5Bnip%5D=&" \
        #        f"cart_flow_address_step%5BbillingAddress%5D%5Bphone%5D=&" \
        #        f"cart_flow_address_step%5BbillingAddress%5D%5Bstreet%5D=&" \
        #        f"cart_flow_address_step%5BbillingAddress%5D%5BhouseNumber%5D=&" \
        #        f"cart_flow_address_step%5BbillingAddress%5D%5BapartmentNumber%5D=&" \
        #        f"cart_flow_address_step%5BbillingAddress%5D%5Bpostcode%5D=&" \
        #        f"cart_flow_address_step%5BbillingAddress%5D%5Bcity%5D=&" \
        #        f"cart_flow_address_step%5BconsentForm%5D%5Bconsent_1778%5D%5B%5D=1778&" \
        #        f"cart_flow_address_step%5BtransportAddress%5D%5BaddressType%5D=person&" \
        #        f"cart_flow_address_step%5BcustomerComment%5D=&" \
        #        f"cart_flow_address_step%5B_token%5D={self.token}"

        data = f"cart_flow_address_step%5BaccountAddress%5D%5BfirstName%5D=gfds&cart_flow_address_step%5BaccountAddress%5D%5BlastName%5D=agfd&cart_flow_address_step%5BaccountAddress%5D%5Bemail%5D=afdasdf%40gmail.com&cart_flow_address_step%5BaccountAddress%5D%5BaddressType%5D=person&cart_flow_address_step%5BaccountAddress%5D%5Bcompany%5D=&cart_flow_address_step%5BaccountAddress%5D%5Bnip%5D=&cart_flow_address_step%5BaccountAddress%5D%5Bphone%5D=543-897-987&cart_flow_address_step%5BaccountAddress%5D%5Bstreet%5D=gsfads&cart_flow_address_step%5BaccountAddress%5D%5BhouseNumber%5D=34&cart_flow_address_step%5BaccountAddress%5D%5BapartmentNumber%5D=&cart_flow_address_step%5BaccountAddress%5D%5Bpostcode%5D=42-341&cart_flow_address_step%5BaccountAddress%5D%5Bcity%5D=hdfsd&cart_flow_address_step%5BsameTransportAddress%5D=1&cart_flow_address_step%5BtransportAddress%5D%5Bcompany%5D=&cart_flow_address_step%5BtransportAddress%5D%5BfirstName%5D=&cart_flow_address_step%5BtransportAddress%5D%5BlastName%5D=&cart_flow_address_step%5BtransportAddress%5D%5Bphone%5D=&cart_flow_address_step%5BtransportAddress%5D%5Bstreet%5D=&cart_flow_address_step%5BtransportAddress%5D%5BhouseNumber%5D=&cart_flow_address_step%5BtransportAddress%5D%5BapartmentNumber%5D=&cart_flow_address_step%5BtransportAddress%5D%5Bpostcode%5D=&cart_flow_address_step%5BtransportAddress%5D%5Bcity%5D=&cart_flow_address_step%5BsameBillingAddress%5D=1&cart_flow_address_step%5BbillingAddress%5D%5BfirstName%5D=&cart_flow_address_step%5BbillingAddress%5D%5BlastName%5D=&cart_flow_address_step%5BbillingAddress%5D%5BaddressType%5D=person&cart_flow_address_step%5BbillingAddress%5D%5Bcompany%5D=&cart_flow_address_step%5BbillingAddress%5D%5Bnip%5D=&cart_flow_address_step%5BbillingAddress%5D%5Bphone%5D=&cart_flow_address_step%5BbillingAddress%5D%5Bstreet%5D=&cart_flow_address_step%5BbillingAddress%5D%5BhouseNumber%5D=&cart_flow_address_step%5BbillingAddress%5D%5BapartmentNumber%5D=&cart_flow_address_step%5BbillingAddress%5D%5Bpostcode%5D=&cart_flow_address_step%5BbillingAddress%5D%5Bcity%5D=&cart_flow_address_step%5BconsentForm%5D%5Bconsent_1925%5D%5B%5D=1925&cart_flow_address_step%5BconsentForm%5D%5Bconsent_1760%5D%5B%5D=1760&cart_flow_address_step%5BconsentForm%5D%5Bconsent_1778%5D%5B%5D=1778&cart_flow_address_step%5BtransportAddress%5D%5BaddressType%5D=person&cart_flow_address_step%5BcustomerComment%5D=&cart_flow_address_step%5B_token%5D={self.token}"

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
        try:
            send_address_req = await client.post("https://sklep.sizeer.com/koszyk/adres/zapisz", headers=headers,
                                                 data=data)

            curr_token = re.search(r'name="cart_flow_summation_step(.)_token(.)" value="(.*?)"',
                                   send_address_req.text)
            while not curr_token:
                await asyncio.sleep(.1)
                self.errors_num += 1
                if self.errors_num > 5:
                    self.errors_num = 0
                    if self.task['bypass'] == "enable":
                        await self.load_bypass_product()
                    else:
                        await self.load_product()
                    return
                send_address_req = await client.post("https://sklep.sizeer.com/koszyk/adres/zapisz",
                                                     headers=headers, data=data)
                curr_token = re.search(r'name="cart_flow_summation_step(.)_token(.)" value="(.*?)"',
                                       send_address_req.text)

            self.checkout_token = curr_token.group().split('"')[-2]
            return client
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Posting address: "
                  f"{error}. Retrying...")
            self.errors_num += 1
            if self.errors_num > 5:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    await self.load_bypass_product()
                else:
                    await self.load_product()
            else:
                await self.send_address()
            return

        # if self.task['bypass'] == "enable":
        #     self.bypass = "done"
        #     self.product_url = self.task['product_url']
        #     print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}]"
        #           f" Bypass loaded.")
        #     await self.load_product()
        #     return
        # else:
        # await self.sum_order(client)

    async def sum_order(self, client):
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}]"
              f" Checking out... {time.time() - self.start}")
        data = f"cart_flow_summation_step%5B_token%5D={self.checkout_token}"
        return
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
        try:
            order_summary = await self.client.post("https://sklep.sizeer.com/koszyk/podsumowanie/zapisz", headers=headers,
                                                    data=data)
            while "Twoje zamówienie zostało zarejestrowane pod" not in order_summary.text:
                await asyncio.sleep(.1)
                self.errors_num += 1
                if self.errors_num > 5:
                    self.errors_num = 0
                    await self.load_product()
                    return
                order_summary = await self.client.post("https://sklep.sizeer.com/koszyk/podsumowanie/zapisz",
                                                        headers=headers, data=data)

            print(f'{datetime.datetime.now().strftime("[%H:%M:%S:%f]")} [TASK {self.task["id"]}] Successful '
                  f'checkout. Email: {self.profile["email"].replace("%40", "@")}')
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Order page: {error}. "
                  f"Retrying...")
            self.errors_num += 1
            if self.errors_num > 5:
                self.errors_num = 0
                await self.load_product()
            else:
                await self.sum_order()
            return

        # await self.send_webhook()
        # return

    # async def send_webhook(self):
    #     webhook = DiscordWebhook(url=self.task['webhook_url'],username="Sizeer")
    #     embed = DiscordEmbed(title='Successfully checked out a product.', color=242424)
    #     embed.set_footer(text='via Internet Explorer', icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb"
    #                                                             "/1/1b/Internet_Explorer_9_icon.svg/384px-Internet_"
    #                                                             "Explorer_9_icon.svg.png")
    #     embed.set_timestamp()
    #     embed.add_embed_field(name='Product', value=self.title)
    #     embed.add_embed_field(name='Style Code', value=self.task['sku'].upper())
    #     embed.add_embed_field(name='Size', value=self.task['size'])
    #     embed.set_thumbnail(url=self.image_url)
    #     embed.add_embed_field(name='Email', value=self.profile["email"].replace("%40", "@"))
    #     webhook.add_embed(embed)
    #     response = await webhook.execute()


# async def main(tasks, profiles):
#     await asyncio.gather(*[SizeerBot(tasks[i], profiles[0]).load_bypass_product() for i in range(len(tasks))])


def main(task, profile):
    task = SizeerBot(task, profile)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    client = loop.run_until_complete(task.load_bypass_product())
    client = loop.run_until_complete(task.add_to_basket(client))
    client = loop.run_until_complete(task.load_cart_page(client))
    client = loop.run_until_complete(task.send_order_info(client))
    client = loop.run_until_complete(task.load_address_page(client))
    client = loop.run_until_complete(task.send_address(client))
    client = loop.run_until_complete(task.sum_order(client))
    # asyncio.get_event_loop().run_until_complete(SizeerBot(task, profile).load_bypass_product())


if __name__ == "__main__":
    with open("USER_INPUT_DATA/tasks.json", "r") as f1, \
            open("USER_INPUT_DATA/proxies.txt", "r") as f2, \
            open("USER_INPUT_DATA/profiles.json", "r") as f3:
        tasks = json.load(f1)
        proxies = f2.read().split("\n")
        profiles = json.load(f3)
    processes = []

    with ThreadPoolExecutor(100) as executor:
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






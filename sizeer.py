# coding=utf8
from discord_webhook import DiscordWebhook, DiscordEmbed
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from bs4 import BeautifulSoup
import datetime
import re
import json
import requests
import time


class SizeerBot:
    def __init__(self, task, profile):
        self.task = task
        self.product_url = ""
        self.path = ""
        self.s = requests.Session()
        self.title = ""
        self.image_url = ""
        self.profile = profile
        self.pid = ""
        self.curr_sizes = []
        self.token = ""
        self.errors_num = 0
        self.start = ''
        self.hash = ""
        self.checkout_token = ""
        self.bypass = ""

    def login(self):
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
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Logging in...")
            login_page = self.s.get("https://sklep.sizeer.com/login", headers=headers, proxies=self.task['proxy_dict'],
                                    timeout=10)
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
            login_check = self.s.post("https://sklep.sizeer.com/login_check", headers=login_headers, data=login_data,
                                      proxies=self.task['proxy_dict'], timeout=10)
            while not json.loads(login_check.content)["loginSuccess"]:
                time.sleep(.1)
                self.errors_num += 1
                if self.errors_num > 10:
                    self.errors_num = 0
                    self.login()
                    return
                login_check = self.s.post("https://sklep.sizeer.com/login_check", headers=login_headers,
                                          data=login_data,
                                          proxies=self.task['proxy_dict'], timeout=10)

        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Login: Connection error."
                  f" Retrying...")
            self.login()
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Login: {error}."
                  f" Retrying...")
            self.login()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Login: "
                  f"Request Error. Retrying...")
            self.login()
            return
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Login: Timeout."
                  f" Retrying...")
            self.login()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Login: {error}."
                  f" Retrying...")
            self.login()
            return

        if self.task['bypass'] == "enable":
            self.load_bypass_product()
        else:
            self.load_product()
        return

    def load_bypass_product(self):
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
            response = self.s.get("https://sklep.sizeer.com/meskie/akcesoria",
                                  headers=headers, proxies=self.task['proxy_dict'], timeout=10)
            print(response.text)
            self.product_url = "https://sklep.sizeer.com" + \
                                BeautifulSoup(response.text, "html.parser").find("a", {"class": "b-itemList_photoLink"})["href"]
            headers["Sec-Fetch-Site"] = "same-origin"
            headers['Referer'] = "https://sklep.sizeer.com/meskie/buty/sneakersy"
            bypass_product_page = self.s.get(self.product_url, headers=headers, proxies=self.task['proxy_dict'],
                                             timeout=10)
            sizes = re.findall(r'EU: (.*?)"', bypass_product_page.text)
            sizes_ids = re.findall(r'data-value="(.*?)"', bypass_product_page.text)
            sizes_dict = {}
            for i in range(len(sizes)):
                sizes_dict[sizes[i].strip()] = sizes_ids[i]
            self.pid = sizes_dict[list(sizes_dict.keys())[0]]
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Bypass: "
                  f"Connection error. Retrying...")
            self.load_bypass_product()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Bypass: {error}."
                  f" Retrying...")
            self.load_bypass_product()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Bypass: "
                  f"Request Error. Retrying...")
            self.load_bypass_product()
            return
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Bypass: Timeout."
                  f" Retrying...")
            self.load_bypass_product()
            return
        # except Exception as error:
        #     print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Bypass: {error}."
        #           f" Retrying...")
        #     self.load_bypass_product()
        #     return

        self.add_to_basket()
        return

    def load_product(self):
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
            product_page = self.s.get(self.product_url, headers=headers, proxies=self.task['proxy_dict'],
                                      timeout=7)

            while "Powiadom mnie" in product_page.text:
                time.sleep(.05)

                product_page = self.s.get(self.product_url, headers=headers, proxies=self.task['proxy_dict'],
                                          timeout=7)
                if "Powiadom mnie" not in product_page.text:
                    break

            sizes = re.findall(r'EU: (.*?) &', product_page.text)
            sizes_ids = re.findall(r'data-value="(.*?)"', product_page.text)
            sizes_dict = {}
            self.image_url = "https://sklep.sizeer.com" + \
                             re.search(rf'/media/cache/(.*?){self.task["sku"]}(.*?)\.jpg', product_page.text).group()
            self.title = re.search(r'data-ga-name="(.*?)"', product_page.text).group().split('"')[-2]
            for i in range(len(sizes)):
                sizes_dict[sizes[i].strip()] = sizes_ids[i]

            if self.task['size'] in list(sizes_dict.keys()):
                self.pid = sizes_dict[self.task['size']]
            else:
                self.task['size'] = list(sizes_dict.keys())[0]
                self.pid = sizes_dict[self.task['size']]

        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Product page: "
                  f"Connection error. Retrying...")
            self.load_product()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Product page: {error}."
                  f" Retrying...")
            self.load_product()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Product page: "
                  f"Request Error. Retrying...")
            self.load_product()
            return
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Product page: Timeout."
                  f" Retrying...")
            self.load_product()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Product page: {error}."
                  f" Retrying...")
            self.load_product()
            return

        self.add_to_basket()
        return

    def add_to_basket(self):
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
            cart_add = self.s.post("https://sklep.sizeer.com/cart/pre-x-add", headers=headers, data=data,
                                   proxies=self.task['proxy_dict'], timeout=10)
            while "Dodano pomyślnie produkt do koszyka" not in cart_add.text:
                time.sleep(.1)
                self.errors_num += 1
                if self.errors_num > 10:
                    self.errors_num = 0
                    if self.task['bypass'] == "enable":
                        self.load_bypass_product()
                    else:
                        self.load_product()
                    return
                cart_add = self.s.post("https://sklep.sizeer.com/cart/pre-x-add", headers=headers, data=data,
                                       proxies=self.task['proxy_dict'], timeout=10)

            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}]"
                  f" Successfully added to cart.")
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Carting: "
                  f"Connection error. Retrying...")
            self.add_to_basket()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Carting: {error}. "
                  f"Retrying...")
            self.errors_num += 1
            if self.errors_num > 15:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    self.load_bypass_product()
                else:
                    self.load_product()
            else:
                self.add_to_basket()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] "
                  f"Carting: Request Error. Retrying...")
            self.add_to_basket()
            return
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Carting: Timeout. "
                  f"Retrying...")
            self.add_to_basket()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Carting: {error}. "
                  f"Retrying...")
            self.errors_num += 1
            if self.errors_num > 15:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    self.load_bypass_product()
                else:
                    self.load_product()
            else:
                self.add_to_basket()
            return

        if self.bypass == "done":
            self.bypass_remove()
            self.sum_order()
            return
        else:
            self.load_cart_page()
            return

    def bypass_remove(self):
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
            bypass_remove = self.s.post("https://sklep.sizeer.com/ajax/cart/mini/remove", headers=headers, data=data,
                                        proxies=self.task['proxy_dict'], timeout=5)
            while not json.loads(bypass_remove.content)["remove"]:
                time.sleep(.1)
                self.errors_num += 1
                if self.errors_num > 10:
                    self.errors_num = 0
                    if self.task['bypass'] == "enable":
                        self.load_bypass_product()
                    else:
                        self.load_product()
                    return
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Bypass remove: "
                  f"Connection error. Retrying...")
            self.bypass_remove()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Bypass remove: {error}. "
                  f"Retrying...")
            self.errors_num += 1
            if self.errors_num > 15:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    self.load_bypass_product()
                else:
                    self.load_product()
            else:
                self.bypass_remove()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] "
                  f"Bypass remove: Request Error. Retrying...")
            self.bypass_remove()
            return
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Bypass remove: "
                  f"Timeout. Retrying...")
            self.bypass_remove()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Bypass remove: "
                  f"{error}. Retrying...")
            self.errors_num += 1
            if self.errors_num > 15:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    self.load_bypass_product()
                else:
                    self.load_product()
            else:
                self.bypass_remove()
            return

        return

    def load_cart_page(self):
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
            cart_page = self.s.get("https://sklep.sizeer.com/koszyk/lista", headers=headers,
                                   proxies=self.task['proxy_dict'], timeout=10)
            while "Sposób płatności" not in cart_page.text:
                time.sleep(.1)
                if self.errors_num > 5:
                    self.errors_num = 0
                    if self.task['bypass'] == "enable":
                        self.load_bypass_product()
                    else:
                        self.load_product()
                    return
                cart_page = self.s.get("https://sklep.sizeer.com/koszyk/lista", headers=headers,
                                       proxies=self.task['proxy_dict'], timeout=10)

            self.token = re.search(r'"cart_flow_list_step(.*?)" value="(.*?)"',
                                   cart_page.text).group().split('"')[-2]
            self.hash = re.search(r'data-item-hash="(.*?)"', cart_page.text).group().split('"')[-2]
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Cart page: "
                  f"Connection error. Retrying...")
            self.load_cart_page()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Cart page: {error}."
                  f" Retrying...")
            self.errors_num += 1
            if self.errors_num > 10:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    self.load_bypass_product()
                else:
                    self.load_product()
            else:
                self.load_cart_page()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] "
                  f"Cart page: Request Error. Retrying...")
            self.load_cart_page()
            return
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Cart page: Timeout."
                  f" Retrying...")
            self.load_cart_page()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Cart page: {error}."
                  f" Retrying...")
            self.errors_num += 1
            if self.errors_num > 5:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    self.load_bypass_product()
                else:
                    self.load_product()
            else:
                self.load_cart_page()
            return

        self.send_order_info()
        return

    def send_order_info(self):
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
            order_info_req = self.s.post("https://sklep.sizeer.com/koszyk/lista/zapisz?isAjax=1", headers=headers,
                                         proxies=self.task['proxy_dict'], data=data, timeout=10)
            while order_info_req.text.split(":")[-1][:-1] != "true":
                time.sleep(.1)
                if self.errors_num > 5:
                    self.errors_num = 0
                    if self.task['bypass'] == "enable":
                        self.load_bypass_product()
                    else:
                        self.load_product()
                    return
                order_info_req = self.s.post("https://sklep.sizeer.com/koszyk/lista/zapisz?isAjax=1", headers=headers,
                                             proxies=self.task['proxy_dict'], data=data, timeout=10)

        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Delivery: "
                  f"Connection error. Retrying...")
            self.load_cart_page()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Delivery: "
                  f"{error}. Retrying...")
            self.errors_num += 1
            if self.errors_num > 5:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    self.load_bypass_product()
                else:
                    self.load_product()
            else:
                self.load_cart_page()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Delivery: "
                  f"Request Error. Retrying...")
            self.load_cart_page()
            return
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Delivery: "
                  f"Timeout. Retrying...")
            self.load_cart_page()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Delivery: "
                  f"{error}. Retrying...")
            self.errors_num += 1
            if self.errors_num > 5:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    self.load_bypass_product()
                else:
                    self.load_product()
            else:
                self.load_cart_page()
            return

        self.load_address_page()
        return

    def load_address_page(self):
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
            address_page = self.s.get("https://sklep.sizeer.com/koszyk/adres", headers=headers,
                                      proxies=self.task['proxy_dict'], timeout=10)
            curr_token = re.search(r'name="cart_flow_address_step(.)_token(.)" value="(.*?)"', address_page.text)
            while not curr_token:
                time.sleep(.1)
                self.errors_num += 1
                if self.errors_num > 5:
                    self.errors_num = 0
                    self.load_product()
                    return
                address_page = self.s.get("https://sklep.sizeer.com/koszyk/adres", headers=headers,
                                          proxies=self.task['proxy_dict'], timeout=10)
                curr_token = re.search(r'name="cart_flow_address_step(.)_token(.)" value="(.*?)"', address_page.text)

            self.token = curr_token.group().split('"')[-2]
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Address page: "
                  f"Connection error. Retrying...")
            self.load_address_page()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Address page: {error}."
                  f" Retrying...")
            self.errors_num += 1
            if self.errors_num > 5:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    self.load_bypass_product()
                else:
                    self.load_product()
            else:
                self.load_address_page()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] "
                  f"Address page: Request Error. Retrying...")
            self.load_address_page()
            return
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Address page: Timeout."
                  f" Retrying...")
            self.load_address_page()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Address page: {error}."
                  f" Retrying...")
            self.errors_num += 1
            if self.errors_num > 5:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    self.load_bypass_product()
                else:
                    self.load_product()
            else:
                self.load_address_page()
            return

        self.send_address()
        return

    def send_address(self):
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}]"
              f" Filling address form...")

        data = f"cart_flow_address_step%5BaccountAddress%5D%5BfirstName%5D={self.profile['first_name']}&" \
               f"cart_flow_address_step%5BaccountAddress%5D%5BlastName%5D={self.profile['last_name']}&" \
               f"cart_flow_address_step%5BaccountAddress%5D%5Bemail%5D={self.profile['email']}&" \
               f"cart_flow_address_step%5BaccountAddress%5D%5BaddressType%5D=person&" \
               f"cart_flow_address_step%5BaccountAddress%5D%5Bcompany%5D=&" \
               f"cart_flow_address_step%5BaccountAddress%5D%5Bnip%5D=&" \
               f"cart_flow_address_step%5BaccountAddress%5D%5Bphone%5D={self.profile['phone']}&" \
               f"cart_flow_address_step%5BaccountAddress%5D%5Bstreet%5D={self.profile['street']}&" \
               f"cart_flow_address_step%5BaccountAddress%5D%5BhouseNumber%5D={self.profile['house_number']}&" \
               f"cart_flow_address_step%5BaccountAddress%5D%5BapartmentNumber%5D=&" \
               f"cart_flow_address_step%5BaccountAddress%5D%5Bpostcode%5D={self.profile['post_code']}&" \
               f"cart_flow_address_step%5BaccountAddress%5D%5Bcity%5D={self.profile['city']}&" \
               f"cart_flow_address_step%5BsameTransportAddress%5D=1&" \
               f"cart_flow_address_step%5BtransportAddress%5D%5Bcompany%5D=&" \
               f"cart_flow_address_step%5BtransportAddress%5D%5BfirstName%5D=&" \
               f"cart_flow_address_step%5BtransportAddress%5D%5BlastName%5D=&" \
               f"cart_flow_address_step%5BtransportAddress%5D%5Bphone%5D=&" \
               f"cart_flow_address_step%5BtransportAddress%5D%5Bstreet%5D=&" \
               f"cart_flow_address_step%5BtransportAddress%5D%5BhouseNumber%5D=&" \
               f"cart_flow_address_step%5BtransportAddress%5D%5BapartmentNumber%5D=&" \
               f"cart_flow_address_step%5BtransportAddress%5D%5Bpostcode%5D=&" \
               f"cart_flow_address_step%5BtransportAddress%5D%5Bcity%5D=&" \
               f"cart_flow_address_step%5BsameBillingAddress%5D=1&" \
               f"cart_flow_address_step%5BbillingAddress%5D%5BfirstName%5D=&" \
               f"cart_flow_address_step%5BbillingAddress%5D%5BlastName%5D=&" \
               f"cart_flow_address_step%5BbillingAddress%5D%5BaddressType%5D=person&" \
               f"cart_flow_address_step%5BbillingAddress%5D%5Bcompany%5D=&" \
               f"cart_flow_address_step%5BbillingAddress%5D%5Bnip%5D=&" \
               f"cart_flow_address_step%5BbillingAddress%5D%5Bphone%5D=&" \
               f"cart_flow_address_step%5BbillingAddress%5D%5Bstreet%5D=&" \
               f"cart_flow_address_step%5BbillingAddress%5D%5BhouseNumber%5D=&" \
               f"cart_flow_address_step%5BbillingAddress%5D%5BapartmentNumber%5D=&" \
               f"cart_flow_address_step%5BbillingAddress%5D%5Bpostcode%5D=&" \
               f"cart_flow_address_step%5BbillingAddress%5D%5Bcity%5D=&" \
               f"cart_flow_address_step%5BconsentForm%5D%5Bconsent_1778%5D%5B%5D=1778&" \
               f"cart_flow_address_step%5BtransportAddress%5D%5BaddressType%5D=person&" \
               f"cart_flow_address_step%5BcustomerComment%5D=&" \
               f"cart_flow_address_step%5B_token%5D={self.token}"
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
            send_address_req = self.s.post("https://sklep.sizeer.com/koszyk/adres/zapisz", headers=headers,
                                           data=data, proxies=self.task['proxy_dict'], timeout=10)
            curr_token = re.search(r'name="cart_flow_summation_step(.)_token(.)" value="(.*?)"',
                                   send_address_req.text)
            while not curr_token:
                time.sleep(.1)
                self.errors_num += 1
                if self.errors_num > 5:
                    self.errors_num = 0
                    if self.task['bypass'] == "enable":
                        self.load_bypass_product()
                    else:
                        self.load_product()
                    return
                send_address_req = self.s.post("https://sklep.sizeer.com/koszyk/adres/zapisz", headers=headers,
                                               data=data, proxies=self.task['proxy_dict'], timeout=10)
                curr_token = re.search(r'name="cart_flow_summation_step(.)_token(.)" value="(.*?)"',
                                       send_address_req.text)

            self.checkout_token = curr_token.group().split('"')[-2]
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Posting address: "
                  f"Connection error. Retrying...")
            self.send_address()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Posting address: "
                  f"{error}. Retrying...")
            self.errors_num += 1
            if self.errors_num > 5:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    self.load_bypass_product()
                else:
                    self.load_product()
            else:
                self.send_address()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Posting address: "
                  f"Request Error. Retrying...")
            self.send_address()
            return
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Posting address: "
                  f"Timeout. Retrying...")
            self.send_address()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Posting address: "
                  f"{error}. Retrying...")
            self.errors_num += 1
            if self.errors_num > 5:
                self.errors_num = 0
                if self.task['bypass'] == "enable":
                    self.load_bypass_product()
                else:
                    self.load_product()
            else:
                self.send_address()
            return

        # if self.task['bypass'] == "enable":
        #     self.bypass = "done"
        #     self.product_url = self.task['product_url']
        #     print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}]"
        #           f" Bypass loaded.")
        #     self.load_product()
        #     return
        # else:
        self.sum_order()
        return

    def sum_order(self):
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}]"
              f" Checking out... {time.time() - self.start}")
        data = f"cart_flow_summation_step%5B_token%5D={self.checkout_token}"
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
            order_summary = self.s.post("https://sklep.sizeer.com/koszyk/podsumowanie/zapisz", headers=headers,
                                        data=data, proxies=self.task['proxy_dict'], timeout=15)
            # edit
            while "Twoje zamówienie zostało zarejestrowane pod" not in order_summary.text:
                time.sleep(.1)
                self.errors_num += 1
                if self.errors_num > 5:
                    self.errors_num = 0
                    self.load_product()
                    return
                order_summary = self.s.post("https://sklep.sizeer.com/koszyk/podsumowanie/zapisz", headers=headers,
                                            data=data, proxies=self.task['proxy_dict'])

            print(f'{datetime.datetime.now().strftime("[%H:%M:%S:%f]")} [TASK {self.task["id"]}] Successful '
                  f'checkout. Email: {self.profile["email"].replace("%40", "@")}')
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Order page: "
                  f"Connection error. Retrying...")
            self.sum_order()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Order page: {error}. "
                  f"Retrying...")
            self.errors_num += 1
            if self.errors_num > 5:
                self.errors_num = 0
                self.load_product()
            else:
                self.sum_order()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] "
                  f"Order page: Request error. Retrying...")
            self.sum_order()
            return
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Order page: Timeout. "
                  f"Retrying...")
            self.sum_order()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Order page: {error}. "
                  f"Retrying...")
            self.errors_num += 1
            if self.errors_num > 5:
                self.errors_num = 0
                self.load_product()
            else:
                self.sum_order()
            return

        # self.send_webhook()

    def send_webhook(self):
        webhook = DiscordWebhook(url=self.task['webhook_url'],username="Sizeer")
        embed = DiscordEmbed(title='Successfully checked out a product.', color=242424)
        embed.set_footer(text='via Internet Explorer', icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb"
                                                                "/1/1b/Internet_Explorer_9_icon.svg/384px-Internet_"
                                                                "Explorer_9_icon.svg.png")
        embed.set_timestamp()
        embed.add_embed_field(name='Product', value=self.title)
        embed.add_embed_field(name='Style Code', value=self.task['sku'].upper())
        embed.add_embed_field(name='Size', value=self.task['size'])
        embed.set_thumbnail(url=self.image_url)
        embed.add_embed_field(name='Email', value=self.profile["email"].replace("%40", "@"))
        webhook.add_embed(embed)
        response = webhook.execute()


def main(task, profile):
    new_instance = SizeerBot(task, profile)
    new_instance.load_bypass_product()


if __name__ == "__main__":
    with open("USER_INPUT_DATA/tasks.json", "r") as f1, \
            open("USER_INPUT_DATA/proxies.txt", "r") as f2, \
            open("USER_INPUT_DATA/profiles.json", "r") as f3:
        tasks = json.load(f1)
        proxies = f2.read().split("\n")
        profiles = json.load(f3)
    threads = []
    from threading import Thread
    from multiprocessing import Process
    # start = time.time()

    for i in range(len(tasks)):
        proxy_list = proxies[i].split(":")
        proxy_dict = {
            "http": f"http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}",
            "https": f"https://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}"
        }
        tasks[i]["proxy_dict"] = proxy_dict
        p = Process(target=main, args=(tasks[i], profiles[0]))
        p.start()
        threads.append(p)

    for p in threads:
        p.join()
    # with ProcessPoolExecutor(max_workers=len(tasks)) as executor:
    #     futures = []
    #     for i in range(len(tasks)):
    #         proxy_list = proxies[i].split(":")
    #         proxy_dict = {
    #             "http": f"http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}",
    #             "https": f"https://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}"
    #         }
    #         tasks[i]["proxy_dict"] = proxy_dict
    #         task_data = [tasks[i], profiles[0]]
    #         futures.append(executor.submit(lambda p: main(*p), task_data))
    #
    #     results = []
    #     for result in as_completed(futures):
    #         results.append(result)
    # print(time.time() - start)
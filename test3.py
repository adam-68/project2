from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import time
import datetime
import json
import httpx
import re


async def load_bypass_product(task, product_url):
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
    try:
        async with httpx.AsyncClient(proxies=task['proxy'], timeout=20.0) as client:
            response = await client.get("https://sklep.sizeer.com/meskie/akcesoria?sort=price_asc&limit=60&page=1",
                                        headers=headers)
            cookies = client.cookies
            # loop = asyncio.new_event_loop()
            # product_url = "https://sklep.sizeer.com" + \
            #                    BeautifulSoup(response.text, "html.parser").find("a", {"class": "b-itemList_photoLink"})[
            #                        "href"]

            # print(product_url)
            headers["Sec-Fetch-Site"] = "same-origin"
            headers['Referer'] = "https://sklep.sizeer.com/meskie/buty/sneakersy"
            bypass_product_page = await client.get(product_url, headers=headers)
            sizes = re.findall(r'EU: (.*?)"', bypass_product_page.text)
            sizes_ids = re.findall(r'data-value="(.*?)"', bypass_product_page.text)
            sizes_dict = {}
            for i in range(len(sizes)):
                sizes_dict[sizes[i].strip()] = sizes_ids[i]
            pid = sizes_dict[list(sizes_dict.keys())[0]]
            return [client, pid, start]
    except Exception as error:
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}] Bypass: {error}."
              f" Retrying...")
        await load_bypass_product(task, product_url)
        return


async def load_product(task, client, product_url):
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

    print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}] Waiting for product...")
    try:
        product_page = await client.get(product_url, headers=headers)
        await asyncio.sleep(0)
        while "Powiadom mnie" in product_page.text:
            await asyncio.sleep(.05)
            product_page = await client.get(product_url, headers=headers)
        product_page_text = product_page.text

        sizes = re.findall(r'EU: (.*?) &', product_page_text)
        sizes_ids = re.findall(r'data-value="(.*?)"', product_page_text)
        sizes_dict = {}
        image_url = "https://sklep.sizeer.com" + \
                         re.search(rf'/media/cache/(.*?){task["sku"]}(.*?)\.jpg', product_page_text).group()
        title = re.search(r'data-ga-name="(.*?)"', product_page_text).group().split('"')[-2]
        for i in range(len(sizes)):
            sizes_dict[sizes[i].strip()] = sizes_ids[i]

        if task['size'] in list(sizes_dict.keys()):
            pid = sizes_dict[task['size']]
        else:
            task['size'] = list(sizes_dict.keys())[0]
            pid = sizes_dict[task['size']]

    except Exception as error:
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}] Product page: {error}."
              f" Retrying...")
        await load_product()
        return


    return [client, pid]


async def add_to_basket(task, client, pid, product_url):
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
        "Referer": product_url,
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
    }

    try:
        cart_add = await client.post("https://sklep.sizeer.com/cart/pre-x-add",
                                     headers=headers, data=data)
        await asyncio.sleep(0)
        while "Dodano pomyślnie produkt do koszyka" not in cart_add.text:
            await asyncio.sleep(.1)
            cart_add = await client.post("https://sklep.sizeer.com/cart/pre-x-add",
                                         headers=headers, data=data)

        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}]"
              f" Successfully added to cart.")

    except Exception as error:
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}] Carting: {error}. "
              f"Retrying...")
        return

    return client

    # if bypass == "done":
    #     await bypass_remove()
    #     await sum_order()
    #     return
    # else:
    #     await load_cart_page()
    #     return


# async def bypass_remove(self):
#     data = f"hash={hash}"
#     headers = {
#         "Host": "sklep.sizeer.com",
#         "Connection": "keep-alive",
#         "Content-Length": str(len(data)),
#         "Accept": "application/json, text/javascript, */*; q=0.01",
#         "X-Requested-With": "XMLHttpRequest",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
#                       "Chrome/83.0.4103.106 Safari/537.36",
#         "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
#         "Origin": "https://sklep.sizeer.com",
#         "Sec-Fetch-Site": "same-origin",
#         "Sec-Fetch-Mode": "cors",
#         "Sec-Fetch-Dest": "empty",
#         "Referer": product_url,
#         "Accept-Encoding": "gzip, deflate, br",
#         "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
#     }
#     try:
#         async with httpx.AsyncClient(proxies=task['proxy'], cookies=cookies) as client:
#             bypass_remove = await client.post("https://sklep.sizeer.com/ajax/cart/mini/remove",
#                                               headers=headers, data=data)
#             while not json.loads(bypass_remove.content)["remove"]:
#                 await asyncio.sleep(.1)
#                 errors_num += 1
#                 if errors_num > 10:
#                     errors_num = 0
#                     if task['bypass'] == "enable":
#                         await load_bypass_product()
#                     else:
#                         await load_product()
#                     return
#     except Exception as error:
#         print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}] Bypass remove: "
#               f"{error}. Retrying...")
#         errors_num += 1
#         if errors_num > 15:
#             errors_num = 0
#             if task['bypass'] == "enable":
#                 await load_bypass_product()
#             else:
#                 await load_product()
#         else:
#             await bypass_remove()
#         return
#
#     return


async def load_cart_page(task, client, product_url):
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
        "Referer": product_url,
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
    }

    try:
        cart_page = await client.get("https://sklep.sizeer.com/koszyk/lista", headers=headers)
        while "Sposób płatności" not in cart_page.text:
            await asyncio.sleep(.1)
            cart_page = await client.get("https://sklep.sizeer.com/koszyk/lista", headers=headers)
        token = re.search(r'"cart_flow_list_step(.*?)" value="(.*?)"',
                          cart_page.text).group().split('"')[-2]
        hash = re.search(r'data-item-hash="(.*?)"', cart_page.text).group().split('"')[-2]
    except Exception as error:
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}] Cart page: {error}."
              f" Retrying...")
        return

    return [client, token, hash]


async def send_order_info(task, client, token):
    print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}]"
          f" Filling delivery form...")
    # Pobranie
    # data = f"cart_flow_list_step%5B_token%5D={token}&" \
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

    try:
        order_info_req = await client.post("https://sklep.sizeer.com/koszyk/lista/zapisz?isAjax=1",
                                           headers=headers, data=data)
        while order_info_req.text.split(":")[-1][:-1] != "true":
            await asyncio.sleep(.1)
            order_info_req = await client.post("https://sklep.sizeer.com/koszyk/lista/zapisz?isAjax=1",
                                               headers=headers, data=data)
    except Exception as error:
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}] Delivery: "
              f"{error}. Retrying...")
        return

    return client


async def load_address_page(task, client):
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

            address_page = await client.get("https://sklep.sizeer.com/koszyk/adres", headers=headers)
            curr_token = re.search(r'name="cart_flow_address_step(.)_token(.)" value="(.*?)"',
                                   address_page.text)

        token = curr_token.group().split('"')[-2]
    except Exception as error:
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}] Address page: {error}."
              f" Retrying...")

        return

    return [client, token]


async def send_address(task, client, token, profile):
    print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}]"
          f" Filling address form...")

    data = f"cart_flow_address_step%5BaccountAddress%5D%5BfirstName%5D={profile['first_name']}&" \
           f"cart_flow_address_step%5BaccountAddress%5D%5BlastName%5D={profile['last_name']}&" \
           f"cart_flow_address_step%5BaccountAddress%5D%5Bemail%5D={profile['email']}&" \
           f"cart_flow_address_step%5BaccountAddress%5D%5BaddressType%5D=person&" \
           f"cart_flow_address_step%5BaccountAddress%5D%5Bcompany%5D=&" \
           f"cart_flow_address_step%5BaccountAddress%5D%5Bnip%5D=&" \
           f"cart_flow_address_step%5BaccountAddress%5D%5Bphone%5D={profile['phone']}&" \
           f"cart_flow_address_step%5BaccountAddress%5D%5Bstreet%5D={profile['street']}&" \
           f"cart_flow_address_step%5BaccountAddress%5D%5BhouseNumber%5D={profile['house_number']}&" \
           f"cart_flow_address_step%5BaccountAddress%5D%5BapartmentNumber%5D=&" \
           f"cart_flow_address_step%5BaccountAddress%5D%5Bpostcode%5D={profile['post_code']}&" \
           f"cart_flow_address_step%5BaccountAddress%5D%5Bcity%5D={profile['city']}&" \
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
           f"cart_flow_address_step%5B_token%5D={token}"

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
    try:
        send_address_req = await client.post("https://sklep.sizeer.com/koszyk/adres/zapisz", headers=headers,
                                             data=data)

        curr_token = re.search(r'name="cart_flow_summation_step(.)_token(.)" value="(.*?)"',
                               send_address_req.text)
        while not curr_token:
            await asyncio.sleep(.1)

            send_address_req = await client.post("https://sklep.sizeer.com/koszyk/adres/zapisz",
                                                 headers=headers, data=data)
            curr_token = re.search(r'name="cart_flow_summation_step(.)_token(.)" value="(.*?)"',
                                   send_address_req.text)

        checkout_token = curr_token.group().split('"')[-2]
    except Exception as error:
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}] Posting address: "
              f"{error}. Retrying...")

        return

    return [client, checkout_token]
    # if task['bypass'] == "enable":
    #     bypass = "done"
    #     product_url = task['product_url']
    #     print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}]"
    #           f" Bypass loaded.")
    #     await load_product()
    #     return
    # else:
    #     await sum_order()
    #     return


async def sum_order(task, client, checkout_token, start):
    print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}]"
          f" Checking out... {time.time() - start}")
    data = f"cart_flow_summation_step%5B_token%5D={checkout_token}"
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
        order_summary = await client.post("https://sklep.sizeer.com/koszyk/podsumowanie/zapisz", headers=headers,
                                               data=data)
        while "Twoje zamówienie zostało zarejestrowane pod" not in order_summary.text:
            await asyncio.sleep(.1)
            errors_num += 1
            if errors_num > 5:
                errors_num = 0
                await load_product()
                return
            order_summary = await client.post("https://sklep.sizeer.com/koszyk/podsumowanie/zapisz",
                                                   headers=headers, data=data)

        print(f'{datetime.datetime.now().strftime("[%H:%M:%S:%f]")} [TASK {task["id"]}] Successful '
              f'checkout. Email: {profile["email"].replace("%40", "@")}')
    except Exception as error:
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {task['id']}] Order page: {error}. "
              f"Retrying...")
        errors_num += 1
        if errors_num > 5:
            errors_num = 0
            await load_product()
        else:
            await sum_order()
        return

    await send_webhook()
    return


async def configure(task, profile):
    product_url = "https://sklep.sizeer.com/sizeer-skarpety-frote-2ppk-mix-7609-unisex-skarpetki-czarny-sisk7609"
    resp = await load_bypass_product(task, product_url)
    resp2 = await add_to_basket(task, resp[0], resp[1], product_url)
    resp3 = await load_cart_page(task, resp2, product_url)
    respp = await send_order_info(task, resp3[0], resp3[1])
    resp4 = await load_address_page(task, respp)
    resp5 = await send_address(task, resp4[0], resp4[1], profile)
    resp6 = await sum_order(task, resp5[0], resp5[1], resp[-1])


# async def main(tasks, profiles):
#     await asyncio.gather(*[configure(tasks[i], profiles[0]) for i in range(len(tasks))])


def start(task, profile):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.get_event_loop().run_until_complete(configure(task, profile))


if __name__ == "__main__":
    with open("USER_INPUT_DATA/tasks.json", "r") as f1, \
            open("USER_INPUT_DATA/proxies.txt", "r") as f2, \
            open("USER_INPUT_DATA/profiles.json", "r") as f3:
        tasks = json.load(f1)
        proxies = f2.read().split("\n")
        profiles = json.load(f3)
    processes = []

    with ThreadPoolExecutor(10) as executor:
        futures = []

        for i in range(len(tasks)):
            proxy_list = proxies[i].split(":")
            proxy = f"http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}"
            tasks[i]["proxy"] = proxy
            task_data = [tasks[i], profiles[0]]
            futures.append(executor.submit(lambda p: start(*p), task_data))

        results = []
        for future in as_completed(futures):
            results.append(future)

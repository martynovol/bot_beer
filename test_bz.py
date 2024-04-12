from id import token
import requests
import asyncio
import time
import json
#from handlers import inf


from multiprocessing import Process
from requests.auth import HTTPBasicAuth
import sqlite3 as sq

from datetime import datetime
from datetime import date, timedelta
import string, random
import aiohttp
import calendar



def generate_random_string():
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.sample(letters_and_digits, 25))

def get_stores():
    url_get_stores = "https://online.moysklad.ru/api/remap/1.2/entity/store"
    response = requests.get(url_get_stores, headers=token.headers)
    data = json.loads(response.text)
    result = {}
    for store in data['rows']:
        result[store['name']] = store['id']
    return result


def get_retailshift():
    momentFrom, momentTo = "2023-12-22 00:00:00", "2023-12-22 00:00:00"
    url_store = "https://api.moysklad.ru/api/remap/1.2/entity/retailstore/65f3e242-9572-11ed-0a80-08e1003154b1"
    url_get_retail = f"https://api.moysklad.ru/api/remap/1.2/entity/retailshift?filter=moment>2023-12-22 5:00:00;retailStore={url_store}"
    response = requests.get(url_get_retail, headers=token.headers)
    data = json.loads(response.text)
    if len(data["rows"]) == 0:
        print("stop")
    if "rows" not in data:
        print('sosi')
    payments = 0
    for store in data['rows']:
        if "closeDate" in store:
            print(store["receivedCash"] / 100, store["proceedsNoCash"] / 100, store["moment"], store["closeDate"])
        else:
            print(store["receivedCash"] / 100, store["proceedsNoCash"] / 100, store["moment"])
        payments = store["operations"]
    print(payments)


def retail_all():
    url_get = "https://api.moysklad.ru/api/remap/1.2/entity/store"
    response = requests.get(url_get, headers=token.headers)
    data = json.loads(response.text)
    for store in data['rows']:
        print(store['name'])

def get_id_store():
    return "https://api.moysklad.ru/api/remap/1.2/entity/retailstore/5ce6acfd-fa70-11eb-0a80-0470000342ca"

def get_retail_oborots_for_day():
    sum_sebesto = 0
    momentFrom, momentTo = get_moments("08.01.2024")
    url_get = f"https://api.moysklad.ru/api/remap/1.2/report/turnover/all?filter=retailStore={get_id_store()}"
    response = requests.get(url_get, headers=token.headers, params={'momentFrom': momentFrom, "momentTo": momentTo, "include": "zeroLines"})
    data = json.loads(response.text)
    result_report = {}
    for obj in data['rows']:
        print(obj["assortment"]['name'],"     ", obj['income']["quantity"], obj['outcome']["quantity"])
        result_report[obj["assortment"]['meta']['href']] = obj["assortment"]['name']
        sum_sebesto += obj['outcome']['sum'] / 100
    print(len(result_report), sum_sebesto)
    return result_report


def get_now_stock_product():
    get_products = get_retail_oborots_for_day()
    product_stock = {}
    print('\n\n')
    i = 0
    for url_product, product_name in get_products.items():
        url_store = get_store(get_id_store())
        url_get = f"https://api.moysklad.ru/api/remap/1.2/report/stock/bystore?filter=store={url_store};product={url_product}"
        response = requests.get(url_get, headers=token.headers)
        data = json.loads(response.text)
        if len(data['rows']) != 0:
            print(product_name, data['rows'][0]['stockByStore'][0]['stock'])
            product_stock[product_name] = int(data['rows'][0]['stockByStore'][0]['stock'])
        else:
            print(product_name, 0)
            product_stock[product_name] = 0
        i += 1
        if i == 30:
            time.sleep(10)
            i = 0
    return product_stock




def get_store(url_store):
    response = requests.get(url_store, headers=token.headers)
    data = json.loads(response.text)
    return data['store']['meta']['href']


def get_test_base():
    global base, cur
    base = sq.connect('report.db')
    cur = base.cursor()
    id_rev = generate_random_string()
    date1 = (id_rev, "5507714303", "7miIyoWYn0qkcXBp24GMJ9DZj", "24", "12", "2023", "5507714303")
    cur.execute("INSERT INTO local_revision VALUES (?,?,?,?,?,?,?)", date1)
    stocks = get_now_stock_product()
    for pr_name, stock in stocks.items():
        date2 = (generate_random_string(), id_rev, pr_name, stock, stock)
        cur.execute("INSERT INTO local_revision_position VALUES (?,?,?,?,?)", date2)
    base.commit()


def get_products_search(name):
    url_get_product = f"https://online.moysklad.ru/api/remap/1.2/entity/product?search={name}"
    response = requests.get(url_get_product, headers=token.headers)
    data = json.loads(response.text)
    result = {}
    for product in data['rows']:
        result[product['id']] = [product['name'], product['salePrices'][0]['value']]
    return result


def get_moments(now_date):
    normal_date = f"{now_date.split('.')[2]}-{now_date.split('.')[1]}-{now_date.split('.')[0]}"
    last_day = datetime.strptime(normal_date, "%Y-%m-%d") - timedelta(days=1)
    normal_last_date = f"{datetime.strftime(last_day, '%Y-%m-%d')} 00:00:00"
    normal_date = normal_date + " 02:00:00"
    return normal_last_date, normal_date

#asyncio.get_event_loop().run_until_complete(tasks())


def get_product_move():
    momentFrom, momentTo = get_moments("10.03.2024")
    url_store = get_store(get_id_store())
    url_get_move = f"https://api.moysklad.ru/api/remap/1.2/entity/move?filter=moment>{momentFrom}"

    response = requests.get(url_get_move, headers=token.headers, params={'momentFrom': momentFrom, "momentTo": momentTo})
    data = json.loads(response.text)

    for products in data['rows']:
        if url_store == products['targetStore']['meta']['href']:
            print(products["moment"], products["id"])




def get_move_positions():
    list_moves = ["ec6326ee-e0f6-11ee-0a80-167c00041789", "242b16bb-e0f1-11ee-0a80-002100149636", "7ae93d26-e02e-11ee-0a80-0bd100035166"]
    for move in list_moves:
        url_move = f"https://api.moysklad.ru/api/remap/1.2/entity/move/{move}/positions"
        response = requests.get(url_move, headers=token.headers)
        data = json.loads(response.text)
        for position in data['rows']:
            print(get_name_position(position["assortment"]["meta"]["href"]), position["quantity"])
        break


def get_name_position(url_position):
    response = requests.get(url_position, headers=token.headers)
    data = json.loads(response.text)
    return data['name']


def get_stocks_on_sklad():
    url_store = get_store(get_id_store())
    url_get_move = f"https://api.moysklad.ru/api/remap/1.2/report/stock/bystore?filter=store={url_store};moment="
    response = requests.get(url_get_move, headers=token.headers)
    data = json.loads(response.text)

    for products in data['rows']:
        #print(products["stockByStore"])
        print(get_name_position(products["meta"]["href"]), products["stockByStore"][0]["stock"])

#get_product_move()
#get_move_positions()
#get_stocks_on_sklad()


#api_key = "d1cad63a-d7a2-526b-d7e3-5a58901d6103" #Бар
#api_key = "87a245c6-d3c8-a577-d409-4a206282bed0" #Разливуха 1
api_key = "b5486293-c5b6-c999-7306-bf9fcb53aa47"#Разливуха 2
#api_keys = ["b5486293-c5b6-c999-7306-bf9fcb53aa47", "87a245c6-d3c8-a577-d409-4a206282bed0"] #Разливуха 2
shop = "593ab0b0-d892-4cf9-907b-c9360ee3bc58"
#shop = "bc55af10-416c-4277-9689-d2dde76ef23d"

curl = "https://api.kontur.ru/market"

headers = {
    "x-kontur-apikey": api_key
}


def get_organization():
    url = "https://api.kontur.ru/market/v1/organizations"
    response = requests.get(url, headers=headers)
    data = response.json()
    for item in data['items']:
        for shop in item["shops"]:
            print(shop["id"])


def get_cheque():
    url = f'{curl}/v1/shops/{shop}/cheques'
    params = {'useTime': True, 'dateFrom': '2024-03-01 00:10:00', 'dateTo': '2024-03-30 23:50:00'}
    response = requests.get(url, headers=headers, params=params)
    totalSum = {'Card': 0, 'Cash': 0}

    data = response.json()
    for i, item in enumerate(data['items']):
        cheque_sum = {'Card': 0, 'Cash': 0}
        product_name = []

        print(f"Чек №{i}")

        for position in item["lines"]:
            product_name.append((get_product_name(position["productId"]), position["count"]))
        for payment in item["payments"]:
            cheque_sum[payment['type']] = float(payment['value'].replace(",", "."))
            totalSum[payment['type']] += float(payment['value'].replace(",", "."))

        print(product_name, "\n", cheque_sum)

        print(f"--------------------------------------")

    print(totalSum)

def get_incoming():
    url = f'{curl}/v1/shops/{shop}/incoming-waybills'
    params = {'receiveDateFrom': '2024-03-01 00:10:00', 'limit': 1000}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    prices = {}
    
    for wb in data['items']:
        for position in wb['positions']:
            pos_name = get_product_name(position['productId'])
            if pos_name not in prices:
                prices[pos_name] = [position['buyPricePerUnit']]
            else:
                prices[pos_name].append(position['buyPricePerUnit'])

    print(prices)


def get_outcoming():
    prices = {}
    url = f'{curl}/v1/shops/{shop}/outgoing-waybills'
    params = {'shippingDateFrom': '2024-03-01 00:10:00', 'limit': 1000}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    for wb in data['items']:
        for position in wb['positions']:
            pos_name = get_product_name(position['positionId'])
            if pos_name not in prices:
                prices[pos_name] = [position['buyPricePerUnit']]
            else:
                prices[pos_name].append(position['buyPricePerUnit'])
    print(prices)
            

def get_product_name(pr_id):
    url = f'{curl}/v1/shops/{shop}/products/{pr_id}'
    response = requests.get(url, headers=headers)
    data = response.json()
    return data["name"]

get_incoming()
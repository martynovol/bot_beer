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


#get_product_move()
#get_move_positions()
#get_stocks_on_sklad()


#api_key = "d1cad63a-d7a2-526b-d7e3-5a58901d6103" #Бар
#api_key = "87a245c6-d3c8-a577-d409-4a206282bed0" #Разливуха 1
api_key = "b5486293-c5b6-c999-7306-bf9fcb53aa47"#Разливуха 2
#api_keys = ["b5486293-c5b6-c999-7306-bf9fcb53aa47", "87a245c6-d3c8-a577-d409-4a206282bed0"] #Разливуха 2
#shop = "593ab0b0-d892-4cf9-907b-c9360ee3bc58"
shop = "bc55af10-416c-4277-9689-d2dde76ef23d"

curl = "https://api.kontur.ru/market"

headers = {"x-kontur-apikey": api_key}


def get_organization():
    url = "https://api.kontur.ru/market/v1/organizations"
    response = requests.get(url, headers=headers)
    data = response.json()
    for item in data['items']:
        for shop in item["shops"]:
            print(shop["id"], shop["name"])



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


shop = "149e2624-4468-47c2-b7f3-e3529c1e82e7"

def get_groups():
    url = f'{curl}/v1/shops/{shop}/product-groups'
    response = requests.get(url, headers=headers)
    groups, load_groups = {}, {}
    data = response.json()
    print(data)
    for group in data['items']:
        if "parentId" not in group.keys():
            groups[group['id']] = group['name']
        else:
            load_groups[group['id']] = [group['name'], group['parentId']]

    check = bool(load_groups)
    while check:
        for group in data['items']:
            if group["id"] in load_groups and group["parentId"] in groups:
                groups[group['id']] = groups[group['parentId']] + "/" + group['name']
                load_groups.pop(group["id"])
        check = bool(load_groups)
    

    
    for gid, gr_name in groups.items():
        print(gid, gr_name)


def get_group_name(group_id):
    url = f'{curl}/v1/shops/{shop}/product-groups/{group_id}'
    response = requests.get(url, headers=headers)
    data = response.json()
    return data['name']


def get_cheque():
    for i in range(0, 1000):
        url = f'{curl}/v1/shops/{shop}/cheques'
        params = {'useTime': True, 'dateFrom': '2024-03-01 00:10:00', 'dateTo': '2024-03-30 23:50:00', 'limit': 1000, 'offset': i * 1000}
        response = requests.get(url, headers=headers, params=params)
        totalSum = {'Card': 0, 'Cash': 0}
        data = response.json()

        if len(data['items']) > 0:
            data = response.json()
            for i, item in enumerate(data['items']):
                cheque_sum = {'Card': 0, 'Cash': 0}
                product_name = []

                for position in item["lines"]:
                    product_name.append((get_product_name(position["productId"]), position["count"]))
                for payment in item["payments"]:
                    cheque_sum[payment['type']] = float(payment['value'].replace(",", "."))
                    totalSum[payment['type']] += float(payment['value'].replace(",", "."))
                print(i, totalSum)

            print(totalSum)

get_cheque()
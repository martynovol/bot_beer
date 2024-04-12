import requests, json


url_req_product = "https://online.moysklad.ru/api/remap/1.2/entity/product"
url_req = 'https://online.moysklad.ru/api/remap/1.2/entity/productfolder/668a36fb-ec5c-11ed-0a80-00cb00929e5e'
url_req_product_group = "https://online.moysklad.ru/api/remap/1.2/entity/productfolder"
#access_token = HTTPBasicAuth("cc267148a65ba4fd05481b8d1cea02fe65959b19")
headers = {"Authorization": "Bearer cc267148a65ba4fd05481b8d1cea02fe65959b19"}
response = requests.get(url_req_product_group, headers=headers)
data = json.loads(response.text)
group_products = data['rows']
for group in group_products:
   print(group['name'], group['pathName'])


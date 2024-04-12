import requests, json

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton

from create_bot import dp, bot

from database import sqlite_db

from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client, main_cassier_kb

from datetime import datetime
from datetime import date, timedelta

from handlers import inf
from requests.auth import HTTPBasicAuth


headers = {"Authorization": "Bearer cc267148a65ba4fd05481b8d1cea02fe65959b19"}


def get_response_data_group():
    url_req_product_group = "https://online.moysklad.ru/api/remap/1.2/entity/productfolder"
    response = requests.get(url_req_product_group, headers=headers)
    data = json.loads(response.text)
    return data['rows']


def get_new_path(path_now):
    group_products = get_response_data_group()
    keyboards = InlineKeyboardMarkup()
    for group in group_products:
        if group['pathName'] == path_now:
            path_name = group["name"] + '\\'
            keyboards.add(InlineKeyboardButton(f'{group["name"]}',
                                               callback_data=f"next_group {path_name}"))
    if path_now != '':
        last_path = path_now.split('\\')
        last_path.pop()
        last_path = "\\".join(last_path)
        keyboards.row(InlineKeyboardButton('<<<', callback_data=f"last_group {last_path}"))
    return keyboards


async def get_groups(message: types.Message):
    last_path = ''
    await bot.send_message(message.from_user.id, 'Группы товаров', reply_markup=get_new_path(last_path))


async def get_next_groups(callback_query: types.CallbackQuery):
    last_path = callback_query.data.split()[1]
    last_name = last_path.split("\\")[-2]
    print(last_path, last_name)
    await callback_query.message.edit_text(f'{last_name}')
    await callback_query.message.edit_reply_markup(reply_markup=get_new_path(last_path))


async def get_last_group(callback_query: types.CallbackQuery):
    last_path = callback_query.data.split()[1]
    print(last_path)
    pass
    await callback_query.message.edit_text(last_path)
    await callback_query.message.edit_reply_markup(reply_markup=get_new_path(last_path))


def register_moy_sklad(dp: Dispatcher):
    dp.register_message_handler(get_groups, Text(equals='Продукты', ignore_case=True), state="*")
    dp.register_callback_query_handler(get_next_groups, lambda x: x.data and x.data.startswith('next_group '))
    dp.register_callback_query_handler(get_last_group, lambda x: x.data and x.data.startswith('last_group '))
import json
from re import L
import sqlite3 as sq
from pprint import pprint

import httplib2
import apiclient.discovery
import requests
import traceback
from oauth2client.service_account import ServiceAccountCredentials

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton

import gspread
from gspread import Cell, Client, Spreadsheet, Worksheet
from gspread.utils import rowcol_to_a1

from create_bot import dp, bot
import sqlite3 as sq
from database import sqlite_db
from id import token

from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client

import time
from datetime import datetime
from datetime import date, timedelta

from handlers import inf
import asyncio


class FSMTable(StatesGroup):
    date1 = State()
table_url_stocks = 'https://docs.google.com/spreadsheets/d/10Yh05RDAHJCIGVhKRd_ITDv9hXDDdXt1slpI6su57io/edit?usp=sharing'
try:
    CREDENTIALS_FILE = 'handlers/admin_func/creds.json'
    spreadsheet_id = '1A5IpfMi5J1--31YfsU76It6H6eSyT-P93wB9v-fDXTM'
    table_url = 'https://docs.google.com/spreadsheets/d/1A5IpfMi5J1--31YfsU76It6H6eSyT-P93wB9v-fDXTM/edit?usp=sharing'

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_FILE,
        ['https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive'])
    httpAuth = credentials.authorize(httplib2.Http())
    service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)
except Exception:
    print('Не работает')


async def get_date_start(message: types.Message):
    admins = inf.get_admin_id()
    if message.from_user.id not in admins:
        await bot.send_message(message.from_user.id, 'Эта функция доступна только администраторам')
        return
    await FSMTable.date1.set()
    b11 = KeyboardButton(str(datetime.now().strftime('%m.%Y')))
    b12 = KeyboardButton('Назад')
    button_case_admin_report = ReplyKeyboardMarkup(resize_keyboard=True).add(b11).row(b12)
    await bot.send_message(message.from_user.id,
                           f'Впишите месяц и год за который нужно загрузить данные в таблицу в формате ММ.ГГГГ:',
                           reply_markup=button_case_admin_report)


async def get_date_finish(message: types.Message, state: FSMContext):
    try:
        await sqlite_db.info_admin(message.from_user.id, f"Выгружает таблицу")
        bit = message.text.split('.')
        if len(bit) != 2 or (len(bit[0]) != 1 and len(bit[0]) != 2) or len(bit[1]) != 4 or not bit[0].isdigit() or not bit[
            1].isdigit():
            await message.reply(f'Вы ввели некорректное число, попробуйте снова, формат "ММ.ГГГГ"')
            return
        month, year = bit[0], bit[1]
        await bot.send_message(message.from_user.id, f'Подождите, данные выгружаются',
                            reply_markup=inf.kb(message.from_user.id))
        
        clear_table()
        #load_table_socks(month, year)
        #time.sleep(10)
        upload_table(month, year)
        upload_table_defects(month, year)
        upload_table_salary(month, year)
        await sqlite_db.info_admin(message.from_user.id, f"Выгрузил таблицу")
        await state.finish()
        await bot.send_message(message.from_user.id, f'Данные успешно загружены в таблицу\n{table_url}')
    except Exception as e:
        traceback.print_exc()
        await bot.send_message(message.from_user.id, f"Произошла ошибка, обратитесь к программисту\n\n{str(e)[0:1024]}", reply_markup=inf.kb(message.from_user.id))
        await state.finish()



def load_base(month, year):
    info_base = []
    for ret in sqlite_db.cur.execute(
            'SELECT person, point1, date1, cash, non_cash, transfers, total, in_box, in_vault,expenses ,comments  FROM menu WHERE month LIKE ? AND year LIKE ?',
            [month, year]):
        u = []
        for i in range(3, 10):
            if i == 4:
                if len(ret[i].split(' ')) == 1:
                    u.append(ret[i].replace('.', ','))
                    u.append('0,0')
                    u.append('0,0')
                elif len(ret[i].split(' ')) == 2:
                    u.append(ret[i].split(' ')[0].replace('.', ','))
                    u.append(ret[i].split(' ')[1].replace('.', ','))
                    u.append('0,0')
                else:
                    u.append(ret[i].split(' ')[0].replace('.', ','))
                    u.append(ret[i].split(' ')[1].replace('.', ','))
                    u.append(ret[i].split(' ')[2].replace('.', ','))
            else:
                u.append(ret[i].replace('.', ','))
        info_base.append(
            [ret[0], ret[1], ret[2], u[0], u[1], u[2], u[3], u[4], u[5], u[6], u[7], u[8], ret[10].replace('\n', ' ')])
    return info_base


def upload_table(month, year):
    result = load_base(month, year)
    values = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"Отчёты!A2:M{len(result) + 1}",
                 "majorDimension": "ROWS",
                 "values": result},
            ]
        }
    ).execute()


def clear_table():
    clear_row = []
    for i in range(0, 399):
        clear_row.append(['', '', '', '', '', '', '', '', '', '', '', '', ''])
    values = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"Отчёты!A2:M400",
                 "majorDimension": "ROWS",
                 "values": clear_row},
            ]
        }
    ).execute()
    val2 = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"Браки!A2:M400",
                 "majorDimension": "ROWS",
                 "values": clear_row},
            ]
        }
    ).execute()
    val3 = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"Зарплаты!A2:M400",
                 "majorDimension": "ROWS",
                 "values": clear_row},
            ]
        }
    ).execute()
    clear_row = []
    for i in range(0, 99):
        clear_row.append([''] * 37)
    val4 = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"Зарплаты!I2:AS100",
                 "majorDimension": "ROWS",
                 "values": clear_row},
            ]
        }
    ).execute()


def load_base_def(month, year):
    info_base = []
    count = 0
    for ret in sqlite_db.cur.execute('SELECT point_name, date, type, product_name ,price,'
                                     ' comments, user_id, token_id FROM defects WHERE month LIKE ? '
                                     'AND year LIKE ?', [month, year]).fetchall():
        url_get_expenses = f"https://api.moysklad.ru/api/remap/1.2/entity/loss/" + ret[7]
        response = requests.get(url_get_expenses, headers=token.headers)
        data = json.loads(response.text)
        if "errors" not in data and "deleted" not in data:
            info_base.append([inf.pt_name(ret[0]), ret[1], ret[2], ret[3], str(float(ret[4]) / 100).replace('.', ',') , ret[5],
                          inf.get_name(ret[6])])
        else:
            count += 1
            print(f'Не загрузилось {ret[-1]},   {count}')
    return info_base


def load_base_sal(month, year):
    info_base, average_days = [], 0
    users_name, user_date, dates, result_date = [], {}, [], []
    for ret in sqlite_db.cur.execute('SELECT DISTINCT day FROM menu WHERE month LIKE ? AND year LIKE ? ORDER BY year ASC, month ASC, day ASC',
                                     [month, year]).fetchall():
        dates.append(ret[0])
    

    for ret in sqlite_db.cur.execute('SELECT DISTINCT person, date1 FROM menu WHERE month LIKE ? AND year LIKE ?',
                                     [month, year]).fetchall():
        if ret[0] not in users_name:
            users_name.append(ret[0])
        user_date[ret[0]] = [0] * len(dates) 

        replaces = inf.check_all_replaces(ret[0], month, year)[1]
        for replace in replaces.keys():
            user_date[ret[0]][int(replace.split('.')[0]) - 1] = round(int(replaces[replace][0]) + int(replaces[replace][1]), 0)


    for ret in sqlite_db.cur.execute("SELECT person_id, day FROM manager_report WHERE month LIKE ? AND year LIKE ? AND close <> ?", [month, year, "0"]).fetchall():
        user_name = inf.get_name(ret[0])
        if user_name not in users_name:
            users_name.append(user_name)
            user_date[user_name] = [0] * (len(dates) + 1)

        user_date[user_name][int(ret[1]) - 1] = 2500

    
    for ret in sqlite_db.cur.execute("SELECT person_id, day FROM operator_report WHERE month LIKE ? AND year LIKE ? AND close <> ?", [month, year, "0"]).fetchall():
        user_name = inf.get_name(ret[0])
        if user_name not in users_name:
            users_name.append(user_name)
            user_date[user_name] = [0] * (len(dates) + 1)

        user_date[user_name][int(ret[1]) - 1] = 1600

    
    for ret in sqlite_db.cur.execute("SELECT person_id, day FROM storager_report WHERE month LIKE ? AND year LIKE ? AND close <> ?", [month, year, "0"]).fetchall():
        user_name = inf.get_name(ret[0])
        if user_name not in users_name:
            users_name.append(user_name)
            user_date[user_name] = [0] * (len(dates) + 1)

        user_date[user_name][int(ret[1]) - 1] = 2050

    
    for ret in sqlite_db.cur.execute("SELECT person_id, day FROM driver_report WHERE month LIKE ? AND year LIKE ? AND close <> ?", [month, year, "0"]).fetchall():
        user_name = inf.get_name(ret[0])
        if user_name not in users_name:
            users_name.append(user_name)
            user_date[user_name] = [0] * (len(dates) + 1)

        user_date[user_name][int(ret[1]) - 1] = 1600

    for ret in sqlite_db.cur.execute('SELECT person, day, point1, date1, total FROM menu WHERE month LIKE ? AND year LIKE ?',
                                     [month, year]).fetchall():
        type_salary, s_day, id_s = inf.get_type_sal(ret[2], ret[3], ret[0]), 0, 0
        if len(type_salary) != 0:
            type_s, id_s = type_salary.pop('type')
            try: 
                k = inf.check_replace(ret[0], ret[3])
                s_day = round((inf.get_salary_day(type_s, type_salary, ret[2], ret[4]) + inf.get_prize(ret[4], id_s)) * k, 0)
            except Exception:
                pass
        if ret[0] != "Олег":
            if s_day != 0:
                user_date[ret[0]][int(ret[1]) - 1] = round(s_day, 0)
            else:
                user_date[ret[0]][int(ret[1]) - 1] = 1

    dates.insert(0, "")
    result_date.append(dates)

    for key in user_date.keys():
        user_date[key].insert(0, key)
        result_date.append(user_date[key])

    for user in users_name:
        salary = inf.get_user_salary(user, month, year)
        if salary['total_days'] != 0:
            average_days = round(salary['day_total_sum']/salary['total_days'], 0)
        without_ = salary['total_sum'] - salary['fines'] - salary['prizes']
        pay = inf.get_sum_pay(user, month, year)
        in_pay = salary['total_sum'] - pay
        if in_pay < 0:
            in_pay = 0
        list1 = [user, lap(salary['total_days']), lap(average_days), lap(salary['fines']), lap(salary['late']),lap(salary['prizes']), lap(salary["premie_plan"]),
                 lap(salary["without"]), lap(salary['total_sum'] + salary['revision']), lap(pay), lap(salary['revision']) ,lap(salary['total_sum'] - pay)]
        info_base.append(list1)
    return info_base, result_date


def lap(text):
    return str(text).replace(".", ",")


def upload_table_defects(month, year):
    result = load_base_def(month, year)
    values = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"Браки!A2:L{len(result) + 1}",
                    "majorDimension": "ROWS",
                    "values": result
                },
            ]
        }
    ).execute()


def upload_table_salary(month, year):
    result, result_date = load_base_sal(month, year)
    values = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"Зарплаты!A2:L{len(result) + 1}",
                    "majorDimension": "ROWS",
                    "values": result
                },
            ]
        }
    ).execute()
    values2 = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {
                    "range": f"Зарплаты!N1:AY{len(result) + 1}",
                    "majorDimension": "ROWS",
                    "values": result_date
                },
            ]
        }
    ).execute()




async def get_url_table(message: types.Message, state: FSMContext):
    await bot.send_message(message.from_user.id, f'{table_url}')


def register_handlers_table(dp: Dispatcher):
    # Кнопка назад
    # dp.register_message_handler(cancel_handler_rep, state="*", commands='Назад')
    # dp.register_message_handler(cancel_handler_rep, Text(equals='Назад', ignore_case=True), state="*")
    # Выгрузка
    dp.register_message_handler(get_date_start, Text(equals=f'Загрузить данные в таблицу', ignore_case=True))
    dp.register_message_handler(get_date_finish, state=FSMTable.date1)
    dp.register_message_handler(get_url_table, Text(equals=f'Ссылка на таблицу', ignore_case=True))

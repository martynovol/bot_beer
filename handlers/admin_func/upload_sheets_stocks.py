import json
from re import L
import sqlite3 as sq
from pprint import pprint

import httplib2
import apiclient.discovery
import requests
import string
from pprint import pprint

import gspread
from gspread import Cell, Client, Spreadsheet, Worksheet
from gspread.utils import rowcol_to_a1
import requests


from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton

from create_bot import dp, bot
import sqlite3 as sq
from database import sqlite_db
from id import token

from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client

from datetime import datetime
from datetime import date, timedelta

from handlers import inf
import asyncio

class FSMTable_stocks(StatesGroup):
    date1 = State()

CREDENTIALS_FILE = 'handlers/admin_func/creds.json'
spreadsheet_id = '10Yh05RDAHJCIGVhKRd_ITDv9hXDDdXt1slpI6su57io'
table_url = 'https://docs.google.com/spreadsheets/d/10Yh05RDAHJCIGVhKRd_ITDv9hXDDdXt1slpI6su57io/edit?usp=sharing'


gc: Client = gspread.service_account("handlers/admin_func/creds.json")
sh: Spreadsheet = gc.open_by_url(table_url)

def create_ws_fill_and_del(sh: Spreadsheet):
    another_worksheet = sh.add_worksheet("another", rows=1000, cols=25)
    print(another_worksheet)
    # input("enter to fill ws")
    another_worksheet.insert_row(["hello", "world"])
    # input("enter to fill ws again")
    another_worksheet.insert_row(list(range(1, 16)))
    # input("enter to delete ws")
    sh.del_worksheet(another_worksheet)





async def start_table_stocks(message: types.Message, state: FSMContext):
    admins = inf.get_admin_id()
    if message.from_user.id not in admins:
        await bot.send_message(message.from_user.id, 'Эта функция доступна только администраторам')
        return
    b11 = KeyboardButton(str(datetime.now().strftime('%m.%Y')))
    b12 = KeyboardButton('Назад')
    button_case_admin_report = ReplyKeyboardMarkup(resize_keyboard=True).add(b11).row(b12)
    await bot.send_message(message.from_user.id,
                           f'Впишите месяц и год за который нужно загрузить данные в таблицу в формате ММ.ГГГГ:',
                           reply_markup=button_case_admin_report)
    await FSMTable_stocks.date1.set()


def register_handlers_table(dp: Dispatcher):
    dp.register_message_handler(start_table_stocks, Text(equals=f'Ревизии в таблицу', ignore_case=True))

import asyncio
import calendar
import os

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
import sqlite3 as sq
from create_bot import dp, bot
import requests, json
import openpyxl
from database import sqlite_db
from id import token
from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client, main_cassier_kb

from datetime import datetime
from datetime import date, timedelta

from handlers import inf
from handlers import emoji_bot


class FSMRevision(StatesGroup):
    date = State()
    point = State()
    value = State()
    time = State()
    id = State()


class FSMRevision_get(StatesGroup):
    point = State()
    date = State()

def punctuation(mes):
    x = mes
    if len(mes.split(',')) == 2:
        x = ''
        for i in mes:
            if i == ',':
                x += '.'
            else:
                x += i
    return round(float(x), 2)


async def cm_start_revision(message: types.Message):
    if message.from_user.id not in inf.get_admin_id():
        await bot.send_message(message.from_user.id, "Вам не доступна эта функция",
                               reply_markup=inf.kb(message.from_user.id))
        return
    
    
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(str(datetime.now().strftime('%m.%Y')))
    keyboard.add('Отмена')

    await bot.send_message(message.from_user.id, f'Выберите месяц и год проведения ревизии:', reply_markup=keyboard)
    await FSMRevision.date.set()


async def get_date_revision(message: types.Message, state: FSMContext):
    if len(message.text.split('.')) != 2:
        return
    month, year = message.text.split('.')
    if len(month) == 1:
        month = "0" + month
    async with state.proxy() as data:
        data['month'], data['year'] = month, year

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for user in inf.get_name_shops():
        keyboard.add(user)
    keyboard.add('Отмена')

    await bot.send_message(message.from_user.id, f'Выберите точку для внесения ревизии:', reply_markup=keyboard)
    await FSMRevision.next()

async def get_point_revision(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['point'] = inf.get_id_point(message.text)

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')

    await bot.send_message(message.from_user.id, f'Введите сумму ревизии:', reply_markup=keyboard)
    await FSMRevision.next()


async def get_value_revision(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['value'] = punctuation(message.text)
        data['time'] = str(datetime.now().strftime('%d.%m.%Y'))

    await sqlite_db.sql_add_revision(state)
    await bot.send_message(message.from_user.id, f'Ревизия успешно загружена', reply_markup=inf.kb(message.from_user.id))
    await state.finish()



async def cm_start_get_revision(message: types.Message):
    if message.from_user.id not in inf.get_admin_id():
        await bot.send_message(message.from_user.id, "Вам не доступна эта функция",
                               reply_markup=inf.kb(message.from_user.id))
        return
    
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(str(datetime.now().strftime('%m.%Y')))
    keyboard.add('Отмена')

    await bot.send_message(message.from_user.id, f'Введите месяц и год (ММ.ГГГГ):', reply_markup=keyboard)
    await FSMRevision_get.date.set()


async def point_revision(message: types.Message, state: FSMContext):
    pass



async def date_revision(message: types.Message, state: FSMContext):
    month, year = message.text.split('.')
    if len(month) == 1:
        month = "0" + month
    
    async with state.proxy() as data:
        await bot.send_message(message.from_user.id, f'Ревизии {month}.{year}:', reply_markup=inf.kb(message.from_user.id))
        for ret in sqlite_db.cur.execute("SELECT id, value, date, point FROM revision WHERE month = ? AND year = ?", [month, year]).fetchall():
            kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Удалить', callback_data=f"del_rev {ret[0]}"))
            await bot.send_message(message.from_user.id, f"Точка: {inf.pt_name(ret[3])}\nДата: {ret[2]} | Сумма: {ret[1]}", reply_markup=kb)

    await state.finish()


async def delete_revision(callback_query: types.CallbackQuery):
    revision_id = callback_query.data.split(' ')[1]
    sqlite_db.cur.execute('DELETE FROM revision WHERE id = ?', [revision_id])
    sqlite_db.base.commit()
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    await callback_query.answer(text=f'Ревизия удалена', show_alert=True)


def register_handlers_revision(dp: Dispatcher):
    dp.register_message_handler(cm_start_revision, Text(equals='Добавить ревизию', ignore_case=True))
    dp.register_message_handler(get_date_revision, state=FSMRevision.date)
    dp.register_message_handler(get_point_revision, state=FSMRevision.point)
    dp.register_message_handler(get_value_revision, state=FSMRevision.value)

    dp.register_message_handler(cm_start_get_revision, Text(equals='Выгрузить ревизии', ignore_case=True))
    dp.register_message_handler(point_revision, state=FSMRevision_get.point)
    dp.register_message_handler(date_revision, state=FSMRevision_get.date)

    dp.register_callback_query_handler(delete_revision, lambda x: x.data and x.data.startswith('del_rev '))
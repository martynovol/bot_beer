from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton

from create_bot import dp, bot

from database import sqlite_db

from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client

from datetime import datetime

import emoji


async def red_callback_run(callback_query: types.CallbackQuery):
    name = callback_query.data.split(' ')[2]
    point = callback_query.data.split(' ')[1] + ' ' + callback_query.data.split(' ')[3]
    if len(callback_query.data) > 4:
        for i in range(4, len(callback_query.data.split(' '))):
            point += ' ' + callback_query.data.split(' ')[i]
    sqlite_db.cur.execute('DELETE FROM last_report WHERE person LIKE ?', [name])
    sqlite_db.base.commit()
    await sqlite_db.sql_delete_command(point)
    await callback_query.answer(text=f'{point} удалена', show_alert=True)


def register_handlers_take_my_salary(dp: Dispatcher):
    dp.register_callback_query_handler(red_callback_run, lambda x: x.data and x.data.startswith('red '))
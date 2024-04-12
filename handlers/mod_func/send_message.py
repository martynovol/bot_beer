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
from datetime import date, timedelta

from handlers import emoji_bot, inf



class FSMAdmin_send(StatesGroup):
    id1 = State()
    mes1 = State()


async def send_mod(message: types.Message):
    b11 = KeyboardButton('Назад')
    mod_id = inf.get_mod_id()
    if message.from_user.id not in mod_id:
        await bot.send_message(message.from_user.id, 'Вам не доступна данная функция')
        return

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    i = 0
    for ret in sqlite_db.cur.execute('SELECT * FROM users'):
        if i % 2 == 0:
            keyboard.row(f'{ret[1]}')
        else:
            keyboard.insert(f'{ret[1]}')
    keyboard.row('Отмена')
    await bot.send_message(message.from_user.id,
                     f'ID person',
                    reply_markup=keyboard)
    await FSMAdmin_send.id1.set()

async def get_id1(message: types.Message, state:FSMContext):
    if message.text.isdigit():
        async with state.proxy() as data:
            data['id1'] = int(message.text)
    else:
        for ret in sqlite_db.cur.execute('SELECT * FROM users WHERE person LIKE ?', [message.text]):
            async with state.proxy() as data:
                data['id1'] = int(ret[0])
    await FSMAdmin_send.next()
    await bot.send_message(message.from_user.id, 'message:', reply_markup = ReplyKeyboardMarkup(resize_keyboard = True).add('Отмена'))

async def send_mes(message: types.Message, state:FSMContext):
    async with state.proxy() as data:
        data['mes1'] = message.text
    mes = data['mes1']
    id1 = data['id1']
    await bot.send_message(data['id1'],f'{mes}')
    await bot.send_message(message.from_user.id, f'OK!', reply_markup=inf.kb(message.from_user.id))
    try:
        await bot.send_message(761694862, f'Отправлено сообщение \'{mes}\' пользователю {id1}')
    except Exception:
        pass
    await state.finish()


def register_handlers_send_mes(dp: Dispatcher):
    dp.register_message_handler(send_mod, Text(equals='Написать', ignore_case=True))
    dp.register_message_handler(get_id1, state=FSMAdmin_send.id1)
    dp.register_message_handler(send_mes, state=FSMAdmin_send.mes1)
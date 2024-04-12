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
from handlers import emoji_bot

import emoji
import statistics


class FSMpremies(StatesGroup):
    person = State()
    date = State()
    premie = State()



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


async def cm_start_premie(message: types.Message):
    if message.from_user.id not in inf.get_admin_id() and message.from_user.id not in inf.get_main_cassier_id():
        await bot.send_message(message.from_user.id, 'Вам не доступна  эта функция')
        return
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    users = inf.get_users()
    available_names = []
    for user in users:
        available_names.append(user[1])
    for name in available_names:
        keyboard.add(name)
    keyboard.add('Отмена')
    await message.reply('Выберите сотрудника:', reply_markup=keyboard)
    await FSMpremies.person.set()


async def load_person_premie(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['id'] = sqlite_db.generate_random_string()
        data['person'] = message.text
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    time = str(datetime.now().strftime('%m.%Y'))
    keyboard.add(time)
    keyboard.add('Отмена')
    await FSMpremies.next()
    await message.reply('Впишите месяц и год(ММ.ГГГГ), за которые будет назначена премия:', reply_markup=keyboard)


async def load_data_premie(message: types.Message, state: FSMContext):
    bit = message.text.split('.')
    if len(bit) != 2 or (len(bit[0]) != 1 and len(bit[0]) != 2) or len(bit[1]) != 4 or not bit[0].isdigit() or not bit[
        1].isdigit():
        await message.reply(f'Вы ввели некорректную дату, попробуйте снова, формат "ММ.ГГГГ"')
        return
    if len(bit[0]) == 1:
        bit[0] = '0' + bit[0]
    month, year = bit[0], bit[1]
    async with state.proxy() as data:
        data['date'] = month + "." + year
    await FSMpremies.next()
    await message.reply('Впишите премию строго числом:',
                        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Отмена')))


async def load_premie(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['premie'] = punctuation(message.text)
        await sqlite_db.info_admin(message.from_user.id, f"Назначил премию: {data['premie']} {data['person']}")
    await sqlite_db.sql_add_premie(state)
    await bot.send_message(message.from_user.id, 'Премия назначена.',
                           reply_markup=inf.kb(message.from_user.id))
    await state.finish()


def register_handlers_premies(dp: Dispatcher):
    dp.register_message_handler(cm_start_premie, Text(equals=f'Назначить премию', ignore_case=True), state=None)
    dp.register_message_handler(load_person_premie, state=FSMpremies.person)
    dp.register_message_handler(load_data_premie, state=FSMpremies.date)
    dp.register_message_handler(load_premie, state=FSMpremies.premie)
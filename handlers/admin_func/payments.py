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


class FSMPayments(StatesGroup):
    person = State()
    date = State()
    payment = State()



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


async def cm_start_payment(message: types.Message):
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
    await FSMPayments.person.set()


async def load_person_payment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['person'] = message.text
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    time = str(datetime.now().strftime('%m.%Y'))
    keyboard.add(time)
    keyboard.add('Отмена')
    await FSMPayments.next()
    await message.reply('Впишите месяц и год(ММ.ГГГГ), за которые производится выплата:', reply_markup=keyboard)


async def load_data_payment(message: types.Message, state: FSMContext):
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
    await FSMPayments.next()
    await message.reply('Впишите выплату строго числом:',
                        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Отмена')))


async def load_payment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['payment'] = punctuation(message.text)
        await sqlite_db.info_admin(message.from_user.id, f"Зачислил выплату {data['payment']} {data['person']}")
        data_user = f"{data['date']}/{data['payment']}/{inf.get_user_id(data['person'])}/{message.from_user.id}"

    kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton('Подтвердить', callback_data=f"agr_pay/{data_user}")).insert(
            InlineKeyboardButton('Отклонить', callback_data=f"dis_pay/{data_user}"))

    await bot.send_message(int(inf.get_user_id(data['person'])), f'Вам зачислена выплата в размере {data["payment"]} руб. Подтвердите получение.', reply_markup=kb)

    await bot.send_message(message.from_user.id, 'Сотрудник должен подтвердить выплату.',
                           reply_markup=inf.kb(message.from_user.id))
    await state.finish()


async def agree_payment(call: types.CallbackQuery):
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    data_pay = call.data.split('/')
    date_pay, payment, person, uid = data_pay[1], data_pay[2], inf.get_name(data_pay[3]), data_pay[4]
    result_data = [person, date_pay, payment]
    await sqlite_db.sql_add_payment(result_data)
    await bot.send_message(int(uid), f'✅Пользователь {person} подтвердил выплату. Она будет записана.')
    await bot.send_message(call.from_user.id, f'Выплата подтверждена.')


async def disagree_payment(call: types.CallbackQuery):
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    data_pay = call.data.split('/')
    date_pay, payment, person, uid = data_pay[1], data_pay[2], inf.get_name(data_pay[3]), data_pay[4]
    await bot.send_message(int(uid), f'⚠️Пользователь {person} НЕ подтвердил выплату. Она НЕ будет записана.')
    await bot.send_message(call.from_user.id, f'Выплата отклонена.')


def register_handlers_payments(dp: Dispatcher):
    dp.register_message_handler(cm_start_payment, Text(equals=f'Начислить зарплату', ignore_case=True), state=None)
    dp.register_message_handler(load_person_payment, state=FSMPayments.person)
    dp.register_message_handler(load_data_payment, state=FSMPayments.date)
    dp.register_message_handler(load_payment, state=FSMPayments.payment)
    dp.register_callback_query_handler(agree_payment, lambda x: x.data and x.data.startswith('agr_pay/'))
    dp.register_callback_query_handler(disagree_payment, lambda x: x.data and x.data.startswith('dis_pay/'))

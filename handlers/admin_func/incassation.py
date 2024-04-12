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


class FSMIncassation(StatesGroup):
    point = State()
    date_start = State()
    date_end = State()
    payment = State()
    comments = State()


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

async def cm_start_incassation(message: types.Message):
    if message.from_user.id not in inf.get_admin_id():
        await bot.send_message(message.from_user.id, 'Вам не доступна  эта функция')
        return
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    points = inf.get_name_shops()
    for name in points:
        keyboard.add(name)
    keyboard.add('Отмена')
    await bot.send_message(message.from_user.id,'Выберите точку проведения инкассации:', reply_markup=keyboard)
    await FSMIncassation.point.set()


async def load_point_incassation(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['person'] = message.from_user.id
        data['point'] = inf.get_id_point(message.text)
        data['day'], data['month'], data['year'] = str(datetime.now().strftime('%d.%m.%Y')).split('.')
    
    last_date = 0
    for ret in sqlite_db.cur.execute("SELECT day, month, year FROM incassations WHERE point_id = ?", [inf.get_id_point(message.text)]).fetchall():
        last_date = f"{ret[0]}.{ret[1]}.{ret[2]}"

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    if last_date != 0:
        keyboard.add(last_date) 
    keyboard.add('Отмена')
    await FSMIncassation.next()
    await bot.send_message(message.from_user.id,'Впишите начало интервала дат, за которое происходит инкассация(ДД.ММ.ГГГГ):', reply_markup=keyboard)


async def load_start_date_incassation(message: types.Message, state: FSMContext):
    if inf.n_date(message.text) is None:
        await bot.send_message(message.from_user.id, f"Вы ввели некорректную дату, попробуйте ещё раз в формате(ДД.ММ.ГГГГ)")
        return

    async with state.proxy() as data:
        data['start_date'] = inf.n_date(message.text)

    now_date = str(datetime.now().strftime('%d.%m.%Y'))
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(now_date)
    keyboard.add('Отмена')

    await FSMIncassation.next()
    await bot.send_message(message.from_user.id,'Впишите конец интервала дат, за которое происходит инкассация(ДД.ММ.ГГГГ):', reply_markup=keyboard)
    

async def load_end_date_incassation(message: types.Message, state: FSMContext):
    if inf.n_date(message.text) is None:
        await bot.send_message(message.from_user.id, f"Вы ввели некорректную дату, попробуйте ещё раз в формате(ДД.ММ.ГГГГ)")
        return
    
    async with state.proxy() as data:
        data['end_date'] = inf.n_date(message.text)
        if datetime.strptime(data['end_date'], "%d.%m.%Y") < datetime.strptime(data['start_date'], "%d.%m.%Y"):
            await bot.send_message(message.from_user.id, f"Дата конца периода должна быть позже даты начала. Впишите дату ещё раз:")
            return

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')

    await FSMIncassation.next()
    await bot.send_message(message.from_user.id,'Впишите количество наличных, инкассированных с точки:', reply_markup=keyboard)
    

async def load_incassation(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['count'] = punctuation(message.text)
    
    await FSMIncassation.next()
    await bot.send_message(message.from_user.id,'Впишите комментарии:')


async def load_comment_incassation(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['comments'] = message.text
        await sqlite_db.sql_add_incassation(sqlite_db.generate_random_string(), data['person'], data['point'], data['day'], data['month'], data['year'], data['start_date'], data["end_date"],data['count'], data['comments'])
        for mod_id in inf.get_mod_id():
            date_now = f"{data['day']}.{data['month']}.{data['year']}"
            await bot.send_message(mod_id, f"[{date_now}] Инкассация проведена пользователем: {inf.get_name(data['person'])}. На точке: {inf.pt_name(data['point'])}. На сумму: {data['count']}")

    await state.finish()
    await bot.send_message(message.from_user.id, "Инкассация успешно проведена", reply_markup=inf.kb(message.from_user.id))


async def start_approve_incassation(message: types.Message):
    i = 1
    for ret in sqlite_db.cur.execute("SELECT * FROM incassations WHERE approve = ?", ["False"]).fetchall():
        if i < 7:
            kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Подтвердить", callback_data=f"approve_in {ret[0]}")).insert(InlineKeyboardButton("Удалить", callback_data=f"in_del {ret[0]}"))
            await bot.send_message(message.from_user.id, f"Инкассация [{ret[3]}.{ret[4]}.{ret[5]} {ret[11]}]\nС: {ret[6]} По: {ret[7]}\nТочка: {inf.pt_name(ret[2])}\nПользователь: {inf.get_name(ret[1])}\nСумма: {ret[8]}\nКомментарии: {ret[9]}", reply_markup=kb)
            i += 1


async def approve_incassation(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in inf.get_mod_id():
        await bot.send_message(callback_query.from_user.id, "У вас нет прав доступа")
        return
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    
    id_rep = callback_query.data.split(' ')[1]
    sqlite_db.cur.execute("UPDATE incassations SET approve = ? WHERE id = ?", ["True", id_rep])
    sqlite_db.base.commit()
    

async def del_incassation(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in inf.get_mod_id():
        await bot.send_message(callback_query.from_user.id, "У вас нет прав доступа")
        return
    
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    id_rep = callback_query.data.split(' ')[1]
    sqlite_db.cur.execute("DELETE FROM incassations WHERE id = ?", [id_rep])
    sqlite_db.base.commit()
    

def register_handlers_incassation(dp: Dispatcher):
    dp.register_message_handler(cm_start_incassation, Text(equals=f'Инкассировать', ignore_case=True), state=None)
    dp.register_message_handler(load_point_incassation, state=FSMIncassation.point)
    dp.register_message_handler(load_start_date_incassation, state=FSMIncassation.date_start)
    dp.register_message_handler(load_end_date_incassation, state=FSMIncassation.date_end)
    dp.register_message_handler(load_incassation, state=FSMIncassation.payment)
    dp.register_message_handler(load_comment_incassation, state=FSMIncassation.comments)

    dp.register_message_handler(start_approve_incassation, Text(equals=f'Неподтверждённые инкассации', ignore_case=True), state=None)
    dp.register_callback_query_handler(approve_incassation, lambda x: x.data and x.data.startswith('approve_in '))
    dp.register_callback_query_handler(del_incassation, lambda x: x.data and x.data.startswith('in_del '))

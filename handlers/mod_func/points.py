from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
import sqlite3 as sq
from create_bot import dp, bot

from database import sqlite_db

from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client, main_cassier_kb

from datetime import datetime
from datetime import date, timedelta

from handlers import inf


class FSMPoint(StatesGroup):
    name = State()
    time_open = State()
    time_close = State()


class FSMRedacting_point(StatesGroup):
    name = State()
    time_open = State()
    time_close = State()


get_data = {}


def global_dictionary(user_id, method="check", data=None):
    if method == "add":
        get_data[user_id] = data
    elif method == "check":
        return get_data[user_id]
    elif method == "clear":
        get_data.pop(user_id, None)


def check_correct_time(time_):
    numbers = time_.split(':')
    if len(numbers) == 2 and len(numbers[0]) == 2 and len(numbers[1]) == 2 and numbers[0].isdigit() \
            and numbers[1].isdigit() and int(numbers[0]) < 24 and int(numbers[1]) < 60:
        return True
    return False


async def cm_start_point(message: types.Message):
    if message.from_user.id not in inf.get_admin_id():
        await bot.send_message(message.from_user.id, "Вам не доступна эта функция",
                               reply_markup=inf.kb(message.from_user.id))
        return
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')
    await bot.send_message(message.from_user.id, f'Введите название новой точки:', reply_markup=keyboard)
    await FSMPoint.name.set()


async def load_name_point(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['id'] = sqlite_db.generate_random_string()
        data['name'] = message.text
    await bot.send_message(message.from_user.id, f'Введите время открытия (ЧЧ:ММ):')
    await FSMPoint.next()


async def load_point_open(message: types.Message, state: FSMContext):
    if not check_correct_time(message.text):
        await bot.send_message(message.from_user.id, f'Введите правильный формат времени (ЧЧ:ММ):')
        return
    async with state.proxy() as data:
        data['time_open'] = message.text
    await bot.send_message(message.from_user.id, f'Введите время закрытия (ЧЧ:ММ):')
    await FSMPoint.next()


async def load_point_close(message: types.Message, state: FSMContext):
    if not check_correct_time(message.text):
        await bot.send_message(message.from_user.id, f'Введите правильный формат времени (ЧЧ:ММ):')
        return
    async with state.proxy() as data:
        data['time_close'] = message.text
        data['diff_time'] = '0'
    await sqlite_db.sql_add_point(state)
    await bot.send_message(message.from_user.id, "Точка успешно добавлена",
                           reply_markup=inf.kb(message.from_user.id))
    await state.finish()


async def list_points(message: types.Message):
    await bot.send_message(message.from_user.id, "Список точек")
    for ret in sqlite_db.cur.execute('SELECT id, name_point, work_hours_start, work_hours_finish FROM shops'):
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton('Редактировать',
                                                                   callback_data=f"red_point {ret[0]}")).\
            insert(InlineKeyboardButton('Удалить', callback_data=f"rm_point {ret[0]}")).row(
            InlineKeyboardButton('Ставка', callback_data=f"sal_point {ret[0]}")
        )
        await bot.send_message(message.from_user.id, f"Название: {ret[1]}\nОткрытие: {ret[2]}\nЗакрытие: {ret[3]}",
                               reply_markup=keyboard)


async def del_point(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    id0 = callback_query.data.split(' ')[1]
    sqlite_db.cur.execute('DELETE FROM shops WHERE id LIKE ?', [id0])
    sqlite_db.base.commit()
    await bot.send_message(callback_query.from_user.id, f'Точка удалена')


async def redact_point(callback_query: types.CallbackQuery):
    point_id = callback_query.data.split(' ')[1]
    dat = ['name', 'open', 'close']
    keyboards = InlineKeyboardMarkup()\
        .add(InlineKeyboardButton('Название', callback_data=f'time_open {dat[0]} {point_id}'))\
        .row(InlineKeyboardButton('Время открытия', callback_data=f'time_open {dat[1]} {point_id}'))\
        .insert(InlineKeyboardButton('Время закрытия', callback_data=f'time_open {dat[2]} {point_id}'))
    await callback_query.message.answer(f'Выберите, что хотите отредактировать с точки '
                                        f'{inf.pt_name(point_id)}', reply_markup=keyboards)


async def red_point(callback_query: types.CallbackQuery):
    uid, point_id, dat_red = callback_query.from_user.id, callback_query.data.split(' ')[2], \
        callback_query.data.split(' ')[1]
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    global_dictionary(uid, "clear")
    global_dictionary(uid, "add", point_id)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена')
    if dat_red == 'name':
        await bot.send_message(callback_query.from_user.id, f'Впишите новое название точки', reply_markup=keyboard)
        await FSMRedacting_point.name.set()
    if dat_red == 'open':
        await bot.send_message(callback_query.from_user.id, f'Впишите новое время открытия в формате ЧЧ:ММ', reply_markup=keyboard)
        await FSMRedacting_point.time_open.set()
    if dat_red == 'close':
        await bot.send_message(callback_query.from_user.id, f'Впишите новое время закрытия в формате ЧЧ:ММ', reply_markup=keyboard)
        await FSMRedacting_point.time_close.set()


async def set_new_name(message: types.Message, state: FSMContext):
    red_info = global_dictionary(message.from_user.id)
    sqlite_db.cur.execute('UPDATE menu SET point1 = ? WHERE point1 LIKE ?', [message.text,
                                                                             inf.pt_name(red_info)])
    sqlite_db.cur.execute('UPDATE last_report SET point1 = ? WHERE point1 LIKE ?', [message.text,
                                                                                    inf.pt_name(red_info)])
    sqlite_db.cur.execute('UPDATE defects SET point = ? WHERE point LIKE ?', [message.text,
                                                                              inf.pt_name(red_info)])
    sqlite_db.cur.execute('UPDATE replace_person SET point = ? WHERE point LIKE ?', [message.text,
                                                                                     inf.pt_name(red_info)])
    sqlite_db.cur.execute('UPDATE reports_open SET point1 = ? WHERE point1 LIKE ?', [message.text,
                                                                                     inf.pt_name(red_info)])
    sqlite_db.cur.execute('UPDATE shops SET name_point = ? WHERE id LIKE ?', [message.text, red_info])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Название точки изменено на {message.text}',
                           reply_markup=inf.kb(message.from_user.id))
    await state.finish()


async def set_time_open(message: types.Message, state: FSMContext):
    red_info = global_dictionary(message.from_user.id)
    if not check_correct_time(message.text):
        await bot.send_message(message.from_user.id, f'Введите правильный формат времени (ЧЧ:ММ):')
        return
    sqlite_db.cur.execute('UPDATE shops SET work_hours_start = ? WHERE id LIKE ?', [message.text, red_info])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Время открытия изменено на {message.text}',
                           reply_markup=inf.kb(message.from_user.id))
    await state.finish()


async def set_time_close(message: types.Message, state: FSMContext):
    red_info = global_dictionary(message.from_user.id)
    if not check_correct_time(message.text):
        await bot.send_message(message.from_user.id, f'Введите правильный формат времени (ЧЧ:ММ):')
        return
    sqlite_db.cur.execute('UPDATE shops SET work_hours_finish = ? WHERE id LIKE ?', [message.text, red_info])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Время закрытия изменено на {message.text}',
                           reply_markup=inf.kb(message.from_user.id))
    await state.finish()


async def salary_point(callback_query: types.CallbackQuery):
    point_id = callback_query.data.split()[1]
    for ret in sqlite_db.cur.execute("SELECT id, point_id, date, type, value FROM salary WHERE point_id LIKE ?",
                                     [point_id]).fetchall():
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Удалить', callback_data=f"del_salar {ret[0]}"))
        await bot.send_message(callback_query.from_user.id, f'Точка: {inf.pt_name(ret[1])} | Дата: {ret[2]}\n'
                                                            f'Тип оплаты: {ret[3]} | Сумма {ret[4]}', reply_markup=kb)
        text = ""
        for jet in sqlite_db.cur.execute("SELECT inter1, inter2, prize_count, is_per FROM prize WHERE salary_id LIKE ?",
                                         [ret[0]]):
            text += f"{jet[0]} - {jet[1]}: {jet[2]}{jet[3]}\n"
        if text != "":
            kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Удалить', callback_data=f"del_prize {ret[0]}"))
            await bot.send_message(callback_query.from_user.id, f"Процент от продаж:\n{text}", reply_markup=kb)


async def delete_salary(callback_query: types.CallbackQuery):
    sid = callback_query.data.split()[1]
    sqlite_db.cur.execute('DELETE FROM salary WHERE id LIKE ?', [sid])
    sqlite_db.cur.execute('DELETE FROM prize WHERE salary_id LIKE ?', [sid])
    sqlite_db.base.commit()
    await bot.send_message(callback_query.from_user.id, "Ставка удалена")


async def delete_prize(callback_query: types.CallbackQuery):
    sid = callback_query.data.split()[1]
    sqlite_db.cur.execute('DELETE FROM prize WHERE salary_id LIKE ?', [sid])
    sqlite_db.base.commit()
    await bot.send_message(callback_query.from_user.id, "Премия удалена")


def register_handlers_points(dp: Dispatcher):
    dp.register_message_handler(cm_start_point,
                                Text(equals=f'Добавить точку', ignore_case=True), state=None)
    dp.register_message_handler(list_points,
                                Text(equals=f'Список точек', ignore_case=True), state=None)
    dp.register_message_handler(load_name_point, state=FSMPoint.name)
    dp.register_message_handler(load_point_open, state=FSMPoint.time_open)
    dp.register_message_handler(load_point_close, state=FSMPoint.time_close)
    dp.register_callback_query_handler(del_point, lambda x: x.data and x.data.startswith('rm_point '))
    dp.register_callback_query_handler(redact_point, lambda x: x.data and x.data.startswith('red_point '))
    dp.register_callback_query_handler(salary_point, lambda x: x.data and x.data.startswith('sal_point '))
    dp.register_callback_query_handler(delete_salary, lambda x: x.data and x.data.startswith('del_salar '))
    dp.register_callback_query_handler(delete_prize, lambda x: x.data and x.data.startswith('del_prize '))
    dp.register_callback_query_handler(red_point, lambda x: x.data and x.data.startswith('time_open '))
    dp.register_message_handler(set_time_open, state=FSMRedacting_point.time_open)
    dp.register_message_handler(set_time_close, state=FSMRedacting_point.time_close)
    dp.register_message_handler(set_new_name, state=FSMRedacting_point.name)

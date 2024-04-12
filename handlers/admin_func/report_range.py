
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton

from create_bot import dp, bot
import sqlite3 as sq
from database import sqlite_db

from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client, main_cassier_kb

from datetime import datetime
from datetime import date, timedelta

from handlers import inf
from handlers import emoji_bot

import emoji


class FSMAdmin_report_months(StatesGroup):
    point1 = State()
    month1 = State()
    month2 = State()

def check_month(m):
    m = m.split('.')
    return not (len(m) == 3 and (len(m[0]) == 2 or len(m[0]) == 1) and (len(m[1]) == 2 or len(m[1]) == 1) and len(m[2]) == 4 
        and m[0].isdigit() and m[1].isdigit() and m[2].isdigit()
        and int(m[0])<32 and int(m[1]) < 13 and int(m[2]) in range(2021, 2030))


async def take_month1(message: types.Message):
    admins = inf.get_admin_id()
    if message.from_user.id not in admins:
        await bot.send_message(message.from_user.id, 'Эта функция доступна только администраторам')
        return
    await FSMAdmin_report_months.point1.set()
    for mod_id in inf.get_mod_id():
        time = str(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        await bot.send_message(mod_id, f'{inf.get_name(str(message.from_user.id))}, {message.from_user.id}, {time} выгружает диапазон: {message.text}')
    keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
    available_points = inf.get_name_shops()
    for name in available_points:
        keyboard.add(name)
    keyboard.add('Назад')
    await bot.send_message(message.from_user.id,
                           f'Выберите точку{emoji_bot.em_report_load_store}',
                           reply_markup=keyboard)   


async def take_point1(message: types.Message, state: FSMContext):
    for mod_id in inf.get_mod_id():
        time = str(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        await bot.send_message(mod_id, f'{inf.get_name(str(message.from_user.id))}, {message.from_user.id}, {time} выгружает диапазон: {message.text}')
    available_points = inf.get_name_shops()
    if message.text not in available_points:
            await message.answer("Выберите точку, используя клавиатуру снизу")
            return
    async with state.proxy() as data:
        data['point1'] = message.text
    b11 = KeyboardButton('Назад')
    button_case_admin_report = ReplyKeyboardMarkup(resize_keyboard=True).add(b11)
    await FSMAdmin_report_months.next()
    await bot.send_message(message.from_user.id, f"Впишите начало диапазона дат (ДД.ММ.ГГГГ){emoji_bot.em_report_load_date}", reply_markup=button_case_admin_report)


async def take_month2(message: types.Message, state: FSMContext):
    for mod_id in inf.get_mod_id():
        time = str(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        await bot.send_message(mod_id, f'{inf.get_name(str(message.from_user.id))}, {message.from_user.id}, {time} выгружает диапазон: {message.text}')
    if check_month(message.text):
        await bot.send_message(message.from_user.id, f'Вы ввели некорректную дату, попробуйте ещё раз(формат ДД.ММ.ГГГГ)')
        return
    async with state.proxy() as data:
        data['month1'] = message.text
    await FSMAdmin_report_months.next()
    b11 = KeyboardButton('Назад')
    button_case_admin_report = ReplyKeyboardMarkup(resize_keyboard=True).add(b11)
    await bot.send_message(message.from_user.id,
                           f'Впишите конец диапазона дат (ДД.ММ.ГГГГ){emoji_bot.em_report_load_date}',
                           reply_markup=button_case_admin_report)


async def take_interval(message: types.Message, state: FSMContext):
    for mod_id in inf.get_mod_id():
        time = str(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        await bot.send_message(mod_id, f'{inf.get_name(str(message.from_user.id))}, {message.from_user.id}, {time} выгружает диапазон: {message.text}')
    if check_month(message.text):
        await bot.send_message(message.from_user.id, f'Вы ввели некорректную дату, попробуйте ещё раз(формат ДД.ММ.ГГГГ)')
        return
    async with state.proxy() as data:
        data['month2'] = message.text
    day, month, year = list(map(int, data['month1'].split('.')))
    d1 = date(year, month, day)  # начальная дата
    day, month, year = list(map(int, data['month2'].split('.')))
    d2 = date(year, month, day)  # конечная дата
    delta = d2 - d1         # timedelta
    if delta.days<=0:
        await state.finish()
        await bot.send_message(message.from_user.id, "Вы ввели некорректный диапазон", reply_markup = inf.kb(message.from_user.id))
        return
    dates = []
    for i in range(delta.days + 1):
        dates.append(d1 + timedelta(i))
    for date1 in dates:
        year, month, day = str(date1).split('-')
        if len(month) == 1:
            month = '0' + month
        if len(day) == 1:
            day = '0' + day
        for ret in sqlite_db.cur.execute("SELECT * FROM menu WHERE month LIKE :month1 AND year LIKE :year1 AND day LIKE :day1 AND point1 LIKE :point1 ORDER BY year ASC, month ASC, day ASC", {'month1':str(month),'year1': str(year), 'day1': str(day), 'point1': str(data['point1'])}).fetchall():
            if len(ret[7].split(' ')) == 3:
                beznal, sbp, qr = ret[7].split(' ')[0], ret[7].split(' ')[1], ret[7].split(' ')[2]
            elif len(ret[7].split(' ')) == 2:
                beznal, sbp, qr = ret[7].split(' ')[0], ret[7].split(' ')[1], '0.0'
            else:
                beznal, sbp, qr = ret[7], '0.0', '0.0'
            await bot.send_message(message.from_user.id,
                               f'Кассир {ret[0]}\nТочка {ret[1]}\nДата {ret[2]}\nНаличными {ret[6]}\nТерминал: {beznal}\nСБП: {sbp}\nQR-Код: {qr}\nПереводы {ret[8]}\nЗа день {ret[9]}\nВ кассе {ret[10]}\nВ сейфе {ret[11]}\nРасходы {ret[12]}\nКомментарии {ret[13]}', reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(f'Выгрузить фото отчётов', callback_data=f'pho {ret[16]} {message.from_user.id}')).add(
            InlineKeyboardButton(f'Удалить за {ret[2]}', callback_data=f'del {ret[16]}')).insert(InlineKeyboardButton(f'Редактировать {ret[2]}', callback_data=f'red {ret[16]}')))
    await state.finish()
    await bot.send_message(message.from_user.id, f'Выгрузка завершена', reply_markup=inf.kb(message.from_user.id))


def register_handlers_range_reports(dp: Dispatcher):
    dp.register_message_handler(take_month1, Text(equals=f'{emoji_bot.em_report_for_diap}Выгрузить диапазон', ignore_case=True))
    dp.register_message_handler(take_month2, state=FSMAdmin_report_months.month1)
    dp.register_message_handler(take_point1, state=FSMAdmin_report_months.point1)
    dp.register_message_handler(take_interval, state=FSMAdmin_report_months.month2)
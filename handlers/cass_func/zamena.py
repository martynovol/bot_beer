import asyncio

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

from handlers import inf, emoji_bot

import emoji

get_data = {}


def global_dictionary(user_id, method="check", data=None):
    if method == "add":
        get_data[int(user_id)] = data
    elif method == "check":
        return get_data[int(user_id)]
    elif method == "clear":
        get_data.pop(int(user_id), None)


class FSMZamena(StatesGroup):
    data1 = State()
    time = State()
    person1 = State()
    person = State()


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


def check_correct_time(time_):
    numbers = time_.split(':')
    if len(numbers) == 2 and len(numbers[0]) == 2 and len(numbers[1]) == 2 and numbers[0].isdigit() \
            and numbers[1].isdigit() and int(numbers[0]) < 24 and int(numbers[1]) < 60:
        return True
    return False


def check_month(m):
    m = m.split('.')
    return not (len(m) == 3 and (len(m[0]) == 2 or len(m[0]) == 1) and (len(m[1]) == 2 or len(m[1]) == 1) and len(
        m[2]) == 4
                and m[0].isdigit() and m[1].isdigit() and m[2].isdigit()
                and int(m[0]) < 32 and int(m[1]) < 13 and int(m[2]) in range(2021, 2030))


async def cm_start_replace(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    if message.from_user.id in inf.get_admin_id():
        time = str(datetime.now().strftime('%d.%m.%Y %H:%M'))
        keyboard.add(time).add('Отмена')
        await bot.send_message(message.from_user.id, f'Впишите дату и время замены в формате (ДД.ММ.ГГГГ ЧЧ:ММ)',
                               reply_markup=keyboard)
        await FSMZamena.data1.set()
    else:
        for ret in sqlite_db.cur.execute('SELECT now_user FROM reports_open WHERE date1 LIKE ?',
                                         [datetime.now().strftime('%d.%m.%Y')]).fetchall():
            keyboard.add(ret[0])
        keyboard.add('Отмена')
        await message.reply('Выберите человека, которого вы заменяете:', reply_markup=keyboard)
        await FSMZamena.person.set()


async def load_data1(message: types.Message, state: FSMContext):
    if len(message.text.split(' ')) != 2:
        await bot.send_message(message.from_user.id,
                               f'Вы ввели некорректную дату, попробуйте ещё раз(формат ДД.ММ.ГГГГ ЧЧ:ММ)')
        return
    if check_month(message.text.split(' ')[0]):
        await bot.send_message(message.from_user.id,
                               f'Вы ввели некорректную дату, попробуйте ещё раз(формат ДД.ММ.ГГГГ ЧЧ:ММ)')
        return
    if not check_correct_time(message.text.split(' ')[1]):
        await bot.send_message(message.from_user.id,
                               f'Вы ввели некорректное время, попробуйте ещё раз(формат ДД.ММ.ГГГГ ЧЧ:ММ)')
        return
    result_date = message.text.split(' ')[0].split('.')
    if len(result_date[0]) == 1:
        result_date[0] = '0' + result_date[0]
    if len(result_date[1]) == 1:
        result_date[1] = '0' + result_date[1]
    async with state.proxy() as data:
        data['data1'] = ".".join(result_date)
        data['time'] = message.text.split(' ')[1]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for ret in sqlite_db.cur.execute('SELECT person FROM users'):
        keyboard.add(ret[0])
    keyboard.add('Отмена')
    await message.reply('Выберите продавца, который заменяет:', reply_markup=keyboard)
    await FSMZamena.person1.set()


async def load_person1(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['person1'] = message.text
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for ret in sqlite_db.cur.execute('SELECT now_user FROM reports_open WHERE date1 LIKE ?',
                                         [data['data1']]).fetchall():
            keyboard.add(ret[0])
    keyboard.add('Отмена')
    await FSMZamena.next()
    await message.reply('Выберите продавца, которого заменяют:', reply_markup=keyboard)


async def load_person(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if 'data1' not in data:
            data['data1'] = str(datetime.now().strftime('%d.%m.%Y'))
            data['time'] = str(datetime.now().strftime('%H:%M'))
            data['person1'] = inf.get_name(message.from_user.id)
        available_persons = []
        for ret in sqlite_db.cur.execute('SELECT now_user FROM reports_open WHERE date1 LIKE ?',
                                         [data['data1']]).fetchall():
            available_persons.append(ret[0])
        if message.text not in available_persons:
            await bot.send_message(message.from_user.id, f'Продавец не открывал смену в этот день')
            return
        data['person'] = message.text
        data['id'] = sqlite_db.generate_random_string()
        for ret in sqlite_db.cur.execute('SELECT id FROM reports_open WHERE now_user = ? AND report_close_id = ?', [data['person'], ""]):
            data['report_open_id'] = ret[0]
        data['report_close_id'] = ''
        for ret in sqlite_db.cur.execute('SELECT point1 FROM reports_open WHERE now_user = ? AND report_close_id = ?',
                                         [data['person'], ""]):
            data['point'] = ret[0]
        for ret in sqlite_db.cur.execute('SELECT id FROM menu WHERE (person LIKE ? OR person LIKE ?) AND date1 LIKE ?'
                                         ' AND point1 LIKE ?',
                                         [data['person1'], data['person'], data['data1'], data['point']]):
            data['report_close_id'] = ret[0]
            sqlite_db.cur.execute('UPDATE menu SET person = ? WHERE id LIKE ?', [data['person1'], data['report_close_id']])
            sqlite_db.base.commit()
        person = data['person']
        global_dictionary(message.from_user.id, "clear")
        global_dictionary(message.from_user.id, "add", list(data.values()))
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(f'Да', callback_data=f'yes_rep {message.from_user.id}')
    ).insert(
        InlineKeyboardButton(f'Нет', callback_data=f'no_rep {message.from_user.id}')
    )
    if message.from_user.id not in inf.get_admin_id():
        await bot.send_message(message.from_user.id, f'{person} должен подтвердить замену в боте',
                               reply_markup=inf.kb(message.from_user.id))
        msg = await bot.send_message(inf.get_user_id(person),
                                     f'Вас заменяет {inf.get_name(message.from_user.id)}. '
                                     f'Подтвердить замену?', reply_markup=keyboard)
    else:
        msg = await bot.send_message(message.from_user.id,
                                     f'Подтвердить замену?', reply_markup=keyboard)
    await state.finish()
    await asyncio.sleep(60 * 2)
    try:
        await bot.delete_message(chat_id=inf.get_user_id(person), message_id=msg.message_id)
    except Exception:
        pass


async def agree_replace(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    mes_id = callback_query.data.split(' ')[1]
    data = global_dictionary(mes_id, "check")
    person1, person, point = data[2], data[3], data[-1]
    admins_id = inf.get_admin_id()
    await sqlite_db.sql_add_replace_person(data)
    if int(mes_id) not in admins_id:
        await bot.send_message(mes_id, 'Замена проведена. Обязательно сверьте наличность в кассе и сейфе.',
                               reply_markup=inf.kb(int(mes_id)))
        for _id in inf.get_admin_id():
            await bot.send_message(_id, f"Была произведена замена на точке {point}.\n{person1} заменил {person}")
    await bot.send_message(callback_query.from_user.id
                           , 'Замена проведена. Обязательно сверьте наличность в кассе и сейфе.',
                           reply_markup=inf.kb(callback_query.from_user.id))


async def disagree_replace(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    mes_id = callback_query.data.split(' ')[1]
    global_dictionary(mes_id, "clear")
    await bot.send_message(mes_id, 'Продавец отменил замену')


def register_handlers_zamena(dp: Dispatcher):
    dp.register_message_handler(cm_start_replace,
                                Text(equals=f'{emoji_bot.em_report_load_zamena}Провести замену', ignore_case=True),
                                state=None)
    dp.register_message_handler(load_data1, state=FSMZamena.data1)
    dp.register_message_handler(load_person1, state=FSMZamena.person1)
    dp.register_message_handler(load_person, state=FSMZamena.person)
    dp.register_callback_query_handler(agree_replace, lambda x: x.data and x.data.startswith('yes_rep '))
    dp.register_callback_query_handler(disagree_replace, lambda x: x.data and x.data.startswith('no_rep '))
# dp.register_message_handler(load_hour, state=FSMZamena.hour)
# dp.register_message_handler(load_box, state=FSMZamena.box)

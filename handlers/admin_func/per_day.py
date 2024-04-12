from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton

from create_bot import dp, bot

from database import sqlite_db

from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client
from handlers import cass_func
from datetime import datetime
from datetime import date, timedelta

from handlers import emoji_bot
from handlers import inf

import emoji


def check_month(m):
    m = m.split('.')
    return not (len(m) == 3 and (len(m[0]) == 2 or len(m[0]) == 1) and (len(m[1]) == 2 or len(m[1]) == 1) and len(
        m[2]) == 4
                and m[0].isdigit() and m[1].isdigit() and m[2].isdigit()
                and int(m[0]) < 32 and int(m[1]) < 13 and int(m[2]) in range(2021, 2030))


class FSMAdmin_report(StatesGroup):
    data1 = State()


# Отчёт за один день
async def one_report(message: types.Message):
    admins = inf.get_admin_id()
    if message.from_user.id not in admins:
        await bot.send_message(message.from_user.id, 'Эта функция доступна только администраторам')
        return
    await FSMAdmin_report.data1.set()
    b11 = KeyboardButton('Назад')
    b = 0
    for ret in sqlite_db.cur.execute('SELECT * FROM menu ORDER BY year ASC, month ASC, day ASC'):
        b = ret[2]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    if b == 0:
        keyboard.add(b11)
    else:
        keyboard.add(b).add(b11)
    await bot.send_message(message.from_user.id,
                           f'Впишите дату за которую нужно выгрузить отчёт в формате (ДД.ММ.ГГГГ){emoji_bot.em_report_load_date}',
                           reply_markup=keyboard)


# Выгрузка отчёта за день
async def take_report(message: types.Message, state: FSMContext):
    if check_month(message.text):
        await bot.send_message(message.from_user.id,
                               f'Вы ввели некорректную дату, попробуйте ещё раз(формат ДД.ММ.ГГГГ)')
        return
    m = message.text.split('.')
    if len(m[0]) == 1:
        m[0] = '0' + m[0]
    if len(m[1]) == 1:
        m[1] = '0' + m[1]
    m = m[0] + '.' + m[1] + '.' + m[2]
    check_report = 0
    for mod_id in inf.get_mod_id():
        time = str(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        await bot.send_message(mod_id,
                               f'{inf.get_name(str(message.from_user.id))}, {message.from_user.id}, {time} выгрузил отчёт за: {message.text}')
    for ret in sqlite_db.cur.execute("SELECT * FROM menu WHERE date1 LIKE ? ORDER BY year ASC, month ASC, day ASC",
                                     [m]).fetchall():
        check_report = ret[1]
        if len(ret[7].split(' ')) == 3:
            beznal, sbp, qr = ret[7].split(' ')[0], ret[7].split(' ')[1], ret[7].split(' ')[2]
        elif len(ret[7].split(' ')) == 2:
            beznal, sbp, qr = ret[7].split(' ')[0], ret[7].split(' ')[1], '0.0'
        else:
            beznal, sbp, qr = ret[7], '0.0', '0.0'
        
        try:
            cass_func.report_open.register_handlers_open_report(dp)
        except Exception:
            print('ОшибОЧКА')
        rep_id, time_rep = 0, 0
        for ret1 in sqlite_db.cur.execute('SELECT id, time FROM replace_person WHERE report_close_id LIKE ?', [ret[16]]):
            rep_id, time_rep = ret1[0], ret1[1]
        keyboards2 = InlineKeyboardMarkup().add(
            InlineKeyboardButton(f'Отменить замену', callback_data=f'del_rep {rep_id}'))
        await bot.send_message(message.from_user.id,
                               f'Кассир: {ret[0]}\nТочка: {ret[1]}\nДата: {ret[2]}\nНаличными: {ret[6]}\nТерминал: {beznal}\nСБП: {sbp}\nQR-Код: {qr}\nПереводы: {ret[8]}\nЗа день: {ret[9]}\nВ кассе: {ret[10]}\nВ сейфе: {ret[11]}\nРасходы: {ret[12]}\nКомментарии: {ret[13]}',
                               reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(f'Выгрузить фото отчётов',
                                                                                            callback_data=f'pho {ret[16]} {message.from_user.id}'))
                               .insert(InlineKeyboardButton(f'Открытие смены', callback_data=f'open_rep {ret[16]}')).add(
                                   InlineKeyboardButton(f'Удалить за {ret[2]}', callback_data=f'del {ret[16]}'))
                               .insert(InlineKeyboardButton(f'Редактировать {ret[2]}', callback_data=f'red {ret[16]}'))
                               .insert(InlineKeyboardButton(f'Браки', callback_data=f'get_defect {inf.get_id_point(ret[1])} {ret[2]}')
                               ))
        if rep_id != 0:
            await bot.send_message(message.from_user.id, f'Была произведена замена в {time_rep}',
                                   reply_markup=keyboards2)
    for ret in sqlite_db.cur.execute("SELECT id, person, point1, report_close_id  FROM reports_open WHERE date1 LIKE ?", [m]):
        if ret[3] == '':
            keyboards = InlineKeyboardMarkup().add(InlineKeyboardButton('Подробнее', callback_data=f'open_rep {ret[0]}'))
            await bot.send_message(message.from_user.id, f'Открытие смены продавцом: {ret[1]}, точка: {ret[2]}',
                                   reply_markup=keyboards)
    await state.finish()
    if check_report == 0:
        await bot.send_message(message.from_user.id, f'Отчёты не найдены',
                               reply_markup=inf.kb(message.from_user.id))
    else:
        await bot.send_message(message.from_user.id, f'Выгрузка завершена',
                               reply_markup=inf.kb(message.from_user.id))


def register_handlers_day_report(dp: Dispatcher):
    dp.register_message_handler(one_report,
                                Text(equals=f'{emoji_bot.em_report_for_day}Выгрузить отчёт за день', ignore_case=True))
    dp.register_message_handler(take_report, state=FSMAdmin_report.data1)

import asyncio
import json,requests

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
import sqlite3 as sq
from create_bot import dp, bot

from id import token
from database import sqlite_db

from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client, main_cassier_kb

from datetime import datetime
from datetime import date, timedelta

from handlers import inf
from handlers import emoji_bot, storage_reports
from handlers.mod_func import action_with_user

import emoji


class FSMAdmin(StatesGroup):
    person = State()
    point = State()
    date = State()
    cash = State()
    non_cash = State()
    non_cash_sbp = State()
    non_cash_qr = State()
    transfers = State()
    in_box = State()
    in_vault = State()
    expenses = State()
    photo1 = State()
    photo2 = State()
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


def check_month(m):
    m = m.split('.')
    return not (len(m) == 3 and (len(m[0]) == 2 or len(m[0]) == 1) and (len(m[1]) == 2 or len(m[1]) == 1) and len(
        m[2]) == 4
                and m[0].isdigit() and m[1].isdigit() and m[2].isdigit()
                and int(m[0]) < 32 and int(m[1]) < 13 and int(m[2]) in range(2021, 2030))


# Загрузка отчёта
async def cm_start(message: types.Message):
    if message.from_user.id in inf.get_storager_id():
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена")
        await bot.send_message(message.from_user.id, f'Комментарии{emoji_bot.em_report_load_comments}:', reply_markup=keyboard)
        await storage_reports.FSMClose_storager.comments.set()
        return
    
    if message.from_user.id in inf.get_drivers_id():
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена")
        await bot.send_message(message.from_user.id, f'Комментарии{emoji_bot.em_report_load_comments}:', reply_markup=keyboard)
        await storage_reports.FSMClose_Driver.comments.set()
        return
    
    if message.from_user.id in inf.get_operators_id():
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена")
        await bot.send_message(message.from_user.id, f'Комментарии{emoji_bot.em_report_load_comments}:', reply_markup=keyboard)
        await storage_reports.FSMClose_Operator.comments.set()
        return

    if message.from_user.id not in inf.get_users_id():
        await bot.send_message(message.from_user.id, 'Вам не доступна  эта функция')
        return
    
    for mod_id in inf.get_mod_id():
        time = str(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        await bot.send_message(mod_id,
                               f'{inf.get_name(str(message.from_user.id))}, {message.from_user.id}, {time} начал загружать отчёт')
        
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    users = inf.get_users()
    available_names = []
    for user in users:
        available_names.append(user[1])
    if message.from_user.id in inf.get_admin_id() or message.from_user.id in inf.get_main_cassier_id():
        for name in range(len(available_names)):
            if name % 2 == 0:
                keyboard.add(available_names[name])
            else:
                keyboard.insert(available_names[name])
        keyboard.add('Отмена')
        await(bot.send_message(message.from_user.id, f'Для отмены отправки отчёта нажмите \'отмена\' ',
                               reply_markup=keyboard))
        await(bot.send_message(message.from_user.id, f'Выберите продавца{emoji_bot.em_report_load_cass}:'))
        await FSMAdmin.person.set()
    else:
        last_point, last_data = "", ""
        for ret in sqlite_db.cur.execute('SELECT now_user, point1, date1 FROM reports_open WHERE report_close_id = ?',
                                         ['']).fetchall():
            if str(inf.get_user_id(ret[0])) == str(message.from_user.id):
                last_point, last_data = ret[1], ret[2]

        if last_point == "":
            return

        await bot.send_message(message.from_user.id, f'Имя: {inf.get_name(message.from_user.id)}'
                                                     f'\nТочка: {last_point}\nДата: {last_data}')
        keyboard.add('Отмена')
        await message.reply(f'Наличными{emoji_bot.em_report_load_cash}:',
                            reply_markup=keyboard)
        await FSMAdmin.cash.set()


async def cancel_handler(message: types.Message, state: FSMContext):
    for mod_id in inf.get_mod_id():
        time = str(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        await bot.send_message(mod_id,
                               f'{inf.get_name(str(message.from_user.id))}, {message.from_user.id}, {time}: {message.text}')
    current_state = await state.get_state()
    if current_state is None or current_state == "FSMAccess:mess":
        await message.reply('Вы вернулись назад', reply_markup=inf.kb(message.from_user.id))
        return
    elif current_state == "FSMAdd_points:state_continue" or current_state == "FSMAdd_points:id1":
        user_id = action_with_user.global_dictionary("", "check")[0][0]
        if len(action_with_user.global_dictionary("", "check")[0]) == 2:
            last_points = action_with_user.global_dictionary("", "check")[0][1]
        else:
            last_points = '0'
        await message.reply('Вы вернулись назад', reply_markup=inf.kb(message.from_user.id))
        sqlite_db.cur.execute('UPDATE users SET points = ? WHERE id LIKE ?', [last_points, user_id])
        sqlite_db.base.commit()
        await state.finish()
        return
    elif current_state.split(':')[0] == "FSMProblem":
        sqlite_db.cur.execute('UPDATE reports_open SET problem_photos = ? WHERE problem_photos LIKE ?',
                              ['False', message.from_user.id])
        sqlite_db.base.commit()
        await message.reply('Отправка проблемы отменена', reply_markup=inf.kb(message.from_user.id))
        await state.finish()
        return
    else:
        await state.finish()
        await message.reply('Отменено', reply_markup=inf.kb(message.from_user.id))
        return


# Продавец
# @dp.message_handler(state=FSMAdmin.person)
async def load_person(message: types.Message, state: FSMContext):
    available_names = []
    for user in inf.get_users():
        available_names.append(user[1])
    async with state.proxy() as data:
        data['person'] = message.text
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    available_points = inf.get_name_shops()
    for name in available_points:
        keyboard.add(name)
    keyboard.add('Отмена')
    await FSMAdmin.next()
    await message.reply(f'Точка{emoji_bot.em_report_load_store}:', reply_markup=keyboard)


# Точка
# @dp.message_handler(state=FSMAdmin.point)
async def load_point(message: types.Message, state: FSMContext):
    available_points = inf.get_name_shops()
    if message.text not in available_points:
        await message.answer("Выберите точку, используя клавиатуру снизу")
        return
    async with state.proxy() as data:
        if 'person' not in data:
            data['person'] = inf.get_name(message.from_user.id)
        data['point'] = message.text
    if message.from_user.id in inf.get_admin_id() or message.from_user.id in inf.get_main_cassier_id():
        await FSMAdmin.next()
        time = str(datetime.now().strftime('%d/%m/%Y %H:%M'))
        time1 = str((datetime.now() - timedelta(days=1)).strftime('%d.%m.%Y'))
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(time1).row('Отмена')
        await message.reply(f'Дата(формат ДД.ММ.ГГГГ){emoji_bot.em_report_load_date}:\n*Время cейчас {time}:',
                            reply_markup=keyboard)
    else:
        await FSMAdmin.cash.set()
        await message.reply(f'Наличными{emoji_bot.em_report_load_cash}:',
                            reply_markup=admin_cancel_kb.button_case_admin_cancel)


# Дата
# @dp.message_handler(state=FSMAdmin.date)
async def load_date(message: types.Message, state: FSMContext):
    if check_month(message.text):
        await bot.send_message(message.from_user.id,
                               f'Вы ввели некорректную дату, попробуйте ещё раз(формат ДД.ММ.ГГГГ)')
        return
    date2 = ''
    for i in range(0, 2):
        if len(message.text.split('.')[i]) == 1:
            date2 += '0' + message.text.split('.')[i] + '.'
        else:
            date2 += message.text.split('.')[i] + '.'
    date2 += message.text.split('.')[2]
    # Проверка уникальности первичного ключа
    async with state.proxy() as data:
        data['date'] = date2
    await FSMAdmin.next()
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add("0").add("Отмена")
    await message.reply(f'Наличными{emoji_bot.em_report_load_cash}:',
                        reply_markup=kb)


# Наличными
# @dp.message_handler(state=FSMAdmin.cash)
async def load_cash(message: types.Message, state: FSMContext):
    x = message.text
    if len(message.text.split(',')) == 2:
        m = message.text.split(',')
        for i in m:
            if i == ',':
                x += '.'
            else:
                x += i
    async with state.proxy() as data:
        if 'person' not in data:
            data['person'] = inf.get_name(message.from_user.id)
        for ret in sqlite_db.cur.execute('SELECT now_user, point1, date1 FROM reports_open WHERE report_close_id = ?',
                                         ['']).fetchall():
            if str(inf.get_user_id(ret[0])) == str(message.from_user.id):
                data["point"], data["date"] = ret[1], ret[2]
        for ret in sqlite_db.cur.execute('SELECT point1 FROM menu WHERE date1 LIKE ?', [data['date']]):
            if ret[0] == data['point']:
                await bot.send_message(message.from_user.id, 'Отчёт с этой датой уже добавлен. Сначала удалите его')
                return
        data['cash'] = punctuation(message.text)
    await FSMAdmin.next()
    await message.reply(f'Безналичными по терминалу{emoji_bot.em_report_load_non_cash}:')


# Безналичными
# @dp.message_handler(state=FSMAdmin.non_cash)
async def load_nonCash(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['non_cash'] = str(punctuation(message.text))
    await FSMAdmin.next()
    await message.reply(f'СБП{emoji_bot.em_report_load_non_cash}:')


# @dp.message_handler(state=FSMAdmin.non_cash)
async def load_nonCashSBP(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['non_cash'] =  data['non_cash'] + " " + str(punctuation(message.text))
    await FSMAdmin.next()
    await message.reply(f'Безналичными по QR-коду{emoji_bot.em_report_load_non_cash}:')


async def load_nonCashQR(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['non_cash'] = data['non_cash'] + " " + str(punctuation(message.text))
    await FSMAdmin.next()
    await message.reply(f'Переводы{emoji_bot.em_report_load_transfers}:')



# Переводы
# @dp.message_handler(state=FSMAdmin.transfers)
async def load_transfers(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['transfers'] = punctuation(message.text)
        total = data['transfers'] + float(data['non_cash'].split(' ')[0]) + float(data['non_cash'].split(' ')[1]) + float(data['non_cash'].split(' ')[2]) +\
                data['cash']
    await FSMAdmin.next()
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(str(total)).row('Отмена')
    await bot.send_message(message.from_user.id, f'Всего{emoji_bot.em_report_load_total}:\n*Наличные + безналичные + '
                                                 f'СБП + переводы = {total}')
    await bot.send_message(message.from_user.id, f'В кассе{emoji_bot.em_report_load_in_box}',
                           reply_markup=admin_cancel_kb.button_case_admin_cancel)


"""
# Итог
# @dp.message_handler(state=FSMAdmin.total)
async def load_total(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['total'] = punctuation(message.text)
    await FSMAdmin.next()
    await message.reply(f'В кассе{emoji_bot.em_report_load_in_box}:',
                        reply_markup=admin_cancel_kb.button_case_admin_cancel)
"""


# В кассе
# @dp.message_handler(state=FSMAdmin.in_box)
async def load_inBox(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        total = data['transfers'] + float(data['non_cash'].split(' ')[0]) + float(data['non_cash'].split(' ')[1]) + float(data['non_cash'].split(' ')[2]) + \
                data['cash']
        data['total'] = total
        data['in_box'] = punctuation(message.text)
    await FSMAdmin.next()
    await message.reply(f'В сейфе{emoji_bot.em_report_load_in_vault}:')


# В сейфе
# @dp.message_handler(state=FSMAdmin.in_vault)
async def load_inVault(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['in_vault'] = punctuation(message.text)
    await FSMAdmin.next()
    await message.reply(f'Расходы{emoji_bot.em_report_load_expenses}:')


# Расходы
# @dp.message_handler(state=FSMAdmin.expenses)
async def load_expenses(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['expenses'] = punctuation(message.text)
    await FSMAdmin.next()
    await message.reply(f'Загрузите фото отчёта с (Моего склада/Эвотор){emoji_bot.em_report_load_photo}')


async def load_photo1(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['photo1'] = message.photo[0].file_id
    await FSMAdmin.next()
    await message.reply(f'Загрузите фото сверки итогов платёжного терминала{emoji_bot.em_report_load_photo}:')


async def load_photo2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['photo2'] = message.photo[0].file_id
    await FSMAdmin.next()
    await message.reply(f'Комментарии{emoji_bot.em_report_load_comments}:')


async def load_comments(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['comments'] = message.text
    admins = inf.get_admin_id()

    data = {}
    async with state.proxy() as data:
        flag = 0
        for ret in sqlite_db.cur.execute("SELECT * FROM menu WHERE date1 = ? AND point1 = ?", [data['date'], data['point']]):
            flag = ret[0]
        if flag != 0:
            await sqlite_db.info_admin(message.from_user.id, f"ПЫТАЛСЯ ЗАГРУЗИТЬ ОТЧЁТ НО НЕ ВЫШЛО")
            return
        intor = f"Продавец: {data['person']}\nТочка: {data['point']}\nДата: {data['date']}\nНаличными: {data['cash']}\n" \
                f"Терминал: {data['non_cash'].split(' ')[0]}\nСБП: {data['non_cash'].split(' ')[1]}\nQR-Код: {data['non_cash'].split(' ')[2]}\nПереводы: {data['transfers']}\nИтог: {data['total']}\n" \
                f"В кассе: {data['in_box']}\nВ сейфе: {data['in_vault']}\nРасходы: {data['expenses']}\nКомментарии: {data['comments']} "
        date1, person, point = data['date'], data['person'], data['point']
        data['id'] = sqlite_db.generate_random_string()
        
        try:
            d = data['date'].split('.')
            cash, non_cash = get_total_day(data['point'], f"{d[2]}-{d[1]}-{d[0]}")
                
        except Exception:
            cash, non_cash = None, None
    await sqlite_db.sql_add_command(state)

    async with state.proxy() as data:
        point_name = data['point']
        for ret in sqlite_db.cur.execute('SELECT id FROM menu WHERE date1 LIKE ? AND point1 LIKE ?',
                                         [data['date'], data['point']]):
            id1 = ret[0]
        await bot.send_message(message.from_user.id, f'{intor}', reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(f'Редактировать {date1}', callback_data=f'red {id1}')))
        time = str(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        sqlite_db.cur.execute('UPDATE reports_open SET report_close_id = ? WHERE date1 LIKE ? AND point1 LIKE ?',
                              [data['id'], data['date'], data['point']])
        sqlite_db.cur.execute('UPDATE replace_person SET report_close_id = ? WHERE data1 LIKE ? AND'
                              ' report_close_id LIKE ? AND person1 LIKE ?', [data['id'], data['date'], '', inf.get_name(message.from_user.id)])
        sqlite_db.base.commit()
        replace_id, rep_id = 0, 0
        for ret in sqlite_db.cur.execute('SELECT time, id FROM replace_person WHERE report_close_id LIKE ?', [data['id']]):
            replace_id, rep_id = ret[0], ret[1]
        if message.from_user.id not in admins:
            await bot.send_message(message.from_user.id,
                                   f"Вы можете редактировать этот отчёт в течении 24 часов после его загрузки.")
            await sqlite_db.sql_add_command_last_report(state)
            await bot.send_message(message.from_user.id, f"Отчёт отправлен. Хорошего вечера!",
                                   reply_markup=inf.kb(message.from_user.id))
        else:
            await bot.send_message(message.from_user.id, f"Отчёт отправлен. Хорошего вечера!",
                                   reply_markup=inf.kb(message.from_user.id))
        id_report = data['id']

        total_b = float(data['non_cash'].split(' ')[1]) + float(data['non_cash'].split(' ')[2]) + float(data['non_cash'].split(' ')[0])
        if cash is None:
            for _id in admins:
                await bot.send_message(_id, f"⚠️Не получилось связаться с Контуром.")
        else:
            if (data['cash'] + data['transfers'] != cash) or (total_b != non_cash):
                for _id in admins:
                    await bot.send_message(_id, f"⚠️Выручка {data['point']} не сошлась с Контуром {data['date']} (Контур/Бот)\nБезналичные: {non_cash}/{total_b}\nНаличные: {cash}/{(data['cash'] + data['transfers'])}")
            else:
                for _id in admins:
                    await bot.send_message(_id, f"Выручка {data['point']} сошлась с Контуром")
            
        for _id in admins:
            if message.from_user.id != _id:
                keyboards = InlineKeyboardMarkup().add(
                    InlineKeyboardButton(f'Выгрузить фото отчётов', callback_data=f'pho {id1} {_id}')
                ).insert(
                    InlineKeyboardButton(f'Открытие смены', callback_data=f'open_rep {id_report}')
                ).row(
                    InlineKeyboardButton(f'Браки', callback_data=f'get_defect {inf.get_id_point(point)} {date1}')
                )
                await bot.send_message(_id, f'{time} был отправлен отчёт пользователем {inf.get_name(message.from_user.id)}:\n{intor}', reply_markup=keyboards)
                if replace_id != 0:
                    keyboards2 = InlineKeyboardMarkup().add(InlineKeyboardButton(f'Отменить замену', callback_data=f'del_rep {rep_id}'))
                    await bot.send_message(_id, f'Была произведена замена в {replace_id}', reply_markup=keyboards2)
            last_box = -1
            for ret in sqlite_db.cur.execute('SELECT in_box, in_vault FROM reports_open WHERE report_close_id LIKE ?', [data['id']]):
                last_box = float(ret[0]) + float(ret[1])
            if last_box != -1:
                cassa_now = float(data['cash']) + last_box - float(data['expenses'])
                if round(cassa_now) == round(float(data['in_box']) + float(data['in_vault'])):
                    await bot.send_message(_id, f'Наличность {point_name} сошлась c открытием смены')
                else:
                    u = cassa_now - float(data['in_box']) - float(data['in_vault'])
                    await bot.send_message(_id, f'⚠️ Наличность {point_name} не сходится с открытием смены на {round(u, 2)} рублей')
        await state.finish()

        open_time = "16:45 04.07.2023"

        for ret in sqlite_db.cur.execute("SELECT work_hours_start FROM shops WHERE name_point LIKE ?", [point]):
            if int(datetime.now().strftime('%H')) >= 8:
                open_time = ret[0] + " " + (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
            else:
                open_time = ret[0] + " " + datetime.now().strftime("%d.%m.%Y")

        await remind_open(point, open_time)


async def remind_open(point1, open_time):
    try:
        time_now = datetime.now()
        open_time = datetime.strptime(open_time, "%H:%M %d.%m.%Y")
        time_dif = str(open_time - time_now).split(':')
        hours, minutes = float(time_dif[0]) * 60 * 60, float(time_dif[1]) * 60
        total_time = hours + minutes + 60 * 4

        await asyncio.sleep(total_time)
        check = 0

        for ret in sqlite_db.cur.execute('SELECT id FROM reports_open WHERE report_close_id LIKE ? '
                                         'AND point1 LIKE ? AND date1 LIKE ?',
                                         ['', point1, datetime.now().strftime("%d.%m.%Y")]):
            check = ret[0]

        if check == 0:
            for _id in inf.get_admin_id():
                await bot.send_message(_id, f'❗️❗️❗️Смена на точке {point1}'
                                            f' не открыта вовремя!')

    except Exception:
        return


async def get_open_report(callback_query: types.CallbackQuery):
    report_id = callback_query.data.split(' ')[1]
    time = 'False'
    tel = 'Открытие смены'
    for ret in sqlite_db.cur.execute('SELECT person, point1, date1, in_box, in_vault, id'
                                     ' FROM reports_open WHERE report_close_id LIKE ? OR id LIKE ?', [report_id, report_id]):
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(f'Селфи', callback_data=f'selfie {ret[5]}')).insert(InlineKeyboardButton(f'Редактировать', callback_data=f'new {ret[5]} {tel}'))\
            .row(InlineKeyboardButton(f'Проблемы', callback_data=f'get_problem {ret[5]}')).\
            insert(InlineKeyboardButton(f'Удалить', callback_data=f'del {ret[5]}'))
        await bot.send_message(callback_query.from_user.id, f'Продавец: {ret[0]}\nТочка: {ret[1]}\nДата:{ret[2]}\n'
                                                            f'В кассе: {ret[3]}\nВ сейфе: {ret[4]}',
                               reply_markup=keyboard)
        time = ret[0]
    if time == 'False':
        await bot.send_message(callback_query.from_user.id, f'Смена за эту дату не открывалась')


async def get_problem_open(callback_query: types.CallbackQuery):
    report_id = callback_query.data.split(' ')[1]
    comments, list_photo = 'False', 'False'
    for ret in sqlite_db.cur.execute('SELECT problem_photos, comments FROM reports_open WHERE id LIKE ?', [report_id]):
        list_photo = ret[0]
        comments = ret[1]
    if comments == 'False':
        await bot.send_message(callback_query.from_user.id, f'Сообщений о проблемах не найдено')
    else:
        if list_photo == 'False':
            await bot.send_message(callback_query.from_user.id, f'Комментарии: {comments}')
        else:
            list_photo = list_photo.split(' ')
            media = types.MediaGroup()
            for photo in list_photo:
                if photo != '' and photo != ' ':
                    media.attach_photo(f'{photo}')
            await bot.send_media_group(callback_query.from_user.id, media=media)
            await bot.send_message(callback_query.from_user.id, f'Комментарии: {comments}')


async def upload_selfie(callback_query: types.CallbackQuery):
    report_id = callback_query.data.split(' ')[1]
    photo = ''
    for ret in sqlite_db.cur.execute('SELECT selfie FROM reports_open WHERE id LIKE ?', [report_id]):
        photo = ret[0]
    media = types.MediaGroup()
    media.attach_photo(f'{photo}')
    await bot.send_media_group(callback_query.from_user.id, media=media)


async def del_rep(callback_query: types.CallbackQuery):
    rep_id, rep_close, person1 = callback_query.data.split(' ')[1], 0, 0
    for ret in sqlite_db.cur.execute('SELECT report_close_id, person FROM replace_person WHERE id LIKE ?', [rep_id]):
        rep_close, person1 = ret[0], ret[1]
    sqlite_db.cur.execute('UPDATE menu SET person = ? WHERE id LIKE ?', [person1, rep_close])
    sqlite_db.cur.execute('DELETE FROM replace_person WHERE id LIKE ?', [rep_id])
    await bot.send_message(callback_query.from_user.id, f'Замена отменена, продавец в закрытии смены изменён на'
                                                        f' {person1}')
    sqlite_db.base.commit()


async def load_defects(callback_query: types.CallbackQuery):
    return
    point, date = inf.pt_name(callback_query.data.split(' ')[1]), callback_query.data.split(' ')[2]
    for ret in sqlite_db.cur.execute('SELECT id, product, price, comments FROM defects WHERE point LIKE ? '
                                     'AND date LIKE ?', [point, date]):
        keyboards = InlineKeyboardMarkup().add(
            InlineKeyboardButton(f'Фото', callback_data=f"get_pho_def {ret[0]}")
        ).insert(
            InlineKeyboardButton(f'Удалить', callback_data=f"del_def {ret[0]}"))
        await bot.send_message(callback_query.from_user.id,
                               f'Брак {point}, {date}\nТовар: {ret[1]}\nСтоимость: {ret[2]}\nПричина: {ret[3]}', reply_markup=keyboards)


async def load_defects_photo(callback_query: types.CallbackQuery):
    def_id = callback_query.data.split(' ')[1]
    for ret in sqlite_db.cur.execute('SELECT photo FROM defects WHERE id LIKE ?', [def_id]):
        photo = ret[0]
    media = types.MediaGroup()
    media.attach_photo(f'{photo}')
    await bot.send_media_group(callback_query.from_user.id, media=media)


def get_total_day(store, date_open):
    store_id, store_api = inf.get_id_sklad_point(store), inf.get_api_point(store)

    if store_api and store_api:
        url = f'{token.curl}/v1/shops/{store_id}/cheques'
        params = {'useTime': True, 'dateFrom': f'{date_open} 00:10:00', 'dateTo': f'{date_open} 23:50:00'}
        response = requests.get(url, headers={"x-kontur-apikey": store_api}, params=params)
        totalSum = {'Card': 0, 'Cash': 0}

        if response.status_code == 200:
            data = response.json()
            for cheq in data["items"]:
                for payment in cheq["payments"]:
                    totalSum[payment['type']] += float(payment['value'].replace(",", "."))
            
            return (totalSum['Cash'], totalSum['Card'])
        
        else:
            return (None, None)
    
    else:
        return 0, 0



async def del_defect(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    def_id = callback_query.data.split(' ')[1]
    sqlite_db.cur.execute('DELETE FROM defects WHERE id LIKE ?', [def_id])
    sqlite_db.base.commit()
    await bot.send_message(callback_query.from_user.id, 'Брак удалён')


def register_handlers_close_reports(dp: Dispatcher):
    dp.register_message_handler(cancel_handler, state="*", commands='Отмена')
    dp.register_message_handler(cancel_handler, Text(equals='Отмена', ignore_case=True), state="*")
    dp.register_message_handler(cm_start, Text(equals=f'{emoji_bot.em_report_close}Закрыть смену', ignore_case=True),
                                state=None)
    dp.register_message_handler(load_person, state=FSMAdmin.person)
    dp.register_message_handler(load_point, state=FSMAdmin.point)
    dp.register_message_handler(load_date, state=FSMAdmin.date)
    dp.register_message_handler(load_cash, state=FSMAdmin.cash)
    dp.register_message_handler(load_nonCash, state=FSMAdmin.non_cash)
    dp.register_message_handler(load_nonCashSBP, state=FSMAdmin.non_cash_sbp)
    dp.register_message_handler(load_nonCashQR, state=FSMAdmin.non_cash_qr)
    # dp.register_message_handler(load_total, state=FSMAdmin.total)
    dp.register_message_handler(load_transfers, state=FSMAdmin.transfers)
    dp.register_message_handler(load_inBox, state=FSMAdmin.in_box)
    dp.register_message_handler(load_inVault, state=FSMAdmin.in_vault)
    dp.register_message_handler(load_expenses, state=FSMAdmin.expenses)
    dp.register_message_handler(load_photo1, content_types=['photo'], state=FSMAdmin.photo1)
    dp.register_message_handler(load_photo2, content_types=['photo'], state=FSMAdmin.photo2)
    dp.register_message_handler(load_comments, state=FSMAdmin.comments)
    dp.register_callback_query_handler(get_open_report, lambda x: x.data and x.data.startswith('open_rep '))
    dp.register_callback_query_handler(get_problem_open, lambda x: x.data and x.data.startswith('get_problem '))
    dp.register_callback_query_handler(upload_selfie, lambda x: x.data and x.data.startswith('selfie '))
    dp.register_callback_query_handler(del_rep, lambda x: x.data and x.data.startswith('del_rep '))
    dp.register_callback_query_handler(load_defects, lambda x: x.data and x.data.startswith('get_defect '))
    dp.register_callback_query_handler(load_defects_photo, lambda x: x.data and x.data.startswith('get_pho_def '))
    dp.register_callback_query_handler(del_defect, lambda x: x.data and x.data.startswith('del_def '))
import asyncio
import json

from id import token

import requests
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

from handlers import inf, storage_reports
from handlers import emoji_bot


class FSMremind_law(StatesGroup):
    know_law = State()
    agree_law = State() 


class FSMOpen(StatesGroup):
    person = State()
    point = State()
    date = State()
    in_box = State()
    in_vault = State()
    selfie = State()


class FSMOpen_storage(StatesGroup):
    person = State()
    selfie = State()

class FSMProblem(StatesGroup):
    problems = State()
    state_continue = State()
    comments = State()


class FSMOnline_Cassa(StatesGroup):
    online_cassa = State()



class FSMOpen_storageman(StatesGroup):
    selfie = State()

get_data = []


def check_time(open, now):
    time_1 = datetime.strptime(open, "%H:%M")
    time_2 = datetime.strptime(now, "%H:%M")
    if time_2 < time_1:
        return 0
    else:
        time_delt = str(time_2 - time_1).split(':')
        return time_delt[0] + ':' + time_delt[1]


def global_dictionary(data, method):
    if method == "add":
        get_data.append(data)
    elif method == "check":
        return get_data
    elif method == "clear":
        get_data.clear()


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


async def cm_open_start(message: types.Message):
    if message.from_user.id in inf.get_storager_id() or message.from_user.id in inf.get_drivers_id() or message.from_user.id in inf.get_operators_id():
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Да", callback_data="storage_law_yes ")).insert(InlineKeyboardButton("Нет", callback_data="storage_law_no "))
        await bot.send_message(message.from_user.id, "Подтвердите что вы осведомлены о материальной ответственности на работе, знакомы с правилами безопасности на рабочем месте", reply_markup=kb)
        return
    
    if message.from_user.id not in inf.get_users_id():
        await bot.send_message(message.from_user.id, 'Вам не доступна  эта функция')
        return
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    available_names = []
    for user in inf.get_users():
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
        await FSMOpen.person.set()
    else:
        for ret in sqlite_db.cur.execute('SELECT points FROM users WHERE id LIKE ?', [message.from_user.id]):
            points = ret[0]  # id точек у пользователя через пробел, если 0, значит точки отсутствуют
        if points == '0':
            await bot.send_message(message.from_user.id, f'У вас нет доступа к загрузке отчёта. Если это ошибка, '
                                                         f'обратитесь к модератору. ')
            return
        elif len(points.split(' ')) > 1:
            for point in points.split(' '):
                keyboard.add(inf.pt_name(point))
            keyboard.add('Отмена')
            await FSMOpen.point.set()
            await message.reply(f'Точка{emoji_bot.em_report_load_store}:', reply_markup=keyboard)
        else:
            keyboard.add('Отмена')
            await bot.send_message(message.from_user.id, f'Имя: {inf.get_name(message.from_user.id)}'
                                                         f'\nТочка: {inf.pt_name(points)}', reply_markup=keyboard)
            await message.reply(f'В кассе:',
                                reply_markup=keyboard)
            await FSMOpen.in_box.set()



async def finish_law_storage(call: types.CallbackQuery):
    if call.from_user.id in inf.get_storager_id():
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена")
        await bot.send_message(call.from_user.id, "Загрузите своё селфи в бота:", reply_markup=keyboard)
        await storage_reports.FSMOpen_storager.selfie.set()
    
    elif call.from_user.id in inf.get_drivers_id():
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена")
        await bot.send_message(call.from_user.id, "Загрузите своё селфи в бота:", reply_markup=keyboard)
        await storage_reports.FSMOpen_Driver.selfie.set()
    

    elif call.from_user.id in inf.get_operators_id():
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена")
        await bot.send_message(call.from_user.id, "Загрузите своё селфи в бота:", reply_markup=keyboard)
        await storage_reports.FSMOpen_Operator.selfie.set()
    
    else:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена")
        await bot.send_message(call.from_user.id, "Загрузите своё селфи в бота:", reply_markup=keyboard)
        await storage_reports.FSMOpen_manager.selfie.set()
    
    

async def show_law_no(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Прочитал, обязуюсь соблюдать", callback_data="storage_law_yes "))
    await bot.send_message(call.from_user.id, "Вы принимаете на себя полную материальную ответственность за сохранность вверенных вам денежных средств, документов и товаров, и несете ОТВЕТСТВЕННОСТЬ в установленном законом порядке. Вы обязуетесь бережно отноститься к переданным денежным средствам, документам. Принимать меры по предотвращению ущерба комапании в которой работаете. Своевременно ставить в известность руководителя наличии угражающих сохранности средств документов и обстоятельств. Гарантируете Сохранность вверенного вам имущества", reply_markup=kb)
    

async def load_person_open(message: types.Message, state: FSMContext):
    available_names = []
    for user in inf.get_users():
        available_names.append(user[1])
    async with state.proxy() as data:
        data['id'] = sqlite_db.generate_random_string()
        data['person'] = message.text
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    available_points = inf.get_name_shops()
    for name in available_points:
        keyboard.add(name)
    keyboard.add('Отмена')
    await FSMOpen.next()
    await message.reply(f'Точка{emoji_bot.em_report_load_store}:', reply_markup=keyboard)


async def load_point_open(message: types.Message, state: FSMContext):
    available_points = inf.get_name_shops()
    if message.text not in available_points:
        await message.answer("Выберите точку, используя клавиатуру снизу")
        return
    async with state.proxy() as data:
        data['id'] = sqlite_db.generate_random_string()
        if 'person' not in data:
            for user in inf.get_users():
                if int(user[0]) == message.from_user.id:
                    user_name = user[1]
            data['person'] = user_name
        data['point'] = message.text
    if message.from_user.id in inf.get_admin_id() or message.from_user.id in inf.get_main_cassier_id():
        await FSMOpen.next()
        time = str(datetime.now().strftime('%d.%m.%Y'))
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(time).row('Отмена')
        await message.reply(f'Дата(формат ДД.ММ.ГГГГ){emoji_bot.em_report_load_date}:\n*Время cейчас {time}:',
                            reply_markup=keyboard)
    else:
        await FSMOpen.in_box.set()
        await message.reply(f'В кассе{emoji_bot.em_report_load_in_box}:',
                            reply_markup=admin_cancel_kb.button_case_admin_cancel)


async def load_date_open(message: types.Message, state: FSMContext):
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
    async with state.proxy() as data:
        for ret in sqlite_db.cur.execute('SELECT point1 FROM reports_open WHERE date1 LIKE ?', [date2]):
            if ret[0] == data['point']:
                await bot.send_message(message.from_user.id,
                                       'Открытие смены с этой датой уже производилось.')
                return
        data['date'] = date2
    await FSMOpen.next()
    await message.reply(f'В кассе{emoji_bot.em_report_load_in_box}:',
                        reply_markup=admin_cancel_kb.button_case_admin_cancel)


async def load_in_box_open(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        check = 'False'
        data['id'] = sqlite_db.generate_random_string()
        if 'person' not in data:
            data['person'] = inf.get_name(message.from_user.id)
        if 'point' not in data:
            for ret in sqlite_db.cur.execute('SELECT points FROM users WHERE id LIKE ?', [message.from_user.id]):
                data['point'] = inf.pt_name(ret[0])
        if 'date' not in data:
            data['date'] = str(datetime.now().strftime('%d.%m.%Y'))
        for ret in sqlite_db.cur.execute('SELECT point1 FROM reports_open WHERE date1 LIKE ? AND point1 LIKE ?',
                                         [data['date'], data['point']]):
            await bot.send_message(message.from_user.id, f'Открытие смены на этой точке уже производилось сегодня')
            return
        data['in_box'] = punctuation(message.text)
    await FSMOpen.next()
    await message.reply(f'В сейфе{emoji_bot.em_report_load_in_vault}:',
                        reply_markup=admin_cancel_kb.button_case_admin_cancel)


async def load_in_vault_open(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['in_vault'] = punctuation(message.text)
    await FSMOpen.next()
    await bot.send_message(message.from_user.id,
                           f'Пришлите селфи, сделанное на точке, в момент открытия смены {emoji_bot.em_report_load_photo}')


async def load_selfie_open(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['selfie'] = message.photo[0].file_id
        data['problems'] = message.from_user.id
        data['comments'] = 'False'
        data['report_close'] = ''
        data['now_user'] = data['person']
    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(f'Проблемы', callback_data=f'problem fg')) \
        .insert(InlineKeyboardButton(f'Закончить', callback_data=f'finish_open fd'))
    await sqlite_db.sql_add_open_report(state)
    await bot.send_message(message.from_user.id, f'Данные записаны', reply_markup=types.ReplyKeyboardRemove())
    mes = await bot.send_message(message.from_user.id, f'Если на точке имеются проблемы - нажмите "Проблемы". Если проблем '
                                                 f'нет - нажмите закончить', reply_markup=keyboard)
    admins = inf.get_admin_id()

    async with state.proxy() as data:
        time1 = str((datetime.now() - timedelta(days=1)).strftime('%d.%m.%Y'))
        time = str(datetime.now().strftime('%H:%M'))
        last_box = -1
        for ret in sqlite_db.cur.execute('SELECT in_box, in_vault FROM menu WHERE point1 LIKE ? ORDER BY year ASC, month ASC, day ASC', [data['point']]):
            last_box = float(ret[0]) + float(ret[1])
        for ret in sqlite_db.cur.execute('SELECT work_hours_start FROM shops WHERE name_point LIKE ?', [data['point']]):
            open_time = ret[0]
        person = data['person']
        point = data['point']
        report_id = data['id']
        for _id in admins:
            try:
                keyboard = InlineKeyboardMarkup().add(
                    InlineKeyboardButton(f'Подробнее', callback_data=f'open_rep {report_id}'))
                time_lapse = check_time(open_time, time)
                if time_lapse != 0:
                    hours, minutes = time_lapse.split(':')
                    fine = int(hours) * 60 * 50 + int(minutes) * 50
                    date_now, day, month, year = datetime.now().strftime('%d.%m.%Y'), datetime.now().strftime('%d'), datetime.now().strftime('%m'), datetime.now().strftime('%Y')
                    await bot.send_message(_id, f'Смена была открыта на точке {point} продавцом {person} с опозданием на {time_lapse}.\n\n⚠️Начислен штраф: {fine} рублей', reply_markup=keyboard)
                    data_fine = [inf.get_name(message.from_user.id), fine, date_now, day, month, year, "Опоздание", sqlite_db.generate_random_string()]
                    data_late = [sqlite_db.generate_random_string(), message.from_user.id, day, month, year, datetime.now().strftime('%H:%M')]
                else:
                    await bot.send_message(_id, f'Смена была открыта на точке {point} продавцом {person} без опоздания', reply_markup=keyboard)
                if last_box != -1 and int(last_box) != int(data['in_box'] + data['in_vault']):
                    u = float(data['in_box']) + float(data['in_vault']) - last_box
                    await bot.send_message(_id, f'⚠️ Наличность на точке не сходится с прошлым отчётом на {round(u, 2)} рублей')
            except Exception:
                continue
    await state.finish()
    if time_lapse != 0:
        sqlite_db.cur.execute('INSERT INTO late VALUES (?,?,?,?,?,?)', data_late) 
        sqlite_db.cur.execute('INSERT INTO fine VALUES (?,?,?,?,?,?,?,?)', data_fine) 
        sqlite_db.base.commit()

    await asyncio.sleep(60*10*1)
    check = -1
    for ret in sqlite_db.cur.execute('SELECT problem_photos FROM reports_open WHERE person LIKE ? '
                                     'AND problem_photos LIKE ?',
                                     [inf.get_name(message.from_user.id), message.from_user.id]):
        check = ret[0]
    if check != -1:
        await bot.delete_message(chat_id=message.from_user.id, message_id=mes.message_id)
        sqlite_db.cur.execute('UPDATE reports_open SET problem_photos = ? WHERE problem_photos LIKE ?',
                              ['False', message.from_user.id])
        sqlite_db.base.commit()
        agree_kb = InlineKeyboardMarkup().add(InlineKeyboardButton(f"Да", callback_data=f"next_law ")).insert(InlineKeyboardButton(f"Нет", callback_data=f"show_law "))
        await bot.send_message(message.from_user.id, f"Вы знаете о том, что продажа алкогольных напитков и табачных изделий лицам, не достигшим 18 лет, строго запрещена?", reply_markup=agree_kb)

    #await FSMremind_law.know_law.set()
    close_time = "00:00"
    for ret in sqlite_db.cur.execute("SELECT work_hours_finish FROM shops WHERE name_point LIKE ?", [point]):
        close_time = ret[0]
        if close_time == "24:00":
            close_time = "23:59"
    if message.from_user.id not in inf.get_admin_id():
        await remind_close(message.from_user.id, close_time)
        #await remind_revision(message.from_user.id, "14:00")


async def show_law(callback_query: types.CallbackQuery):
    await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text = "Продажи несовершеннолетним всей никотиносодержащей продукции, Pod-систем, кальянов и почти всего ассортимента в наших магазинах СТРОГО ЗАПРЕЩЕНА!")
    await asyncio.sleep(3)
    next_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Ознакомился, обязаусь соблюдать",  callback_data=f"next_law "))
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=next_kb )

async def next_law(callback_query: types.CallbackQuery):
    await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text = "Так же обращаем Ваше внимание, что продажа 18+ осуществляется только НА СЛЕДУЮЩИЙ ДЕНЬ ПОСЛЕ ДНЯ РОЖДЕНИЯ. В день рождения продавать нельзя!!!🚫\n\nОснование фз рф от 23.02.2013 номер 15/ фз от 10.07.2001 номер 87")
    await asyncio.sleep(6)
    next_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Ознакомился, обязаусь соблюдать",  callback_data=f"finish_law "))
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=next_kb )


async def finish_law(callback_query: types.CallbackQuery):
    await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text = "Обращаем ваше внимание‼️ Что при внутренней проверке на продажу лицам не достигшим 18 лет - назначается штраф. Просим быть предельно внимательными!")
    await asyncio.sleep(3)
    next_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Ознакомился, обязаусь соблюдать",  callback_data=f"finish_law2 "))
    await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=next_kb )


async def finish_law2(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    #await bot.send_message(callback_query.from_user.id, f"⚠️Внимание! Необходимо произвести локальную ревизию на точку, при помощи кнопки 'Локальная ревизия'.\nРевизия должна быть проведена до 15:00")
    await bot.send_message(callback_query.from_user.id, "Смена успешно открыта. Удачного дня!", reply_markup=inf.kb(callback_query.from_user.id))

async def remind_revision(id1, close_time):
    print('НАЧАЛОСЬ')
    try:
        time_now = str(datetime.now().strftime('%H:%M'))
        now_time = datetime.strptime(time_now, "%H:%M")
        close_time = datetime.strptime(close_time, "%H:%M") - timedelta(hours=0, minutes=15)
        try:
            s = now_time > close_time > datetime.strptime(time_now, "04:00")
        except Exception:
            return
        time_dif = str(close_time - now_time).split(':')
        hours, minutes = float(time_dif[0]) * 60 * 60, float(time_dif[1]) * 60
        total_time = hours + minutes
        await asyncio.sleep(total_time)
        check = 0
        for ret in sqlite_db.cur.execute('SELECT report_close_id FROM reports_open WHERE report_close_id LIKE ? '
                                         'AND person LIKE ?', ['', inf.get_name(id1)]):
            check = ret[0]
        if check != 0:
            await bot.send_message(id1, f'⚠️Напоминание⚠️ ️ Не забудьте провести локальную ревизию на точке. Ревизия должна быть проведена до 15:00')
    except Exception:
        return


def time_to_seconds(time_str):
    try:
        hours, minutes = map(int, time_str.split(':'))
        if 0 <= hours < 24 and 0 <= minutes < 60:
            total_seconds = hours * 3600 + minutes * 60
            return total_seconds
        else:
            raise ValueError("Неверный формат времени")
    except ValueError as e:
        print(f"Ошибка: {e}")
        return None
    

async def expenses_api(uid):
    time_skip = 1
    await asyncio.sleep(time_skip)
    while True:
        time_start = datetime.now() - timedelta(hours=0, minutes=15)
        url_get_expenses = f"https://api.moysklad.ru/api/remap/1.2/entity/retaildrawercashout/" \
                           f"?filter=moment>{time_start}"
        response = requests.get(url_get_expenses, headers=token.headers)
        data = json.loads(response.text)
        for expense in data['rows']:
            kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Выбрать категорию', callback_data="exp "))
            await bot.send_message(uid, f'В "Мой склад" {str(expense["created"])} была добавлена выплата с пометкой:'
                                        f'\n{expense["description"]}', reply_markup=kb)
        await asyncio.sleep(time_skip*60)


async def remind_close(id1, close_time):
    try:
        time_now = str(datetime.now().strftime('%H:%M'))
        now_time = datetime.strptime(time_now, "%H:%M")
        close_time = datetime.strptime(close_time, "%H:%M") - timedelta(hours=0, minutes=15)
        try:
            s = now_time > close_time > datetime.strptime(time_now, "04:00")
        except Exception:
            return
        time_dif = str(close_time - now_time).split(':')
        hours, minutes = float(time_dif[0]) * 60 * 60, float(time_dif[1]) * 60
        total_time = hours + minutes
        await asyncio.sleep(total_time)
        check = 0
        for ret in sqlite_db.cur.execute('SELECT report_close_id FROM reports_open WHERE report_close_id LIKE ? '
                                         'AND person LIKE ?', ['', inf.get_name(id1)]):
            check = ret[0]
        if check != 0:
            close_time = str(close_time + timedelta(hours=0, minutes=16)).split(" ")[1]
            await bot.send_message(id1, f'⚠️Напоминание⚠️ ️ Не забудь закрыть смену в боте и проверить чистоту на точке.\n'
                                        f'Закрытие смены должно быть не раньше {close_time}')
            await remind_close2(id1)
    except Exception:
        return


async def remind_close2(id1):
    await asyncio.sleep(60*45)
    check, point, person = 0, 0, 0
    for ret in sqlite_db.cur.execute('SELECT report_close_id, point1, person FROM reports_open WHERE report_close_id '
                                     'LIKE ? AND person LIKE ?', ['', inf.get_name(id1)]):
        check, point, person = ret[0], ret[1], ret[2]
    if check != 0:
        for _id in inf.get_admin_id():
            await bot.send_message(_id, f'❗️❗️❗️Смена на точке {point} продавцом {person} не закрыта вовремя!')
        await bot.send_message(id1, f'❗️❗️❗️ ️Смена не закрыта вовремя.'
                                    f' Если есть проблемы - напиши в чат с ботом')
#        await remind_close3(id1)


async def remind_close3(id1):
    await asyncio.sleep(30)
    check, point, person = 0, 0, 0
    for ret in sqlite_db.cur.execute('SELECT report_close_id, point1, person FROM reports_open WHERE report_close_id '
                                     'LIKE ? AND person LIKE ?', ['', inf.get_name(id1)]):
        check, point, person = ret[0], ret[1], ret[2]
    if check != 0:
        for _id in inf.get_admin_id():
            sqlite_db.cur.execute('DELETE FROM reports_open WHERE report_close_id LIKE ? AND person LIKE ?', ['', inf.get_name(id1)])
            sqlite_db.base.commit()
            await bot.send_message(_id, f'❗️Открытие {point} продавцом {person} было удалено, поскольку смена не'
                                        f' была закрыта в течение двух часов, после закрытия магазина')


async def finish_report_open(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    sqlite_db.cur.execute('UPDATE reports_open SET problem_photos = ? WHERE problem_photos LIKE ?',
                          ['False', callback_query.from_user.id])
    sqlite_db.base.commit()
    #agree_kb = InlineKeyboardMarkup().add(InlineKeyboardButton(f"Да", callback_data=f"next_law ")).insert(InlineKeyboardButton(f"Нет", callback_data=f"show_law "))
    #await bot.send_message(callback_query.from_user.id, f"Вы знаете о том, что продажа алкогольных напитков и табачных изделий лицам, не достигшим 18 лет, строго запрещена?", reply_markup=agree_kb)
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    agree_kb = InlineKeyboardMarkup().add(InlineKeyboardButton(f"Да", callback_data=f"next_law ")).insert(InlineKeyboardButton(f"Нет", callback_data=f"show_law "))
    await bot.send_message(callback_query.from_user.id, f"Вы знаете о том, что продажа алкогольных напитков и табачных изделий лицам, не достигшим 18 лет, строго запрещена?", reply_markup=agree_kb)



async def online_cassa_yes(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    agree_kb = InlineKeyboardMarkup().add(InlineKeyboardButton(f"Да", callback_data=f"next_law ")).insert(InlineKeyboardButton(f"Нет", callback_data=f"show_law "))
    await bot.send_message(callback_query.from_user.id, f"Вы знаете о том, что продажа алкогольных напитков и табачных изделий лицам, не достигшим 18 лет, строго запрещена?", reply_markup=agree_kb)


async def online_cassa_no(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id, f"Впишите наличность в кассе, указанную в 'Мой Склад':")
    await FSMOnline_Cassa.online_cassa.set()
            

async def online_cassa_set(message: types.Message, state: FSMContext):
    cassa = punctuation(message.text)
    for id in inf.get_admin_id():
        await bot.send_message(id, f"❗️Наличность в кассе, указанная в Мой Склад: {cassa}")
    agree_kb = InlineKeyboardMarkup().add(InlineKeyboardButton(f"Да", callback_data=f"next_law ")).insert(InlineKeyboardButton(f"Нет", callback_data=f"show_law "))
    await bot.send_message(message.from_user.id, f"Вы знаете о том, что продажа алкогольных напитков и табачных изделий лицам, не достигшим 18 лет, строго запрещена?", reply_markup=agree_kb)
    await state.finish()



async def problem_open(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Без фото').add('Отмена')
    await callback_query.message.answer(f'Зафиксируйте проблему с помощью фото и отправьте. Если фото не нужно, '
                                        f'нажмите "Без фото" ', reply_markup=keyboard)
    await FSMProblem.problems.set()


async def add_photo_problem(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    keyboards = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboards.add('Добавить фото').insert('Закончить').row('Отмена')
    if current_state == "FSMProblem:problems":
        async with state.proxy() as data:
            if message.photo:
                if 'problem_photos' not in data:
                    data['problem_photos'] = message.photo[0].file_id + ' '
                else:
                    data['problem_photos'] += message.photo[0].file_id + ' '
                await bot.send_message(message.from_user.id, f'Фото успешно загружено', reply_markup=keyboards)
                await FSMProblem.next()
            else:
                data['problem_photos'] = 'False'
                await bot.send_message(message.from_user.id, f'Опишите проблемы:',
                                       reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена'))
                await FSMProblem.comments.set()


async def state_continue(message: types.Message):
    if message.text == 'Добавить фото':
        await bot.send_message(message.from_user.id, f'Загрузите ещё одно фото',
                               reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена'))
        await FSMProblem.problems.set()


async def finish_problem(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['comments'] = message.text
        for ret in sqlite_db.cur.execute('SELECT id, point1, person FROM reports_open WHERE problem_photos LIKE ?',
                                         [message.from_user.id]):
             id1, point, person = ret[0], ret[1], ret[2]
        sqlite_db.cur.execute('UPDATE reports_open SET comments = ? WHERE problem_photos LIKE ?',
                              [data['comments'], message.from_user.id])
        sqlite_db.cur.execute('UPDATE reports_open SET problem_photos = ? WHERE problem_photos LIKE ?',
                              [data['problem_photos'], message.from_user.id])
        sqlite_db.base.commit()
        await state.finish()
        admins = inf.get_admin_id()
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(f'Подробности', callback_data=f'get_problem {id1}'))
        for _id in admins:
            try:
                await bot.send_message(_id, f'На точке {point} обнаружены проблемы. Продавец: {person}', reply_markup=keyboard)
            except Exception:
                pass
        await bot.send_message(message.from_user.id, f'Администраторы будут уведомлены о проблеме.')
        agree_kb = InlineKeyboardMarkup().add(InlineKeyboardButton(f"Да", callback_data=f"next_law ")).insert(InlineKeyboardButton(f"Нет", callback_data=f"show_law "))
        await bot.send_message(message.from_user.id, f"Вы знаете о том, что продажа алкогольных напитков и табачных изделий лицам, не достигшим 18 лет, строго запрещена?", reply_markup=agree_kb)




def register_handlers_open_report(dp: Dispatcher):
    dp.register_message_handler(cm_open_start,
                                Text(equals=f'{emoji_bot.em_report_close}Открыть смену', ignore_case=True), state=None)
    dp.register_message_handler(load_person_open, state=FSMOpen.person)
    dp.register_message_handler(load_point_open, state=FSMOpen.point)
    dp.register_message_handler(load_date_open, state=FSMOpen.date)
    dp.register_message_handler(load_in_box_open, state=FSMOpen.in_box)
    dp.register_message_handler(load_in_vault_open, state=FSMOpen.in_vault)
    dp.register_message_handler(load_selfie_open, content_types=['photo'], state=FSMOpen.selfie)
    
    dp.register_callback_query_handler(finish_law_storage, lambda x: x.data and x.data.startswith('storage_law_yes '))
    dp.register_callback_query_handler(show_law_no, lambda x: x.data and x.data.startswith('storage_law_no '))

    dp.register_callback_query_handler(show_law, lambda x: x.data and x.data.startswith('show_law '))
    dp.register_callback_query_handler(next_law, lambda x: x.data and x.data.startswith('next_law '))
    dp.register_callback_query_handler(finish_law, lambda x: x.data and x.data.startswith('finish_law '))
    dp.register_callback_query_handler(finish_law2, lambda x: x.data and x.data.startswith('finish_law2 '))
    dp.register_callback_query_handler(problem_open, lambda x: x.data and x.data.startswith('problem '))
    dp.register_callback_query_handler(finish_report_open, lambda x: x.data and x.data.startswith('finish_open '))
    dp.register_callback_query_handler(online_cassa_yes, lambda x: x.data and x.data.startswith('cass_law_yes '))
    dp.register_callback_query_handler(online_cassa_no, lambda x: x.data and x.data.startswith('cass_law_no '))

    dp.register_message_handler(online_cassa_set, state=FSMOnline_Cassa.online_cassa)
    dp.register_message_handler(add_photo_problem, content_types=['any'], state=FSMProblem.problems)
    # dp.register_message_handler(add_photo_open, content_types=['any'], state=FSMProblem.problems)
    # dp.register_message_handler(start_state_continue, state=FSMProblem.state_continue)
    dp.register_message_handler(state_continue, state=FSMProblem.state_continue)
    dp.register_message_handler(finish_problem, state=FSMProblem.comments)
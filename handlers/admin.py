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


class FSMRedacting(StatesGroup):
    person = State()
    point = State()
    date = State()
    cash = State()
    non_cash = State()
    non_cash_sbp = State()
    non_cash_qr = State()
    transfers = State()
    total = State()
    in_box = State()
    in_vault = State()
    expenses = State()
    photo1 = State()
    photo2 = State()
    comments = State()
    open_box = State()
    open_vault = State()


get_data = {}


def punctutation(mes):
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
    return not (len(m) == 3 and (len(m[0]) == 2 or len(m[0]) == 1) and (len(m[1]) == 2 or len(m[1]) == 1) and len(m[2]) == 4 
        and m[0].isdigit() and m[1].isdigit() and m[2].isdigit()
        and int(m[0])<32 and int(m[1]) < 13 and int(m[2]) in range(2021, 2030))
################################
#УЧЕСТЬ ОТКРЫТИЕ СМЕНЫ
################################

# @dp.message_handler(commands=['admin'], user_id=int(0))
async def admin(message: types.Message):
    if message.from_user.id in inf.get_mod_id():
        await bot.send_message(message.from_user.id, 'Вы успешно зашли в модератора', reply_markup=inf.kb(message.from_user.id))
    elif message.from_user.id not in inf.get_users_id():
        await bot.send_message(message.from_user.id, 'Эта функция вам не доступна')
    elif message.from_user.id in inf.get_admin_id():
        await(bot.send_message(message.from_user.id, f"Вы успешно зашли в админа",
                               reply_markup=inf.kb(message.from_user.id)))
    elif message.from_user.id in inf.get_main_cassier_id():
        await(bot.send_message(message.from_user.id, f"Вы успешно зашли в старшего кассира",
                               reply_markup=inf.kb(message.from_user.id)))
    elif message.from_user.id in inf.get_storager_id():
        await(bot.send_message(message.from_user.id, f"Вы успешно зашли в кладовщика",
                               reply_markup=inf.kb(message.from_user.id)))
    elif message.from_user.id in inf.get_users_id():
        await(bot.send_message(message.from_user.id, f"Вы успешно зашли в кассира",
                               reply_markup=inf.kb(message.from_user.id)))
    for mod_id in inf.get_mod_id():
        time = str(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        await bot.send_message(mod_id, f'{inf.get_name(str(message.from_user.id))}, {message.from_user.id}, {time}: {message.text}')


async def update_buttons(message:types.Message):
    ids = []
    for ret in sqlite_db.cur.execute('SELECT * FROM users'):
        ids.append(int(ret[0]))
    for id0 in ids:
        await bot.send_message(id0, f'Клавиатура бота была обновлена', reply_markup = inf.kb(id0))


async def update_buttons_admin(message:types.Message):
    ids = []
    for ret in sqlite_db.cur.execute('SELECT * FROM users'):
        if ret[2] == "Администратор" or ret[2] == "Модератор":
            ids.append(int(ret[0]))
    for id0 in ids:
        await bot.send_message(id0, f'Клавиатура бота была обновлена', reply_markup = inf.kb(id0))

# Удаление отчёта
# @dp.callback_query_handler(lambda x: x.data and x.data.startswith('del '))
async def del_callback_run(callback_query: types.CallbackQuery):
    id1 = callback_query.data.split(' ')[1]
    sqlite_db.cur.execute('DELETE FROM last_report WHERE id LIKE ?', [id1])
    sqlite_db.cur.execute('DELETE FROM reports_open WHERE report_close_id LIKE ?', [id1])
    sqlite_db.cur.execute('DELETE FROM reports_open WHERE id LIKE ?', [id1])
    sqlite_db.base.commit()
    await sqlite_db.sql_delete_command(id1)
    await callback_query.answer(text=f'Отчёт удалён', show_alert=True)

async def take_photo(callback_query: types.CallbackQuery):
    id_report = callback_query.data.split(' ')[1]
    id_user = callback_query.data.split(' ')[2]
    for ret in sqlite_db.cur.execute('SELECT photo1, photo2, date1, point1 FROM menu WHERE id LIKE ?', [id_report]):
        date = ret[2]
        point = ret[3]
        if ret[0] is None:
            await bot.send_message(id_user, f'Фото за этот день не добавлено')
        else:
            media = types.MediaGroup()
            media.attach_photo(f'{ret[0]}')
            media.attach_photo(f'{ret[1]}', f'Фото отчётов за {date} с {point}')
            await bot.send_media_group(int(id_user), media = media)


async def take_photo_invoices(callback_query: types.CallbackQuery):
    id0 = callback_query.data.split(' ')[1]
    id_user = callback_query.data.split(' ')[2]
    photos = []
    description = 0
    for ret in sqlite_db.cur.execute('SELECT * FROM invoices WHERE id LIKE ?', [id0]):
        photos.append(ret[9])
        if description == 0: 
            description = [ret[0], ret[1], ret[2], ret[3], ret[4], ret[8]]
    desc = f'Номер накладной: {ret[0]}\nЗагружено пользователем: {ret[1]}\nТочка: {ret[2]}\nПоставщик: {ret[3]}\nДата: {ret[4]}\nСумма документа: {ret[8]}'
    media = types.MediaGroup()
    for photo in photos:
        media.attach_photo(f'{photo}')
    await bot.send_media_group(id_user, media = media)
    await bot.send_message(id_user, f'{desc}')


async def take_last_report(message: types.Message):
    for mod_id in inf.get_mod_id():
        time = str(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        await bot.send_message(mod_id, f'{inf.get_name(str(message.from_user.id))}, {message.from_user.id}, {time} получает прошлый отчёт: {message.text}')
    users_id = inf.get_users_id()
    if message.from_user.id not in users_id:
        await bot.send_message(message.from_user.id, 'Вам не доступна эта функция')
        return
    for user in inf.get_users():
        if int(user[0]) == message.from_user.id:
            user_name = user[1]
    last_date = ''
    for ret in sqlite_db.cur.execute('SELECT * FROM last_report WHERE person LIKE ?', [user_name]).fetchall():
        last_date = datetime.strptime(ret[16], '%Y-%m-%d %H:%M:%S.%f')
        if last_date != '':
            if (datetime.now() > last_date):
                sqlite_db.cur.execute('DELETE FROM last_report WHERE person LIKE ?', [user_name])
                sqlite_db.base.commit()
                await bot.send_message(message.from_user.id, 'У вас больше нет доступа к этому отчёту в связи с истечением срока давности')
                break
            if len(ret[7].split(' ')) == 3:
                beznal, sbp, qr = ret[7].split(' ')[0], ret[7].split(' ')[1], ret[7].split(' ')[2]
            elif len(ret[7].split(' ')) == 2:
                beznal, sbp, qr = ret[7].split(' ')[0], ret[7].split(' ')[1], '0.0'
            else:
                beznal, sbp, qr = ret[7], '0.0', '0.0'
            await bot.send_message(message.from_user.id,
                               f'Кассир {ret[0]}\nТочка {ret[1]}\nДата {ret[2]}\nНаличными {ret[6]}\nТерминал'
                               f' {beznal}\n СБП {sbp}\nQR-Код: {qr}\nПереводы {ret[8]}\nЗа день {ret[9]}\nВ кассе {ret[10]}\nВ сейфе'
                               f' {ret[11]}\nРасходы {ret[12]}\nКомментарии {ret[13]}',
                                   reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(
                                       f'Выгрузить фото отчётов', callback_data=f'pho {ret[17]} {message.from_user.id}')
                                   ).add(InlineKeyboardButton(f'Редактировать {ret[2]}', callback_data=f'red {ret[17]}'))
                                   .insert(InlineKeyboardButton(f'Браки', callback_data=f'get_defect {inf.get_id_point(ret[1])} {ret[2]}')))
    if last_date == '':
        await bot.send_message(message.from_user.id, 'Отчёта не существует')


def global_dictionary(user_id, method="check", data=None):
    if method == "add":
        get_data[user_id] = data
    elif method == "check":
        return get_data[user_id]
    elif method == "clear":
        get_data.pop(user_id, None)


async def del_fine_callback_run(callback_query: types.CallbackQuery):
    id0 = callback_query.data.split(' ')[1]
    sqlite_db.cur.execute('DELETE FROM fine WHERE id LIKE ?', [id0])
    sqlite_db.base.commit()
    await callback_query.answer(text=f'Штраф удалён', show_alert=True)


async def red_callback_run(callback_query: types.CallbackQuery):
    id1 = callback_query.data.split(' ')[1]
    keyboard = InlineKeyboardMarkup(resize_keyboard = True)
    if callback_query.message.chat.id in inf.get_mod_id() or callback_query.message.chat.id in inf.get_admin_id() or callback_query.message.chat.id in inf.get_main_cassier_id():
        data_for_report = ['Кассир', 'Точка', 'Дата', 'Наличными', 'Терминал', 'СБП' ,'QR-Код', 'Переводы', 'Всего', 'В кассе', 'В сейфе', 'Расходы', 'Первое фото', 'Второе фото', 'Комментарии']
    else:
        last_date = ''
        for ret in sqlite_db.cur.execute('SELECT * FROM last_report WHERE id LIKE ?', [id1]).fetchall():
            last_date = datetime.strptime(ret[16], '%Y-%m-%d %H:%M:%S.%f')
        if last_date != '':
            if (datetime.now() > last_date):
                sqlite_db.cur.execute('DELETE FROM last_report WHERE id LIKE ?', [id1])
                sqlite_db.base.commit()
                await callback_query.message.answer(f'Вы больше не можете отредактировать отчёт.', reply_markup = inf.kb(callback_query.message.chat.id))
                return
        if last_date == '':
            await callback_query.message.answer(f'Вы больше не можете отредактировать отчёт.', reply_markup = inf.kb(callback_query.message.chat.id))
            return
        data_for_report = ['Наличными', 'Терминал', 'СБП' ,'QR-Код', 'Переводы', 'Всего', 'В кассе', 'В сейфе', 'Расходы', 'Первое фото', 'Второе фото', 'Комментарии']
    for i in range(len(data_for_report)):
        if i % 3 == 0:
            keyboard.row(InlineKeyboardButton(f'{data_for_report[i]}', callback_data=f'new {callback_query.message.from_user.id} {data_for_report[i]}'))
        else:
            keyboard.insert(InlineKeyboardButton(f'{data_for_report[i]}', callback_data=f'new {callback_query.message.from_user.id} {data_for_report[i]}'))
    msg = await callback_query.bot.send_message(callback_query.message.chat.id,f'Загрузка...', reply_markup = ReplyKeyboardMarkup(resize_keyboard = True).add('Отмена'))
    global_dictionary(callback_query.from_user.id, "clear")
    global_dictionary(callback_query.from_user.id, "add", id1)
    for ret in sqlite_db.cur.execute('SELECT date1, point1 FROM menu WHERE id LIKE ?', [id1]):
        point, date1 = ret[0], ret[1]
    await callback_query.message.answer(f'Выберите, что хотите отредактировать за {date1} с точки {point}', reply_markup = keyboard)


async def new_callback_run(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    name = callback_query.data.split(' ')[2]
    if len(callback_query.data.split(' ')) > 3:
        for i in range(3, len(callback_query.data.split(' '))):
            name += ' ' + callback_query.data.split(' ')[i]
    keyboard = ReplyKeyboardMarkup(resize_keyboard = True)
    if name == 'Кассир':
        for user in inf.get_users():
            keyboard.add(user[1])
        keyboard.add('Отмена')
        await callback_query.message.answer(f'Впишите кассира или выберите из кнопок внизу:', reply_markup = keyboard)
        await FSMRedacting.person.set()
    if name == 'Точка':
        available_points = inf.get_name_shops()
        for i in available_points:
            keyboard.add(i)
        keyboard.add('Отмена')
        await callback_query.message.answer(f'Выберите точку:', reply_markup = keyboard)
        await FSMRedacting.point.set()
    if name == 'Дата':
        keyboard.add(str((datetime.now() - timedelta(days = 1)).strftime('%d.%m.%Y')))
        keyboard.add('Отмена')
        await callback_query.message.answer(f'Впишите дату формата (ДД.ММ.ГГГГ):', reply_markup = keyboard)
        await FSMRedacting.date.set()
    if name == 'Наличными':
        keyboard.add('Отмена')
        await callback_query.message.answer(f'Впишите новое значение наличными:', reply_markup = keyboard)
        await FSMRedacting.cash.set()
    if name == 'Терминал':
        keyboard.add('Отмена')
        await callback_query.message.answer(f'Впишите новое значение безналичными:', reply_markup = keyboard)
        await FSMRedacting.non_cash.set()
    if name == 'СБП':
        keyboard.add('Отмена')
        await callback_query.message.answer(f'Впишите новое значение СБП:', reply_markup = keyboard)
        await FSMRedacting.non_cash_sbp.set()
    if name == 'QR-Код':
        keyboard.add('Отмена')
        await callback_query.message.answer(f'Впишите новое значение QR-Кода:', reply_markup = keyboard)
        await FSMRedacting.non_cash_qr.set()
    if name == 'Переводы':
        keyboard.add('Отмена')
        await callback_query.message.answer(f'Впишите новое значение переводами:', reply_markup = keyboard)
        await FSMRedacting.transfers.set()
    if name == 'Всего':
        keyboard.add('Отмена')
        await callback_query.message.answer(f'Впишите новое значение всего:', reply_markup = keyboard)
        await FSMRedacting.total.set()
    if name == 'В кассе':
        keyboard.add('Отмена')
        await callback_query.message.answer(f'Впишите новое значение для кассы:', reply_markup = keyboard)
        await FSMRedacting.in_box.set()
    if name == 'В сейфе':
        keyboard.add('Отмена')
        await callback_query.message.answer(f'Впишите новое значение для сейфа', reply_markup = keyboard)
        await FSMRedacting.in_vault.set()
    if name == 'Расходы':
        keyboard.add('Отмена')
        await callback_query.message.answer(f'Впишите новое значение для расходов:', reply_markup = keyboard)
        await FSMRedacting.expenses.set()
    if name == 'Первое фото':
        keyboard.add('Отмена')
        await callback_query.message.answer(f'Загрузите фото:', reply_markup = keyboard)
        await FSMRedacting.photo1.set()
    if name == 'Второе фото':
        keyboard.add('Отмена')
        await callback_query.message.answer(f'Загрузите фото:', reply_markup = keyboard)
        await FSMRedacting.photo2.set()
    if name == 'Комментарии':
        keyboard.add('Отмена')
        await callback_query.message.answer(f'Впишите новые комментарии:', reply_markup = keyboard)
        await FSMRedacting.comments.set()
    if name == 'Открытие смены':
        global_dictionary(callback_query.from_user.id, "add", callback_query.data.split(' ')[1])
        id1 = callback_query.data.split(' ')[1]
        name_but = ['Сейф', 'Касса']
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(
            f'В кассе', callback_data=f"red_op_box {id1} {name_but[1]}")
        ).add(InlineKeyboardButton(
            f'В сейфе', callback_data=f"red_op_box {id1} {name_but[0]}"
        ))
        await bot.send_message(callback_query.from_user.id, f'Выберите, что хотите отредактировать:',
                               reply_markup=keyboard)



async def red_person(message: types.Message, state: FSMContext):
    last_data = 0
    info = global_dictionary(message.from_user.id)
    info_id = info
    for ret in sqlite_db.cur.execute('SELECT person, date1, point1 FROM menu WHERE id LIKE ?', [info_id]):
        last_data = ret[0]
        info_data = ret[1]
        info_point = ret[2]
    sqlite_db.cur.execute('UPDATE menu SET person = ? WHERE id LIKE ?', [message.text,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET person = ? WHERE id LIKE ?', [message.text,info_id])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Отчёт успешно обновлён', reply_markup = inf.kb(message.from_user.id))
    for id0 in inf.get_admin_id():
        await bot.send_message(id0, f'Кассир за {info_data} с {info_point} был отредактирован пользователем {inf.get_name(message.from_user.id)} (Заменено {last_data} на {message.text})')
    await state.finish()


async def red_point(message: types.Message, state: FSMContext):
    last_data = 0
    info = global_dictionary(message.from_user.id)
    info_id = info
    available_points = inf.get_name_shops()
    checking = 0
    if message.text not in available_points:
        await message.reply('Выберите магазин из кнопок внизу')
        return
    for ret in sqlite_db.cur.execute('SELECT point1,date1 FROM menu WHERE id LIKE ?', [info_id]):
        last_data = ret[0]
        last_date = ret[1]
        info_data = ret[1]
        info_point = ret[0]
    for ret in sqlite_db.cur.execute('SELECT * FROM menu WHERE date1 LIKE ? AND point1 LIKE ?', [last_date, message.text]):
        checking = ret[2]
    if checking != 0:
        await message.reply('Отчёт с этой точкой за эту дату уже загружен.')
        return
    sqlite_db.cur.execute('UPDATE menu SET point1 = ? WHERE id LIKE ?', [message.text, info_id])
    sqlite_db.cur.execute('UPDATE reports_open SET point1 = ? WHERE report_close_id LIKE ?', [message.text, info_id])
    sqlite_db.cur.execute('UPDATE last_report SET point1 = ? WHERE id LIKE ?', [message.text, info_id])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Отчёт успешно обновлён', reply_markup = inf.kb(message.from_user.id))
    for id0 in inf.get_admin_id():
        await bot.send_message(id0, f'Точка отчёта за {info_data} с {info_point} была отредактирована пользователем {inf.get_name(message.from_user.id)} (Заменено {last_data} на {message.text})')
    await state.finish()


async def red_date(message: types.Message, state: FSMContext):
    last_data = 0
    info = global_dictionary(message.from_user.id)
    info_id = info
    if check_month(message.text):
        await bot.send_message(message.from_user.id, f'Вы ввели некорректную дату, попробуйте ещё раз(формат ДД.ММ.ГГГГ)')
        return
    date2 = ''
    for i in range(0, 2):
        if len(message.text.split('.')[i]) == 1:
            date2 += '0' + message.text.split('.')[i] + '.'
        else:
            date2 += message.text.split('.')[i] + '.'
    date2 += message.text.split('.')[2]
    r = 0
    for ret in sqlite_db.cur.execute('SELECT point1 FROM menu WHERE id LIKE ?', [info_id]):
        info_point = ret[0]
    for ret in sqlite_db.cur.execute('SELECT * FROM menu WHERE date1 LIKE ? AND point1 LIKE ?', [date2, info_point]):
        r = ret[0]
    if r != 0:
        await bot.send_message(message.from_user.id, f'Отчёт с такой датой уже добавлен.', reply_markup = inf.kb(message.from_user.id))
        await state.finish()
        return
    for ret in sqlite_db.cur.execute('SELECT date1, date1, point1 FROM menu WHERE id LIKE ?', [info_id]):
        last_data = ret[0]
        info_data = ret[1]
        info_point = ret[2]
        for ret1 in sqlite_db.cur.execute('SELECT * FROM reports_open WHERE date1 LIKE ? AND point1 LIKE ?',
                                         [date2, info_point]):
            for ret2 in sqlite_db.cur.execute('SELECT * FROM reports_open WHERE date1 LIKE ? AND point1 LIKE ?',
                                             [last_data, info_point]):
                if ret1[2] == ret2[2]:
                    await bot.send_message(message.from_user.id, f'Уже было произведено открытие смены с этой датой и с'
                                                                 f' этим отчётом, удалите одно из них',
                                           reply_markup=inf.kb(message.from_user.id))
                    await state.finish()
                    return
    parse = date2.split('.')
    day, month, year = parse[0], parse[1], parse[2]
    sqlite_db.cur.execute('UPDATE menu SET day = ? WHERE id LIKE ?', [day,info_id])
    sqlite_db.cur.execute('UPDATE menu SET month = ? WHERE id LIKE ?', [month,info_id])
    sqlite_db.cur.execute('UPDATE menu SET year = ? WHERE id LIKE ?', [year,info_id])
    sqlite_db.cur.execute('UPDATE menu SET date1 = ? WHERE id LIKE ?', [date2,info_id])
    sqlite_db.cur.execute('UPDATE reports_open SET date1 = ? WHERE report_close_id LIKE ?', [date2, info_id])
    sqlite_db.cur.execute('UPDATE last_report SET date1 = ? WHERE id LIKE ?', [date2,info_id])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Отчёт успешно обновлён', reply_markup = inf.kb(message.from_user.id))
    for id0 in inf.get_admin_id():
        await bot.send_message(id0, f'Дата отчёта за {info_data} с {info_point} была отредактирована пользователем {inf.get_name(message.from_user.id)} (Заменено {last_data} на {message.text})')
    await state.finish()


async def red_cash(message: types.Message, state: FSMContext):
    info = global_dictionary(message.from_user.id)
    info_id = info
    if punctutation(message.text) == None:
        await bot.send_message(message.from_user.id, f'Вы ввели некорректное число')
        return
    last_data = 0
    result = punctutation(message.text)
    for ret in sqlite_db.cur.execute('SELECT cash, date1, point1, non_cash, transfers FROM menu WHERE id LIKE ?', [info_id]):
        last_data = ret[0]
        info_data = ret[1]
        info_point = ret[2]
        if len(ret[3].split(' ')) == 3:
            last_non_cash = float(ret[3].split(' ')[0]) + float(ret[3].split(' ')[1]) + float(ret[3].split(' ')[2])
        elif len(ret[3].split(' ')) == 2:
            last_non_cash = float(ret[3].split(' ')[0]) + float(ret[3].split(' ')[1])
        else:
            last_non_cash = float(ret[3])
        last_transfers = float(ret[4])
    new_total = last_non_cash + last_transfers + result
    sqlite_db.cur.execute('UPDATE menu SET cash = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET cash = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.cur.execute('UPDATE menu SET total = ? WHERE id LIKE ?', [new_total,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET total = ? WHERE id LIKE ?', [new_total,info_id])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Отчёт успешно обновлён, Итог заменён на {new_total}', reply_markup = inf.kb(message.from_user.id))
    for id0 in inf.get_admin_id():
        await bot.send_message(id0, f'Сумма наличными отчёта за {info_data} с {info_point} было отредактировано пользователем {inf.get_name(message.from_user.id)} (Заменено {last_data} на {message.text}, Итого заменено на {new_total})')
    await state.finish()


async def red_non_cash(message: types.Message, state: FSMContext):
    info = global_dictionary(message.from_user.id)
    info_id = info
    last_beznal = 0
    for ret in sqlite_db.cur.execute('SELECT non_cash, date1, point1, cash, transfers FROM menu WHERE id LIKE ?', [info_id]):
        if len(ret[0].split(' ')) == 3:
            last_beznal, last_sbp, last_qr = ret[0].split(' ')[0], ret[0].split(' ')[1], ret[0].split(' ')[2]
        elif len(ret[0].split(' ')) == 2:
            last_beznal, last_sbp, last_qr = ret[0].split(' ')[0], ret[0].split(' ')[1], '0.0'
        else:
            last_beznal, last_sbp, last_qr = ret[0], '0.0', '0.0'
        info_data = ret[1]
        info_point = ret[2]
        result = f"{punctutation(message.text)} {last_sbp} {last_qr}"
        new_total = float(ret[3]) + float(ret[4]) + float(last_sbp) + float(last_qr) + punctutation(message.text)
    sqlite_db.cur.execute('UPDATE menu SET non_cash = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET non_cash = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.cur.execute('UPDATE menu SET total = ? WHERE id LIKE ?', [new_total,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET total = ? WHERE id LIKE ?', [new_total,info_id])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Отчёт успешно обновлён, Итог заменён на {new_total}', reply_markup = inf.kb(message.from_user.id))
    for id0 in inf.get_admin_id():
        await bot.send_message(id0, f'Сумма безналичными с терминала за {info_data} с {info_point} было отредактировано пользователем {inf.get_name(message.from_user.id)} (Заменено {last_beznal} на {punctutation(message.text)}, Итого заменено на {new_total})')
    await state.finish()


async def red_non_cashSBP(message: types.Message, state: FSMContext):
    info = global_dictionary(message.from_user.id)
    info_id = info
    last_beznal = 0
    for ret in sqlite_db.cur.execute('SELECT non_cash, date1, point1, cash, transfers FROM menu WHERE id LIKE ?', [info_id]):
        if len(ret[0].split(' ')) == 3:
            last_beznal, last_sbp, last_qr = ret[0].split(' ')[0], ret[0].split(' ')[1], ret[0].split(' ')[2]
        elif len(ret[0].split(' ')) == 2:
            last_beznal, last_sbp, last_qr = ret[0].split(' ')[0], ret[0].split(' ')[1], '0.0'
        else:
            last_beznal, last_sbp, last_qr = ret[0], '0.0', '0.0'
        result = f"{last_beznal} {punctutation(message.text)} {last_qr}"
        info_data = ret[1]
        info_point = ret[2]
        new_total = float(ret[3]) + float(ret[4]) + float(last_beznal) + float(last_qr) + punctutation(message.text)
    sqlite_db.cur.execute('UPDATE menu SET non_cash = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET non_cash = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.cur.execute('UPDATE menu SET total = ? WHERE id LIKE ?', [new_total,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET total = ? WHERE id LIKE ?', [new_total,info_id])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Отчёт успешно обновлён, Итог заменён на {new_total}', reply_markup = inf.kb(message.from_user.id))
    for id0 in inf.get_admin_id():
        await bot.send_message(id0, f'Сумма безналичными СБП за {info_data} с {info_point} было отредактировано пользователем {inf.get_name(message.from_user.id)} (Заменено {last_sbp} на {punctutation(message.text)}, Итого заменено на {new_total})')
    await state.finish()


async def red_non_cashQR(message: types.Message, state: FSMContext):
    info = global_dictionary(message.from_user.id)
    info_id = info
    last_beznal = 0
    for ret in sqlite_db.cur.execute('SELECT non_cash, date1, point1, cash, transfers FROM menu WHERE id LIKE ?', [info_id]):
        if len(ret[0].split(' ')) == 3:
            last_beznal, last_sbp, last_qr = ret[0].split(' ')[0], ret[0].split(' ')[1], ret[0].split(' ')[2]
        elif len(ret[0].split(' ')) == 2:
            last_beznal, last_sbp, last_qr = ret[0].split(' ')[0], ret[0].split(' ')[1], '0.0'
        else:
            last_beznal, last_sbp, last_qr = ret[0], '0.0', '0.0'
        result = f"{last_beznal} {last_sbp} {punctutation(message.text)}"
        info_data = ret[1]
        info_point = ret[2]
        new_total = float(ret[3]) + float(ret[4]) + float(last_sbp) + float(last_beznal) + punctutation(message.text)
    sqlite_db.cur.execute('UPDATE menu SET non_cash = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET non_cash = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.cur.execute('UPDATE menu SET total = ? WHERE id LIKE ?', [new_total,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET total = ? WHERE id LIKE ?', [new_total,info_id])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Отчёт успешно обновлён, Итог заменён на {new_total}', reply_markup = inf.kb(message.from_user.id))
    for id0 in inf.get_admin_id():
        await bot.send_message(id0, f'Сумма безналичными по QR за {info_data} с {info_point} было отредактировано пользователем {inf.get_name(message.from_user.id)} (Заменено {last_qr} на {punctutation(message.text)}, Итого заменено на {new_total})')
    await state.finish()

async def red_transfers(message: types.Message, state: FSMContext):
    info = global_dictionary(message.from_user.id)
    info_id = info
    if punctutation(message.text) == None:
        await bot.send_message(message.from_user.id, f'Вы ввели некорректное число')
        return
    last_data = 0
    result = punctutation(message.text)
    for ret in sqlite_db.cur.execute('SELECT transfers, date1, point1, cash, non_cash FROM menu WHERE id LIKE ?', [info_id]):
        if len(ret[4].split(' ')) == 3:
            last_beznal, last_sbp, last_qr = ret[4].split(' ')[0], ret[4].split(' ')[1], ret[4].split(' ')[2]
        elif len(ret[4].split(' ')) == 2:
            last_beznal, last_sbp, last_qr = ret[4].split(' ')[0], ret[4].split(' ')[1], '0.0'
        else:
            last_beznal, last_sbp, last_qr = ret[4], '0.0', '0.0'
        last_data = ret[0]
        info_data = ret[1]
        info_point = ret[2]
        new_total = float(ret[3]) + float(last_beznal) + float(last_sbp) + result + float(last_qr)
    sqlite_db.cur.execute('UPDATE menu SET transfers = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET transfers = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.cur.execute('UPDATE menu SET total = ? WHERE id LIKE ?', [new_total,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET total = ? WHERE id LIKE ?', [new_total,info_id])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Отчёт успешно обновлён, Итог заменён на {new_total}', reply_markup = inf.kb(message.from_user.id))
    for id0 in inf.get_admin_id():
        await bot.send_message(id0, f'Сумма переводами отчёта за {info_data} с {info_point} было отредактировано пользователем {inf.get_name(message.from_user.id)} (Заменено {last_data} на {message.text}, Итого заменено на {new_total})')
    await state.finish()


async def red_total(message: types.Message, state: FSMContext):
    info = global_dictionary(message.from_user.id)
    info_id = info
    if punctutation(message.text) == None:
        await bot.send_message(message.from_user.id, f'Вы ввели некорректное число')
        return
    last_data = 0
    result = punctutation(message.text)
    for ret in sqlite_db.cur.execute('SELECT total, date1, point1 FROM menu WHERE id LIKE ?', [info_id]):
        last_data = ret[0]
        info_data = ret[1]
        info_point = ret[2]
    sqlite_db.cur.execute('UPDATE menu SET total = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET total = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Отчёт успешно обновлён', reply_markup = inf.kb(message.from_user.id))
    for id0 in inf.get_admin_id():
        await bot.send_message(id0, f'Общая сумма отчёта за {info_data} с {info_point} было отредактировано пользователем {inf.get_name(message.from_user.id)} (Заменено {last_data} на {message.text})')
    await state.finish()


async def red_in_box(message: types.Message, state: FSMContext):
    info = global_dictionary(message.from_user.id)
    info_id = info
    if punctutation(message.text) == None:
        await bot.send_message(message.from_user.id, f'Вы ввели некорректное число')
        return
    last_data = 0
    result = punctutation(message.text)
    for ret in sqlite_db.cur.execute('SELECT in_box, date1, point1 FROM menu WHERE id LIKE ?', [info_id]):
        last_data = ret[0]
        info_data = ret[1]
        info_point = ret[2]
    sqlite_db.cur.execute('UPDATE menu SET in_box = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET in_box = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Отчёт успешно обновлён', reply_markup = inf.kb(message.from_user.id))
    for id0 in inf.get_admin_id():
        await bot.send_message(id0, f'В кассе отчёта за {info_data} с {info_point} было отредактировано пользователем {inf.get_name(message.from_user.id)} (Заменено {last_data} на {message.text})')
    await state.finish()


async def red_in_vault(message: types.Message, state: FSMContext):
    info = global_dictionary(message.from_user.id)
    info_id = info
    if punctutation(message.text) == None:
        await bot.send_message(message.from_user.id, f'Вы ввели некорректное число')
        return
    last_data = 0
    result = punctutation(message.text)
    for ret in sqlite_db.cur.execute('SELECT in_vault, date1, point1 FROM menu WHERE id LIKE ?', [info_id]):
        last_data = ret[0]
        info_data = ret[1]
        info_point = ret[2]
    sqlite_db.cur.execute('UPDATE menu SET in_vault = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET in_vault = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Отчёт успешно обновлён', reply_markup = inf.kb(message.from_user.id))
    for id0 in inf.get_admin_id():
        await bot.send_message(id0, f'В сейфе отчёта за {info_data} с {info_point} было отредактировано пользователем {inf.get_name(message.from_user.id)} (Заменено {last_data} на {message.text})')
    await state.finish()


async def red_expenses(message: types.Message, state: FSMContext):
    info = global_dictionary(message.from_user.id)
    info_id = info
    if punctutation(message.text) == None:
        await bot.send_message(message.from_user.id, f'Вы ввели некорректное число')
        return
    last_data = 0
    result = punctutation(message.text)
    for ret in sqlite_db.cur.execute('SELECT expenses, date1, point1 FROM menu WHERE id LIKE ?', [info_id]):
        last_data = ret[0]
        info_data = ret[1]
        info_point = ret[2]
    sqlite_db.cur.execute('UPDATE menu SET expenses = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET expenses = ? WHERE id LIKE ?', [result,info_id])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Отчёт успешно обновлён', reply_markup = inf.kb(message.from_user.id))
    for id0 in inf.get_admin_id():
        await bot.send_message(id0, f'Расходы отчёта за {info_data} с {info_point} были отредактированы пользователем {inf.get_name(message.from_user.id)} (Заменено {last_data} на {message.text})')
    await state.finish()


async def red_photo1(message: types.Message, state: FSMContext):
    info = global_dictionary(message.from_user.id)
    info_id = info
    last_data = 0
    for ret in sqlite_db.cur.execute('SELECT date1, point1 FROM menu WHERE id LIKE ?', [info_id]):
        info_data = ret[0]
        info_point = ret[1]
    sqlite_db.cur.execute('UPDATE menu SET photo1 = ? WHERE id LIKE ?', [message.photo[0].file_id,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET photo1 = ? WHERE id LIKE ?', [message.photo[0].file_id,info_id])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Отчёт успешно обновлён', reply_markup = inf.kb(message.from_user.id))
    for id0 in inf.get_admin_id():
        await bot.send_message(id0, f'Фото отчёта за {info_data} с {info_point} было отредактировано пользователем {inf.get_name(message.from_user.id)}')
    await state.finish()


async def red_photo2(message: types.Message, state: FSMContext):
    info = global_dictionary(message.from_user.id)
    info_id = info
    for ret in sqlite_db.cur.execute('SELECT date1, point1 FROM menu WHERE id LIKE ?', [info_id]):
        info_data = ret[0]
        info_point = ret[1]
    sqlite_db.cur.execute('UPDATE menu SET photo2 = ? WHERE id LIKE ?', [message.photo[0].file_id,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET photo2 = ? WHERE id LIKE ?', [message.photo[0].file_id,info_id])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Отчёт успешно обновлён', reply_markup = inf.kb(message.from_user.id))
    for id0 in inf.get_admin_id():
        await bot.send_message(id0, f'Фото отчёта за {info_data} с {info_point} было отредактировано пользователем {inf.get_name(message.from_user.id)}')
    await state.finish()


async def red_comments(message: types.Message, state: FSMContext):
    info = global_dictionary(message.from_user.id)
    info_id = info
    last_data = 0
    for ret in sqlite_db.cur.execute('SELECT comments, date1, point1 FROM menu WHERE id LIKE ?', [info_id]):
        last_data = ret[0]
        info_data = ret[1]
        info_point = ret[2]
    sqlite_db.cur.execute('UPDATE menu SET comments = ? WHERE id LIKE ?', [message.text,info_id])
    sqlite_db.cur.execute('UPDATE last_report SET comments = ? WHERE id LIKE ?', [message.text,info_id])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Отчёт успешно обновлён', reply_markup = inf.kb(message.from_user.id))
    for id0 in inf.get_admin_id():
        await bot.send_message(id0, f'Комментарии отчёта за {info_data} с {info_point} были отредактированы пользователем {inf.get_name(message.from_user.id)}')
    await state.finish()


async def red_box_open(callback_query: types.CallbackQuery):
    name, _id = callback_query.data.split(' ')[2], callback_query.data.split(' ')[1]
    global_dictionary(callback_query.from_user.id, "clear")
    global_dictionary(callback_query.from_user.id, "add", _id)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена')
    if name == "Касса":
        await bot.send_message(callback_query.from_user.id, f'Введите новое значение в кассе:', reply_markup=keyboard)
        await FSMRedacting.open_box.set()
    elif name == "Сейф":
        await bot.send_message(callback_query.from_user.id, f'Введите новое значение в сейфе:', reply_markup=keyboard)
        await FSMRedacting.open_vault.set()


async def red_open_box(message: types.Message, state: FSMContext):
    info = global_dictionary(message.from_user.id)
    if punctutation(message.text) == None:
        await bot.send_message(message.from_user.id, f'Вы ввели некорректное число')
        return
    sqlite_db.cur.execute("UPDATE reports_open SET in_box = ? WHERE id LIKE ?", [message.text, info])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Открытие смены успешно обновлено',
                           reply_markup=inf.kb(message.from_user.id))
    await state.finish()


async def red_open_vault(message: types.Message, state: FSMContext):
    info = global_dictionary(message.from_user.id)
    if punctutation(message.text) == None:
        await bot.send_message(message.from_user.id, f'Вы ввели некорректное число')
        return
    sqlite_db.cur.execute("UPDATE reports_open SET in_vault = ? WHERE id LIKE ?", [message.text, info])
    sqlite_db.base.commit()
    await bot.send_message(message.from_user.id, f'Открытие смены успешно обновлено',
                           reply_markup=inf.kb(message.from_user.id))
    await state.finish()



async def set_incassation(message: types.Message):
    kb = ReplyKeyboardMarkup()
    await bot.send_message(message.from_user.id, "Выберите точку для проведения инкассации")
    

def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(take_last_report, Text(equals=f'{emoji_bot.em_last_report}Выгрузить прошлый отчёт', ignore_case=True))
    dp.register_message_handler(update_buttons, Text(equals=f'Обновить все кнопки', ignore_case=True))
    dp.register_message_handler(update_buttons_admin, Text(equals=f'Обновить все кнопки администраторам', ignore_case=True))
    dp.register_message_handler(set_incassation, Text(equals=f'Инкассировать', ignore_case=True))
    dp.register_message_handler(admin, commands=['admin']) # admin panel

    dp.register_message_handler(red_person, state=FSMRedacting.person)
    dp.register_message_handler(red_point, state=FSMRedacting.point)
    dp.register_message_handler(red_date, state=FSMRedacting.date)
    dp.register_message_handler(red_cash, state=FSMRedacting.cash)
    dp.register_message_handler(red_non_cash, state=FSMRedacting.non_cash)
    dp.register_message_handler(red_non_cashSBP, state=FSMRedacting.non_cash_sbp)
    dp.register_message_handler(red_non_cashQR, state=FSMRedacting.non_cash_qr)
    dp.register_message_handler(red_total, state=FSMRedacting.total)
    dp.register_message_handler(red_transfers, state=FSMRedacting.transfers)
    dp.register_message_handler(red_in_box, state=FSMRedacting.in_box)
    dp.register_message_handler(red_in_vault, state=FSMRedacting.in_vault)
    dp.register_message_handler(red_expenses, state=FSMRedacting.expenses)
    dp.register_message_handler(red_photo1, content_types=['photo'], state=FSMRedacting.photo1)
    dp.register_message_handler(red_photo2, content_types=['photo'], state=FSMRedacting.photo2)
    dp.register_message_handler(red_comments, state=FSMRedacting.comments)
    dp.register_message_handler(red_open_box, state=FSMRedacting.open_box)
    dp.register_message_handler(red_open_vault, state=FSMRedacting.open_vault)

    dp.register_callback_query_handler(red_box_open, lambda x: x.data and x.data.startswith('red_op_box '))
    dp.register_callback_query_handler(del_callback_run, lambda x: x.data and x.data.startswith('del ')) #Удаление отчёта
    dp.register_callback_query_handler(red_callback_run, lambda x: x.data and x.data.startswith('red ')) #Начало редактирования отчёта
    dp.register_callback_query_handler(new_callback_run, lambda x: x.data and x.data.startswith('new ')) #Редактирование отчёта
    dp.register_callback_query_handler(del_fine_callback_run, lambda x: x.data and x.data.startswith('delfine ')) #удаление отчёта
    dp.register_callback_query_handler(take_photo, lambda x: x.data and x.data.startswith('pho ')) 
    dp.register_callback_query_handler(take_photo_invoices, lambda x: x.data and x.data.startswith('dho ')) #фото отчёта
    #dp.register_message_handler(start_notific, commands='snot', state="*")
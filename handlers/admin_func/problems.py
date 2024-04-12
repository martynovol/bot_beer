import asyncio

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
from handlers import emoji_bot


class FSMGet_problems(StatesGroup):
    date = State()


def check_month(m):
    m = m.split('.')
    return not (len(m) == 3 and (len(m[0]) == 2 or len(m[0]) == 1) and (len(m[1]) == 2 or len(m[1]) == 1) and len(
        m[2]) == 4
                and m[0].isdigit() and m[1].isdigit() and m[2].isdigit()
                and int(m[0]) < 32 and int(m[1]) < 13 and int(m[2]) in range(2021, 2030))

async def cm_start_get_problems(message: types.Message):
    time = str(datetime.now().strftime('%d.%m.%Y'))
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(time).row('Отмена')
    await bot.send_message(message.from_user.id,'Дата выгрузки проблем на точках:', reply_markup=keyboard)
    await FSMGet_problems.date.set()


async def load_date_get_problem(message: types.Message, state: FSMContext):
    if check_month(message.text):
        await bot.send_message(message.from_user.id,
                               f'Вы ввели некорректную дату, попробуйте ещё раз(формат ДД.ММ.ГГГГ)')
        return
    date2, check = '', True
    for i in range(0, 2):
        if len(message.text.split('.')[i]) == 1:
            date2 += '0' + message.text.split('.')[i] + '.'
        else:
            date2 += message.text.split('.')[i] + '.'
    date2 += message.text.split('.')[2]
    await bot.send_message(message.from_user.id, f'Проблемы на точках {date2}:')
    for ret in sqlite_db.cur.execute('SELECT person, point1, problem_photos, comments, id FROM reports_open WHERE date1 LIKE ?', [date2]):
        if ret[3] != 'False':
            keyboard = InlineKeyboardMarkup(resize_keyboard=True).add(
                InlineKeyboardButton('Решено', callback_data=f'del_problem {ret[4]}'))
            await bot.send_message(message.from_user.id, f'Пользователь: {ret[0]}\nТочка: {ret[1]}\n'
                                                         f'Комментарии: {ret[3]}', reply_markup=keyboard)
            check = False
            if ret[2] != 'False':
                list_photo, media = ret[2].split(' '), types.MediaGroup()
                for photo in list_photo:
                    if photo != '' and photo != ' ':
                        media.attach_photo(f'{photo}')
                await bot.send_media_group(message.from_user.id, media=media)
    if check:
        await bot.send_message(message.from_user.id, f'Проблем не найдено')
    check = True
    await bot.send_message(message.from_user.id, f'Не схождение в кассе с открытием смен на точках {date2}:')
    for ret in sqlite_db.cur.execute('SELECT person, point1, in_box, in_vault, id FROM reports_open WHERE date1 LIKE ?', [date2]).fetchall():
        now_box = float(ret[2]) + float(ret[3])
        date_last = (datetime.strptime(date2, "%d.%m.%Y") - timedelta(days=1)).strftime('%d.%m.%Y')
        for jet in sqlite_db.cur.execute('SELECT in_box, in_vault, id FROM menu WHERE date1 LIKE ? AND point1 LIKE ?',
                                         [date_last, ret[1]]):
            check = False
            keyboard = InlineKeyboardMarkup().add(
                InlineKeyboardButton('Открытие', callback_data=f'open_rep {ret[4]}')).insert(
                InlineKeyboardButton('Закрытие', callback_data=f'close_rep {jet[2]}')
            )
            last_box = float(jet[0]) + float(jet[1])
            if int(last_box) != int(now_box):
                u = now_box - last_box
                await bot.send_message(message.from_user.id, f'⚠️ Наличность на точке {ret[1]} при открытии '
                                                             f'не сходится с прошлым закрытием на {round(u, 2)} рублей',
                                       reply_markup=keyboard)
    if check:
        await bot.send_message(message.from_user.id, f'Не схождений не найдено')
    check = True
    await bot.send_message(message.from_user.id, f'Не схождение в кассе с закрытием смен на точках {date2}:')
    for ret in sqlite_db.cur.execute('SELECT person, point1, in_box, in_vault, cash, expenses, id FROM menu WHERE date1 LIKE ?',
                                     [date2]).fetchall():
        now_box, cash, expenses = float(ret[2]) + float(ret[3]), float(ret[4]), float(ret[5])
        for jet in sqlite_db.cur.execute(
                'SELECT person, point1, in_box, in_vault, id FROM reports_open WHERE date1 LIKE ? AND point1 LIKE ?', [date2, ret[1]]):
            last_box = float(jet[2]) + float(jet[3])
            check = False
            keyboard = InlineKeyboardMarkup().add(
                InlineKeyboardButton('Закрытие', callback_data=f'close_rep {ret[6]}')).insert(
                InlineKeyboardButton('Открытие', callback_data=f'open_rep {jet[4]}')
            )
            if int(last_box + cash - expenses) != int(now_box):
                u = now_box - (last_box + cash - expenses)
                await bot.send_message(message.from_user.id, f'⚠️ Наличность на точке {ret[1]} не сходится '
                                                             f'с открытием смены на {round(u, 2)} рублей',
                                       reply_markup=keyboard)
    if check:
        await bot.send_message(message.from_user.id, f'Не схождений не найдено')
    await bot.send_message(message.from_user.id, f'Выгрузка закончена',
                           reply_markup=inf.kb(message.from_user.id))
    await state.finish()


async def get_close_report(callback_query: types.CallbackQuery):
    rep_id = callback_query.data.split(' ')[1]
    for ret in sqlite_db.cur.execute("SELECT * FROM menu WHERE id LIKE ? ORDER BY year ASC, month ASC, day ASC", [rep_id]):
        if len(ret[7].split(' ')) == 2:
            beznal, sbp = ret[7].split(' ')[0], ret[7].split(' ')[1]
        else:
            beznal, sbp = ret[7], '0.0'
        repr_id = 0
        for ret1 in sqlite_db.cur.execute('SELECT id, time FROM replace_person WHERE report_close_id LIKE ?', [ret[16]]):
            repr_id, time_rep = ret1[0], ret1[1]
        keyboards2 = InlineKeyboardMarkup().add(
            InlineKeyboardButton(f'Отменить замену', callback_data=f'del_rep {repr_id}'))
        await bot.send_message(callback_query.from_user.id,
                               f'Кассир {ret[0]}\nТочка {ret[1]}\nДата {ret[2]}\nНаличными {ret[6]}\nБезналичными {beznal}\nСБП {sbp}\nПереводы {ret[8]}\nЗа день {ret[9]}\nВ кассе {ret[10]}\nВ сейфе {ret[11]}\nРасходы {ret[12]}\nКомментарии {ret[13]}',
                               reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(f'Выгрузить фото отчётов',
                                                                                            callback_data=f'pho {ret[16]} {callback_query.from_user.id}'))
                               .insert(
                                   InlineKeyboardButton(f'Открытие смены', callback_data=f'open_rep {ret[16]}')).add(
                                   InlineKeyboardButton(f'Удалить за {ret[2]}', callback_data=f'del {ret[16]}'))
                               .insert(InlineKeyboardButton(f'Редактировать {ret[2]}', callback_data=f'red {ret[16]}'))
                               .insert(InlineKeyboardButton(f'Браки',
                                                            callback_data=f'get_defect {inf.get_id_point(ret[1])} {ret[2]}')
                                       ))
        if repr_id != 0:
            await bot.send_message(callback_query.from_user.id, f'Была произведена замена в {time_rep}',
                                   reply_markup=keyboards2)


async def del_problemo(callback_query: types.CallbackQuery):
    pr_id = callback_query.data.split(' ')[1]
    sqlite_db.cur.execute('UPDATE reports_open SET comments = ? WHERE id LIKE ?', ['False', pr_id])
    sqlite_db.base.commit()
    await bot.send_message(callback_query.from_user.id, f'Удалено')

def register_handlers_get_problems(dp: Dispatcher):
    dp.register_callback_query_handler(get_close_report, lambda x: x.data and x.data.startswith('close_rep '))
    dp.register_callback_query_handler(del_problemo, lambda x: x.data and x.data.startswith('del_problem '))
    dp.register_message_handler(cm_start_get_problems, Text(equals=f'Проблемы', ignore_case=True), state=None)
    dp.register_message_handler(load_date_get_problem, state=FSMGet_problems.date)
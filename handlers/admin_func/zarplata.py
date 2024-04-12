from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton

from create_bot import dp, bot
import matplotlib.pyplot as plt
from PIL import Image
from aiogram.types import InputFile
import numpy as np
from database import sqlite_db

from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client, main_cassier_kb

from datetime import datetime
from datetime import date, timedelta

from handlers import inf
from handlers import emoji_bot

import emoji
import statistics


class FSMZarplata(StatesGroup):
    person = State()
    data3 = State()


async def cm_start_zarplata(message: types.Message):
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
    await FSMZarplata.person.set()


async def cancel_handler(message: types.Message, state: FSMContext):
    for mod_id in inf.get_mod_id():
        time = str(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        await bot.send_message(mod_id,
                               f'{inf.get_name(str(message.from_user.id))}, {message.from_user.id}, {time}: {message.text}')
    current_state = await state.get_state()
    kb = cassier_kb.button_cassier if message.from_user.id not in inf.get_admin_id() else admin_kb.button_case_admin
    kb = mod_kb.button_case_mod if message.from_user.id in inf.get_mod_id() else kb
    if current_state is None:
        await message.reply('Вы вернулись назад', reply_markup=kb)
        return
    await state.finish()
    await message.reply('Отправка отчёта отменена', reply_markup=kb)


async def load_person_zarplata(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['person'] = message.text
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    time = str(datetime.now().strftime('%m.%Y'))
    keyboard.add(time)
    keyboard.add('Отмена')
    await FSMZarplata.next()
    await message.reply('Выберите месяц и год(ММ.ГГГГ):', reply_markup=keyboard)


async def load_data3(message: types.Message, state: FSMContext):
    bit = message.text.split('.')
    if len(bit) != 2 or (len(bit[0]) != 1 and len(bit[0]) != 2) or len(bit[1]) != 4 or not bit[0].isdigit() or not bit[
        1].isdigit():
        await message.reply(f'Вы ввели некорректную дату, попробуйте снова, формат "ММ.ГГГГ"')
        return
    if len(bit[0]) == 1:
        bit[0] = '0' + bit[0]
    month, year = bit[0], bit[1]
    async with state.proxy() as data:
        data['data3'] = message.text
        user = data['person']
        result, payments = inf.get_user_salary(user, month, year), inf.get_sum_pay(user, month, year)
        in_pay = result["total_sum"] - payments
        premies = inf.get_premie(user, month, year)
        if in_pay < 0:
            in_pay = 0
        average_day = 0
        if result["total_days"] != 0:
            average_day = int(result["day_total_sum"] / result["total_days"])
        tupls = f'{inf.get_user_id(user)}-{month}-{year}-{result["total_sum"]}'
        text = f'Информация по сотруднику {user} за {month}.{year}\n--------------------------------------------\n' \
               f'Дней отработано: {result["total_days"]}\nСредняя сумма продаж за день: {average_day}\n' \
               f'Процент от продаж: {result["prizes"]} руб.\n' \
               f'Премии: {premies} руб.\n' \
               f'Премии (план продаж): {result["premie_plan"]} руб.\n' \
               f'Удержано в счёт ревизии: {result["revision"]} руб.\n' \
               f'Штрафы: {result["fines"]} руб.\n' \
               f'Опоздания: {result["late"]} руб.\n' \
               f'Взято в счёт зарплаты: {result["user_loss"]} руб. (Скидка: {result["disc_user"]}%)\n' \
               f'Без учёта премии и штрафов: {result["without"]} руб.\n' \
               f'Итог: {result["total_sum"]} руб.' \
               f'\n--------------------------------------------\n' \
               f'Выплачено: {payments} руб.\nК выплате: {in_pay} руб.'
        await bot.send_message(message.from_user.id, text, reply_markup=InlineKeyboardMarkup().add(
                                   InlineKeyboardButton(f'Штрафы', callback_data=f'fine {tupls}')).insert(
            InlineKeyboardButton(f'Премии', callback_data=f'prem {tupls}')
        ).row(
            InlineKeyboardButton(f'Выплаты', callback_data=f'pay {tupls}')
            ).insert(InlineKeyboardButton(f'Детализация', callback_data=f'det:{tupls}')))
    await bot.send_message(message.from_user.id, 'Выгрузка завершена', reply_markup=inf.kb(message.from_user.id))
    await state.finish()
    await sqlite_db.info_admin(message.from_user.id, f"Получил ЗП {user}")


def get_salaries_person(person, month, year):
    day_tl, prize, date_day, s_day, type_s = 0,  0, "", 0, ""
    salarie = {}
    for ret in sqlite_db.cur.execute('SELECT total, point1, date1, day FROM menu WHERE person LIKE ?'
                                     ' AND month LIKE ? AND year LIKE ? ORDER BY year ASC, month ASC, day ASC',
                                     [person, month, year]).fetchall():
        day_tl, point_day, date_day = float(ret[0]), ret[1], ret[2]
        type_salary = inf.get_type_sal(point_day, date_day, person)
        if len(type_salary) != 0:
            type_s, id_s = type_salary.pop('type')
            salary_for_day = inf.get_salary_day(type_s, type_salary, point_day, day_tl)
            if salary_for_day:
                s_day += salary_for_day
            prize += inf.get_prize(day_tl, id_s)
        salarie[ret[3]] = (salary_for_day, inf.get_prize(day_tl, id_s), day_tl)
    return salarie





async def get_detail(call: types.CallbackQuery):
    await sqlite_db.info_admin(call.from_user.id, f"Получил детализацию")
    info = call.data.split(':')[1].split('-')
    if info[0].isdigit():
        user, month, year = inf.get_name(info[0]), info[1], info[2]
    else:
        user, month, year = info[0], info[1], info[2]
    salarie = inf.get_user_salary(user, month, year, True)[1]
    text = f"Детализация по сотруднику {user} [{month}.{year}]:\n\n"
    for day in salarie.keys():
        salary = salarie[day]
        text += f"{day} | Выручка: {salary[2]}\nВсего: {salary[0] + salary[1]} | k: {salary[3]}\nСтавка: {salary[0]} | Процент: {salary[1]}\n"
        text += "-----------------------------------------------------\n"
    text += "\n*k - Коэффициент ставки и премии. Изменяется в случае замен на точке."
    await call.message.answer(text)
    


async def prem_callback_run(call: types.CallbackQuery):
    info = call.data.split(' ')[1].split('-')
    user, month, year, total = inf.get_name(info[0]), info[1], info[2], float(info[3])
    for ret in sqlite_db.cur.execute(
            'SELECT id, date1, premie FROM premies WHERE person LIKE ? AND date1 LIKE ?',
            [user, f"{month}.{year}"]).fetchall():
        await call.message.answer(
            f'Премия за {ret[1]} пользователю {user}:\nНазначено: {ret[2]} рублей\n',
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(f'Отменить премию', callback_data=f'delprem {ret[0]}')))



async def pay_callback_run(callback_query: types.CallbackQuery):
    info = callback_query.data.split(' ')[1].split('-')
    user, month, year, total = inf.get_name(info[0]), info[1], info[2], float(info[3])
    pay_sum = 0
    for ret in sqlite_db.cur.execute(
            'SELECT date1, payment, date2, id FROM payments WHERE person LIKE ? AND month LIKE ? AND year LIKE ?',
            [user, month, year]).fetchall():
        pay_sum += float(ret[1])
        await callback_query.message.answer(
            f'Выплата за {ret[0]} пользователю {user}:\nВыплачено: {ret[1]} рублей\nДата выплаты: {ret[2]}',
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(f'Отменить выплату', callback_data=f'delpay {ret[3]}')))


async def fine_callback_run(callback_query: types.CallbackQuery):
    info = callback_query.data.split()[1]
    user, month, year = inf.get_name(info.split('-')[0]), info.split('-')[1], info.split('-')[2]
    fines = inf.get_fine_user(user, month, year)
    if len(fines) != 0:
        for fine in fines:
            await callback_query.message.answer(
                f'Штраф за {fines[fine][1]}:\nСумма: {fines[fine][0]} рублей\nКомментарии: {fines[fine][2]}',
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(f'Отменить штраф', callback_data=f'delfine {fines[fine][3]}')))


async def del_pay_callback_run(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    id0 = callback_query.data.split(' ')[1]
    sqlite_db.cur.execute('DELETE FROM payments WHERE id LIKE ?', [id0])
    sqlite_db.base.commit()
    await callback_query.answer(text=f'Выплата отменена', show_alert=True)


async def del_prem_callback_run(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    id0 = callback_query.data.split(' ')[1]
    sqlite_db.cur.execute('DELETE FROM premies WHERE id LIKE ?', [id0])
    sqlite_db.base.commit()
    await callback_query.answer(text=f'Премия отменена', show_alert=True)


def register_handlers_zarplata(dp: Dispatcher):
    dp.register_message_handler(cm_start_zarplata,
                                Text(equals=f'{emoji_bot.em_salary_button}Рассчитать зарплату сотрудника',
                                     ignore_case=True), state=None)
    dp.register_message_handler(load_person_zarplata, state=FSMZarplata.person)
    dp.register_message_handler(load_data3, state=FSMZarplata.data3)
    dp.register_callback_query_handler(pay_callback_run,
                                       lambda x: x.data and x.data.startswith('pay '))  # Выгрузка выплат
    dp.register_callback_query_handler(fine_callback_run,
                                       lambda x: x.data and x.data.startswith('fine '))  # Выгрузка штрафов
    dp.register_callback_query_handler(del_pay_callback_run,
                                       lambda x: x.data and x.data.startswith('delpay '))  # Удаление выплаты
    dp.register_callback_query_handler(prem_callback_run,
                                       lambda x: x.data and x.data.startswith('prem '))  # Выгрузка премии
    dp.register_callback_query_handler(del_prem_callback_run,
                                       lambda x: x.data and x.data.startswith('delprem '))
    dp.register_callback_query_handler(get_detail,
                                       lambda x: x.data and x.data.startswith('det:'))
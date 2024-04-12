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
import statistics
import emoji

from aiogram.types import InputFile
import numpy as np
from create_bot import dp, bot
from database import sqlite_db
from PIL import Image


async def take_my_salary(message: types.Message):
    await sqlite_db.info_admin(message.from_user.id, f"Получил свою ЗП")
    if message.from_user.id not in inf.get_users_id():
        await bot.send_message(message.from_user.id, 'Вам не доступна  эта функция')
        return
    user = inf.get_name(message.from_user.id)
    month, year = str(datetime.now().strftime('%m')), str(datetime.now().strftime('%Y'))
    result, payments = inf.get_user_salary(user, month, year), inf.get_sum_pay(user, month, year)
    in_payment = result["total_sum"] - payments
    premies = inf.get_premie(user, month, year)
    if in_payment < 0:
        in_payment = 0
    average_day = 0
    if result["total_days"] != 0:
        average_day = int(result["day_total_sum"] / result["total_days"])
    text = f'Информация по сотруднику {user} за {month}.{year}\n--------------------------------------------\n' \
           f'Дней отработано: {result["total_days"]}\n' \
           f'Средняя сумма продаж за день: {average_day}\n' \
           f'Процент от продаж: {result["prizes"]} руб.\n' \
           f'Премии: {premies} руб.\n' \
           f'Премии (план продаж): {result["premie_plan"]} руб.\n' \
           f'Удержано в счёт ревизии: {result["revision"]} руб.\n' \
           f'Депремирование: {result["fines"]} руб.\n' \
           f'Опоздания: {result["late"]} руб.\n' \
           f'Взято в счёт зарплаты: {result["user_loss"]} руб. (Скидка: {result["disc_user"]}%)\n' \
           f'Без учёта премии и штрафов: {result["without"]} руб.\n' \
           f'Итог: {result["total_sum"] + inf.get_loss_user(user, month, year)} руб.' \
           f'\n--------------------------------------------\n' \
           f'Выплачено: {payments} руб.\nК выплате: {in_payment} руб.'

    tupls = f'{user}-{month}-{year}'
    kb = InlineKeyboardMarkup().row(
                               InlineKeyboardButton(f'Детализация', callback_data=f'det:{tupls}')
                           ).row(
                               InlineKeyboardButton(f'Прошлый месяц', callback_data=f'last_m-{tupls}')
                           )
    if message.from_user.id in inf.get_storager_id() or message.from_user.id in inf.get_drivers_id() or message.from_user.id in inf.get_operators_id() or message.from_user.id in inf.get_only_admin_id():
        await bot.send_message(message.from_user.id, f'{text}\n--------------------------------------------\nВНИМАНИЕ! Функция расчёта предоставлена ИСКЛЮЧИТЕЛЬНО В ОЗНАКОМИТЕЛЬНЫХ ЦЕЛЯХ для сотрудника, поскольку она является всего лишь ПРИБЛИЗИТЕЛЬНОЙ оценкой его заработка и может не совпадать с реальными расчётами.\n\n*В расчёте не учитываются замены, незаписанные в бот депремирования, доп.премии и другие подобные изменения в заработке\n')
    else:
        await bot.send_message(message.from_user.id, f'{text}\n--------------------------------------------\nВНИМАНИЕ! Функция расчёта предоставлена ИСКЛЮЧИТЕЛЬНО В ОЗНАКОМИТЕЛЬНЫХ ЦЕЛЯХ для сотрудника, поскольку она является всего лишь ПРИБЛИЗИТЕЛЬНОЙ оценкой его заработка и может не совпадать с реальными расчётами.\n\n*В расчёте не учитываются замены, незаписанные в бот депремирования, доп.премии и другие подобные изменения в заработке\n',
                           reply_markup= kb)


async def get_last_month_user_salary(callback_query: types.CallbackQuery):
    user = callback_query.data.split('-')[1]
    last_month = datetime.now().replace(day=1) - timedelta(days=1)
    month, year = last_month.strftime("%m.%Y").split('.')
    result, payments = inf.get_user_salary(user, month, year), inf.get_sum_pay(user, month, year)
    in_payment = result["total_sum"] - payments
    premies = inf.get_premie(user, month, year)
    if in_payment < 0:
        in_payment = 0
    average_day = 0
    if result["total_days"] != 0:
        average_day = int(result["day_total_sum"] / result["total_days"])
    text = f'Информация по сотруднику {user} за {month}.{year}\n--------------------------------------------\n' \
           f'Дней отработано: {result["total_days"]}\n' \
           f'Средняя сумма продаж за день: {average_day}\n' \
           f'Процент от продаж: {result["prizes"]} руб.\n' \
           f'Премии: {premies} руб.\n' \
           f'Премии (план продаж): {result["premie_plan"]} руб.\n' \
           f'Удержано в счёт ревизии: {result["revision"]} руб.\n' \
           f'Депремирование: {result["fines"]} руб.\n' \
           f'Опоздания: {result["late"]} руб.\n' \
           f'Взято в счёт зарплаты: {result["user_loss"]} руб. (Скидка: {result["disc_user"]}%)\n' \
           f'Без учёта премии и штрафов: {result["without"]} руб.\n' \
           f'Итог: {result["total_sum"]} руб.' \
           f'\n--------------------------------------------\n' \
           f'Выплачено: {payments} руб.\nК выплате: {in_payment} руб.'
    
    tupls = f'{user}-{month}-{year}'
    await bot.send_message(callback_query.from_user.id, text, reply_markup=InlineKeyboardMarkup().row(
                               InlineKeyboardButton(f'Детализация', callback_data=f'det:{tupls}')
                           ))


def register_handlers_take_my_salary(dp: Dispatcher):
    dp.register_message_handler(take_my_salary,
                                Text(equals=f'{emoji_bot.em_my_salary}Рассчитать мою зарплату за этот месяц',
                                     ignore_case=True), state=None)
    dp.register_callback_query_handler(get_last_month_user_salary,
                                       lambda x: x.data and x.data.startswith('last_m-'))

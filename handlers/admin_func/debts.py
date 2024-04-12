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
import statistics


class FSMDebt(StatesGroup):
    date = State()


async def cm_start_debts(message: types.Message):
    if message.from_user.id not in inf.get_admin_id() and message.from_user.id not in inf.get_main_cassier_id():
        await bot.send_message(message.from_user.id, 'Вам не доступна  эта функция')
        return
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    time = str(datetime.now().strftime('%m.%Y'))
    keyboard.add(time)
    keyboard.add('Отмена')
    await message.reply('Выберите месяц и год(ММ.ГГГГ):', reply_markup=keyboard)
    await FSMDebt.date.set()


async def load_date_debt(message: types.Message, state: FSMContext):
    bit = message.text.split('.')
    if len(bit) != 2 or (len(bit[0]) != 1 and len(bit[0]) != 2) or len(bit[1]) != 4 or not bit[0].isdigit() or not bit[
        1].isdigit():
        await message.reply(f'Вы ввели некорректную дату, попробуйте снова, формат "ММ.ГГГГ"')
        return
    if len(bit[0]) == 1:
        bit[0] = '0' + bit[0]
    month, year = bit[0], bit[1]
    users = []
    for ret in sqlite_db.cur.execute('SELECT person FROM menu WHERE month LIKE ? AND year LIKE ?', [month, year]):
        if ret[0] not in users:
            users.append(ret[0])
    str_ = f"------------------------------\n"
    total_sum, total_sum_pay, total_sum_debt = 0, 0, 0
    result_money = {'total_sum': 0}
    for user in users:
        result_money = inf.get_user_salary(user, month, year)
        pay_sum = 0
        if result_money['total_sum'] > 0:
            for ret in sqlite_db.cur.execute(
                    'SELECT payment FROM payments WHERE person LIKE ? AND month LIKE ? AND year LIKE ?',
                    [user, month, year]).fetchall():
                pay_sum += float(ret[0])
            str_ += f"Сотрудник: {user}, Итог за месяц: {result_money['total_sum']} руб\n"
            str_ += f"Выплачено: {round(pay_sum, 1)} руб, Долг: {result_money['total_sum'] - pay_sum} руб\n"
            str_ += f"------------------------------\n"
            total_sum_debt += result_money['total_sum']
            total_sum += result_money['total_sum'] - pay_sum
            total_sum_pay += pay_sum
    str_ += f"Нужно выплатить: {round(total_sum_debt, 1)}\n"
    str_ += f"Всего выплачено: {round(total_sum_pay, 1)}\n"
    str_ += f"Осталось выплатить: {round(total_sum, 1)}"
    await bot.send_message(message.from_user.id, f'Долги по выплатам за {month}.{year}\n{str_}',
                           reply_markup=inf.kb(message.from_user.id))
    await state.finish()


def register_handlers_debts(dp: Dispatcher):
    dp.register_message_handler(cm_start_debts, Text(equals=f'Долги по выплатам', ignore_case=True), state=None)
    dp.register_message_handler(load_date_debt, state=FSMDebt.date)

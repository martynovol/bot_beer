from telnetlib import KERMIT
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

b1 = KeyboardButton('Отчёты')
b2 = KeyboardButton('Пользователи')
b3 = KeyboardButton('Зарплаты')
b4 = KeyboardButton('Точки')
b5 = KeyboardButton('Расходы')
button_case_mod = ReplyKeyboardMarkup(resize_keyboard=True).add(b1).insert(b2).add(b3).insert(b4).insert(b5)


async def menu_reports(message: types.Message):
    bp = KeyboardButton(f'Загрузка отчётов')
    bn = KeyboardButton(f'Выгрузка отчётов')
    bt = KeyboardButton(f'Задачи')
    b5 = KeyboardButton(f'Списания')
    b6 = KeyboardButton(f'Планы продаж')
    b7 = KeyboardButton(f'Ревизии')
    b9 = KeyboardButton(f'Инкассации')
    b8 = KeyboardButton('Вернуться')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(bp).insert(bn).insert(bt).row(b5).insert(b6).insert(b7).row(b9).row(b8)
    await bot.send_message(message.from_user.id, 'Вы перешли в меню <<Отчёты>>', reply_markup=keyboard)


async def menu_reports_load(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    b1 = KeyboardButton(f'{emoji_bot.em_report_for_day}Выгрузить отчёт за день')
    b3 = KeyboardButton(f'{emoji_bot.em_report_for_diap}Выгрузить диапазон')
    b7 = KeyboardButton('Проблемы')
    b4 = KeyboardButton('Загрузить данные в таблицу')
    b5 = KeyboardButton('Ссылка на таблицу')
    b2 = KeyboardButton(f'{emoji_bot.em_report_for_month}Выгрузить выручку за месяц')
    if message.from_user.id in inf.get_mod_id():
        b6 = KeyboardButton('Сформировать ОПУ')
        keyboard.add(b1).insert(b2).row(b3).insert(b7).row(b4).insert(b5).row(b6)
    else:
        keyboard.add(b1).insert(b3).row(b7).insert(b4).row(b5).insert(b2)
    b8 = KeyboardButton('Вернуться')
    keyboard.row(b8)
    await bot.send_message(message.from_user.id, 'Вы перешли в меню <<Выгрузка отчётов>>', reply_markup=keyboard)


async def menu_incassation_load(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    b1 = KeyboardButton(f'Инкассировать')
    b2 = KeyboardButton(f'Неподтверждённые инкассации')
    #b3 = KeyboardButton(f'Все инкассации')

    b8 = KeyboardButton('Вернуться')
    keyboard.add(b1).row(b2).row(b8)
    await bot.send_message(message.from_user.id, 'Вы перешли в меню <<Инкассации>>', reply_markup=keyboard)


async def menu_users(message: types.Message):
    b1 = KeyboardButton('Добавить пользователя')
    b2 = KeyboardButton('Список пользователей')
    b3 = KeyboardButton('Написать')
    b5 = KeyboardButton(f'{emoji_bot.em_report_load_zamena}Провести замену')
    b4 = KeyboardButton('Вернуться')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(b1).insert(b2).row(b3).insert(b5).row(b4)
    await bot.send_message(message.from_user.id, 'Вы перешли в меню <<Пользователи>>', reply_markup=keyboard)


async def menu_salary(message: types.Message):
    b1 = KeyboardButton(f'{emoji_bot.em_salary_button}Рассчитать зарплату сотрудника')
    b2 = KeyboardButton('Назначить ставку')
    b3 = KeyboardButton(f'{emoji_bot.em_fine_button}Оштрафовать сотрудника')
    b4 = KeyboardButton(f'{emoji_bot.em_my_salary}Рассчитать мою зарплату за этот месяц')
    b5 = KeyboardButton(f'Начислить зарплату')
    b6 = KeyboardButton(f'Долги по выплатам')
    b7 = KeyboardButton(f'Ставки')
    b8 = KeyboardButton(f'Назначить премию')
    bn = KeyboardButton('Вернуться')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(b1).insert(b2).row(b3).insert(b4).row(b5).insert(b6).row(b7).insert(b8).row(bn)
    await bot.send_message(message.from_user.id, 'Вы перешли в меню <<Зарплаты>>', reply_markup=keyboard)


async def menu_invoices(message: types.Message):
    b1 = KeyboardButton('Загрузить накладную')
    b2 = KeyboardButton('Выгрузить накладные')
    b3 = KeyboardButton('Вернуться')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(b1).row(b2).row(b3)
    await bot.send_message(message.from_user.id, 'Вы перешли в меню <<Накладные>>', reply_markup=keyboard)


async def points(message: types.Message):
    b1 = KeyboardButton('Добавить точку')
    b2 = KeyboardButton('Список точек')
    b3 = KeyboardButton('Вернуться')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(b1).row(b2).row(b3)
    await bot.send_message(message.from_user.id, 'Вы перешли в меню <<Накладные>>', reply_markup=keyboard)


async def in_main_menu(message: types.Message):
    await bot.send_message(message.from_user.id, 'Вернуться', reply_markup=inf.kb(message.from_user.id))


async def menu_reports_up(message: types.Message):
    b1 = KeyboardButton(f'{emoji_bot.em_report_close}Открыть смену')
    b2 = KeyboardButton(f'{emoji_bot.em_report_close}Закрыть смену')
    b3 = KeyboardButton('Вернуться')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(b1).row(b2)

    if message.from_user.id not in inf.get_mod_id():
        open_report = False
        for ret in sqlite_db.cur.execute('SELECT close FROM manager_report WHERE close = ? AND person_id = ?', ["0", message.from_user.id]):
            open_report = True
        if open_report:
            keyboard.row(KeyboardButton(f"{emoji_bot.em_report_close}Закрыть смену управляющего"))
        else:
            keyboard.row(KeyboardButton(f"{emoji_bot.em_report_close}Открыть смену управляющего"))

    keyboard.row(b3)
    await bot.send_message(message.from_user.id, 'Вы перешли в меню <<Загрузки отчётов>>', reply_markup=keyboard)


async def menu_tasks(message: types.Message):
    b1 = KeyboardButton(f'📔Назначить задачу')
    b2 = KeyboardButton(f'📔Список задач')
    b3 = KeyboardButton(f'📔Мои задачи')
    b4 = KeyboardButton('Вернуться')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(b1).insert(b2).row(b3).row(b4)
    await bot.send_message(message.from_user.id, 'Вы перешли в меню <<Задачи>>', reply_markup=keyboard)


async def exp_kb(message: types.Message):
    b1 = KeyboardButton(f'Добавить категорию расходов')
    b2 = KeyboardButton(f'Добавить категорию выплат')
    b4 = KeyboardButton(f'Категории выплат')
    b3 = KeyboardButton(f'Категории расходов')
    b5 = KeyboardButton('Вернуться')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(b1).insert(b2).row(b3).insert(b4).row(b5)
    await bot.send_message(message.from_user.id, 'Вы перешли в меню <<Расходы>>', reply_markup=keyboard)


async def menu_loss(message: types.Message):
    b1 = KeyboardButton('📝Добавить списание')
    b2 = KeyboardButton('📝Выгрузить списания')
    b3 = KeyboardButton('Вернуться')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(b1).row(b2).row(b3)
    await bot.send_message(message.from_user.id, 'Вы перешли в меню <<Списания>>', reply_markup=keyboard)


async def menu_plans(message: types.Message):
    b1 = KeyboardButton('📔Создать план продаж')
    b2 = KeyboardButton('📔План продаж')
    b4 = KeyboardButton("📔Начислить премии по планам")
    b5 = KeyboardButton("📔Таблица с планом")
    b3 = KeyboardButton('Вернуться')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(b1).insert(b2).row(b4).insert(b5).row(b3)
    await bot.send_message(message.from_user.id, 'Вы перешли в меню <<Планы продаж>>', reply_markup=keyboard)


async def rev_kb(message: types.Message):
    b1 = KeyboardButton('Добавить ревизию')
    b2 = KeyboardButton('Выгрузить ревизии')
    b4 = KeyboardButton(f'📒Локальная ревизия')
    b5 = KeyboardButton(f'📒Получить локальную ревизию') 
    b6 = KeyboardButton(f'Выгрузить таблицу')
    b3 = KeyboardButton('Вернуться')
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(b1).insert(b2).row(b4).insert(b6).row(b5).row(b3)
    await bot.send_message(message.from_user.id, 'Вы перешли в меню <<Ревизии>>', reply_markup=keyboard)


def register_handlers_mod_kb(dp: Dispatcher):
    dp.register_message_handler(menu_tasks, Text(equals='Задачи', ignore_case=True), state=None)
    dp.register_message_handler(menu_reports_up, Text(equals='Загрузка отчётов', ignore_case=True), state=None)
    dp.register_message_handler(menu_reports, Text(equals='Отчёты', ignore_case=True), state=None)
    dp.register_message_handler(menu_users, Text(equals='Пользователи', ignore_case=True), state=None)
    dp.register_message_handler(menu_salary, Text(equals='Зарплаты', ignore_case=True), state=None)
    dp.register_message_handler(menu_loss, Text(equals='Списания', ignore_case=True), state=None)
    dp.register_message_handler(menu_plans, Text(equals='Планы продаж', ignore_case=True), state=None)
    dp.register_message_handler(menu_invoices, Text(equals='Накладные', ignore_case=True), state=None)
    dp.register_message_handler(in_main_menu, Text(equals='Вернуться', ignore_case=True), state=None)
    dp.register_message_handler(menu_incassation_load, Text(equals='Инкассации', ignore_case=True), state=None)
    dp.register_message_handler(points, Text(equals='Точки', ignore_case=True), state=None)
    dp.register_message_handler(menu_reports_load, Text(equals='Выгрузка отчётов', ignore_case=True), state=None)
    dp.register_message_handler(exp_kb, Text(equals='Расходы', ignore_case=True), state=None)
    dp.register_message_handler(rev_kb, Text(equals='Ревизии', ignore_case=True), state=None)
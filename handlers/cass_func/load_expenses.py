import asyncio

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
import sqlite3 as sq
from create_bot import dp, bot
import requests, json
import openpyxl
from database import sqlite_db
from id import token
from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client, main_cassier_kb

from datetime import datetime
from datetime import date, timedelta

from handlers import inf


class FSMCategorie_expense(StatesGroup):
    name = State()
    point = State()
    value = State()
    _continue = State()


class FSMCategorie_invoice(StatesGroup):
    name = State()
    type = State()


class FSMCategory_invoice_set(StatesGroup):
    category = State()
    photo = State()

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


async def cm_set_categorie_invoice(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена")
    await bot.send_message(message.from_user.id, "Введите наименование категорий:", reply_markup=kb)
    await FSMCategorie_invoice.name.set()


async def load_name_categorie_invoice(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['id'] = sqlite_db.generate_random_string()
        data['name'] = message.text
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Расходы').row('Другое').row('Отмена')
    await bot.send_message(message.from_user.id, f"Выберите является ли выплата расходами:", reply_markup=kb)
    await FSMCategorie_invoice.next()

async def load_type_categorie_invoice(message: types.Message, state: FSMContext):
    if message.text != "Расходы" and message.text != "Другое":
        await bot.send_message(message.from_user.id, f'Выберите из предложенных вариантов')
        return
    async with state.proxy() as data:
        data['type'] = message.text
    await sqlite_db.sql_add_category_invoices(state)
    await bot.send_message(message.from_user.id, f"Категория выплат добавлена",
                           reply_markup=inf.kb(message.from_user.id))
    await state.finish()


async def cm_set_categorie_expense(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена")
    await bot.send_message(message.from_user.id, "Введите наименование категорий:", reply_markup=kb)
    await FSMCategorie_expense.name.set()


async def load_name_categorie(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['id'] = sqlite_db.generate_random_string()
        data['point'] = ""
        data['name'] = message.text
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Для всех')
    for i, store in enumerate(inf.get_name_shops()):
        if i % 2 == 0:
            kb.row(store)
        else:
            kb.insert(store)
    kb.row('Отмена')
    await bot.send_message(message.from_user.id, "Выберите точку:", reply_markup=kb)
    await FSMCategorie_expense.next()


async def load_point_categorie(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text == 'Для всех':
            data['point'] = "All"
        else:
            data['point'] = inf.get_id_point(message.text)
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена')
    await bot.send_message(message.from_user.id, "Введите значение по умолчанию для категории:", reply_markup=kb)
    await FSMCategorie_expense.next()


async def load_value_categorie(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['value'] = punctuation(message.text)
    await sqlite_db.sql_add_category_expenses(state)
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Добавить значение на точку').row('Закончить добавление')
    await bot.send_message(message.from_user.id, "Значение для точки добавлено", reply_markup=kb)
    await FSMCategorie_expense.next()


async def load_continue_categorie(message: types.Message, state: FSMContext):
    if message.text == "Добавить значение на точку":
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for i, store in enumerate(inf.get_name_shops()):
            if i % 2 == 0:
                kb.row(store)
            else:
                kb.insert(store)
        kb.row('Отмена')
        await bot.send_message(message.from_user.id, "Выберите точку", reply_markup=kb)
        await FSMCategorie_expense.point.set()
    elif message.text == "Закончить добавление":
        await bot.send_message(message.from_user.id, "Категория добавлена",
                               reply_markup=inf.kb(message.from_user.id))
        await state.finish()


async def get_categorie_expense(message: types.Message):
    category = {}
    for ret in sqlite_db.cur.execute("SELECT id, name, point, value FROM categories_expenses"):
        if (ret[0], ret[1]) not in category:
            category[(ret[0], ret[1])] = {ret[2]: ret[3]}
        else:
            category[(ret[0], ret[1])][ret[2]] = ret[3]
    for key in list(category.keys()):
        text = f"Категория: {key[1]}"
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton(f'Удалить {key[1]}', callback_data=f"del_cat_ex {key[0]}"))
        for point, value in category[key].items():
            if point == "All":
                text += f"\nДля всех по умолчанию | Значение: {value}"
            else:
                text += f"\nТочка: {inf.pt_name(point)} | Значение: {value}"
        await bot.send_message(message.from_user.id, text, reply_markup=kb)


async def get_categorie_invoices(message: types.Message):
    for ret in sqlite_db.cur.execute("SELECT id, name, type FROM categories_invoices"):
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton(f'Удалить {ret[1]}', callback_data=f'del_cat_in {ret[0]}'))
        await bot.send_message(message.from_user.id, f'Категория: {ret[1]}, Тип: {ret[2]}', reply_markup=kb)


async def del_cat_expense(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    rid = callback_query.data.split()[1]
    sqlite_db.cur.execute("DELETE FROM categories_expenses WHERE id LIKE ?", [rid])
    sqlite_db.base.commit()
    await bot.send_message(callback_query.from_user.id, f'Категория удалена')


async def del_cat_invoice(callback_query: types.CallbackQuery):
    await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
    rid = callback_query.data.split()[1]
    sqlite_db.cur.execute("DELETE FROM categories_invoices WHERE id LIKE ?", [rid])
    sqlite_db.base.commit()
    await bot.send_message(callback_query.from_user.id, f'Категория удалена')


async def cm_start_expense_point(callback_query: types.CallbackQuery):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in inf.get_categories():
        kb.insert(cat)
    kb.add('Отмена')
    await bot.send_message(callback_query.from_user.id, f'Выберите категорию выплаты:')
    await FSMCategory_invoice_set.category.set()


async def load_name_categorie_inv(message: types.Message, state: FSMContext):
    if message.text not in inf.get_categories():
        await bot.send_message(message.from_user.id, f'Выберите категорию из клавиатуры')
        return
    async with state.proxy() as data:
        data['category'] = message.text
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена')
    await bot.send_message(message.from_user.id, f'Отправьте фото чека (если чека нет, нажмите "Без фото"):',
                           reply_markup=kb)
    await FSMCategory_invoice_set.next()


async def load_photo_categorie_inv(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.photo:
            data['photo'] = message.photo[0].file_id
        else:
            data['photo'] = "False"
    await bot.send_message(message.from_user.id, f'Выплата добавлена')





def register_handlers_expenses(dp: Dispatcher):
    dp.register_message_handler(cm_set_categorie_expense,
                                Text(equals=f'Добавить категорию расходов', ignore_case=True), state=None)
    dp.register_message_handler(cm_set_categorie_invoice,
                                Text(equals=f'Добавить категорию выплат', ignore_case=True), state=None)
    dp.register_message_handler(load_name_categorie, state=FSMCategorie_expense.name)
    dp.register_message_handler(load_point_categorie, state=FSMCategorie_expense.point)
    dp.register_message_handler(load_value_categorie, state=FSMCategorie_expense.value)
    dp.register_message_handler(load_continue_categorie, state=FSMCategorie_expense._continue)
    dp.register_message_handler(get_categorie_expense,
                                Text(equals=f'Категории расходов', ignore_case=True), state=None)
    dp.register_message_handler(get_categorie_invoices,
                                Text(equals=f'Категории выплат', ignore_case=True), state=None)
    dp.register_callback_query_handler(del_cat_expense, lambda x: x.data and x.data.startswith('del_cat_ex '))
    dp.register_callback_query_handler(del_cat_invoice, lambda x: x.data and x.data.startswith('del_cat_in '))
    dp.register_message_handler(load_name_categorie_invoice, state=FSMCategorie_invoice.name)
    dp.register_message_handler(load_type_categorie_invoice,state=FSMCategorie_invoice.type )
    #dp.register_message_handler(load_photo_categorie_inv, content_types=['any'], state=FSMCategory_invoice_set.photo)
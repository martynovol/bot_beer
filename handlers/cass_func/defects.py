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
import calendar

from datetime import datetime
from datetime import date, timedelta

from handlers import inf
from handlers import emoji_bot


class FSMDefect(StatesGroup):
    id = State()
    point = State()
    date = State()
    type = State()
    product = State()
    price = State()
    photo = State()
    comments = State()


class FSMDefect_day(StatesGroup):
    type = State()
    point = State()
    day = State()


def check_month(m):
    m = m.split('.')
    return not (len(m) == 3 and (len(m[0]) == 2 or len(m[0]) == 1) and (len(m[1]) == 2 or len(m[1]) == 1) and len(
        m[2]) == 4
                and m[0].isdigit() and m[1].isdigit() and m[2].isdigit()
                and int(m[0]) < 32 and int(m[1]) < 13 and int(m[2]) in range(2021, 2030))


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


def get_stores():
    url_get_stores = "https://api.moysklad.ru/api/remap/1.2/entity/store"
    response = requests.get(url_get_stores, headers=token.headers)
    data = json.loads(response.text)
    result = {}
    for store in data['rows']:
        result[store['name']] = store['id']
    return result


type_loss = ['В счёт зарплаты', 'Брак']


async def cm_start_defect(message: types.Message):
    if message.from_user.id not in inf.get_users_id():
        await bot.send_message(message.from_user.id, 'Вам не доступна  эта функция')
        return
    await sqlite_db.info_admin(message.from_user.id, "Начал грузить брак")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for store in inf.get_shops():
        keyboard.add(store['name'])
    keyboard.add('Отмена')
    if message.from_user.id in inf.get_admin_id():
        await bot.send_message(message.from_user.id, f'Выберите склад для добавления брака:', reply_markup=keyboard)
        await FSMDefect.point.set()
    else:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.insert(type_loss[1]).row(type_loss[0])
        kb.row('Отмена')
        await bot.send_message(message.from_user.id, f'Выберите тип списания:', reply_markup=kb)
        await FSMDefect.type.set()


async def load_point_defect(message: types.Message, state: FSMContext):
    available_points = [x['name'] for x in inf.get_shops()]

    if message.text not in available_points:
        await bot.send_message(message.from_user.id, f'Выберите точку из кнопок снизу')
        return

    async with state.proxy() as data:
        data['id'] = sqlite_db.generate_random_string()
        data['point_id'] = inf.get_id_sklad_point(message.text)
        data['point_name'] = inf.get_id_point(message.text)
    keyboards = ReplyKeyboardMarkup(resize_keyboard=True)
    for type_ in type_loss:
        keyboards.add(type_)
    keyboards.add('Отмена')
    await bot.send_message(message.from_user.id, f'Выберите тип списания:', reply_markup=keyboards)
    await FSMDefect.type.set()


async def load_date_defect(message: types.Message, state: FSMContext):
    date1 = message.text
    try:
        date1 = datetime.strptime(date1, "%d.%m.%Y")
    except Exception:
        await bot.send_message(message.from_user.id,
                               f'Вы ввели некорректную дату, попробуйте ещё раз(формат ДД.ММ.ГГГГ)')
        return

    async with state.proxy() as data:
        data['date'] = date1
    keyboards = ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена')
    await bot.send_message(message.from_user.id, f'Введите часть названия товара с браком как он забит в "Мой Склад":',
                           reply_markup=keyboards)
    await FSMDefect.next()


async def load_type_defect(message: types.Message, state: FSMContext):
    if message.text not in type_loss:
        await bot.send_message(message.from_user.id, f'Выберите тип из списка')
        return
    async with state.proxy() as data:
        if 'id' not in data or 'point_id' not in data:
            for ret in sqlite_db.cur.execute(
                    'SELECT point1 FROM reports_open WHERE now_user LIKE ? AND report_close_id LIKE ?',
                    [inf.get_name(message.from_user.id), ""]):
                data['id'] = sqlite_db.generate_random_string()
                data['point_id'] = inf.get_id_sklad_point(ret[0])
                data['point_name'] = inf.get_id_point(ret[0])
        data['date'] = datetime.now()
        data['type'] = message.text
    keyboards = ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена')
    await bot.send_message(message.from_user.id, f'Введите часть названия товара с браком как он забит в "Мой Склад":',
                           reply_markup=keyboards)
    await FSMDefect.next()


async def load_product_defect(message: types.Message, state: FSMContext):
    products = get_products_search(message.text)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if len(products) == 0:
        await message.reply(f'Товаров по запросу: {message.text} не найдено')
        return
    if len(products) > 10:
        await message.reply(f'Слишком много товаров по запросу: {message.text}. '
                            f'Добавьте дополнительные данные в название')
        return
    kb.row('Нет в списке')
    for i, product in enumerate(products):
        if i % 2 != 0:
            kb.insert(products[product][0])
        else:
            kb.row(products[product][0])
    kb.row('Отмена')
    await bot.send_message(message.from_user.id, 'Выберите товар:', reply_markup=kb)
    await FSMDefect.next()


async def load_price_defect(message: types.Message, state: FSMContext):
    if message.text == "Нет в списке":
        kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена')
        await bot.send_message(message.from_user.id, 'Впишите название товара:', reply_markup=kb)
        await FSMDefect.product.set()
        return
    products = get_products_search(message.text)
    if len(products) == 0:
        await bot.send_message(message.from_user.id, 'Выберите товар из списка снизу:')
        return
    async with state.proxy() as data:
        for key, product in products.items():
            if product[0] == message.text:
                data['product_id'] = key
                data['product_name'] = product[0]
                data['price'] = product[1]
    await bot.send_message(message.from_user.id, 'Отправьте фото товара:',
                           reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена'))
    await FSMDefect.next()


async def load_photo_defect(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id
        type_ = data['type']
        if type_ == type_loss[0]:
            data['date'] = data['date'].strftime("%d.%m.%Y")
            data['comments'] = f"{data['date']}, {inf.get_name(message.from_user.id)}"
            data['user_id'] = message.from_user.id
            check, data['token_id'] = in_sklad(data['product_id'], data['point_id'], data['comments'], data['type'])
            if check != 0:
                await bot.send_message(message.from_user.id, f'{check}',
                                       reply_markup=inf.kb(message.from_user.id))
                await state.finish()
                return
            elif data['token_id'] == 0:
                await bot.send_message(message.from_user.id, f'Неизвестная ошибка списания.',
                                       reply_markup=inf.kb(message.from_user.id))
                await state.finish()
                return
    if type_ == type_loss[0]:
        await sqlite_db.sql_add_defects(state)
        await bot.send_message(message.from_user.id, f'Списание успешно добавлено и загружено в "Мой Склад"',
                               reply_markup=inf.kb(message.from_user.id))
        await state.finish()
        return
    await bot.send_message(message.from_user.id, 'Напишите причину брака:')
    await FSMDefect.next()


def get_products_search(name):
    url_get_product = f"https://api.moysklad.ru/api/remap/1.2/entity/product?search={name}"
    response = requests.get(url_get_product, headers=token.headers)
    data = json.loads(response.text)
    result = {}
    for product in data['rows']:
        result[product['id']] = [product['name'], product['salePrices'][0]['value']]
    return result


async def load_comment_defect(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['comments'] = f"{inf.get_name(message.from_user.id)} {message.text}"
        check, data['token_id'] = in_sklad(data['product_id'], data['point_id'], data['comments'], data['type'])

        if check != 0:
            await bot.send_message(message.from_user.id, f'{check}',
                                   reply_markup=inf.kb(message.from_user.id))
            await state.finish()
            return
        elif data['token_id'] == 0:
            await bot.send_message(message.from_user.id, f'Неизвестная ошибка списания.',
                                   reply_markup=inf.kb(message.from_user.id))
            await state.finish()
            return

        data['date'] = data['date'].strftime("%d.%m.%Y")
        data['user_id'] = message.from_user.id
    await sqlite_db.sql_add_defects(state)
    await bot.send_message(message.from_user.id, f'Брак успешно добавлен и загружен в "Мой Склад"',
                           reply_markup=inf.kb(message.from_user.id))
    await state.finish()


async def cm_start_loss_day(message: types.Message):
    keyboards = ReplyKeyboardMarkup(resize_keyboard=True)
    for type_ in type_loss:
        keyboards.add(type_)
    keyboards.add('Отмена')
    await bot.send_message(message.from_user.id, 'Выберите тип списания:', reply_markup=keyboards)
    await FSMDefect_day.type.set()


async def load_type_loss_day(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['type'] = message.text
    keyboards = ReplyKeyboardMarkup(resize_keyboard=True)
    for store in inf.get_shops():
        keyboards.add(store['name'])
    keyboards.add('Отмена')
    await bot.send_message(message.from_user.id, 'Выберите точку:', reply_markup=keyboards)
    await FSMDefect_day.next()


async def load_point_loss_day(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['point'] = inf.get_id_point(message.text)
    time = datetime.now().strftime("%d.%m.%Y")
    time_ = (datetime.now() - timedelta(days=7)).strftime("%d.%m.%Y") + "-" + time
    month, year = time.split('.')[1], time.split('.')[2]
    last_day = str(calendar.monthrange(int(year), int(month))[1]) + '.' + month + '.' + year
    start_day = "01" + '.' + month + '.' + year
    time_month = start_day + '-' + last_day
    keyboards = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboards.row(time_month).row(time_).row('Отмена')
    await bot.send_message(message.from_user.id, 'Введите интервал дат для выгрузки (ДД.ММ.ГГГГ-ДД.ММ.ГГГГ):',
                           reply_markup=keyboards)
    await FSMDefect_day.next()


async def load_date_loss_for_day(message: types.Message, state: FSMContext):
    interval = message.text.replace(' ', '').split('-')
    date_from, date_to = datetime.strptime(interval[0], "%d.%m.%Y"), datetime.strptime(interval[1], "%d.%m.%Y")
    async with state.proxy() as data:
        await bot.send_message(message.from_user.id, f'Выгрузка за {message.text} с точки {inf.pt_name(data["point"])}')
        for ret in sqlite_db.cur.execute(
                'SELECT id, token_id, date, product_name FROM defects WHERE point_name = ? AND type = ?',
                [data['point'], data['type']]).fetchall():
            if date_from <= datetime.strptime(ret[2], "%d.%m.%Y") <= date_to:
                url_get_expenses = f"https://api.moysklad.ru/api/remap/1.2/entity/loss/" + ret[1]
                response = requests.get(url_get_expenses, headers=token.headers)
                data = json.loads(response.text)
                if "errors" in data:
                    sqlite_db.cur.execute('DELETE FROM defects WHERE id = ?', [ret[0]])
                    sqlite_db.base.commit()
                elif "deleted" not in data:
                    kb = InlineKeyboardMarkup().add(InlineKeyboardButton(f'Фото {ret[3]}',
                                                                         callback_data=f"pho_def {ret[0]}"))
                    await bot.send_message(message.from_user.id, f'Дата: {ret[2]} | Товар: {ret[3]}\n'
                                                                 f'Цена: {data["sum"] / 100}\nПричина: {data["description"]}',
                                           reply_markup=kb)
    await bot.send_message(message.from_user.id, f'Выгрузка завершена', reply_markup=inf.kb(message.from_user.id))
    await state.finish()


def get_at_date(text):
    date2 = ''
    for i in range(0, 2):
        if len(text.split('.')[i]) == 1:
            date2 += '0' + text.split('.')[i] + '.'
        else:
            date2 += text.split('.')[i] + '.'
    date2 += text.split('.')[2]
    return date2


async def get_pho_def(callback_query: types.CallbackQuery):
    rid = callback_query.data.split(' ')[1]
    for ret in sqlite_db.cur.execute('SELECT photo FROM defects WHERE id LIKE ?', [rid]):
        media = types.MediaGroup()
        media.attach_photo(ret[0])
        await bot.send_media_group(callback_query.from_user.id, media)


def organization():
    add_sklad = "https://api.moysklad.ru/api/remap/1.2/entity/organization"
    response = requests.get(add_sklad, headers=token.headers)
    data = json.loads(response.text)
    for i in data['rows']:
        if i['name'].startswith("ИП"):
            return {"meta": i['meta']}


def get_product(product_id):
    url_get_product = f"https://api.moysklad.ru/api/remap/1.2/entity/product/{product_id}"
    response = requests.get(url_get_product, headers=token.headers)
    data = json.loads(response.text)
    product = data
    result = {"quantity": 1, "assortment": {"meta": " "}, "price": product['salePrices'][0]['value']}
    result["assortment"]["meta"] = product['meta']
    return result


def get_project(project_type):
    url_get_proj = f"https://api.moysklad.ru/api/remap/1.2/entity/project?search={project_type}"
    response = requests.get(url_get_proj, headers=token.headers)
    data = json.loads(response.text)
    return data['rows'][0]


def in_sklad(product_id, retail_id, description, project_type):
    url_set_loss = "https://api.moysklad.ru/api/remap/1.2/entity/loss"
    meta_store, meta_org, meta_product, meta_project = \
        inf.get_retail_store(retail_id), organization(), get_product(product_id), get_project(project_type)
    data_loss = {"store": meta_store, "organization": meta_org, "positions": [meta_product],
                 "project": meta_project, "description": description}
    response = requests.post(url_set_loss, headers=token.headers, json=data_loss)
    data = json.loads(response.text)
    if "id" in data:
        return 0, data['id']
    if "errors" in data:
        return data['errors'][0]['error'], 0
    return 0


def register_handlers_loss(dp: Dispatcher):
    dp.register_callback_query_handler(get_pho_def, lambda x: x.data and x.data.startswith('pho_def '))
    dp.register_message_handler(cm_start_defect,
                                Text(equals=f'📝Добавить списание', ignore_case=True),
                                state=None)
    dp.register_message_handler(load_point_defect, state=FSMDefect.point)
    dp.register_message_handler(load_date_defect, state=FSMDefect.date)
    dp.register_message_handler(load_type_defect, state=FSMDefect.type)
    dp.register_message_handler(load_product_defect, state=FSMDefect.product)
    dp.register_message_handler(load_price_defect, state=FSMDefect.price)
    dp.register_message_handler(load_photo_defect, content_types=['photo'], state=FSMDefect.photo)
    dp.register_message_handler(load_comment_defect, state=FSMDefect.comments)
    dp.register_message_handler(cm_start_loss_day,
                                Text(equals=f'📝Выгрузить списания', ignore_case=True),
                                state=None)
    dp.register_message_handler(load_type_loss_day, state=FSMDefect_day.type)
    dp.register_message_handler(load_point_loss_day, state=FSMDefect_day.point)
    dp.register_message_handler(load_date_loss_for_day, state=FSMDefect_day.day)

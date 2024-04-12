from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton

from create_bot import dp, bot

from database import sqlite_db

from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client

from datetime import datetime
from datetime import date, timedelta

from handlers import inf


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


class FSMSalary(StatesGroup):
    id = State()
    person_id = State()
    date = State()
    type = State()
    value = State()
    inter = State()

class FSMPrize(StatesGroup):
    salary_id = State()
    inter1 = State()
    inter2 = State()
    prize = State()
    state_continue = State()


class FSM_add_sal(StatesGroup):
    id1 = State()
    user_id = State()
    day_month = State()
    date1 = State()
    count = State()
    is_per = State()
    is_minus = State()


class FSM_get_sal(StatesGroup):
    data1 = State()


get_data = {}


def global_dictionary(user_id, method="check", data=None):
    if method == "add":
        get_data[int(user_id)] = data
    elif method == "check":
        return get_data[int(user_id)]
    elif method == "clear":
        get_data.pop(int(user_id), None)


async def cm_start_set_salary(message: types.Message):
    if message.from_user.id not in inf.get_admin_id():
        await bot.send_message(message.from_user.id, 'Вам не доступна  эта функция')
        return
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    available_points = inf.get_name_shops()
    available_users = inf.get_users()
    for user in available_users:
        available_points.append(user[1])
    for i, point in enumerate(available_points):
        if i % 3 != 0:
            keyboard.insert(point)
        else:
            keyboard.row(point)
    keyboard.add('Отмена')
    await message.reply('Выберите точку или пользователя:', reply_markup=keyboard)
    await FSMSalary.person_id.set()


async def load_person_salary(message: types.Message, state: FSMContext):
    available_points = inf.get_name_shops()
    available_users = inf.get_users()
    s = []
    for user in available_users:
        s.append(user[1])
    async with state.proxy() as data:
        data['id'] = sqlite_db.generate_random_string()
        if message.text in available_points:
            data['point_id'] = inf.get_id_point(message.text)
        elif message.text in s:
            data['point_id'] = inf.get_user_id(message.text)
        else:
            return
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(str(datetime.now().strftime('%d.%m.%Y')))
    keyboard.row('Отмена')
    await FSMSalary.next()
    await message.reply('Дата назначения:', reply_markup=keyboard)


async def load_date_salary(message: types.Message, state: FSMContext):
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
        data['date'] = date2
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Почасовая').insert('Суточная')
    keyboard.row('Отмена')
    await FSMSalary.next()
    await message.reply('Вид оклада:', reply_markup=keyboard)


async def load_salary(message: types.Message, state: FSMContext):
    types_salary = ['Почасовая', 'Суточная']
    if message.text not in types_salary:
        await bot.send_message(message.from_user.id, 'Выберите тип, используя клавиатуру')
        return
    async with state.proxy() as data:
        data['type'] = message.text
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Отмена')
    await FSMSalary.next()
    await message.reply('Впишите интервал от выручки для ставки в час/сутки через тире и значения для него через пробел'
                        ' (10000-20000 1200):', reply_markup=keyboard)


async def load_value_salary(message: types.Message, state: FSMContext):
    text = message.text.split(' ')
    inter = text[0].replace(' ', '').split('-')
    print(inter[0].isdigit() and inter[1].isdigit() and int(inter[1]) > int(inter[0]))
    if len(text) == 2 and text[1].isdigit() and len(inter) == 2 and inter[0].isdigit() and inter[1].isdigit() \
            and int(inter[1]) > int(inter[0]):
        async with state.proxy() as data:
            data['inter'], data['value'] = text[0], text[1]
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add('Закончить добавление')
        await sqlite_db.sql_add_salary(state)
        await bot.send_message(message.from_user.id, f'Впишите ещё интервал или нажмите "Закончить добавление"',
                               reply_markup=keyboard)
        return
    elif message.text == "Закончить добавление":
        async with state.proxy() as data:
            person, sal_id = data['point_id'], data['id']
        await bot.send_message(message.from_user.id, 'Ставка  успешно назначена',
                               reply_markup=inf.kb(message.from_user.id))
        keyboards = InlineKeyboardMarkup().add(InlineKeyboardButton('Процент', callback_data=f"percent {sal_id}"))
        await bot.send_message(message.from_user.id, f'Добавить процент с выручки?', reply_markup=keyboards)
        await state.finish()
    else:
        await bot.send_message(message.from_user.id, "Введите правильный интервал со значением Пример: 10000-20000 3000")
        return


async def load_percent(callback_query: types.CallbackQuery):
    salary_id = callback_query.data.split(' ')[1]
    global_dictionary(callback_query.from_user.id, "add", salary_id)
    keyboards = ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена')
    await bot.send_message(callback_query.from_user.id,
                           f'Впишите интервал выручки за день для процента в виде (10000-20000)', reply_markup=keyboards)
    await FSMPrize.inter1.set()


async def add_percent(message: types.Message, state: FSMContext):
    key = message.text.replace(' ', '').split('-')
    if len(key) != 2 or not key[0].isdigit() or not key[1].isdigit() or int(key[1]) < int(key[0]):
        await bot.send_message(message.from_user.id, f'Впишите интервал правильно (10000-20000)')
        return
    async with state.proxy() as data:
        data['id'], data['inter_1'], data['inter_2'] = global_dictionary(message.from_user.id), key[0], key[1]
    await bot.send_message(message.from_user.id, f'Впишите процент (Пример: 10%) со знаком процента или надбавку'
                                                 f' (Пример: 200) для этого интервала, если необходимо начислять'
                                                 f' определённую сумму за шаг, то впишите специальную конструкцию со словом "каждую"'
                                                 f'(Пример: 100 каждую 1000), но без процента:')
    await FSMPrize.prize.set()


async def add_percent_value(message: types.Message, state: FSMContext):
    keyboards = ReplyKeyboardMarkup(resize_keyboard=True).add('Добавить интервал').insert('Закончить добавление')
    async with state.proxy() as data:
        if '%' in message.text:
            key = message.text.replace('%', '')
            if not key.isdigit() and not (0 < float(key) < 100):
                await bot.send_message(message.from_user.id, f'Впишите правильный формат (Пример: "10%" или "150")')
                return
            data['prize'], data['is_per'], data['step'] = key, '%', '0'
        else:
            key = message.text
            if "каждую" in key.lower().split() and len(key.split()) == 3 and key.split()[0].isdigit() and key.split()[2].isdigit():
                data['prize'], data['is_per'], data['step'] = key.split()[0], '', key.split()[2]
            elif not key.isdigit():
                await bot.send_message(message.from_user.id, f'Впишите правильный формат')
                return
            else:
                data['prize'], data['is_per'], data['step'] = key, '', '0'
    await sqlite_db.sql_add_percent(state)
    await bot.send_message(message.from_user.id, 'Интервал добавлен', reply_markup=keyboards)
    await FSMPrize.state_continue.set()


async def state_percent_contiune(message: types.Message, state: FSMContext):
    if message.text == 'Добавить интервал':
        await bot.send_message(message.from_user.id, f'Впишите ещё интервал выручки за день для процента в виде (10000-20000)',
                               reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена'))
        await FSMPrize.inter1.set()
    else:
        await bot.send_message(message.from_user.id, 'Ставка на точку назначена', reply_markup=inf.kb(message.from_user.id))
        await state.finish()


async def cm_set_sal_user(message: types.Message):
    if message.from_user.id not in inf.get_admin_id():
        return
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for user in inf.get_users():
        keyboard.add(user[1])
    keyboard.add("Отмена")
    await message.answer("Выберите пользователя:", reply_markup=keyboard)
    await FSM_add_sal.user_id.set()


async def load_user_salary(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['id'] = sqlite_db.generate_random_string()
        data['user_id'] = message.text
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("В месяц").insert('В день').row('Отмена')
    await bot.send_message(message.from_user.id, "Введите дату назначения (ДД.ММ.ГГГГ):", reply_markup=keyboard)
    await FSM_add_sal.date1.set()


async def load_day_month_user(message: types.Message, state: FSMContext):
    if message.text not in ["В месяц", "В день"]:
        return
    async with state.proxy() as data:
        data['day_month'] = message.text
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(str(datetime.now().strftime('%d.%m.%Y')))
    keyboard.row('Отмена')
    await bot.send_message(message.from_user.id, f'Введите дату назначения (ДД.ММ.ГГГГ):', reply_markup=keyboard)
    await FSM_add_sal.next()


async def load_date_user_salary(message: types.Message, state: FSMContext):
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
        data['day_month'] = "В день"
        data['date1'] = date2
    await bot.send_message(message.from_user.id, f'Введите процент "50%" от ставки или наличную надбавку "500" за день.\n'
                                                 f'Добавьте знак минус если на эту сумму нужно уменьшить'
                                                 f'("-50%", "-500"', reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена"))
    await FSM_add_sal.next()


async def load_number_user_salary(message: types.Message, state: FSMContext):
    number = message.text.replace("%", "").replace("-", "").replace(" ", "")
    async with state.proxy() as data:
        if "%" in message.text:
            if number.isdigit() and 0 < int(number) < 100:
                data['count'] = number
                data['is_per'] = "%"
        elif number.isdigit():
            data['count'] = number
            data['is_per'] = ""
        else:
            return

        if "-" in message.text:
            data['is_minus'] = "-"
        else:
            data['is_minus'] = "+"
        s = data["day_month"]
        data["day_month"] = data["date1"]
        data["date1"] = s
    await sqlite_db.sql_add_prize_user(state)
    await bot.send_message(message.from_user.id, "Надбавка назначена", reply_markup=inf.kb(message.from_user.id))
    await state.finish()


async def get_salary(message: types.Message):
    time = datetime.now().strftime("%m.%Y")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add('Последние').add(time).row('Отмена')
    await bot.send_message(message.from_user.id, "Впишите месяц и год (ММ.ГГГГ) или выберите 'Последние':", reply_markup=keyboard)
    await FSM_get_sal.data1.set()


async def get_sal(message: types.Message):
    if message.text == "Последние":
        pass
    available_points, all_id = inf.get_name_shops(), {}
    for ret in sqlite_db.cur.execute('SELECT id, point_id, date, type, int, value FROM salary').fetchall():
        #myear = f'{ret[2].split(".")[1]}.{ret[2].split(".")[2]}'
        if ret[0] not in all_id:
            if inf.pt_name(ret[1]) in available_points:
                all_id[ret[0]] = f"Точка: {inf.pt_name(ret[1])} | Дата: {ret[2]}\nТип: {ret[3]}\nИнтервал: {ret[4]} Ставка: {ret[5]}\n"
            else:
                all_id[ret[0]] = f"Пользователь: {inf.get_name(ret[1])} | Дата: {ret[2]}\nТип: {ret[3]}\nИнтервал: {ret[4]} Ставка: {ret[5]}\n"
        elif ret[0] in all_id:
            all_id[ret[0]] += f"Интервал: {ret[4]} Ставка: {ret[5]}\n"
    for id_sal, text in all_id.items():
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Удалить', callback_data=f"del_salar {id_sal}"))
        await bot.send_message(message.from_user.id, text, reply_markup=kb)
        text = ""
        for jet in sqlite_db.cur.execute(
                "SELECT inter1, inter2, prize_count, is_per FROM prize WHERE salary_id LIKE ?",
                [id_sal]):
            text += f"{jet[0]} - {jet[1]}: {jet[2]}{jet[3]}\n"
        if text != "":
            kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Удалить', callback_data=f"del_prize {id_sal}"))
            await bot.send_message(message.from_user.id, f"Процент от продаж:\n{text}", reply_markup=kb)
    await bot.send_message(message.from_user.id, f'Выгрузка завершена', reply_markup=inf.kb(message.from_user.id))


async def auth_site(message: types.Message):
    if message.from_user.id not in inf.get_admin_id():
        return
    user_token = sqlite_db.generate_random_string()
    #await dba.add_auth(message.from_user.id, user_token)

    auth_url = f'http://127.0.0.1:5000/auth?token={user_token}'
    await message.answer(f'Для авторизации на сайте перейдите по ссылке: {auth_url}')


def register_handlers_salary(dp: Dispatcher):
    dp.register_message_handler(cm_set_sal_user, Text(equals='Добавить надбавку', ignore_case=True),
                                state=None)
    dp.register_message_handler(cm_start_set_salary, Text(equals='Назначить ставку', ignore_case=True),
                                state=None)
    dp.register_message_handler(auth_site, Text(equals='Сайт', ignore_case=True),
                                state=None)
    dp.register_message_handler(load_person_salary, state=FSMSalary.person_id)
    dp.register_message_handler(load_date_salary, state=FSMSalary.date)
    dp.register_message_handler(load_salary, state=FSMSalary.type)
    dp.register_message_handler(load_value_salary, state=FSMSalary.value)
    #Премия
    dp.register_message_handler(add_percent, state=FSMPrize.inter1)
    dp.register_message_handler(add_percent_value, state=FSMPrize.prize)
    dp.register_message_handler(state_percent_contiune, state=FSMPrize.state_continue)
    dp.register_callback_query_handler(load_percent, lambda x: x.data and x.data.startswith('percent '))
    #Загрузка надбавки
    dp.register_message_handler(load_user_salary, state=FSM_add_sal.user_id)
    dp.register_message_handler(load_day_month_user, state=FSM_add_sal.day_month)
    dp.register_message_handler(load_date_user_salary, state=FSM_add_sal.date1)
    dp.register_message_handler(load_number_user_salary, state=FSM_add_sal.count)

    dp.register_message_handler(get_sal, Text(equals='Ставки', ignore_case=True),state=None)
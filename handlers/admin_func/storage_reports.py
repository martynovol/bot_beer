import asyncio

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton

from create_bot import dp, bot

from database import sqlite_db


from datetime import datetime
from datetime import date, timedelta

from handlers import emoji_bot, inf


class FSMOpen_storager(StatesGroup):
    selfie = State()


class FSMOpen_manager(StatesGroup):
    selfie = State()


class FSMClose_storager(StatesGroup):
    cash = State()
    non_cash = State()
    transfers = State()
    comments = State()


class FSMOpen_Operator(StatesGroup):
    privilegie = State()
    selfie = State()


class FSMOpen_Driver(StatesGroup):
    privilegie = State()
    selfie = State()


class FSMClose_Operator(StatesGroup):
    comments = State()


class FSMClose_manager(StatesGroup):
    comments = State()


class FSMClose_Driver(StatesGroup):
    comments = State()


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


async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply('Отмена', reply_markup=inf.kb(message.from_user.id))
    return


async def load_selfie_storager(message: types.Message, state: FSMContext):
    photo = message.photo[0].file_id
    user = message.from_user.id
    day, month, year = str(datetime.now().strftime('%d.%m.%Y')).split(".")
    now_time = str(datetime.now().strftime('%H:%M'))
    id_rep = sqlite_db.generate_random_string()
    await sqlite_db.sql_add_storager_open_report(id_rep, user, day, month, year, photo, now_time)

    for id in inf.get_mod_id():
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Селфи", callback_data=f"selfie_storager {id_rep}"))
        await bot.send_message(id, f"Пользователь {inf.get_name(message.from_user.id)} открыл смену кладовщика", reply_markup=kb)

    await bot.send_message(message.from_user.id, "Смена успешно открыта!", reply_markup=inf.kb(message.from_user.id))
    await state.finish()
    await remind_close_storage(message.from_user.id, "Кладовщик")


async def get_storager_selfie(callback_query: types.CallbackQuery):
    report_id = callback_query.data.split(' ')[1]
    photo = ''
    for ret in sqlite_db.cur.execute('SELECT selfie FROM storager_report WHERE id LIKE ?', [report_id]):
        photo = ret[0]
    for ret in sqlite_db.cur.execute('SELECT selfie FROM driver_report WHERE id LIKE ?', [report_id]):
        photo = ret[0]
    for ret in sqlite_db.cur.execute('SELECT selfie FROM operator_report WHERE id LIKE ?', [report_id]):
        photo = ret[0]
    media = types.MediaGroup()
    media.attach_photo(f'{photo}')
    await bot.send_media_group(callback_query.from_user.id, media=media)


async def load_cash_storager(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['cash'] = str(punctuation(message.text))
    await FSMClose_storager.next()
    await bot.send_message(message.from_user.id,f'Безналичными{emoji_bot.em_report_load_non_cash}:')


async def load_nonCash_storager(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['nonCash'] = str(punctuation(message.text))
    await FSMClose_storager.next()
    await message.reply(f'Переводами{emoji_bot.em_report_load_transfers}:')


async def load_transfers_storager(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['transfers'] = str(punctuation(message.text))
    await FSMClose_storager.next()
    await message.reply(f'Комментарии{emoji_bot.em_report_load_comments}:')


async def load_comments_storager(message: types.Message, state: FSMContext):
    id_rep = 0
    for ret in sqlite_db.cur.execute("SELECT id FROM storager_report WHERE person_id = ? AND close = ?", [message.from_user.id, "0"]):
        id_rep = ret[0]
    async with state.proxy() as data:
        data['comments'] = message.text
        data["cash"], data["nonCash"], data['transfers'], data['comments'] = 0, 0, 0, 0
        await sqlite_db.sql_add_storager_close_report(id_rep, data["cash"], data["nonCash"], data['transfers'], data['comments'])
        for uid in inf.get_mod_id():
            time_now = datetime.now().strftime("%d/%m/%Y %H:%M")
            kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Селфи", callback_data=f"selfie_storager {id_rep}"))
            #await bot.send_message(uid, f'[{time_now}] Был отправлен отчёт кладовщика пользователем {inf.get_name(message.from_user.id)}:\nНаличными: {data["cash"]}\nБезналичными: {data["nonCash"]}\nПереводами: {data["transfers"]}\nКомментарии: {data["comments"]}')
            await bot.send_message(uid, f'[{time_now}] Была закрыта смена кладовщика пользователем {inf.get_name(message.from_user.id)}\nКомментарии: {message.text}')
        await bot.send_message(message.from_user.id, f'Смена успешно закрыта! Отчёт отправлен', reply_markup=inf.kb(message.from_user.id))
    await state.finish()
    await remind_open_storage_admin("Кладовщик")


async def remind_close_storage(id1, privilegie):
    try:
        closed_time = "18:00"
        time_now = str(datetime.now().strftime('%H:%M'))
        now_time = datetime.strptime(time_now, "%H:%M")
        close_time = datetime.strptime(closed_time, "%H:%M") - timedelta(hours=0, minutes=15)
        time_dif = str(close_time - now_time).split(':')
        hours, minutes = float(time_dif[0]) * 60 * 60, float(time_dif[1]) * 60
        total_time = hours + minutes

        await asyncio.sleep(total_time)
        await bot.send_message(id1, f'⚠️Напоминание⚠️ ️ Не забудь закрыть смену в боте.\n'
                                    f'Закрытие смены должно быть произведено в течение 10 минут после {closed_time}')
        await remind_close_storage_admin(id1, privilegie)
    except Exception:
        await remind_close_storage_admin(id1, privilegie)
        return


async def remind_close_storage_admin(id1, privilegie):
    privilegies = {"Оператор": "operator_report", "Кладовщик": "storager_report", "Водитель": "driver_report", "Управляющий": "manager_report"}
    
    await asyncio.sleep(60*25)

    check, person = 0, 0
    for ret in sqlite_db.cur.execute(f'SELECT close, person_id FROM {privilegies[privilegie]} WHERE close LIKE ? AND person_id LIKE ?', ['0', id1]):
        check, person = ret[0], inf.get_name(ret[1])
    if check != 0:
        for _id in inf.get_admin_id():
            await bot.send_message(_id, f'❗️❗️❗️Смена {privilegie} {person} не закрыта вовремя!')
        await bot.send_message(id1, f'❗️❗️❗️ ️Смена не закрыта вовремя.'
                                    f' Если есть проблемы - напиши в чат с ботом')


async def remind_open_storage_admin(privilegie):
    privilegies = {"Оператор": "operator_report", "Кладовщик": "storager_report", "Водитель": "driver_report", "Управляющий": "manager_report"}
    try:
        open_time = "09:00"
        if int(datetime.now().strftime('%H')) >= 8:
            open_time = open_time + " " + (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
        else:
            open_time = open_time + " " + datetime.now().strftime("%d.%m.%Y")

        time_now = datetime.now()
        open_time = datetime.strptime(open_time, "%H:%M %d.%m.%Y")
        time_dif = str(open_time - time_now).split(':')
        hours, minutes = float(time_dif[0]) * 60 * 60, float(time_dif[1]) * 60
        total_time = hours + minutes + 60 * 10

        await asyncio.sleep(total_time)
        check = 0

        for ret in sqlite_db.cur.execute(f'SELECT id FROM {privilegies[privilegie]} WHERE close LIKE ? AND day = ? AND month = ? AND year = ?', ['0', datetime.now().strftime("%d.%m.%Y").split(".")]):
            check = ret[0]

        if check == 0:
            for _id in inf.get_admin_id():
                await bot.send_message(_id, f'❗️❗️❗️Смена {privilegie} не открыта вовремя!')

    except Exception:
        return
        
async def load_selfie_driver(message: types.Message, state: FSMContext):
    photo = message.photo[0].file_id
    user = message.from_user.id
    day, month, year = str(datetime.now().strftime('%d.%m.%Y')).split(".")
    now_time = str(datetime.now().strftime('%H:%M'))
    id_rep = sqlite_db.generate_random_string()
    await sqlite_db.sql_add_driver_open_report(id_rep, user, day, month, year, photo, now_time)

    for id in inf.get_mod_id():
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Селфи", callback_data=f"selfie_storager {id_rep}"))
        await bot.send_message(id, f"Пользователь {inf.get_name(message.from_user.id)} открыл смену водителя", reply_markup=kb)

    await bot.send_message(message.from_user.id, "Смена успешно открыта!", reply_markup=inf.kb(message.from_user.id))
    await state.finish()
    await remind_close_storage(message.from_user.id, "Водитель")


async def load_comments_driver(message: types.Message, state: FSMContext):
    id_rep = 0
    for ret in sqlite_db.cur.execute("SELECT id FROM driver_report WHERE person_id = ? AND close = ?", [message.from_user.id, "0"]):
        id_rep = ret[0]
    async with state.proxy() as data:
        data['comments'] = message.text
        await sqlite_db.sql_add_driver_close_report(id_rep, data['comments'])
        for uid in inf.get_mod_id():
            time_now = datetime.now().strftime(f"%d/%m/%Y %H:%M")
            kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Селфи", callback_data=f"selfie_storager {id_rep}"))
            await bot.send_message(uid, f'[{time_now}] Была закрыта смена водителя пользователем {inf.get_name(message.from_user.id)}\nКомментарии: {message.text}')
        await bot.send_message(message.from_user.id, f'Смена успешно закрыта! Отчёт отправлен', reply_markup=inf.kb(message.from_user.id))
    await state.finish()
    await remind_open_storage_admin("Водитель")


async def load_comments_operator(message: types.Message, state: FSMContext):
    id_rep = 0
    for ret in sqlite_db.cur.execute("SELECT id FROM operator_report WHERE person_id = ? AND close = ?", [message.from_user.id, "0"]):
        id_rep = ret[0]
    async with state.proxy() as data:
        data['comments'] = message.text
        await sqlite_db.sql_add_operator_close_report(id_rep, data['comments'])
        for uid in inf.get_mod_id():
            time_now = datetime.now().strftime("%d/%m/%Y %H:%M")
            kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Селфи", callback_data=f"selfie_storager {id_rep}"))
            await bot.send_message(uid, f'[{time_now}] Была закрыта смена оператора пользователем {inf.get_name(message.from_user.id)}\nКомментарии: {message.text}')
        await bot.send_message(message.from_user.id, f'Смена успешно закрыта! Отчёт отправлен', reply_markup=inf.kb(message.from_user.id))
    await state.finish()
    await remind_open_storage_admin("Оператор")


async def load_selfie_operator(message: types.Message, state: FSMContext):
    photo = message.photo[0].file_id
    user = message.from_user.id
    day, month, year = str(datetime.now().strftime('%d.%m.%Y')).split(".")
    now_time = str(datetime.now().strftime('%H:%M'))
    id_rep = sqlite_db.generate_random_string()
    await sqlite_db.sql_add_operator_open_report(id_rep, user, day, month, year, photo, now_time)

    for id in inf.get_mod_id():
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Селфи", callback_data=f"selfie_storager {id_rep}"))
        await bot.send_message(id, f"Пользователь {inf.get_name(message.from_user.id)} открыл смену оператора", reply_markup=kb)

    await bot.send_message(message.from_user.id, "Смена успешно открыта!", reply_markup=inf.kb(message.from_user.id))
    await state.finish()
    await remind_close_storage(message.from_user.id, "Оператор")


async def cm_close_start_manager(message: types.Message):
    if message.from_user.id not in inf.get_admin_id():
        await bot.send_message(message.from_user.id, 'Вам не доступна  эта функция')
        return
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена")
    await bot.send_message(message.from_user.id, "Впишите комментарии к закрытию:", reply_markup=kb)
    await FSMClose_manager.comments.set()


async def load_comments_manager(message: types.Message, state: FSMContext):
    id_report = 0
    for ret in sqlite_db.cur.execute('SELECT id FROM manager_report WHERE close = ? AND person_id = ?', ["0", message.from_user.id]):
        id_report = ret[0]
    now_time = str(datetime.now().strftime('%H:%M'))
    sqlite_db.cur.execute("UPDATE manager_report SET close = ? WHERE id = ?", [now_time, id_report])
    sqlite_db.base.commit()
    if id_report != 0 and id_report != "0":
        await bot.send_message(message.from_user.id, f"Смена управляющего закрыта в {now_time}", reply_markup=inf.kb(message.from_user.id))
        for user_id in inf.get_mod_id():
            await bot.send_message(user_id, f"Смена управляющего закрыта в {now_time} пользователем {inf.get_name(message.from_user.id)}\nКомментарии: {message.text}")
    else:
        await bot.send_message(message.from_user.id, f"Произошла ошибка, невозможно закрыть смену!")
    await state.finish()
    await remind_open_storage_admin("Управляющий")


async def cm_open_start_manager(message: types.Message):
    if message.from_user.id not in inf.get_admin_id():
        await bot.send_message(message.from_user.id, 'Вам не доступна  эта функция')
        return
    
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Да", callback_data="storage_law_yes ")).insert(InlineKeyboardButton("Нет", callback_data="storage_law_no "))
    await bot.send_message(message.from_user.id, "Подтвердите что вы осведомлены о материальной ответственности на работе, знакомы с правилами безопасности на рабочем месте", reply_markup=kb)
    return


async def load_selfie_manager(message: types.Message, state: FSMContext):
    photo = message.photo[0].file_id
    user = message.from_user.id
    day, month, year = str(datetime.now().strftime('%d.%m.%Y')).split(".")
    now_time = str(datetime.now().strftime('%H:%M'))
    id_rep = sqlite_db.generate_random_string()
    await sqlite_db.sql_add_manager_report(id_rep, user, day, month, year, photo, now_time)

    for id in inf.get_mod_id():
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Селфи", callback_data=f"selfie_manage {id_rep}"))
        await bot.send_message(id, f"Пользователь {inf.get_name(message.from_user.id)} открыл смену управляющего", reply_markup=kb)

    await bot.send_message(message.from_user.id, "Смена управляющего успешно открыта!", reply_markup=inf.kb(message.from_user.id))
    await state.finish()
    await remind_close_storage(message.from_user.id, "Управляющий")


async def get_manager_selfie(callback_query: types.CallbackQuery):
    report_id = callback_query.data.split(' ')[1]
    photo = ''
    for ret in sqlite_db.cur.execute('SELECT selfie FROM manager_report WHERE id LIKE ?', [report_id]):
        photo = ret[0]
    media = types.MediaGroup()
    media.attach_photo(f'{photo}')
    await bot.send_media_group(callback_query.from_user.id, media=media)


def register_handlers_open_report_storager(dp: Dispatcher):
    dp.register_message_handler(cm_open_start_manager,
                                Text(equals=f"{emoji_bot.em_report_close}Открыть смену управляющего", ignore_case=True), state=None)
    dp.register_message_handler(load_selfie_manager, content_types=['photo'], state=FSMOpen_manager.selfie)
    dp.register_message_handler(cancel_handler, state="*", commands='Отмена')
    dp.register_message_handler(cancel_handler, Text(equals='Отмена', ignore_case=True), state="*")
    dp.register_message_handler(load_selfie_storager, content_types=['photo'], state=FSMOpen_storager.selfie)
    dp.register_message_handler(load_selfie_driver, content_types=['photo'], state=FSMOpen_Driver.selfie)
    dp.register_message_handler(load_selfie_operator, content_types=['photo'], state=FSMOpen_Operator.selfie)

    dp.register_callback_query_handler(get_storager_selfie, lambda x: x.data and x.data.startswith('selfie_storager '))
    #dp.register_message_handler(load_opt_storager, state=FSMClose_storager.opt)
    dp.register_message_handler(load_cash_storager, state=FSMClose_storager.cash)
    dp.register_message_handler(load_nonCash_storager, state=FSMClose_storager.non_cash)
    dp.register_message_handler(load_transfers_storager, state=FSMClose_storager.transfers)
    dp.register_message_handler(load_comments_storager, state=FSMClose_storager.comments)

    dp.register_message_handler(load_comments_driver, state=FSMClose_Driver.comments)

    dp.register_message_handler(load_comments_operator, state=FSMClose_Operator.comments)

    dp.register_callback_query_handler(get_manager_selfie, lambda x: x.data and x.data.startswith('selfie_manage '))

    dp.register_message_handler(cm_close_start_manager,
                                Text(equals=f"{emoji_bot.em_report_close}Закрыть смену управляющего", ignore_case=True), state=None)
    dp.register_message_handler(load_comments_manager, state=FSMClose_manager.comments)
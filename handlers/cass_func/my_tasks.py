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

from handlers import inf

get_data = {}


def global_dictionary(user_id, method="check", data=None):
    if method == "add":
        get_data[user_id] = [data]
    elif method == "check":
        return get_data[user_id]
    elif method == "append":
        get_data[user_id].append(data)
    elif method == "clear":
        get_data.pop(user_id, None)


class FSMReport_task(StatesGroup):
    photo = State()
    comments = State()


class FSMReport_comment(StatesGroup):
    comments = State()


async def get_tasks(message: types.Message):
    comment_admin, check_report = 0, True
    for ret in sqlite_db.cur.execute('SELECT id, person, comments, time FROM tasks WHERE person LIKE ?',
                                     [inf.get_name(message.from_user.id)]).fetchall():
        check_report = False
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton(f'Предоставить отчёт', callback_data=f'task_rep {ret[0]}'))
        await bot.send_message(message.from_user.id, f'Задача: {ret[2]}\nДедлайн: {ret[3]}', reply_markup=keyboard)
        for jet in sqlite_db.cur.execute('SELECT photos, comments, comment_admin FROM task_report WHERE task_id LIKE ?', [ret[0]]).fetchall():
            await bot.send_message(message.from_user.id, "Отправленные отчёты:")
            media = types.MediaGroup()
            for i, photo in enumerate(jet[0].split()):
                if i == len(jet[0].split()) - 1:
                    media.attach_photo(photo, f'Комментарии отчёта: {jet[1]}')
                else:
                    media.attach_photo(photo)
            await bot.send_media_group(message.from_user.id, media)
            comment_admin = jet[2]
    if comment_admin != 0:
        await bot.send_message(message.from_user.id, f'Комментарии к прошлому отчёту от проверяющего: {comment_admin}')
    elif check_report:
        await bot.send_message(message.from_user.id, f'Задач не найдено')


async def task_report(callback_query: types.CallbackQuery):
    uid, task_id = callback_query.from_user.id, callback_query.data.split()[1]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Закончить").row("Отмена")
    global_dictionary(uid, "clear")
    global_dictionary(uid, "add", task_id)
    await bot.send_message(uid, "Вставьте несколько фото с результатами выполненной задачи, после чего "
                                "нажмите 'Закончить':",
                           reply_markup=keyboard)
    await FSMReport_task.photo.set()


async def get_photo_task(message: types.Message, state: FSMContext):
    if message.content_type == 'photo':
        global_dictionary(message.from_user.id, "append", message.photo[0].file_id)
        return
    if message.content_type == 'text' and message.text == "Закончить":
        data_global = global_dictionary(message.from_user.id)
        keyboards = ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена")
        if len(data_global) >= 2:
            async with state.proxy() as data:
                data['photo'] = ""
                for i in range(1, len(data_global)):
                    data['photo'] += data_global[i] + " "
        await bot.send_message(message.from_user.id, f"Напишите комментарии:", reply_markup=keyboards)
        await FSMReport_task.next()


async def get_comment_task(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        task_id = global_dictionary(message.from_user.id)[0]
        data["comments"] = message.text
        data["comment_admin"] = "False"
        data["task_id"] = task_id
    async with state.proxy() as data:
        await bot.send_message(message.from_user.id, f"Отчёт отправлен. Вам придёт уведомление, когда его рассмотрят.",
                               reply_markup=inf.kb(message.from_user.id))
        for ret in sqlite_db.cur.execute('SELECT _id FROM tasks WHERE id LIKE ?', [task_id]).fetchall():
            _id = ret[0]
            await bot.send_message(_id, f'Отчёт о выполненной задачи от {inf.get_name(message.from_user.id)}:')
            media = types.MediaGroup()
            for i, photo in enumerate(data["photo"].split()):
                if i == len(data["photo"].split()) - 1:
                    media.attach_photo(photo, f'Комментарии: {data["comments"]}')
                else:
                    media.attach_photo(photo)
            keyboard = InlineKeyboardMarkup().add(
                InlineKeyboardButton(f'Принять', callback_data=f"accept_task {task_id}")).insert(
                InlineKeyboardButton(f'Отказать', callback_data=f'dis_task {task_id}'))
            await bot.send_media_group(_id, media)
            await bot.send_message(_id, f'Принять отчёт?', reply_markup=keyboard)
    await sqlite_db.sql_add_task_report(state)
    await state.finish()


async def accept_task(callback_query: types.CallbackQuery):
    task_id = callback_query.data.split()[1]
    for ret in sqlite_db.cur.execute('SELECT person FROM tasks WHERE id LIKE ?', [task_id]):
        person_id = inf.get_user_id(ret[0])
    sqlite_db.cur.execute("DELETE FROM tasks WHERE id LIKE ?", [task_id])
    sqlite_db.cur.execute("DELETE FROM task_report WHERE task_id LIKE ?", [task_id])
    sqlite_db.base.commit()
    await bot.send_message(callback_query.from_user.id, "✅Отчёт принят")
    await bot.send_message(person_id, "✅Ваш отчёт принят")


async def dis_task(callback_query: types.CallbackQuery):
    task_id = callback_query.data.split()[1]
    keyboards = ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена")
    global_dictionary(callback_query.from_user.id, "add", task_id)
    await bot.send_message(callback_query.from_user.id, f'Введите комментарии:', reply_markup=keyboards)
    await FSMReport_comment.comments.set()


async def set_comment_report_task(message: types.Message, state: FSMContext):
    task_id = global_dictionary(message.from_user.id)[0]
    sqlite_db.cur.execute("UPDATE task_report SET comment_admin = ? WHERE task_id LIKE ?", [message.text, task_id])
    sqlite_db.base.commit()
    for ret in sqlite_db.cur.execute("SELECT person FROM tasks WHERE id LIKE ?", [task_id]):
        person_id = inf.get_user_id(ret[0])
    await bot.send_message(message.from_user.id, f'Комментарии отправлены', reply_markup=inf.kb(message.from_user.id))
    await bot.send_message(person_id, f"❌Отчёт не принят c комментарием: {message.text}")
    await state.finish()


def register_handlers_get_tasks(dp: Dispatcher):
    dp.register_message_handler(get_tasks, Text(equals=f'📔Мои задачи', ignore_case=True), state=None)
    dp.register_callback_query_handler(task_report, lambda x: x.data and x.data.startswith('task_rep '))
    dp.register_callback_query_handler(accept_task, lambda x: x.data and x.data.startswith('accept_task '))
    dp.register_callback_query_handler(dis_task, lambda x: x.data and x.data.startswith('dis_task '))
    dp.register_message_handler(get_photo_task, content_types=['any'], state=FSMReport_task.photo)
    dp.register_message_handler(get_comment_task, state=FSMReport_task.comments)
    dp.register_message_handler(set_comment_report_task, state=FSMReport_comment.comments)

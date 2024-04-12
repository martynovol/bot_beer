import calendar
import json

from aiogram import types

from id import token

import requests
from create_bot import dp, bot
from database import sqlite_db
from keyboards import admin_kb, admin_cancel_kb, cassier_kb, mod_kb, kb_client, main_cassier_kb, cassier_kb_close, storager_kb, storager_kb_close
from datetime import timedelta, datetime
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton


def n_date(in_date):
    try:
        spl_date = list(map(int, in_date.split(".")))
        if len(spl_date) == 3 and all(isinstance(item, int) for item in spl_date):
            day, month, year = spl_date
            if (0 < day < 32) and (0 < month < 13) and (0 < year < 2050):
                if year < 50:
                    year = "20" + str(year)
                if len(str(day)) == 1:
                    day = "0" + str(day)
                if len(str(month)) == 1:
                    month = "0" + str(month)
                
                return ".".join(list(map(str, [day, month, year])))
    except Exception:
        return None
    return None



def get_users():  # Вывести пользователей с их id и ролями
    ids = []
    for ret in sqlite_db.cur.execute('SELECT * FROM users').fetchall():
        ids.append((int(ret[0]), ret[1], ret[2], ret[3]))
    return ids


def get_users_id():  # Получить id всех пользователей
    ids = []
    for ret in sqlite_db.cur.execute('SELECT * FROM users').fetchall():
        ids.append(int(ret[0]))
    return ids


def get_name_shops():  # Получить все имена магазинов
    shops = []
    for ret in sqlite_db.cur.execute('SELECT name_point FROM shops').fetchall():
        shops.append(ret[0])
    return shops


def get_mod_id():  # Получить id модератеров
    id_mod = []
    for ret in sqlite_db.cur.execute('SELECT * FROM users WHERE privileges LIKE ?', ['Модератор']).fetchall():
        id_mod.append(int(ret[0]))
    return id_mod


def get_name(user_id):  # Получить имя пользователя по id
    name = f"Пользователь с id: {user_id}"
    for ret in sqlite_db.cur.execute('SELECT person FROM users WHERE id LIKE ?', [user_id]).fetchall():
        name = ret[0]
    return name


def get_admin_id():  # Получить id администраторов
    ids = []
    for ret in sqlite_db.cur.execute('SELECT * FROM users WHERE privileges LIKE ? OR privileges LIKE ?',
                                     ['Администратор', 'Модератор']).fetchall():
        ids.append(int(ret[0]))
    return ids

def get_only_admin_id():  # Получить id администраторов
    ids = []
    for ret in sqlite_db.cur.execute('SELECT * FROM users WHERE privileges LIKE ?',
                                     ['Администратор']).fetchall():
        ids.append(int(ret[0]))
    return ids

def get_categories():  # Получить id администраторов
    ids = []
    for ret in sqlite_db.cur.execute('SELECT name FROM categories_invoices').fetchall():
        ids.append(ret[0])
    return ids


def get_user_id(name):
    for ret in sqlite_db.cur.execute('SELECT * FROM users WHERE person LIKE ?', [name]).fetchall():
        return ret[0]


def get_uid(name):
    for ret in sqlite_db.cur.execute('SELECT * FROM users WHERE person LIKE ?', [name]).fetchall():
        return int(ret[0])


def get_main_cassier_id():
    ids = []
    for ret in sqlite_db.cur.execute('SELECT * FROM users WHERE privileges LIKE ?', ['Старший кассир']).fetchall():
        ids.append(int(ret[0]))
    return ids


def get_id_point(name):
    result = ''
    for ret in sqlite_db.cur.execute('SELECT id FROM shops WHERE name_point LIKE ?', [name]).fetchall():
        result = ret[0]
    return result


def pt_name(id1):
    result = 'Unknown'
    for ret in sqlite_db.cur.execute('SELECT name_point FROM shops WHERE id LIKE ?', [id1]).fetchall():
        result = ret[0]
    return result


def get_cassier_id():
    ids = []
    for ret in sqlite_db.cur.execute('SELECT * FROM users WHERE privileges LIKE ?', ['Кассир']).fetchall():
        ids.append(int(ret[0]))
    return ids


def kb(id0):  # Получить кнопки пользователей
    if id0 in get_mod_id():
        return mod_kb.button_case_mod
    elif id0 in get_admin_id():
        return mod_kb.button_case_mod
    elif id0 in get_main_cassier_id():
        return main_cassier_kb.main_cassier_kb
    elif id0 in get_cassier_id():
        for ret in sqlite_db.cur.execute('SELECT now_user FROM reports_open WHERE report_close_id = ?', ['']).fetchall():
            if str(get_user_id(ret[0])) == str(id0):
                return cassier_kb_close.button_cassier
        return cassier_kb.button_cassier
    
    elif id0 in get_storager_id():
        for ret in sqlite_db.cur.execute("SELECT person_id FROM storager_report WHERE person_id = ? AND close = ?", [id0, "0"]):
            if ret[0] == str(id0):
                return storager_kb_close.button_storager
        return storager_kb.button_storager
    
    elif id0 in get_drivers_id():
        for ret in sqlite_db.cur.execute("SELECT person_id FROM driver_report WHERE person_id = ? AND close = ?", [id0, "0"]):
            if ret[0] == str(id0):
                return storager_kb_close.button_storager
        return storager_kb.button_storager
    
    elif id0 in get_operators_id():
        for ret in sqlite_db.cur.execute("SELECT person_id FROM operator_report WHERE person_id = ? AND close = ?", [id0, "0"]):
            if ret[0] == str(id0):
                return storager_kb_close.button_storager
        return storager_kb.button_storager
    
    return kb_client


def get_storager_id():
    ids = []
    for ret in sqlite_db.cur.execute('SELECT * FROM users WHERE privileges LIKE ?', ['Кладовщик']).fetchall():
        ids.append(int(ret[0]))
    return ids


def get_operators_id():
    ids = []
    for ret in sqlite_db.cur.execute('SELECT * FROM users WHERE privileges LIKE ?', ['Оператор']).fetchall():
        ids.append(int(ret[0]))
    return ids


def get_drivers_id():
    ids = []
    for ret in sqlite_db.cur.execute('SELECT * FROM users WHERE privileges LIKE ?', ['Водитель']).fetchall():
        ids.append(int(ret[0]))
    return ids

def get_user_work_monthes(person, month, year):
    work_dates = []
    for ret in sqlite_db.cur.execute('SELECT month, year FROM menu WHERE person LIKE ?', [person]):
        if f'{ret[0]}.{ret[1]}' not in work_dates:
            work_dates.append(f'{ret[0]}.{ret[1]}')
    return work_dates


def get_temp(id0):
    result = ''
    for ret in sqlite_db.cur.execute('SELECT * FROM temp WHERE id LIKE ?', [id0]):
        result = ret[1]
    return result


def del_temp(id0):
    sqlite_db.cur.execute('DELETE FROM temp WHERE id LIKE ?', [id0])
    sqlite_db.base.commit()


def get_work_hours_shops():  # Получить рабочие часы магазинов
    shops = {}
    for ret in sqlite_db.cur.execute('SELECT * FROM shops').fetchall():
        shops[ret[0]] = (ret[1], ret[2], ret[3])
    return shops


def get_bonus(person, date, day_s, is_end=False):
    day_m, count, per, minus = 0, 0, 0, 0
    for ret in sqlite_db.cur.execute('SELECT date1, day_month, count, is_per, is_minus FROM prize_user '
                                     'WHERE user_id LIKE ?', [person]):
        if datetime.strptime(date, '%d.%m.%Y') >= datetime.strptime(ret[0], '%d.%m.%Y'):
            day_m, count, per, minus = ret[1], ret[2], ret[3], ret[4]
    if day_m == "В день" and not is_end:
        if per == "%" and minus == "-":
            return day_s * (float(count) / 100)
        elif per == "%" and minus == "+":
            return day_s * ((float(count) / 100) + 1)
        elif per != "%":
            return float(minus + count)
    elif day_m == "В месяц" and is_end:
        if per == "%" and minus == "-":
            return is_end * (float(count) / 100)
        elif per == "%" and minus == "+":
            return is_end * ((float(count) / 100) + 1)
        elif per != "%":
            return float(minus + count)
    else:
        return 0

def get_salary_storage(person, month, year):
    res = None
    for ret in sqlite_db.cur.execute("SELECT * FROM menu WHERE month = ? AND year = ? AND person = ?", [month, year, person]):
        res = get_user_salary(person, month, year, pers=True)

    privs = {"Оператор": ("operator_report", 1600), "Кладовщик": ("storager_report",2050), "Водитель": ("driver_report",1600), "Администратор": ("manager_report", 2500)}
    for ret in sqlite_db.cur.execute("SELECT privileges FROM users WHERE id = ?", [get_user_id(person)]):
        priv = ret[0]
    total_days = 0

    for ret in sqlite_db.cur.execute(f"SELECT id FROM {privs[priv][0]} WHERE person_id = ? AND close <> ? AND month = ? AND year = ?", [get_user_id(person), "0", month, year]).fetchall():
        total_days += 1

    salary = total_days * privs[priv][1]
    premie = get_premie(person, month, year)
    fines = get_sum_fine_user(person, month, year)[0]

    result = {'total_sum': int(salary) + int(premie) - int(fines), 'total_days': int(total_days), 'prizes': 0, 'bonuses': 0, 'day_total_sum': 0, 'fines': int(fines), 'premie_plan': 0, 'user_loss': 0, 'without': salary, 'disc_user': 0, 'revision': 0, 'late': 0, 'late_count': 0}
    
    if res:
        res["total_sum"] += result["total_sum"]
        res["total_days"] += result["total_days"]
        res["without"] += result["without"]
        return res
    
    return result
    
def get_user_salary(person, month, year, detail = False, pers = False):  # Получить зарплату пользователя по дням
    if (get_uid(person) in get_storager_id() or get_uid(person) in get_drivers_id() or get_uid(person) in get_operators_id() or get_uid(person) in get_only_admin_id()) and not pers:
        res = get_salary_storage(person, month, year)
        return res
    day_tl, c_day, prize, s_bonus, date_day, s_day, type_s = 0, 0, 0, 0, "", 0, ""
    total_s, total_days, day_tl_all = 0, 0, 0
    salaries = {}
    dates = []
    for ret in sqlite_db.cur.execute('SELECT total, point1, date1 FROM menu WHERE person LIKE ?'
                                     ' AND month LIKE ? AND year LIKE ? ORDER BY year ASC, month ASC, day ASC',
                                     [person, month, year]).fetchall():
        if (ret[1], ret[2]) in dates:
            continue
        dates.append((ret[1], ret[2]))
        salary_for_day, prize_for_day, day_tl, k = 0,0,0,0
        day_tl, point_day, date_day = float(ret[0]), ret[1], ret[2]
        type_salary = get_type_sal(point_day, date_day, person)
        if len(type_salary) != 0:
            type_s, id_s = type_salary.pop('type')
            k = check_replace(person, date_day)
            try:
                salary_for_day = round(get_salary_day(type_s, type_salary, point_day, day_tl) * k, 0)
            except Exception:
                salary_for_day = 0
            try:
                s_bonus += get_bonus(person, date_day, s_day)
            except Exception:
                s_bonus += 0
            if salary_for_day:
                s_day += salary_for_day
            prize_for_day = round(get_prize(day_tl, id_s) * k, 0)
            prize += prize_for_day
        
        total_days += 1
        day_tl_all += day_tl
        salaries[ret[2]] = (salary_for_day, prize_for_day, day_tl, k, point_day)

    replaces_ = check_all_replaces(person, month, year)
    for rep_data in replaces_[1].keys():
        salaries[rep_data] = replaces_[1][rep_data]
        s_day += replaces_[1][rep_data][0]
        prize += replaces_[1][rep_data][1]

    revision = get_revision_user(person, month, year)
    premie_plan = get_premie_plan(person, month, year)
    discount_user = get_discount_user(person)
    try:
        late_user = get_late_user(person, month, year)
    except Exception:
        late_user = -1

    loss_user = round(get_loss_user(person, month, year) * (1 - (get_discount_user(person) / 100)), 2)
    fines, late = get_sum_fine_user(person, month, year)

    total_s += s_day + prize + s_bonus + get_premie(person, month, year) + premie_plan - fines - late - loss_user - revision 

    result = {'total_sum': int(total_s), 'total_days': int(total_days), 'prizes': int(prize), 'bonuses': int(s_bonus),
            'day_total_sum': int(day_tl_all), 'fines': int(fines), 
            'premie_plan': round(premie_plan, 0), 'user_loss': loss_user, 'without': s_day, 'disc_user': discount_user, 'revision': revision, 'late': late, 'late_count': late_user}
    
    if not detail:
        return result 
    else:
        sorted_dict = dict(sorted(salaries.items(), key=lambda item: extract_date(item[0])))
        return (result, sorted_dict)


def extract_date(date_str):
    return datetime.strptime(date_str, "%d.%m.%Y")


def check_replace(person, date_day):
    start, finish, k = "10:00", "23:59", 1.0
    for ret in sqlite_db.cur.execute('SELECT time, point FROM replace_person WHERE data1 = ? AND person1 = ?', [date_day, person]):
        i = 0
        for net in sqlite_db.cur.execute("SELECT * FROM replace_person WHERE data1 = ? AND point = ?", [date_day, ret[1]]).fetchall():
            i += 1
        if i == 1:
            for jet in sqlite_db.cur.execute('SELECT work_hours_start, work_hours_finish FROM shops WHERE name_point = ?', [ret[1]]):
                start, finish = jet[0], jet[1]
                if finish == "00:00":
                    finish = "23:59"
            k = calculate_time_intervals(start, ret[0], finish)[1]
        if k < 0:
            k = 0
        elif k > 1:
            k = 1
    return round(k, 2)
            

def calculate_time_intervals(start_time, intermediate_time, end_time):
    # Преобразуем строки в объекты datetime
    start = datetime.strptime(start_time, "%H:%M")
    intermediate = datetime.strptime(intermediate_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")

    if 0 < int(end_time.split(":")[0]) < 6:
        end += timedelta(days=1)
    

    # Расчитываем интервалы времени
    time_before_intermediate = intermediate - start
    time_after_intermediate = end - intermediate
    total_time = end - start

    # Проценты времени
    percent_before = (time_before_intermediate.total_seconds() / total_time.total_seconds()) 
    percent_after = (time_after_intermediate.total_seconds() / total_time.total_seconds()) 

    return percent_before, percent_after


def check_all_replaces(person, month, year):
    day_tl, point_day, date_day, s_day, prize, res = 0, 0, 0, 0, 0, 0
    start, finish, k = "10:00", "23:59", 1
    salaries = {}
    for day in range(1, 32):
        day = str(day)
        if len(day) == 1:
            day = "0" + day
        salary_for_day, prize_for_day = 0, 0
        for ret in sqlite_db.cur.execute("SELECT time, point, data1 FROM replace_person WHERE data1 = ? AND person = ?", [f"{day}.{month}.{year}", person]):
            i = 0
            for net in sqlite_db.cur.execute("SELECT * FROM replace_person WHERE data1 = ? AND point = ?", [f"{day}.{month}.{year}", ret[1]]).fetchall():
                i += 1
            if i == 1:
                for jet in sqlite_db.cur.execute('SELECT work_hours_start, work_hours_finish FROM shops WHERE name_point = ?', [ret[1]]):
                    start, finish = jet[0], jet[1]
                    if finish == "00:00":
                        finish = "23:59"
                k = round(calculate_time_intervals(start, ret[0], finish)[0], 2)
                if k < 0:
                    k = 0
                elif k > 1:
                    k = 1
                for jet in sqlite_db.cur.execute('SELECT total, point1, date1 FROM menu WHERE date1 = ? AND point1 = ?', [ret[2], ret[1]]):
                    day_tl, point_day, date_day = float(jet[0]), jet[1], jet[2]
                    type_salary = get_type_sal(point_day, date_day, person)
                    if len(type_salary) != 0:
                        type_s, id_s = type_salary.pop('type')
                        salary_for_day = round(get_salary_day(type_s, type_salary, point_day, day_tl) * k, 0)
                        prize_for_day = round(get_prize(day_tl, id_s) * k, 0)
        if salary_for_day and salary_for_day != 0:
            s_day += salary_for_day
            prize += prize_for_day
            salaries[jet[2]] = (salary_for_day, prize_for_day, day_tl, k, ret[1])
            res += salary_for_day + prize_for_day
    return (res, salaries)



def get_salary_day(type_s, val_s, shop, day_tl):  # ДОДЕЛАТЬ ПРОВЕРКУ НА ЗАМЕНУ
    if type_s == "Почасовая":
        dif_time = 0
        for ret in sqlite_db.cur.execute("SELECT work_hours_start, work_hours_finish FROM shops WHERE id LIKE ?",
                                         [get_id_point(shop)]):
            t_open, t_close = datetime.strptime(ret[0], "%H:%M"), datetime.strptime(ret[1], "%H:%M")
            if t_close < t_open:
                t_close += timedelta(days=1)
            dif_time = (t_close - t_open).seconds
            for interval, value in val_s.items():
                int1, int2 = int(interval.split('-')[0]), int(interval.split('-')[1])
                if int1 < float(day_tl) < int2:
                    return value * (dif_time / 3600)
    elif type_s == "Суточная":
        for interval, value in val_s.items():
            int1, int2 = int(interval.split('-')[0]), int(interval.split('-')[1])
            if int1 <= float(day_tl) < int2:
                return value
    else:
        return 0


def get_type_sal(point_id, date, user):
    result, result_user = {}, {}
    last_date = "01.01.1999"
    for ret in sqlite_db.cur.execute("SELECT type, value, date, id,int FROM salary WHERE point_id LIKE ?",
                                     [get_id_point(point_id)]).fetchall():
        if datetime.strptime(date, '%d.%m.%Y') >= datetime.strptime(ret[2], '%d.%m.%Y'):
            if datetime.strptime(ret[2], '%d.%m.%Y') > datetime.strptime(last_date, '%d.%m.%Y'):
                last_date = ret[2]
                result, result_user = {}, {}
                result[f"{ret[4]}"] = float(ret[1])
                result['type'] = [ret[0], ret[3]]
            elif datetime.strptime(ret[2], '%d.%m.%Y') == datetime.strptime(last_date, '%d.%m.%Y'):
                result[f"{ret[4]}"] = float(ret[1])
                result['type'] = [ret[0], ret[3]]
    for jet in sqlite_db.cur.execute("SELECT type, value, date, id FROM salary WHERE point_id LIKE ?",
                                     [get_user_id(user)]).fetchall():
        if datetime.strptime(date, '%d.%m.%Y') >= datetime.strptime(jet[2], '%d.%m.%Y'):
            result_user[f"{jet[4]}"] = float(jet[1])
            result_user['type'] = [jet[0], jet[3]]
    if len(result_user) != 0:
        return result_user
    return result


def get_prize(day_tl, id_sal):  # Премия
    prizes = {}
    for ret in sqlite_db.cur.execute("SELECT inter1, inter2, prize_count, is_per, is_step FROM prize "
                                     "WHERE salary_id LIKE ?", [id_sal]):
        prizes[(int(ret[0]), int(ret[1]))] = (float(ret[2]), ret[3], ret[4])
    for prize, value in prizes.items():
        if prize[0] < float(day_tl) < prize[1]:
            if value[1] == "%":
                return round((value[0] / 100) * float(day_tl), 0)
            else:
                if value[2] != '0':
                    return ((round(float(day_tl), -3) - prize[0]) / float(value[2])) * value[0]
                return value[0]
    return 0


def get_premie(person, month, year):
    date_ = f"{month}.{year}"
    prem = 0
    for ret in sqlite_db.cur.execute('SELECT premie FROM premies WHERE person LIKE ? AND date1 LIKE ?',
                                     [person, date_]).fetchall():
        prem += float(ret[0])
    return int(prem)


def reports_open(date):
    result = []
    for ret in sqlite_db.cur.execute('SELECT person FROM reports_open WHERE report_close_id LIKE ? AND date1 LIKE ?',
                                     ['', date]):
        result.append(ret[0])
    return result


def get_sum_pay(person, month, year):
    result = 0
    for ret in sqlite_db.cur.execute('SELECT payment FROM payments WHERE person LIKE ? AND month LIKE ? and year LIKE ?'
            , [person, month, year]).fetchall():
        result += float(ret[0])
    return round(result, 0)


def get_fine_user(person, month,
                  year):  # Получить штрафы пользователя(возращает список словаря с данными штрафов и общей суммы штрафов)
    fines = {}
    for ret in sqlite_db.cur.execute(
            'SELECT * FROM fine WHERE person LIKE ? AND month LIKE ? AND year LIKE ? ORDER BY year ASC, month ASC, day ASC',
            [person, month, year]):
        fines[ret[7]] = [float(ret[1]), ret[2], ret[6], ret[7]]
    return fines


def get_sum_fine_user(person, month, year):
    fines, late = 0, 0
    for ret in sqlite_db.cur.execute(
            'SELECT fine, comments FROM fine WHERE person LIKE ? AND month LIKE ? AND year LIKE ? ORDER BY year ASC, month ASC, day ASC',
            [person, month, year]):
        if ret[1] == "Опоздание":
            late += float(ret[0])
        else:
            fines += float(ret[0])
    return int(fines), int(late)


def get_late_user(person, month, year):
    late = 0
    for ret in sqlite_db.cur.execute(
            'SELECT count(*) FROM late WHERE id_user LIKE ? AND month LIKE ? AND year LIKE ? ORDER BY year ASC, month ASC, day ASC', [get_user_id(person), month, year]):
        late = ret[0]
    return late


def get_id_sklad_point(point_id_name):
    for ret in sqlite_db.cur.execute('SELECT id_sklad FROM shops WHERE id LIKE ? OR name_point LIKE ?',
                                     [point_id_name, point_id_name]):
        return ret[0]


def get_now_salary(person, date_month_year):  # Получить последнюю ставку за прошлые месяцы
    result = 0
    date_month_year = datetime.strptime(date_month_year, '%m.%Y')
    for ret in sqlite_db.cur.execute('SELECT * FROM salary WHERE person LIKE ? ORDER BY year ASC, month ASC, day ASC',
                                     [person]):
        let_date = datetime.strptime(f'{ret[4]}.{ret[5]}', '%m.%Y')
        if let_date < date_month_year:
            result = float(ret[1])
    return result


def get_shops():
    res = []
    for ret in sqlite_db.cur.execute('SELECT id, name_point, id_sklad FROM shops'):
        res.append({"id": ret[0], "name": ret[1], "token_id": ret[2]})
    return res


def get_retail_store(store_id):
    add_retail = f"https://api.moysklad.ru/api/remap/1.2/entity/retailstore/{store_id}"
    response = requests.get(add_retail, headers=token.headers)
    data = json.loads(response.text)
    return data['store']


def get_premie_plan(user, month, year):
    for ret in sqlite_db.cur.execute('SELECT premie FROM premies_plan WHERE person = ? AND month = ? AND year = ?',
                                     [user, month, year]):
        return float(ret[0])
    return 0


def get_revision_user(user, month, year):
    result = 0
    shop_count = 0
    user_shop = {}
    for ret in sqlite_db.cur.execute('SELECT point1 FROM menu WHERE person = ? AND month = ? AND year = ?',
                                     [user, month, year]).fetchall():
        if ret[0] not in user_shop.keys():
            user_shop[ret[0]] = 1
        else:
            user_shop[ret[0]] += 1

    for shop in user_shop.keys():
        for ret in sqlite_db.cur.execute('SELECT point1 FROM menu WHERE point1 = ? AND month = ? AND year = ?',
                                     [shop, month, year]).fetchall():
            shop_count += 1
        
        try:
            user_shop[shop] = user_shop[shop] / shop_count
        except Exception:
            user_shop[shop] = 0
        shop_count = 0
    
    for shop, k in user_shop.items():
        for ret in sqlite_db.cur.execute('SELECT value FROM revision WHERE point = ? AND month = ? AND year = ?',
                                     [get_id_point(shop), month, year]).fetchall():
            result += float(ret[0]) * k
    return round(result, 0)


def get_loss_user(user, month, year):
    sum_loss = 0
    for ret in sqlite_db.cur.execute("SELECT token_id, price FROM defects WHERE month = ? AND year = ? AND"
                                     " user_id = ? AND type = ?", [month, year, get_user_id(user), "В счёт зарплаты"]):
        url_get_expenses = f"https://api.moysklad.ru/api/remap/1.2/entity/loss/" + ret[0]
        response = requests.get(url_get_expenses, headers=token.headers)
        data = json.loads(response.text)

        if "deleted" not in data and "errors" not in data:
            sum_loss += round(float(ret[1]) / 100, 2)

    return sum_loss


def get_discount_user(person):
    for ret in sqlite_db.cur.execute("SELECT date1 FROM users WHERE person = ?", [person]):
        try:
            time1 = datetime.strptime(ret[0], "%d.%m.%Y")
            if monthdelta(time1) >= 3:
                return 15
        except Exception:
            return 10
    return 10


def monthdelta(d1):
    delta = 0
    d2 = datetime.now()
    while True:
        mdays = calendar.monthrange(d1.year, d1.month)[1]
        d1 += timedelta(days=mdays)
        if d1 <= d2:
            delta += 1
        else:
            break
    return delta
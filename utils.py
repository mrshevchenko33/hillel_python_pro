from flask import Flask, request, render_template, session, redirect
from functools import wraps
import sqlite3
import datetime


app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class SQLiteDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None

    def __enter__(self):
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = dict_factory
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()

    def select_method(self, table, condition=None, columns=None, fetch_all=True, join=None):
        query = f'SELECT '
        if columns:
            query += ', '.join(columns)
        else:
            query += '*'
        query += f' FROM {table}'
        if join:
            for join_table, join_condinion in join.items():
                query += f' JOIN {join_table} ON {join_condinion}'
        conditions = []
        if condition is not None:
            for key, val in condition.items():
                conditions.append(f" {key} = '{val}'")
            str_conditions = ' AND '.join(conditions)
            str_conditions = ' WHERE ' + str_conditions
            query = query + str_conditions

        cursor = self.connection.cursor()
        cursor.execute(query)

        if fetch_all:
            res = cursor.fetchall()
        else:
            res = cursor.fetchone()

        if res:
            return res
        return None

    def commit(self, table, data):
        keys = []
        vals = []
        for key, value in data.items():
            keys.append(key)
            vals.append("'" + str(value) + "'")
        str_keys = ', '.join(keys)
        str_vals = ', '.join(vals)
        query = f'INSERT INTO {table} ({str_keys}) VALUES ({str_vals})'
        cursor = self.connection.cursor()
        cursor.execute(query)
        self.connection.commit()

    def edit(self, table, data, condition):
        update_values = []
        conditions = []
        for key, value in data.items():
            update_values.append(f"{key} = '{value}'")
        set_clause = ', '.join(update_values)
        query = f'UPDATE {table} SET {set_clause}'
        if condition is not None:
            for key, val in condition.items():
                conditions.append(f" {key} = '{val}'")
            str_conditions = ' AND '.join(conditions)
            str_conditions = ' WHERE ' + str_conditions
            query = query + str_conditions
        cursor = self.connection.cursor()
        cursor.execute(query)
        self.connection.commit()


def clac_slots(user_id, trainer_id, service_id):
    with SQLiteDatabase('DB.db') as db:
        booked_time = db.select_method('reservation',
                                       {'trainer_id': trainer_id, 'date': '31.05.2024'},
                                       join={'service': 'service.id = reservation.service_id'})
        trainer_schedule = db.select_method('trainer_schedule', {'trainer_id': trainer_id, 'date': '31.05.2024'},
                                            fetch_all=False)
        trainer_capacity = db.select_method('trainer_services', {'trainer_id': trainer_id, 'service_id': service_id}, fetch_all=False)
        service_info = db.select_method('service', {'id': service_id}, fetch_all=False)
        start_dt = datetime.datetime.strptime(trainer_schedule['date'] + ' ' + trainer_schedule['start_time'],
                                             '%d.%m.%Y %H:%M')
        end_dt = datetime.datetime.strptime(trainer_schedule['date'] + ' ' + trainer_schedule['end_time'],
                                            '%d.%m.%Y %H:%M')
        curr_dt = start_dt
        trainer_schedule = {}
        while curr_dt < end_dt:
            trainer_schedule[curr_dt] = trainer_capacity['capacity']
            curr_dt += datetime.timedelta(minutes=15)
        for one_booking in booked_time:
            booking_date = one_booking['date']
            booking_time = one_booking['time']
            booking_duration = one_booking['duration']
            one_booking_start = datetime.datetime.strptime(booking_date + ' ' + booking_time, '%d.%m.%Y %H:%M')
            booking_end = one_booking_start + datetime.timedelta(minutes=booking_duration)
            curr_dt = one_booking_start
            while curr_dt < booking_end:
                trainer_schedule[curr_dt] -= 1
                curr_dt += datetime.timedelta(minutes=15)
        result_times = []
        service_duration = service_info['duration']
        service_start_time = start_dt
        while service_start_time < end_dt:
            service_end_time = service_start_time + datetime.timedelta(minutes=service_duration)
            everyting_is_free = True
            iter_start_time = service_start_time
            while iter_start_time < service_end_time:
                if trainer_schedule[iter_start_time] == 0 or service_end_time > end_dt:
                    everyting_is_free = False
                    break
                iter_start_time += datetime.timedelta(minutes=15)

            if everyting_is_free:
                result_times.append(service_start_time)
            service_start_time += datetime.timedelta(minutes=15)
        return result_times


    print('')

clac_slots(1, 1, 2)

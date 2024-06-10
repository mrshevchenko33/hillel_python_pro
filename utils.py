from flask import Flask, request, render_template, session, redirect
from functools import wraps
import sqlite3
from datetime import datetime, timedelta

from project_package.models import *
from project_package.database import *

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d



def clac_slots(trainer_id, service_id, date):

    booked_time = db_session.query(Reservation).join(Service, Service.id == Reservation.service_id).filter(Reservation.trainer_id == trainer_id, Reservation.date == date).all()
    trainer_schedule = db_session.query(TrainerSchedule).filter(TrainerSchedule.trainer_id == trainer_id, TrainerSchedule.date == date).first()
    trainer_capacity = db_session.query(TrainerServices).filter(TrainerServices.trainer_id == trainer_id, TrainerServices.service_id == service_id).first()
    service_info = db_session.query(Service).get(service_id)

    if not trainer_schedule or not trainer_capacity or not service_info:
        return []

    start_dt = datetime.strptime(trainer_schedule.date + ' ' + trainer_schedule.start_time, '%Y-%m-%d %H:%M')
    end_dt = datetime.strptime(trainer_schedule.date + ' ' + trainer_schedule.end_time, '%Y-%m-%d %H:%M')
    curr_dt = start_dt
    schedule = {}

    while curr_dt < end_dt:
        schedule[curr_dt] = trainer_capacity.capacity
        curr_dt += timedelta(minutes=15)

    for one_booking in booked_time:
        booking_start = datetime.strptime(one_booking.date + ' ' + one_booking.time, '%Y-%m-%d %H:%M')
        booking_end = booking_start + timedelta(minutes=one_booking.service.duration)
        curr_dt = booking_start
        while curr_dt < booking_end:
            schedule[curr_dt] -= 1
            curr_dt += timedelta(minutes=15)

    result_times = []
    service_duration = service_info.duration
    service_start_time = start_dt

    while service_start_time < end_dt:
        service_end_time = service_start_time + timedelta(minutes=service_duration)
        everything_is_free = True
        iter_start_time = service_start_time

        while iter_start_time < service_end_time:
            if schedule.get(iter_start_time, 0) == 0 or service_end_time > end_dt:
                everything_is_free = False
                break
            iter_start_time += timedelta(minutes=15)

        if everything_is_free:
            result_times.append(service_start_time)
        service_start_time += timedelta(minutes=15)

    return result_times







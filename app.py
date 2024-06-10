from flask import Flask, request, render_template, session, redirect
from functools import wraps
import os
import sqlite3

from dotenv import load_dotenv

from project_package.models import *
from project_package.database import *
from utils import clac_slots

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv('FLASK_SECRET_KEY')


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/login')

    return wrapper


@login_required
@app.route('/', methods=['GET'])
def index():
    return render_template('homepage.html')


@app.route('/register', methods=['GET', 'POST'])
def get_register():
    if request.method == 'POST':
        form_data = request.form
        user = User(login=form_data['login'], password=form_data['password'],
                    birth_date=form_data['birth_date'], phone=form_data['phone'])
        db_session.add(user)
        db_session.commit()
        return 'User registered'
    else:
        return render_template('register.html')


def check_credentials(username, password):
    user = db_session.query(User).filter_by(login=username, password=password).first()
    return user


@app.route('/login', methods=['GET', 'POST'])
def get_login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        user = check_credentials(login, password)
        if user is not None:
            session['user'] = {'id': user.id, 'login': user.login}
            return redirect('/user')
        else:
            return 'Incorrect login or password'

    else:
        user_id = session.get('user', None)
        if user_id:
            return redirect(f'/user')
        return render_template('login.html')


@app.route('/logout', methods=['GET'])
@login_required
def get_logout():
    session.pop('user', None)
    return redirect('/login')


@app.route('/user', methods=['GET'])
@login_required
def get_users():
    user = session.get('user', None)
    user = db_session.query(User).filter_by(id=user['id']).first()
    return render_template('user_info.html', user=user)


@app.route('/funds/<int:user_id>', methods=['GET', 'POST'])
@login_required
def get_funds(user_id):
    if request.method == 'POST':
        return 'user account was successfully funded'
    else:
        user = db_session.query(User).filter_by(id=user_id).first()
        return user


@login_required
@app.route('/fitness_center/<int:gym_id>/services', methods=['GET'])
def get_services(gym_id):
    services = db_session.query(Service).join(Gym, Service.gym_id == Gym.id).filter(Service.gym_id == gym_id).all()
    for service in services:
        service.trainers = db_session.query(Trainer).join(TrainerServices,
                                                          Trainer.id == TrainerServices.trainer_id).filter(
            TrainerServices.service_id == service.id).all()
    return render_template('services.html', services=services, gym_id=gym_id)


@app.route('/fitness_center/<int:gym_id>/services/<int:service_id>', methods=['GET'])
def service_info(gym_id, service_id):
    service = db_session.query(Service).join(Gym, Service.gym_id == Gym.id).filter(Service.gym_id == gym_id,
                                                                                   Service.id == service_id).first()
    if service:
        return render_template('service.html', service=service)
    else:
        return 'Послуга не знайдена'


@app.route('/fitness_center/<gym_id>/trainer', methods=['GET'])
def get_trainer(gym_id):
    trainers = db_session.query(Trainer).join(Gym, Trainer.gym_id == Gym.id).filter(Gym.id == gym_id).all()
    return render_template('trainers_info.html', trainers=trainers)


@app.route('/fitness_center/<gym_id>/trainer/<trainer_id>/service/<int:service_id>', methods=['GET', 'POST'])
@login_required
def get_trainer_service(gym_id, trainer_id, service_id):
    trainer = db_session.query(Trainer).filter_by(id=trainer_id).first()
    service = db_session.query(Service).filter_by(id=service_id).first()
    if request.method == 'POST':
        form_data = request.form
        date = form_data.get('date')
        available_slots = clac_slots(trainer_id, service_id, date)
        return render_template('trainer_info.html', trainer=trainer, service=service, available_slots=available_slots,
                               date=date)
    else:
        user = session.get('user', None)
        return render_template('trainer_info.html', trainer=trainer, service=service)


@app.route('/fitness_center/<gym_id>/trainer/<trainer_id>/rating', methods=['GET', 'POST'])
@login_required
def trainer_rating(gym_id, trainer_id):
    user = session.get('user', None)
    if request.method == 'POST':
        rating = request.form.get('rating')
        review_text = request.form.get('review')
        user_review = db_session.query(Review).filter_by(user_id=user['id'], trainer_id=trainer_id).first()
        if user_review is not None:
            user_review.points = rating
            user_review.text = review_text
        else:
            new_review = Review(user_id=user['id'], trainer_id=trainer_id, gym_id=gym_id, points=int(rating),
                                text=review_text)
            db_session.add(new_review)
        db_session.commit()

        return redirect(f'/fitness_center/{gym_id}/trainer/{trainer_id}/rating')

    else:
        user_reviw = db_session.query(Review).filter_by(user_id=user['id'], trainer_id=trainer_id).first()
        trainer = db_session.query(Trainer).join(Gym, Trainer.gym_id == Gym.id).filter(Trainer.id == trainer_id).first()
        reviews = db_session.query(Review).filter_by(trainer_id=trainer_id).all()
        return render_template('trainer_rating.html', reviews=reviews, users=user, trainer=trainer,
                               user_reviw=user_reviw)

@app.route('/user/reservations', methods=['GET', 'POST'])
@login_required
def user_reservations():
    if request.method == 'GET':
        reservations = db_session.query(Reservation).join(User, Reservation.user_id == User.id).join(Trainer,
                                                                                                     Reservation.trainer_id == Trainer.id).join(
            Service, Reservation.service_id == Service.id).filter(User.id == session['user']['id']).all()
        return render_template('reservations.html', reservations=reservations)

    else:
        form_dict = request.form
        service_id = form_dict.get('service_id')
        trainer_id = form_dict.get('trainer_id')
        date = form_dict.get('date')
        time = form_dict.get('time')
        new_reservation = Reservation(user_id=user['id'], service_id=int(service_id), trainer_id=int(trainer_id),
                                      date=date, time=time)
        db_session.add(new_reservation)
        db_session.commit()
        return redirect('/user/reservations')


@app.route('/user/reservations/<reservation_id>', methods=['GET', 'POST'])
@login_required
def user_reservation(reservation_id):
    if request.method == 'GET':
        reservation = db_session.query(Reservation).join(User, Reservation.user_id == User.id).join(Trainer,
                                                                                                     Reservation.trainer_id == Trainer.id).join(
            Service, Reservation.service_id == Service.id).filter(User.id == session['user']['id']).first()
        return render_template('reservation.html', reservation=reservation)
    else:  # POST (DELETE, UPDATE)
        return 'update user reservation', 'delete user reservation'


@app.route('/user/checkout', methods=['GET', 'POST'])
@login_required
def user_checkout():
    if request.method == 'GET':
        return 'get user checkout information'
    elif request.method == 'POST':
        return 'create user checkout', 'update user checkout', 'delete user checkout'


@app.route('/fitness_center', methods=['GET'])
def fitness_centers():
    fitness_centers = db_session.query(Gym).all()
    return render_template('fitness_center.html', centers=fitness_centers)


@app.route('/fitness_center/<int:center_id>', methods=['GET'])
def fitness_center(center_id):
    res = db_session.query(Gym).filter(Gym.id == center_id).first()
    if res is not None:
        return render_template('center.html', center=res)
    else:
        return "Center not found"


@app.route('/fitness_center/<center_id>/loyalty_programs', methods=['GET'])
def loyalty_programs(center_id):
    return f'get loyalty programs for fitness center with id {center_id}'


if __name__ == '__main__':
    app.run(debug=True)

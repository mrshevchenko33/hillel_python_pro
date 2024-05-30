from flask import Flask, request, render_template, session, redirect
from functools import wraps
import sqlite3

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)
app.secret_key = 'my_secret_key'


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
        with SQLiteDatabase('DB.db') as db:
            db.commit("user", {"login": form_data['login'], "password": form_data['password'],
                               "birth_date": form_data['birth_date'], "phone": form_data['phone']})
        return 'User registered'
    else:
        return render_template('register.html')


def check_credentials(username, password):
    with SQLiteDatabase('DB.db') as db:
        user = db.select_method("user", {"login": username, "password": password}, fetch_all=False)
    return user is not None


@app.route('/login', methods=['GET', 'POST'])
def get_login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        if check_credentials(login, password):
            with SQLiteDatabase('DB.db') as db:
                user = db.select_method("user", {"login": login, "password": password}, fetch_all=False)
            session['user'] = user
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
    return render_template('user_info.html', user=user)


@app.route('/funds/<int:user_id>', methods=['GET', 'POST'])
@login_required
def get_funds(user_id):
    if request.method == 'POST':
        return 'user account was successfully funded'
    else:
        with SQLiteDatabase('DB.db') as db:
            res = db.select_method("user", {"id": user_id}, columns=['funds'], fetch_all=False)
            return res


@login_required
@app.route('/fitness_center/<int:gym_id>/services', methods=['GET'])
def get_services(gym_id):
    with SQLiteDatabase('DB.db') as db:
        res = db.select_method('service', {'gym_id': gym_id}, join={'gym': 'service.gym_id = gym.id'},
                               columns=['service.id AS service_id', 'service.name', 'service.duration', 'service.price',
                                        'service.description', 'service.max_attendees', 'gym.name AS gym_name'])
    return render_template('services.html', services=res)


@app.route('/fitness_center/<int:gym_id>/services/<int:service_id>', methods=['GET'])
def service_info(gym_id, service_id):
    with SQLiteDatabase('DB.db') as db:
        res = db.select_method('service', {'gym_id': gym_id, 'service_id': service_id},
                               join={'gym': 'service.gym_id = gym.id'},
                               columns=['service.id AS service_id', 'service.name', 'service.duration', 'service.price',
                                        'service.description', 'service.max_attendees', 'gym.name AS gym_name'],
                               fetch_all=False)
        if res is not None:
            return render_template('service.html', service=res)
        else:
            return "Service not found"


@app.route('/fitness_center/<gym_id>/trainer', methods=['GET'])
def get_trainer(gym_id):
    with SQLiteDatabase('DB.db') as db:
        res = db.select_method("trainer", {'gym_id': gym_id}, join={'gym': 'trainer.gym_id = gym.id'},
                               columns=['trainer.id AS trainer_id', 'trainer.name AS trainer_name',
                                        'gym.name AS gym_name'])
        return render_template('trainers_info.html', trainers=res)


@app.route('/fitness_center/<gym_id>/trainer/<trainer_id>', methods=['GET'])
def trainer_info(gym_id, trainer_id):
    with SQLiteDatabase('DB.db') as db:
        res = db.select_method("trainer", {'trainer.gym_id': gym_id, 'trainer.id': trainer_id},
                               join={'gym': 'trainer.gym_id = gym.id'},
                               columns=['trainer.id AS trainer_id', 'trainer.name AS trainer_name',
                                        'gym.name AS gym_name'],
                               fetch_all=False)
        if res is not None:
            return render_template('trainer_info.html', trainer=res)
        else:
            return "Trainer not found"


@app.route('/fitness_center/<gym_id>/trainer/<trainer_id>/rating', methods=['GET', 'POST'])
@login_required
def trainer_rating(gym_id, trainer_id):
    user = session.get('user', None)
    if request.method == 'POST':
        rating = request.form.get('rating')
        review_text = request.form.get('review')

        with SQLiteDatabase('DB.db') as db:
            reviews = db.select_method("review", condition={'trainer_id': trainer_id, 'user_id': user['id']},
                                       fetch_all=False)
            if reviews is not None:
                db.edit("review", {'points': rating, 'text': review_text},
                        condition={'trainer_id': trainer_id, 'user_id': user['id']})
            else:
                db.commit("review",
                          {'trainer_id': trainer_id, 'gym_id': gym_id, 'user_id': user['id'], 'points': rating,
                           'text': review_text})
        return redirect(f'/fitness_center/{gym_id}/trainer/{trainer_id}/rating')
    else:
        with SQLiteDatabase('DB.db') as db:
            user_reviw = db.select_method("review", condition={'trainer_id': trainer_id, 'user_id': user['id']},
                                          fetch_all=False)
            trainer = db.select_method("trainer", condition={'id': trainer_id}, fetch_all=False)
            reviews = db.select_method("review",
                                       join={'trainer': 'review.trainer_id = trainer.id',
                                             'gym': 'review.gym_id = gym.id',
                                             'user': 'review.user_id = user.id'},
                                       columns=['review.text', 'review.points', 'user.login', 'gym.name AS gym_name',
                                                'trainer.name AS trainer_name'], condition={'trainer_id': trainer_id},
                                       fetch_all=True)

        return render_template('trainer_rating.html', reviews=reviews, users=user, trainer=trainer,
                               user_reviw=user_reviw)


@app.route('/user/reservations', methods=['GET', 'POST'])
@login_required
def user_reservations():
    user = session.get('user', None)
    if request.method == 'GET':
        with SQLiteDatabase('DB.db') as db:
            services = db.select_method("service", columns=['id', 'name'], fetch_all=True)
            reservations = db.select_method("reservation", join={'user': 'reservation.user_id = user.id',
                                                                 'service': 'reservation.service_id = service.id',
                                                                 'gym': 'service.gym_id = gym.id'},
                                            columns=['reservation.id AS reservation_id', 'reservation.date',
                                                     'reservation.time', 'user.login AS user_name',
                                                     'service.name AS service_name', 'gym.name AS gym_name'],
                                            condition={'user_id': user['id']}, fetch_all=True)
        return render_template('reservations.html', reservations=reservations, services=services)

    else:
        with SQLiteDatabase('DB.db') as db:
            db.commit("reservation", {'user_id': user['id'], 'service_id': request.form.get('service_id'),
                                      'date': request.form.get('date'), 'time': request.form.get('time')})
        return redirect('/user/reservations')


@app.route('/user/reservations/<reservation_id>', methods=['GET', 'POST'])
@login_required
def user_reservation(reservation_id):
    if request.method == 'GET':
        user = session.get('user', None)
        with SQLiteDatabase('DB.db') as db:
            reservation = db.select_method("reservation", {'reservation_id': reservation_id, 'user_id': user['id']},
                                           join={'user': 'reservation.user_id = user.id',
                                                 'service': 'reservation.service_id = service.id'},
                                           columns=['reservation.id AS reservation_id', 'reservation.date',
                                                    'reservation.time', 'user.login AS user_name',
                                                    'service.name AS service_name'], fetch_all=False)
            if reservation:
                return render_template('reservation.html', reservation=reservation)
            else:
                return f'Reservation with ID {reservation_id} not found'
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
    with SQLiteDatabase('DB.db') as db:
        res = db.select_method("gym")
        return render_template('fitness_center.html', centers=res)


@app.route('/fitness_center/<int:center_id>', methods=['GET'])
def fitness_center(center_id):
    with SQLiteDatabase('DB.db') as db:
        res = db.select_method("gym", {'id': center_id}, fetch_all=False)
        if res is not None:
            return render_template('center.html', center=res)
        else:
            return "Center not found"


@app.route('/fitness_center/<center_id>/loyalty_programs', methods=['GET'])
def loyalty_programs(center_id):
    return f'get loyalty programs for fitness center with id {center_id}'


if __name__ == '__main__':
    app.run(debug=True)

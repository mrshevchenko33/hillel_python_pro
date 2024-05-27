from flask import Flask, request, render_template, session
import sqlite3

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)
import sqlite3


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


@app.route('/', methods=['GET'])
def index():
    return 'Welcome to the homepage!'


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
            return 'successful login'
        else:
            return 'Incorrect login or password'

    else:
        return render_template('login.html')


@app.route('/user', methods=['GET'])
def get_users():
    with SQLiteDatabase('DB.db') as db:
        res = db.select_method("user")
    return render_template('users_info.html', users=res)


@app.route('/user/<user_id>', methods=['GET', 'POST', 'PUT'])
def get_user(user_id):
    if request.method == 'POST':
        return 'user data modified'
    elif request.method == 'PUT':
        return 'user info successfully updated'
    else:
        with SQLiteDatabase('DB.db') as db:
            res = db.select_method("user", {"id": user_id}, fetch_all=False)
        return render_template('user_info.html', user=res)


@app.route('/funds/<int:user_id>', methods=['GET', 'POST'])
def get_funds(user_id):
    if request.method == 'POST':
        return 'user account was successfully funded'
    else:
        with SQLiteDatabase('DB.db') as db:
            res = db.select_method("user", {"id": user_id}, columns=['funds'], fetch_all=False)
            return res


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


@app.route('/fitness_center/<gym_id>/trainer/<trainer_id>/rating', methods=['GET', 'POST', 'PUT'])
def trainer_rating(gym_id, trainer_id):
    if request.method == 'POST':
        user_id = session.get('user_id')
        rating = request.form.get('rating')
        review_text = request.form.get('review')
        with SQLiteDatabase('DB.db') as db:
            db.commit("review",
                      {'trainer_id': trainer_id, 'gym_id': gym_id, 'user_id': user_id, 'points': rating,
                       'text': review_text})
    elif request.method == 'PUT':
        return f'Review of {trainer_id} in {gym_id} has been edited'

    with SQLiteDatabase('DB.db') as db:
        users = db.select_method("user", fetch_all=True)
        reviews = db.select_method("review",
                                   join={'trainer': 'review.trainer_id = trainer.id',
                                         'gym': 'review.gym_id = gym.id',
                                         'user': 'review.user_id = user.id'},
                                   columns=['review.text', 'review.points', 'user.login', 'gym.name AS gym_name',
                                            'trainer.name AS trainer_name'],
                                   fetch_all=True)
    return render_template('trainer_rating.html', reviews=reviews, users=users)


@app.route('/user/reservations', methods=['GET', 'POST'])
def user_reservations():
    if request.method == 'GET':
        with SQLiteDatabase('DB.db') as db:
            reservations = db.select_method("reservation", join={'user': 'reservation.user_id = user.id',
                                                                 'service': 'reservation.service_id = service.id'},
                                            columns=['reservation.id AS reservation_id', 'reservation.date',
                                                     'reservation.time', 'user.login AS user_name',
                                                     'service.name AS service_name'])
            return render_template('reservations.html', reservations=reservations)
    elif request.method == 'POST':
        return 'create user reservation'


@app.route('/user/reservations/<reservation_id>', methods=['GET', 'PUT', 'DELETE'])
def user_reservation(reservation_id):
    if request.method == 'GET':
        with SQLiteDatabase('DB.db') as db:
            reservation = db.select_method("reservation", {'reservation_id': reservation_id},
                                           join={'user': 'reservation.user_id = user.id',
                                                 'service': 'reservation.service_id = service.id'},
                                           columns=['reservation.id AS reservation_id', 'reservation.date',
                                                    'reservation.time', 'user.login AS user_name',
                                                    'service.name AS service_name'], fetch_all=False)
            if reservation:
                return render_template('reservations.html', reservation=reservation)
            else:
                return f'Reservation with ID {reservation_id} not found'
    elif request.method == 'PUT':
        return f'Update reservation with ID {reservation_id}'
    elif request.method == 'DELETE':
        return f'Delete reservation with ID {reservation_id}'


@app.route('/user/checkout', methods=['GET', 'POST', 'PUT'])
def user_checkout():
    if request.method == 'GET':
        return 'get user checkout information'
    elif request.method == 'POST':
        return 'create user checkout'
    elif request.method == 'PUT':
        return 'update user checkout'


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

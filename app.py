from flask import Flask, request
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

    def fetch_all(self, query, *args, **kwargs):
        cursor = self.connection.cursor()
        cursor.execute(query, *args, **kwargs)
        res = cursor.fetchall()
        if res:
            return res
        return None

    def fetch_one(self, query, *args, **kwargs):
        cursor = self.connection.cursor()
        cursor.execute(query, *args, **kwargs)
        res = cursor.fetchone()
        if res:
            return res
        return None

    def commit(self, query, *args, **kwargs):
        cursor = self.connection.cursor()
        cursor.execute(query, *args, **kwargs)
        self.connection.commit()


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


@app.route('/', methods=['GET'])
def index():
    return 'Welcome to the homepage!'

@app.route('/register', methods=['GET', 'POST'])
def get_register():
    if request.method == 'POST':
        form_data = request.form
        with SQLiteDatabase('DB.db') as db:
            db.commit("INSERT INTO user (login, password, birth_date, phone) VALUES (?, ?, ?, ?)",
                      (form_data['login'], form_data['password'], form_data['birth_date'], form_data['phone']))
        return 'User registered'
    else:
        return f"""<form action='/register' method='POST'>
  <label for="login">login:</label><br>
  <input type="text" id="login" name="login"><br>
  <label for="password">password:</label><br>
  <input type="password" id="password" name="password">
  <label for="birth_date">birth_date:</label><br>
  <input type="date" id="birth_date" name="birth_date">
  <label for="phone">phone:</label><br>
  <input type="text" id="phone" name="phone">
  
  <input type="submit" value="Submit">
</form>"""

def check_credentials(username, password):
    conn = sqlite3.connect('DB.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user WHERE login = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()
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
        return """<form action='/login' method='POST'>
          <label for="login">login:</label><br>
          <input type="text" id="login" name="login"><br>
          <label for="password">password:</label><br>
          <input type="password" id="password" name="password">
          <input type="submit" value="enter">
        </form>"""
@app.route('/user', methods=['GET', 'POST', 'PUT'])
def get_user():
    if request.method == 'POST':
        return 'user data modified'
    elif request.method == 'PUT':
        return 'user info successfully updated'
    else:
        with SQLiteDatabase('DB.db') as db:
            res = db.fetch_one('SELECT login, phone, birth_date FROM user WHERE id=?', (1,))
        return str(res)



@app.route('/funds', methods=['GET', 'POST'])
def get_funds():
    if request.method == 'POST':
        return 'user account was successfully funded'
    else:
        with SQLiteDatabase('DB.db') as db:
            res = db.fetch_one('SELECT funds FROM user WHERE id=?', (1,))
        return res

@app.route('/fitness_center/<int:gym_id>/services', methods=['GET'])
def get_services(gym_id):
    with SQLiteDatabase('DB.db') as db:
        res = db.fetch_all('SELECT * FROM service WHERE gym_id = ?', (gym_id,))
        return res


@app.route('/fitness_center/<int:gym_id>/services/<int:service_id>', methods=['GET'])
def service_info(gym_id, service_id):
    with SQLiteDatabase('DB.db') as db:
        res = db.fetch_one('SELECT * FROM service WHERE gym_id = ? AND id = ?', (gym_id, service_id))
        if res is not None:
            return res
        else:
            return "Service not found"
@app.route('/fitness_center/<gym_id>/trainer', methods=['GET'])
def get_trainer(gym_id):
    with SQLiteDatabase('DB.db') as db:
        res = db.fetch_all('SELECT * FROM trainer WHERE gym_id = ?', (gym_id,))
        return res

@app.route('/fitness_center/<gym_id>/trainer/<trainer_id>', methods=['GET'])
def trainer_info(gym_id, trainer_id):
    with SQLiteDatabase('DB.db') as db:
        res = db.fetch_one('SELECT * FROM trainer WHERE gym_id = ? AND id = ?', (gym_id, trainer_id))
        if res is not None:
            return res
        else:
            return "Trainer not found"

@app.route('/fitness_center/<gym_id>/trainer/<trainer_id>/rating', methods=['GET','POST', 'PUT'])
def trainer_rating(gym_id, trainer_id):
    if request.method == 'POST':
        return f'review of {trainer_id} in {gym_id} has been added'
    elif request.method == 'PUT':
        return f'review of {trainer_id} in {gym_id} has been edited'
    else:
        with SQLiteDatabase('DB.db') as db:
            res = db.fetch_one('SELECT * FROM review WHERE gym_id = ? AND trainer_id = ?', (gym_id, trainer_id))
            if res is not None:
                return res
            else:
                return "rating not found"

@app.route('/user/reservations', methods=['GET', 'POST'])
def user_reservations():
    if request.method == 'GET':
        with SQLiteDatabase('DB.db') as db:
            res = db.fetch_all('SELECT * FROM reservation WHERE user_id = ?', (1,))
            return res
    elif request.method == 'POST':
        return 'create user reservation'

@app.route('/user/reservations/<reservation_id>', methods=['GET', 'PUT', 'DELETE'])
def user_reservation(reservation_id):
    if request.method == 'GET':
        with SQLiteDatabase('DB.db') as db:
            res = db.fetch_one('SELECT * FROM reservation WHERE id = ?', (reservation_id,))
            return res
    elif request.method == 'PUT':
        return f'update reservation with id {reservation_id}'
    elif request.method == 'DELETE':
        return f'delete reservation with id {reservation_id}'

@app.route('/user/checkout', methods=['GET', 'POST', 'PUT'])
def user_checkout():
    if request.method == 'GET':
        return 'get user checkout information'
    elif request.method == 'POST':
        return 'create user checkout'
    elif request.method == 'PUT':
        return 'update user checkout'

@app.route('/fitness_centers', methods=['GET'])
def fitness_centers():
    with SQLiteDatabase('DB.db') as db:
        res = db.fetch_all('SELECT * FROM gym')
        return res

@app.route('/fitness_center/<int:center_id>', methods=['GET'])
def fitness_center(center_id):
    with SQLiteDatabase('DB.db') as db:
        res = db.fetch_one('SELECT * FROM gym WHERE id = ?', (center_id,))
        if res is not None:
            return res
        else:
            return "Center not found"



@app.route('/fitness_center/<center_id>/loyalty_programs', methods=['GET'])
def loyalty_programs(center_id):
    return f'get loyalty programs for fitness center with id {center_id}'

if __name__ == '__main__':
    app.run(debug=True)

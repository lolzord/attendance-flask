from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash
from datetime import datetime
from flask_mysqldb import MySQL
from flask_login import LoginManager, logout_user, login_required, UserMixin
import MySQLdb.cursors
import pytz

malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
malaysia_time = datetime.now(malaysia_tz)

selected_email = None

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Configuration
app.config['MYSQL_HOST'] = 'rfidattendance-server.mysql.database.azure.com'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'rfidattendanceadmin@rfidattendance-server'
app.config['MYSQL_PASSWORD'] = 'your_password'
app.config['MYSQL_DB'] = 'RFIDAttendanceDB'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

app.secret_key = 'XAbxaKXbLpB2ZwnLw8-ABA'
mysql = MySQL(app)

@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM employees WHERE id = %s", [user_id])
    user = cursor.fetchone()
    cursor.close()
    if user:
        return User(id=user['id'], email=user['email'], password=user['password'])
    else:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

class User(UserMixin):
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password

@app.route('/capture_card')
def capture_card():
    global selected_email
    card_id = request.args.get('id')
    if not card_id or not selected_email:
        return jsonify({'error': 'No card ID or email provided'}), 400

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE employees SET card_id = %s WHERE email = %s", (card_id, selected_email))
        mysql.connection.commit()
        cursor.close()
        return redirect('/dashboard')
    except Exception as e:
        return jsonify({'error': 'Database update failed', 'message': str(e)}), 500

@app.route('/select_user', methods=['GET', 'POST'])
def select_user():
    if request.method == 'POST':
        email = request.form.get('email')
        card_id = request.form.get('card_id')

        try:
            cursor = mysql.connection.cursor()
            cursor.execute("UPDATE employees SET card_id = %s WHERE email = %s", (card_id, email))
            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('dashboard'))
        except Exception as e:
            return jsonify({'error': 'Database update failed', 'message': str(e)}), 500
    else:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT email FROM employees")
        emails = [item['email'] for item in cursor.fetchall()]
        cursor.close()
        return render_template('select_user.html', emails=emails)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM employees WHERE email = %s", [email])
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['is_admin'] = user['is_admin']
            session['email'] = email
            return redirect(url_for('dashboard'))
        else:
            return "Invalid email or password"
    else:
        return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    if session.get('is_admin'):
        cursor.execute("SELECT employees.name, attendance.in_time, attendance.out_time, attendance.working_hours, attendance.subject FROM employees JOIN attendance ON employees.id = attendance.employee_id")
    else:
        cursor.execute("SELECT employees.name, attendance.in_time, attendance.out_time, attendance.working_hours, attendance.subject FROM employees JOIN attendance ON employees.id = attendance.employee_id WHERE employees.email = %s", [session['email']])

    attendance_records = cursor.fetchall()
    cursor.execute("SELECT employees.name, employees.email, employees.card_id FROM employees")
    employees = cursor.fetchall()
    cursor.execute("SELECT start_time, end_time, subject FROM timetable ORDER BY start_time")
    timetable = [{"start_time": str(row['start_time']), "end_time": str(row['end_time']), "subject": row['subject']} for row in cursor.fetchall()]

    cursor.close()

    show_tabs = session.get('is_admin', False)

    return render_template('dashboard.html', attendance_records=attendance_records, employees=employees, timetable=timetable, show_tabs=show_tabs)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

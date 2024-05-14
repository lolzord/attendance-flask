import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
from datetime import datetime
import pytz

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Set the connection string to SQLALCHEMY_DATABASE_URI from environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app.secret_key = 'XAbxaKXbLpB2ZwnLw8-ABA'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    card_id = db.Column(db.String(255))
    token = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/capture_card')
def capture_card():
    global selected_email
    card_id = request.args.get('id')
    if not card_id or not selected_email:
        return jsonify({'error': 'No card ID or email provided'}), 400

    try:
        user = User.query.filter_by(email=selected_email).first()
        if user:
            user.card_id = card_id
            db.session.commit()
            return redirect('/dashboard')
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': 'Database update failed', 'message': str(e)}), 500

@app.route('/select_user', methods=['GET', 'POST'])
def select_user():
    if request.method == 'POST':
        email = request.form.get('email')
        card_id = request.form.get('card_id')

        try:
            user = User.query.filter_by(email=email).first()
            if user:
                user.card_id = card_id
                db.session.commit()
                return redirect(url_for('dashboard'))
            else:
                return jsonify({'error': 'User not found'}), 404
        except Exception as e:
            return jsonify({'error': 'Database update failed', 'message': str(e)}), 500
    else:
        users = User.query.with_entities(User.email).all()
        emails = [user.email for user in users]
        return render_template('select_user.html', emails=emails)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['logged_in'] = True
            session['is_admin'] = user.is_admin
            session['email'] = email
            return redirect(url_for('dashboard'))
        else:
            return "Invalid email or password"
    else:
        return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('is_admin'):
        attendance_records = db.session.query(
            User.name, Attendance.in_time, Attendance.out_time, Attendance.working_hours, Attendance.subject
        ).join(Attendance, User.id == Attendance.employee_id).all()
    else:
        attendance_records = db.session.query(
            User.name, Attendance.in_time, Attendance.out_time, Attendance.working_hours, Attendance.subject
        ).join(Attendance, User.id == Attendance.employee_id).filter(User.email == session['email']).all()

    employees = User.query.with_entities(User.name, User.email, User.card_id).all()
    timetable = Timetable.query.with_entities(Timetable.start_time, Timetable.end_time, Timetable.subject).order_by(Timetable.start_time).all()
    
    return render_template('dashboard.html', attendance_records=attendance_records, employees=employees, timetable=timetable, show_tabs=session.get('is_admin', False))

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    in_time = db.Column(db.DateTime)
    out_time = db.Column(db.DateTime)
    working_hours = db.Column(db.Float)
    subject = db.Column(db.String(255))

class Timetable(db.Model):
    __tablename__ = 'timetable'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    subject = db.Column(db.String(255))

@app.route('/test_db_connection')
def test_db_connection():
    try:
        result = db.engine.execute("SELECT DB_NAME() AS [Current Database]")
        db_name = result.fetchone()[0]
        return f"Connected to database: {db_name}"
    except Exception as e:
        return f"Failed to connect to database: {e}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

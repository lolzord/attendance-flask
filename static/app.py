from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash
from datetime import datetime
from flask_mysqldb import MySQL
from flask_login import LoginManager
from flask_login import logout_user
from flask_login import login_required
import MySQLdb.cursors
import pytz

malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')  # Add this line
malaysia_time = datetime.now(malaysia_tz)  # Add this line

selected_email = None


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = ''
# app.config['MYSQL_DB'] = 'attendance_system'
# app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

app.config['MYSQL_DATABASE_HOST'] = 'rfidattendance-server.database.windows.net'
app.config['MYSQL_DATABASE_PORT'] = 1433
app.config['MYSQL_DATABASE_USER'] = 'rfidattendanceadmin'
app.config['MYSQL_DATABASE_PASSWORD'] = '{your_password}'
app.config['MYSQL_DATABASE_DB'] = 'RFIDAttendanceDB'

app.secret_key = 'XAbxaKXbLpB2ZwnLw8-ABA'
mysql = MySQL(app)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password

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
        return redirect('/dashboard')  # Redirect to the dashboard page
    except Exception as e:
        return jsonify({'error': 'Database update failed', 'message': str(e)}), 500

# @app.route('/capture_card')
# def capture_card():
#     card_id = request.args.get('id')
#     selected_email = session.get('selected_email', None)  # Default to None if not set
    
#     app.logger.debug(f"Card ID: {card_id}, Selected Email from session: {selected_email}")  # Debug print

#     if not card_id or not selected_email:
#         app.logger.error("Error: No card ID or email provided")  # Logging the error
#         flash('No card ID or email provided')
#         return redirect(url_for('select_user'))

#     try:
#         cursor = mysql.connection.cursor()
#         cursor.execute("UPDATE employees SET card_id = %s WHERE email = %s", (card_id, selected_email))
#         mysql.connection.commit()
#         cursor.close()
#         session.pop('selected_email', None)  # Clear the selected email from the session
#         flash('Card ID captured successfully')
#         return redirect(url_for('dashboard'))
#     except Exception as e:
#         app.logger.error(f"Database operation failed: {e}")  # Logging the error
#         flash('Database operation failed')
#         return redirect(url_for('error', message=str(e)))



   
@app.route('/select_user', methods=['GET', 'POST'])
def select_user():
    if request.method == 'POST':
        email = request.form.get('email')  # Get selected email from form data
        card_id = request.form.get('card_id')  # Get card_id from form data

        try:
            cursor = mysql.connection.cursor()
            cursor.execute("UPDATE employees SET card_id = %s WHERE email = %s", (card_id, email))
            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('dashboard'))  # Redirect to the dashboard route
        except Exception as e:
            return jsonify({'error': 'Database update failed', 'message': str(e)}), 500
    else:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT email FROM employees")
        emails = [item[0] for item in cursor.fetchall()]
        cursor.close()
        return render_template('select_user.html', emails=emails)  # Pass the emails to the template
    
# @app.route('/select_user', methods=['GET', 'POST'])
# def select_user():
#     if request.method == 'POST':
#         selected_email = request.form.get('email')  # Retrieve the selected email from the form
#         if selected_email:
#             session['selected_email'] = selected_email  # Store it in session
#             flash('User selected successfully.')
#             return redirect(url_for('capture_card'))  # Redirect to dashboard or another appropriate route
#         else:
#             flash('No email selected. Please select an email.')
#             return redirect(url_for('select_user'))
#     else:
#         cursor = mysql.connection.cursor()
#         cursor.execute("SELECT email FROM employees")
#         emails = [item[0] for item in cursor.fetchall()]
#         cursor.close()
#         return render_template('select_user.html', emails=emails)



@app.route('/success', methods=['GET', 'POST'])
def success():
    if request.method == 'POST':
        card_id = request.form.get('card_id')  # Get card_id from form data

        # ... rest of your logic here ...

    else:
        return render_template('success.html')  # Render a form for inputting card_id

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if request.method == 'POST':
        card_id = request.form.get('card_id')
        subject = request.form.get('subject')

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO attendance (card_id, subject, timestamp) VALUES (%s, %s, %s)", (card_id, subject, datetime.now()))
        mysql.connection.commit()
        cur.close()

        return jsonify({'message': 'Attendance marked successfully.'})
    else:
        return render_template('attendance.html')

from flask import render_template
from flask_mysqldb import MySQL

from flask_login import current_user

from functools import wraps
from flask import session, redirect, url_for, request

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/protected_route')
@login_required
def protected_route():
    return "You are logged in!"

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
            session['is_admin'] = user['is_admin']  # Store the is_admin field in the session
            session['email'] = email  # Store the email in the session
            return redirect(url_for('dashboard'))
        else:
            return "Invalid email or password"
    else:
        return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    # Fetch attendance records with working_hours and subject
    if session.get('is_admin'):
        # If the user is an admin, fetch all attendance records
        cursor.execute("SELECT employees.name, attendance.in_time, attendance.out_time, attendance.working_hours, attendance.subject FROM employees JOIN attendance ON employees.id = attendance.employee_id")
    else:
        # If the user is not an admin, fetch only their attendance records
        cursor.execute("SELECT employees.name, attendance.in_time, attendance.out_time, attendance.working_hours, attendance.subject FROM employees JOIN attendance ON employees.id = attendance.employee_id WHERE employees.email = %s", [session['email']])

    attendance_records = cursor.fetchall()

    # Fetch user data
    cursor.execute("SELECT employees.name, employees.email, employees.card_id FROM employees")
    employees = cursor.fetchall()

    # Fetch timetable data
    cursor.execute("SELECT start_time, end_time, subject FROM timetable ORDER BY start_time")
    timetable = [{"start_time": str(row[0]), "end_time": str(row[1]), "subject": row[2]} for row in cursor.fetchall()]

    # Initialize timetable_data as an empty list
    timetable_data = []

    # Fetch timetable data again for the new integration
    result_value = cursor.execute("SELECT * FROM timetable")
    if result_value > 0:
        timetable_data = cursor.fetchall()

    cursor.close()

    # Check if the user is an admin
    if session.get('is_admin'):
        show_tabs = True
    else:
        show_tabs = False

    return render_template('dashboard.html', attendance_records=attendance_records, employees=employees, timetable=timetable, show_tabs=show_tabs, timetable_data=timetable_data)

# Make sure to implement the logout functionality as well
# @app.route('/logout')
# def logout():
#     session.pop('logged_in', None)
#     return redirect(url_for('login'))


@app.route('/register_card', methods=['POST'])
def register_card():
    email = request.form['email']
    card_id = request.form['card_id']

    cur = mysql.connection.cursor()
    cur.execute("UPDATE employees SET card_id = %s WHERE email = %s", (card_id, email))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('dashboard'))  # replace 'dashboard' with the name of your view function for the homepage


@app.route('/register_employee')
def register_employee():
    return render_template('register_employee.html')

from werkzeug.security import generate_password_hash

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)  # Hash the password

        try:
            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO employees (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('dashboard'))  # Redirect to the dashboard route
        except Exception as e:
            return jsonify({'error': 'Database insert failed', 'message': str(e)}), 500
    else:
        return render_template('register.html')

@app.route('/get_attendance')
def get_attendance():
    try:
        cursor = mysql.connection.cursor()
        # Fetch attendance records from the database
        cursor.execute("SELECT * FROM attendances")
        records = cursor.fetchall()
        cursor.close()
        # Pass these records to the attendance template
        return render_template('attendance.html', records=records)
    except Exception as e:
        return jsonify({'error': 'Failed to fetch records', 'message': str(e)}), 500

@app.route('/select_user_attendance', methods=['GET', 'POST'])
def select_user_attendance():
    global selected_email
    if request.method == 'POST':
        selected_email = request.form.get('email')
        return redirect('/success_attendance')
    else:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT email FROM employees")
        emails = [item[0] for item in cursor.fetchall()]
        cursor.close()
        return render_template('select_user_attendance.html', emails=emails)

@app.route('/success_attendance')
def success_attendance():
    return render_template('success_attendance.html')

@app.route('/capture_attendance', methods=['GET', 'POST'])
def capture_attendance():
    if request.method == 'POST':
        selected_email = request.form.get('email')
        scanned_card_id = request.args.get('id')
        if not scanned_card_id or not selected_email:
            return redirect('/error?message=No card ID or email provided')

        try:
            cursor = mysql.connection.cursor()
            # Get the current date and time
            from datetime import datetime
            current_time = datetime.now()
            # Get the employee_id and card_id for the selected email
            cursor.execute("SELECT id, card_id FROM employees WHERE email = %s", [selected_email])
            result = cursor.fetchone()
            if result is None:
                return redirect('/error?message=No user associated with this email')
            employee_id, card_id = result
            # Check if the scanned card_id matches the card_id in the database
            if card_id != scanned_card_id:
                return redirect('/error?message=Scanned card ID does not match the card ID associated with this email')
            # Record the in-time for the selected user
            cursor.execute("INSERT INTO attendances (employee_id, date, in_time) VALUES (%s, %s, %s)", (employee_id, current_time.date(), current_time.time()))
            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('dashboard', message='Attendance recorded successfully'))
        except Exception as e:
            return redirect('/error?message=Database update failed')

    try:
        cursor = mysql.connection.cursor()
        # Get the current date and time
        from datetime import datetime
        current_time = datetime.now()
        # Get the employee_id and card_id for the selected email
        cursor.execute("SELECT id, card_id FROM employees WHERE email = %s", [selected_email])
        result = cursor.fetchone()
        if result is None:
            return redirect('/error?message=No user associated with this email')
        employee_id, card_id = result
        # Check if the scanned card_id matches the card_id in the database
        if card_id != scanned_card_id:
            return redirect('/error?message=Scanned card ID does not match the card ID associated with this email')
        # Record the in-time for the selected user
        cursor.execute("INSERT INTO attendances (employee_id, date, in_time) VALUES (%s, %s, %s)", (employee_id, current_time.date(), current_time.time()))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('dashboard', message='Attendance recorded successfully'))
    except Exception as e:
        return redirect('/error?message=Database update failed')

@app.route('/error')
def error():
    message = request.args.get('message')
    return render_template('error.html', message=message)

# class Timetable:
#     def __init__(self):
#         self.subjects = []

#     def register_subject(self, start_time, end_time, subject):
#         self.subjects.append({
#             'start_time': datetime.strptime(start_time, "%H:%M").time(),
#             'end_time': datetime.strptime(end_time, "%H:%M").time(),
#             'subject': subject
#         })

#     def get_subject(self, current_time):
#         current_time = datetime.strptime(current_time, "%H:%M").time()
#         for subject in self.subjects:
#             if subject['start_time'] <= current_time <= subject['end_time']:
#                 return subject['subject']
#         return None

#     def get_subjects(self):
#         return self.subjects

class Timetable:
    def __init__(self):
        self.subjects = []

    def register_subject(self, start_time, end_time, subject):
        self.subjects.append({
            'start_time': datetime.strptime(start_time, "%H:%M").time(),
            'end_time': datetime.strptime(end_time, "%H:%M").time(),
            'subject': subject
        })

    def get_subject(self, current_time):
        current_time = datetime.strptime(current_time, "%H:%M").time()
        for subject in self.subjects:
            if subject['start_time'] <= current_time <= subject['end_time']:
                return subject['subject']
        return None

    def get_subjects(self):
        return self.subjects

# Initialize the timetable
from datetime import datetime

# Create an instance of Timetable
timetable = Timetable()

# Register some subjects
# timetable.register_subject("09:00", "11:00", "Math")
# timetable.register_subject("00:00", "23:59", "English")

# Get the current subject
current_subject = timetable.get_subject(datetime.now().strftime("%H:%M"))

if current_subject:
    print(f"The current subject is {current_subject}")
else:
    print("There is no subject at this time")

from datetime import datetime

from flask import Flask, redirect, url_for
from flask_mysqldb import MySQL

def reset_timetable():
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM timetable")
    mysql.connection.commit()
    timetable.subjects.clear()

@app.route('/reset_timetable', methods=['POST'])
def reset_timetable_route():
    reset_timetable()
    return redirect(url_for('dashboard'))

@app.route('/register_subject', methods=['POST'])
def register_subject():
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    subject = request.form['subject']

    # Convert the start_time and end_time to the correct format
    start_time = datetime.strptime(start_time, "%H:%M").strftime("%H:%M")
    end_time = datetime.strptime(end_time, "%H:%M").strftime("%H:%M")

    # Register the subject in the timetable instance
    timetable.register_subject(start_time, end_time, subject)

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO timetable(start_time, end_time, subject) VALUES(%s, %s, %s)", (start_time, end_time, subject))
    mysql.connection.commit()

    return redirect(url_for('dashboard'))

# @app.route('/get_timetable', methods=['GET'])
# def get_timetable():
#     try:
#         cursor = mysql.connection.cursor()
#         cursor.execute("SELECT start_time, end_time, subject FROM timetable")
#         timetable = [{"start_time": str(row[0]), "end_time": str(row[1]), "subject": row[2]} for row in cursor.fetchall()]
#         return jsonify(timetable), 200
#     except Exception as e:
#         return jsonify({'message': 'An error occurred while fetching the timetable: ' + str(e)}), 500

# @app.route('/update_timetable', methods=['POST'])
# def update_timetable():
#     try:
#         # Get the new data from the request
#         data = request.form
#         start_time = data.get('start_time')
#         end_time = data.get('end_time')
#         subject = data.get('subject')
#         slot_id = data.get('slot_id')  # Retrieve the slot_id from the request data

#         if not start_time or not end_time or not subject:
#             return jsonify({'message': 'Invalid input'}), 400

#         # Update the subject in the timetable
#         cursor = mysql.connection.cursor()
        
#         cursor.execute("UPDATE timetable SET start_time = %s, end_time = %s, subject = %s WHERE slot_id = %s",
#                        (start_time, end_time, subject, slot_id))
#         mysql.connection.commit()
#         cursor.close()

#         # Update the timetable in memory
#         timetable.register_subject(start_time, end_time, subject)

#         return jsonify({'message': 'Timetable updated successfully'}), 200
#     except Exception as e:
#         return jsonify({'message': 'An error occurred while updating the timetable: ' + str(e)}), 500
    
# @app.route('/register_subject', methods=['POST'])
# def register_subject():
#     start_time = request.form.get('start_time')
#     end_time = request.form.get('end_time')
#     subject = request.form.get('subject')

#     timetable = Timetable()
#     timetable.register_subject(start_time, end_time, subject)

#     return redirect(url_for('dashboard'))

@app.route('/record_attendance', methods=['GET', 'POST'])
def record_attendance():
    if request.method == 'POST':
        card_id = request.json.get('card_id')
        subject = request.json.get('subject')
    else:
        card_id = request.args.get('id', '')
        subject = request.args.get('subject', None)  # Get the subject from the GET parameters

        if not subject:  # If subject is not provided in the GET parameters, get it from the timetable
            in_time = datetime.now().strftime("%H:%M")
            subject = timetable.get_subject(in_time)

        if not subject:  # If get_subject returned None, provide a default subject
            subject = "Default Subject"

        if not card_id:
            return render_template('attendance.html', id_value=card_id)

    # Continue with the rest of the function...

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, name FROM employees WHERE card_id = %s", (card_id,))
    employee = cursor.fetchone()

    if employee:
        employee_id, employee_name = employee
        cursor.execute("SELECT id, in_time FROM attendance WHERE employee_id = %s AND out_time IS NULL", (employee_id,))
        attendance_record = cursor.fetchone()

        if attendance_record:
            # Employee is clocking out
            out_time = datetime.now()
            attendance_id, in_time = attendance_record
            working_hours = (out_time - in_time).total_seconds()  # Calculate working hours
            cursor.execute("UPDATE attendance SET out_time = %s, working_hours = %s WHERE id = %s", (out_time, working_hours, attendance_id))
            response_message = f"Goodbye, {employee_name}. Your out-time and working hours have been recorded."
        else:
            # Employee is clocking in
            in_time = datetime.now()
            if not subject:  # If subject is not provided in the GET parameters, get it from the timetable
                subject = timetable.get_subject(in_time.strftime("%H:%M"))
            cursor.execute("INSERT INTO attendance (employee_id, in_time, subject) VALUES (%s, %s, %s)", (employee_id, in_time, subject))
            response_message = f"Welcome, {employee_name}. Your in-time has been recorded for {subject}."

        mysql.connection.commit()
        cursor.close()
        return jsonify({'message': response_message}), 200
    else:
        return jsonify({'error': 'Invalid card ID'}), 404

@app.route('/set_subject', methods=['POST'])
def set_subject():
    # Store the subject in a session variable
    session['subject'] = request.form.get('subject')
    return jsonify({'message': 'Subject set successfully'}), 200

from flask import jsonify

@app.route('/get_subjects')
def get_subjects():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT subject_name FROM subjects")
    subjects = [row[0] for row in cursor.fetchall()]
    return jsonify(subjects)

# @app.route('/get_timetable')
# def get_timetable():
#     cursor = mysql.connection.cursor()
#     cursor.execute("SELECT start_time, end_time, subject FROM timetable")
#     timetable = [{"start_time": str(row[0]), "end_time": str(row[1]), "subject": row[2]} for row in cursor.fetchall()]
#     return jsonify(timetable)

# @app.route('/update_timetable', methods=['POST'])
# def update_timetable():
#     start_time = request.form.get('start_time')
#     end_time = request.form.get('end_time')
#     subject = request.form.get('subject')
#     slot_id = request.form.get('slot_id')

#     if not start_time or not end_time or not subject or not slot_id:
#         return jsonify({'message': 'Invalid input'}), 400

#     try:
#         cursor = mysql.connection.cursor()
#         cursor.execute("UPDATE timetable SET start_time = %s, end_time = %s, subject = %s WHERE id = %s",
#                        (start_time, end_time, subject, slot_id))
#         mysql.connection.commit()
#         cursor.close()
#         return jsonify({'message': 'Timetable updated successfully'}), 200
#     except Exception as e:
#         return jsonify({'message': 'An error occurred while updating the timetable: ' + str(e)}), 500





if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')


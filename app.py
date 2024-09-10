from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import threading

app = Flask(__name__)
app.secret_key = 'ertyu0987654578900987654edvjkljhgfcvbnm'

# Function to get a new database connection
def get_new_connection():
    return sqlite3.connect('library_database.db')

# Initialize the SQLite database connection for each thread
def get_db():
    if not hasattr(threading.current_thread(), 'library_db_connection'):
        threading.current_thread().library_db_connection = get_new_connection()
    return threading.current_thread().library_db_connection

# Close the database connection at the end of each request
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(threading.current_thread(), 'library_db_connection', None)
    if db is not None:
        db.close()

# Create tables if they do not exist
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS images (
                            study_room TEXT PRIMARY KEY,
                            image BLOB
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS seat_utilization (
                            study_room TEXT PRIMARY KEY,
                            vacant_seats INTEGER,
                            total_seats INTEGER
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            username TEXT PRIMARY KEY,
                            password TEXT
                          )''')
        db.commit()

# Initialize the SQLite database
init_db()

# Routes

@app.route('/')
def index():
    if 'username' in session:
        # Fetch data from the database
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users")  
        data = cursor.fetchall()

        # Pass fetched data to the template
        return render_template('index.html', username=session['username'], data=data)
    else:
        return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
       
        return render_template('dashboard.html', username=session['username'])
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_user(username, password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        insert_user(username, password)
        return redirect(url_for('login'))
    else:
        return render_template('register.html')

@app.route('/seats')
def seats():
    if 'username' in session:
        study_rooms, total_seats = get_seat_info()
        return render_template('seats.html', username=session['username'], study_rooms=study_rooms, total_seats=total_seats)
    else:
        return redirect(url_for('login'))

@app.route('/reserve_seat', methods=['POST'])
def reserve_seat():
    if 'username' in session:
        study_room = request.form['study_room']
        
        return jsonify({'message': 'Seat reserved successfully'})
    else:
        return jsonify({'error': 'User not logged in'}), 401

@app.route('/admin')
def admin():
    if 'username' in session:
        seat_utilization = get_seat_utilization()
        return render_template('admin.html', username=session['username'], seat_utilization=seat_utilization)
    else:
        return redirect(url_for('login'))

@app.route('/delete_seat', methods=['POST'])
def delete_seat():
    if 'username' in session:
        study_room = request.form['study_room']
      
        return jsonify({'message': 'Seat deleted successfully'})
    else:
        return jsonify({'error': 'User not logged in'}), 401

# Database Functions

def insert_image(study_room, image_data):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO images (study_room, image) VALUES (?, ?)", (study_room, image_data))
    db.commit()

def get_image(study_room):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT image FROM images WHERE study_room=?", (study_room,))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        return None

def insert_seat_utilization(study_room, vacant_seats, total_seats):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT OR REPLACE INTO seat_utilization (study_room, vacant_seats, total_seats) VALUES (?, ?, ?)", (study_room, vacant_seats, total_seats))
    db.commit()

def get_seat_utilization():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT study_room, vacant_seats, total_seats FROM seat_utilization")
    rows = cursor.fetchall()
    return rows

def insert_user(username, password):
    db = get_db()
    cursor = db.cursor()
    hashed_password = generate_password_hash(password)
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    db.commit()

def verify_user(username, password):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT password FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    if row:
        hashed_password = row[0]
        return check_password_hash(hashed_password, password)
    else:
        return False

def get_seat_info():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT study_room, total_seats FROM seat_utilization")
    rows = cursor.fetchall()
    study_rooms = [row[0] for row in rows]
    total_seats = {row[0]: row[1] for row in rows}
    return study_rooms, total_seats

if __name__ == '__main__':
    app.run(debug=True)

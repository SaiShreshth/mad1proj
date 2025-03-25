from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3,time
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'asd'

def init_db():
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY, 
                 username TEXT UNIQUE, 
                 password TEXT, 
                 role TEXT,
                 fname TEXT,
                 dob TEXT,
                 qualification TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS subject (
                 id INTEGER PRIMARY KEY, 
                 subject_name TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS chapter (
                 id INTEGER PRIMARY KEY, 
                 chapter_name TEXT, 
                 subject_id INTEGER,
                 FOREIGN KEY(subject_id) REFERENCES subject(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS quiz (
                 id INTEGER PRIMARY KEY,
                 subject_id INTEGER, 
                 quiz_name TEXT, 
                 quiz_date TEXT,
                 quiz_time TEXT,
                 quiz_duration TEXT,
                 FOREIGN KEY(subject_id) REFERENCES subject(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS questions (
                 id INTEGER PRIMARY KEY, 
                 quiz_id INTEGER, 
                 question_stat TEXT, 
                 option1 TEXT, 
                 option2 TEXT, 
                 option3 TEXT, 
                 option4 TEXT, 
                 correct_answer TEXT,
                 FOREIGN KEY(quiz_id) REFERENCES quiz(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS scores (
                 id INTEGER PRIMARY KEY, 
                 user_id INTEGER, 
                 quiz_id INTEGER, 
                 score INTEGER, 
                 date TEXT,
                 FOREIGN KEY(user_id) REFERENCES users(id),
                 FOREIGN KEY(quiz_id) REFERENCES quiz(id))''')

    
    # Create default admin if not exists
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                 ('s', 's', 'admin'))
    except sqlite3.IntegrityError:
        pass
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('quiz.db')
        c = conn.cursor()
        
        # Check if username exists
        c.execute("SELECT id, username, password, role FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user is None:
            print("❌ Login failed. Username does not exist.")
            flash('Error: Username does not exist.', 'danger')
        elif user[2] != password:  # Checking if password matches
            print("❌ Login failed. Incorrect password.")
            flash('Error: Incorrect password.', 'danger')
        else:
            session['user_id'] = user[0]  # user ID
            session['username'] = user[1]  # username
            session['role'] = user[3]  # admin/user
            print("✅ Login successful! Redirecting to dashboard...")
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
    print("❌ Login failed. Showing login page again.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('quiz.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, 'user'))
            conn.commit()
            conn.close()
            flash('Registration successful', 'success')
            print("✅ Registration successful. Redirecting to login page...")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            print("❌ Registration failed. Username already exists.")
            flash('Username already exists', 'danger')
        conn.close()
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("You must be logged in to view the dashboard.", "warning")
        print("❌Not logged in. Redirecting to login page...")
        return redirect(url_for('login'))
    conn=sqlite3.connect('quiz.db')
    c=conn.cursor()
    c.execute("SELECT * FROM scores WHERE user_id = ?", (session['user_id'],))
    return render_template('dashboard.html', username=session['username'])

@app.route('/edit_page')
def edit_page():
    if 'user_id' not in session or session['role'] != 'admin':
        flash("You must be logged in to view the dashboard.", "warning")
        print("❌Not logged in. Redirecting to login page...")
        return redirect(url_for('login'))
    conn=sqlite3.connect('quiz.db')
    c=conn.cursor()
    c.execute("SELECT * FROM questions")
    return render_template('edit_page.html', username=session['username'])

@app.route('/subsnchaps')
def subsnchaps():
    if 'user_id' not in session:
        flash("You must be logged in to view the dashboard.", "warning")
        print("❌Not logged in. Redirecting to login page...")
        return redirect(url_for('login'))
    conn=sqlite3.connect('quiz.db')
    c=conn.cursor()
    c.execute("SELECT * FROM questions")
    return render_template('subsnchaps.html', username=session['username'])

@app.route('/users')
def users():
    if 'user_id' not in session or session['role'] != 'admin':
        flash("You must be logged in to view the dashboard.", "warning")
        print("❌Not logged in. Redirecting to login page...")
        return redirect(url_for('login'))
    conn=sqlite3.connect('quiz.db')
    c=conn.cursor()
    c.execute("SELECT * FROM users")
    return render_template('users.html', username=session['username'])

@app.route('/summary')
def summary():
    if 'user_id' not in session:
        flash("You must be logged in to view the dashboard.", "warning")
        print("❌Not logged in. Redirecting to login page...")
        return redirect(url_for('login'))
    conn=sqlite3.connect('quiz.db')
    c=conn.cursor()
    c.execute("SELECT * FROM scores")
    return render_template('summary.html', username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    print("✅❌ Logged out successfully.")
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
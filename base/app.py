# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'asd'  # Change this to a secure key

# Database initialization
def init_db():
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS questions 
                 (id INTEGER PRIMARY KEY, subject TEXT, question TEXT, 
                 option1 TEXT, option2 TEXT, option3 TEXT, option4 TEXT, 
                 correct_answer TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (id INTEGER PRIMARY KEY, user_id INTEGER, subject TEXT, 
                 score INTEGER, date TEXT)''')
    
    # Create default admin if not exists
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                 ('admin', 'admin123', 'admin'))
    except sqlite3.IntegrityError:
        pass
    
    conn.commit()
    conn.close()

# Routes
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
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
                 (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('quiz.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                     (username, password, 'user'))
            conn.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists')
        conn.close()
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT subject FROM questions")
    subjects = [row[0] for row in c.fetchall()]
    conn.close()
    
    return render_template('dashboard.html', subjects=subjects)

@app.route('/quiz/<subject>')
def quiz(subject):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute("SELECT * FROM questions WHERE subject = ?", (subject,))
    questions = c.fetchall()
    conn.close()
    
    return render_template('quiz.html', questions=questions, subject=subject)

@app.route('/submit_quiz/<subject>', methods=['POST'])
def submit_quiz(subject):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    score = 0
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute("SELECT id, correct_answer FROM questions WHERE subject = ?", (subject,))
    questions = c.fetchall()
    
    for q_id, correct_answer in questions:
        user_answer = request.form.get(str(q_id))
        if user_answer == correct_answer:
            score += 1
    
    c.execute("INSERT INTO scores (user_id, subject, score, date) VALUES (?, ?, ?, ?)",
             (session['user_id'], subject, score, datetime.now().strftime('%Y-%m-%d')))
    conn.commit()
    conn.close()
    
    flash(f'Your score: {score}/{len(questions)}')
    return redirect(url_for('dashboard'))

@app.route('/admin/manage_questions', methods=['GET', 'POST'])
def manage_questions():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        if 'add' in request.form:
            conn = sqlite3.connect('quiz.db')
            c = conn.cursor()
            c.execute("""INSERT INTO questions 
                        (subject, question, option1, option2, option3, option4, correct_answer) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                     (request.form['subject'], request.form['question'],
                      request.form['option1'], request.form['option2'],
                      request.form['option3'], request.form['option4'],
                      request.form['correct_answer']))
            conn.commit()
            conn.close()
            flash('Question added successfully')
        
        elif 'delete' in request.form:
            conn = sqlite3.connect('quiz.db')
            c = conn.cursor()
            c.execute("DELETE FROM questions WHERE id = ?", (request.form['question_id'],))
            conn.commit()
            conn.close()
            flash('Question deleted successfully')
    
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute("SELECT * FROM questions")
    questions = c.fetchall()
    conn.close()
    
    return render_template('manage_questions.html', questions=questions)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

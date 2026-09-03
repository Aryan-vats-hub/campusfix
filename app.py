from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "campusfix_secret_key"
DB_NAME = "campusfix.db"
ADMIN_PASSWORD = "CampusHead"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            room TEXT,
            category TEXT,
            description TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def is_mobile(user_agent):
    if not user_agent:
        return False
    ua = user_agent.lower()
    return any(k in ua for k in ['mobile', 'android', 'iphone', 'ipad', 'phone'])

@app.route('/')
def home():
    user_agent = request.headers.get('User-Agent', '')
    if is_mobile(user_agent):
        return render_template('index.html')
    return redirect(url_for('admin_dashboard'))

@app.route('/submit', methods=['POST'])
def submit_complaint():
    name = request.form.get('name')
    room = request.form.get('room') or request.form.get('location') or 'Not Specified'
    category = request.form.get('category')
    description = request.form.get('description')
    created_at = datetime.now().strftime("%d %b %Y, %I:%M %p")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO complaints (name, room, category, description, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, room, category, description, created_at))
    complaint_id = cursor.lastrowid
    conn.commit()
    conn.close()

    flash(f"Complaint successfully register ! Your Complaint ID: #{complaint_id}", "success")
    return redirect(url_for('home'))

@app.route('/check-status', methods=['GET', 'POST'])
def check_status():
    complaint = None
    searched = False
    if request.method == 'POST':
        c_id = request.form.get('complaint_id')
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, room, category, description, status, created_at FROM complaints WHERE id = ?', (c_id,))
        complaint = cursor.fetchone()
        conn.close()

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        entered_pass = request.form.get('password')
        if entered_pass == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = "Invalid Security Key!"
    return render_template('login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))

        conn = sqlite3.connect(DB_NAME)
     cursor = conn.cursor()
     cursor.execute('SELECT id, name, room, category, description, status, created_at FROM complaints ORDER BY id DESC')
     complaints = cursor.fetchall()
     conn.close()
      return render_template('admin.html', complaints=complaints)     


@app.route('/update-status/<int:complaint_id>', methods=['POST'])
def update_status(complaint_id):
    new_status = request.form.get('status')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE complaints SET status = ? WHERE id = ?', (new_status, complaint_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/delete/<int:complaint_id>', methods=['POST'])
def delete_complaint(complaint_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM complaints WHERE id = ?', (complaint_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
# app.py — NO AUTH, NO ERRORS
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "gold2025"
DB = "girls.db"
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# CREATE TABLES
with get_db() as db:
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT, email TEXT UNIQUE, phone TEXT UNIQUE,
            password TEXT, role TEXT, created_at TEXT
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY,
            user_id INTEGER, path TEXT, approved INTEGER DEFAULT 0
        )
    ''')

# ADMIN ACCOUNT
with get_db() as db:
    admin = db.execute("SELECT * FROM users WHERE email=?", ("admin@datelock.ng",)).fetchone()
    if not admin:
        db.execute("INSERT INTO users (name,email,phone,password,role,created_at) VALUES (?,?,?,?,?,?)",
                   ("Boss Admin", "admin@datelock.ng", "08000000000", "admin123", "admin", datetime.now()))
        db.commit()
        print("ADMIN: admin@datelock.ng / admin123")

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    password = request.form['password']
    role = request.form['role']

    with get_db() as db:
        try:
            db.execute("INSERT INTO users (name,email,phone,password,role,created_at) VALUES (?,?,?,?,?,?)",
                       (name, email, phone, password, role, datetime.now()))
            db.commit()
            flash("Account created! Login now")
            return redirect("/")
        except:
            flash("Email or phone already used")
            return redirect("/register")

@app.route("/login", methods=["POST"])
def login():
    email = request.form['email']
    password = request.form['password']
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password)).fetchone()
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']
            return redirect("/dashboard")
    flash("Wrong email or password")
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect("/")
    user = get_db().execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    return render_template("dashboard.html", user=user)

@app.route("/queue")
def queue():
    with get_db() as db:
        girls = db.execute("""
            SELECT u.id, u.name, p.path 
            FROM users u JOIN photos p ON u.id = p.user_id 
            WHERE u.role='girl' AND p.approved=1
            LIMIT 10
        """).fetchall()
        return [{"id": g['id'], "name": g['name'], "photo": "/" + g['path']} for g in girls]

@app.route("/upload", methods=["POST"])
def upload():
    if 'user_id' not in session:
        return "Login required", 401
    file = request.files['file']
    filename = f"{uuid.uuid4().hex}.jpg"
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    with get_db() as db:
        db.execute("INSERT INTO photos (user_id, path) VALUES (?, ?)",
                   (session['user_id'], f"static/uploads/{filename}"))
        db.commit()
    return "Photo sent! Wait for approval"

@app.route("/admin")
def admin():
    if session.get('role') != 'admin':
        return "Access Denied", 403
    with get_db() as db:
        photos = db.execute("SELECT * FROM photos WHERE approved=0").fetchall()
    return render_template("admin.html", photos=photos)

@app.route("/approve/<int:pid>")
def approve(pid):
    if session.get('role') == 'admin':
        with get_db() as db:
            db.execute("UPDATE photos SET approved=1 WHERE id=?", (pid,))
            db.commit()
    return redirect("/admin")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    print("Starting DateLock NG...")
    print("Go to: http://localhost:5000")
    app.run(debug=True, port=5000)

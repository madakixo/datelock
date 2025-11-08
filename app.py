# app.py — LIVELY + AI + CHAT + MATCH
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, os, uuid, random
from datetime import datetime

app = Flask(__name__)
app.secret_key = "gold2025"
DB = "girls.db"
UPLOAD = "static/uploads"
os.makedirs(UPLOAD, exist_ok=True)

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# CREATE ALL TABLES
with db() as c:
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, phone TEXT, password TEXT, role TEXT, created TEXT);
        CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY, user_id INTEGER, path TEXT, approved INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, sender INTEGER, receiver INTEGER, msg TEXT, time TEXT);
        CREATE TABLE IF NOT EXISTS stories (id INTEGER PRIMARY KEY, user_id INTEGER, path TEXT, expires INTEGER);
        CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY, guy_id INTEGER, girl_id INTEGER);
    ''')

# ADMIN
with db() as c:
    if not c.execute("SELECT * FROM users WHERE email='admin@datelock.ng'").fetchone():
        c.execute("INSERT INTO users (name,email,phone,password,role,created) VALUES (?,?,?,?,?,?)",
                  ("Boss", "admin@datelock.ng", "08000000000", "admin123", "admin", datetime.now()))
        c.commit()
        print("ADMIN: admin@datelock.ng / admin123")

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/register")
def reg_page():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    with db() as c:
        try:
            c.execute("INSERT INTO users (name,email,phone,password,role,created) VALUES (?,?,?,?,?,?)",
                      (request.form['name'], request.form['email'], request.form['phone'],
                       request.form['password'], request.form['role'], datetime.now()))
            c.commit()
            flash("Registered!")
            return redirect("/")
        except:
            flash("Email/phone taken")
            return redirect("/register")

@app.route("/login", methods=["POST"])
def login():
    with db() as c:
        u = c.execute("SELECT * FROM users WHERE email=? AND password=?", 
                      (request.form['email'], request.form['password'])).fetchone()
        if u:
            session.update({'user_id': u['id'], 'name': u['name'], 'role': u['role']})
            return redirect("/dashboard")
    flash("Wrong login")
    return redirect("/")

@app.route("/dashboard")
def dash():
    if 'user_id' not in session: return redirect("/")
    user = db().execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    return render_template("dashboard.html", user=user)

@app.route("/queue")
def queue():
    girls = db().execute("""
        SELECT u.id, u.name, p.path FROM users u 
        JOIN photos p ON u.id=p.user_id 
        WHERE u.role='girl' AND p.approved=1 LIMIT 10
    """).fetchall()
    return [{"id":g['id'], "name":g['name'], "photo":"/"+g['path']} for g in girls]

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files['file']
    fn = f"{uuid.uuid4().hex}.jpg"
    file.save(f"{UPLOAD}/{fn}")
    with db() as c:
        c.execute("INSERT INTO photos (user_id, path) VALUES (?,?)",
                  (session['user_id'], f"static/uploads/{fn}"))
        c.commit()
    return "Sent for approval!"

@app.route("/admin")
def admin():
    if session.get('role') != 'admin': return "Denied", 403
    photos = db().execute("SELECT * FROM photos WHERE approved=0").fetchall()
    return render_template("admin.html", photos=photos)

@app.route("/approve/<int:pid>")
def approve(pid):
    if session.get('role') == 'admin':
        db().execute("UPDATE photos SET approved=1 WHERE id=?", (pid,))
        db().commit()
    return redirect("/admin")

@app.route("/chat/<int:girl_id>")
def chat(girl_id):
    girl = db().execute("SELECT * FROM users WHERE id=?", (girl_id,)).fetchone()
    msgs = db().execute("SELECT * FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY id",
                        (session['user_id'], girl_id, girl_id, session['user_id'])).fetchall()
    return render_template("chat.html", girl=girl, msgs=msgs)

@app.route("/send", methods=["POST"])
def send():
    with db() as c:
        c.execute("INSERT INTO messages (sender,receiver,msg,time) VALUES (?,?,?,?)",
                  (session['user_id'], request.form['girl_id'], request.form['msg'], datetime.now()))
        c.commit()
    return "sent"

@app.route("/matchme")
def matchme():
    if session.get('role') != 'guy': return "Guys only"
    girls = db().execute("SELECT * FROM users WHERE role='girl'").fetchall()
    matches = []
    for g in girls:
        photos = db().execute("SELECT COUNT(*) FROM photos WHERE user_id=? AND approved=1", (g['id'],)).fetchone()[0]
        score = photos * 15 + random.randint(10, 30)
        matches.append((score, g))
    matches.sort(reverse=True)
    return render_template("matchme.html", matches=matches[:3])

@app.route("/profile/<int:uid>")
def profile(uid):
    girl = db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    photos = db().execute("SELECT path FROM photos WHERE user_id=? AND approved=1", (uid,)).fetchall()
    comp = random.randint(72, 98)
    return render_template("profile.html", girl=girl, photos=photos, comp=comp)

@app.route("/top")
def top():
    top5 = db().execute("""
        SELECT u.name, COUNT(b.id)*15000 AS cash FROM users u
        LEFT JOIN bookings b ON u.id=b.girl_id
        WHERE u.role='girl' GROUP BY u.id ORDER BY cash DESC LIMIT 5
    """).fetchall()
    return render_template("top.html", top=top5)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    print("DATELOCK NG 2.0 LIVE")
    print("PC: http://localhost:5000")
    print("PHONE: http://YOUR-PC-IP:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)

# app.py — PAYSTACK + VIDEO CALL + LIVE LOCATION
from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit
import sqlite3, os, uuid, random
from datetime import datetime

app = Flask(__name__)
app.secret_key = "gold2025"
socketio = SocketIO(app, cors_allowed_origins="*")
DB = "girls.db"
UPLOAD = "static/uploads"
os.makedirs(UPLOAD, exist_ok=True)

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# TABLES
with db() as c:
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, phone TEXT, password TEXT, role TEXT);
        CREATE TABLE IF NOT EXISTS photos (id INTEGER PRIMARY KEY, user_id INTEGER, path TEXT, approved INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, ref TEXT, girl_id INTEGER, guy_id INTEGER, status TEXT);
    ''')

# ADMIN
with db() as c:
    if not c.execute("SELECT 1 FROM users WHERE email='admin@datelock.ng'").fetchone():
        c.execute("INSERT INTO users (name,email,phone,password,role) VALUES (?,?,?,?,?)",
                  ("Admin", "admin@datelock.ng", "08000000000", "admin123", "admin"))
        c.commit()

# ROUTES
@app.route("/")
def home():
    return render_template("login.html")

@app.route("/pay/<int:girl_id>")
def pay(girl_id):
    ref = str(uuid.uuid4())
    with db() as c:
        c.execute("INSERT INTO payments (ref, girl_id, guy_id, status) VALUES (?,?,?,?)",
                  (ref, girl_id, session.get('user_id'), "pending"))
        c.commit()
    return render_template("pay.html", ref=ref, girl_id=girl_id)

@app.route("/verify/<ref>")
def verify(ref):
    # Paystack verify (replace with your secret key)
    import requests
    headers = {"Authorization": "Bearer sk_test_YOUR_SECRET_KEY"}
    r = requests.get(f"https://api.paystack.co/transaction/verify/{ref}", headers=headers)
    if r.json().get("data", {}).get("status") == "success":
        with db() as c:
            c.execute("UPDATE payments SET status='paid' WHERE ref=?", (ref,))
            c.commit()
        return "<h1>UNLOCKED! WhatsApp: +2349012345678</h1>"
    return "<h1>Failed</h1>"

@app.route("/video/<int:girl_id>")
def video(girl_id):
    return render_template("video.html", girl_id=girl_id)

@app.route("/share_location", methods=["POST"])
def share_location():
    data = request.json
    socketio.emit("location", {"lat": data["lat"], "lng": data["lng"], "user": session['name']}, room=f"chat_{data['girl_id']}")
    return "sent"

# SOCKET EVENTS
@socketio.on("join")
def join(data):
    room = f"chat_{data['girl_id']}"
    emit("status", {"msg": f"{session['name']} joined"}, room=room)

@socketio.on("message")
def message(data):
    room = f"chat_{data['girl_id']}"
    emit("message", {"msg": data['msg'], "user": session['name']}, room=room)

if __name__ == "__main__":
    print("DATELOCK NG 3.0")
    print("Paystack + Video + Location")
    print("http://YOUR-PC-IP:5000")
    socketio.run(app, host="0.0.0.0", port=5000)

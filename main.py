import sys
import os

# import eventlet
# eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit
from database import DB_Functions as db
from datetime import datetime
app = Flask(__name__, static_folder='static')
socketio = SocketIO(app, cors_allowed_origins="*")
app.secret_key = os.urandom(24)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:eb564ff0@localhost:5432/studioa_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 1800
}

db.init_db(app)


@app.route('/')
def index():
    return redirect('/BG/')

@app.route('/BG/')
def index_BG():
    return render_template('/BG/index.html')

@app.route('/login', methods=['GET'])
def login():
    userName = request.cookies.get('username')
    return f"Login page. Cookie username={userName}", 200


if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=8001)
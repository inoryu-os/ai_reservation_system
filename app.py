import os
from flask import Flask, render_template, request, jsonify, url_for, redirect
from datetime import datetime, timedelta
from dotenv import load_dotenv

from config.rooms import ROOMS_CONFIG

load_dotenv()
import models

app = Flask(__name__)

user_name = "guest"

@app.route('/')
def index():
    models.init_db()
    rooms = models.get_all_rooms()
    return render_template('index.html', rooms=rooms, user_name=user_name)

@app.route('/api/reserve', methods=['POST'])
def create_reservation():
    data = request.get_json(silent=True) or {}
    room_id = data.get("room-id")
    date = data.get("date")
    start_time = data.get("start-time")
    end_time = data.get("end-time")


if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json
import os

# 🔧 First define the app
app = Flask(__name__)

# ✅ Now pass it to SocketIO (with eventlet)
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*')

DATA_FILE = 'data.json'
AUTH_PASSWORD = '12345687'  # 🔐 Change this for production security


def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    emit('refresh_list', load_data())


@socketio.on('add_delivery')
def handle_add(data):
    if data.get('password') != AUTH_PASSWORD:
        emit('auth_failed', {'action': 'add'})
        return
    entry = data.get('entry')
    if entry:
        deliveries = load_data()
        deliveries.append(entry)
        save_data(deliveries)
        emit('refresh_list', deliveries, broadcast=True)


@socketio.on('delete_delivery')
def handle_delete(data):
    if data.get('password') != AUTH_PASSWORD:
        emit('auth_failed', {'action': 'delete'})
        return
    target = data.get('entry')
    if target:
        deliveries = load_data()
        deliveries = [
            d for d in deliveries
            if not (d['delivery_date'] == target['delivery_date'] and
                    d['file_number'] == target['file_number'] and
                    d['party_name'] == target['party_name'])
        ]
        save_data(deliveries)
        emit('refresh_list', deliveries, broadcast=True)


@socketio.on('update_status')
def handle_update(data):
    if data.get('password') != AUTH_PASSWORD:
        emit('auth_failed', {'action': 'update'})
        return

    updated = data.get('entry')
    original = updated.pop('original')  # old values

    deliveries = load_data()
    for item in deliveries:
        if (item['delivery_date'] == original['delivery_date'] and
            item['file_number'] == original['file_number'] and
            item['party_name'] == original['party_name']):
            item.update(updated)
            break
    save_data(deliveries)
    emit('refresh_list', deliveries, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, debug=True)

import sqlite3
import uuid

import flask
from dotenv import load_dotenv
from flask import request
from flask_cors import CORS

from chat import delete_messages, get_messages, new_message, run_thread, wait_for_run

app = flask.Flask(__name__)
CORS(app, supports_credentials=True)

with app.app_context():
    load_dotenv()
    conn = sqlite3.connect('threads.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS threads (user_id text, thread_id text)")


@app.route('/api/v1/chat', methods=["POST"])
def chat():
    data = request.get_json()
    message = data["message"]
    user_id = request.cookies.get("user_id")
    if user_id is None:
        user_id = str(uuid.uuid4())

    new_message(user_id, message)
    run = run_thread(user_id)
    wait_for_run(user_id, run.id)

    messages = get_messages(user_id)
    res = flask.make_response(messages.model_dump_json())
    res.set_cookie("user_id", user_id, max_age=60 * 60 * 24 * 365)

    return res


@app.route('/api/v1/messages/<user_id>', methods=["GET"])
def get(user_id):
    return get_messages(user_id).model_dump_json()


@app.route('/api/v1/chat', methods=["DELETE"])
def delete():
    user_id = request.cookies.get("user_id")
    delete_messages(user_id)
    return "Deleted"

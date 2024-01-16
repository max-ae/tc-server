import os
import sqlite3
import time

from openai import Client

client = Client()


def new_thread(user_id):
    conn = sqlite3.connect('threads.db')
    c = conn.cursor()
    thread = client.beta.threads.create()
    c.execute("INSERT INTO threads VALUES (?, ?)", (user_id, thread.id))
    conn.commit()
    return thread


def get_thread(user_id):
    conn = sqlite3.connect('threads.db')
    c = conn.cursor()
    c.execute("SELECT thread_id FROM threads WHERE user_id=?", (user_id,))
    thread_id = c.fetchone()
    if thread_id is None:
        return None
    return thread_id[0]


def new_message(user_id, message):
    thread_id = get_thread(user_id)
    if thread_id is None:
        thread = new_thread(user_id)
        thread_id = thread.id
    client.beta.threads.messages.create(thread_id=thread_id, role='user', content=message)


def run_thread(user_id):
    thread_id = get_thread(user_id)
    if thread_id is None:
        return "No thread found"
    return client.beta.threads.runs.create(thread_id=thread_id, assistant_id=os.getenv("OPENAI_ASSISTANT_ID"))


def wait_for_run(user_id, run_id):
    thread_id = get_thread(user_id)
    if thread_id is None:
        return "No thread found"
    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status == "completed":
            break
        elif run.status == "failed":
            raise RuntimeError(run.last_error)
        else:
            time.sleep(1)


def get_messages(user_id):
    thread_id = get_thread(user_id)
    if thread_id is None:
        return "No thread found"
    return client.beta.threads.messages.list(thread_id=thread_id)


def delete_messages(user_id):
    conn = sqlite3.connect('threads.db')
    c = conn.cursor()
    c.execute("DELETE FROM threads WHERE user_id=?", (user_id,))
    conn.commit()

from flask import Flask, request, jsonify, abort
import sqlite3
import json

app = Flask(__name__)
DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)

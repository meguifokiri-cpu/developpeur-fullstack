from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector, os
import time

app = Flask(__name__)
CORS(app)

def db():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'todo_db'),
        port=os.getenv('DB_PORT', 3306)
    )

def init_db():
    time.sleep(2)
    c = db()
    cur = c.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY, 
        username VARCHAR(255) UNIQUE, 
        password VARCHAR(255))''')
    
    cur.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        status ENUM('todo', 'doing', 'done') DEFAULT 'todo',
        startDate DATETIME,
        user_id INT DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cur.execute("INSERT IGNORE INTO users (username, password) VALUES ('admin', '1234')")
    c.commit()
    c.close()

@app.route('/api/register', methods=['POST'])
def register():
    try:
        d = request.json
        c = db()
        cur = c.cursor()
        # On vérifie si l'utilisateur existe déjà
        cur.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (d['username'], d['password']))
        c.commit()
        c.close()
        return jsonify({'ok': True, 'message': 'Utilisateur créé !'}), 201
    except mysql.connector.Error as err:
        return jsonify({'ok': False, 'message': 'Cet identifiant est déjà pris'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    c = db()
    cur = c.cursor(dictionary=True)
    cur.execute('SELECT id, username FROM users WHERE username=%s AND password=%s', (d['username'], d['password']))
    user = cur.fetchone()
    c.close()
    return jsonify({'ok': True, 'user': user}) if user else (jsonify({'ok': False}), 401)

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    uid = request.args.get('user_id')
    c = db()
    cur = c.cursor(dictionary=True)
    cur.execute('SELECT * FROM tasks WHERE user_id=%s', (uid,))
    tasks = cur.fetchall()
    c.close()
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def add_task():
    try:
        data = request.json
        c = db()
        cursor = c.cursor()
        # Correction : On utilise data['startDate'] et data['user_id'] envoyés par le front
        cursor.execute("INSERT INTO tasks (title, startDate, status, user_id) VALUES (%s, %s, 'todo', %s)", 
                       (data['title'], data['startDate'], data['user_id']))
        c.commit()
        cursor.close()
        c.close()
        return jsonify({"ok": True}), 201
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/tasks/<int:i>', methods=['PUT'])
def update_status(i):
    new_status = request.json.get('status')
    c = db()
    cur = c.cursor()
    cur.execute('UPDATE tasks SET status=%s WHERE id=%s', (new_status, i))
    c.commit()
    c.close()
    return jsonify({'ok': 1})

@app.route('/api/tasks/<int:i>', methods=['DELETE'])
def delete_task(i):
    c = db()
    cur = c.cursor()
    cur.execute('DELETE FROM tasks WHERE id=%s', (i,))
    c.commit()
    c.close()
    return jsonify({'ok': 1})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
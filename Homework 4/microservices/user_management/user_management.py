import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_PATH = 'user_profiles.db'


class UserRepository:
    def __init__(self, db_path):
        self.db_path = db_path

    def find_user(self, username):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT email, phone, resume FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            if row:
                return {'email': row[0], 'phone': row[1], 'resume': row[2]}
            return None

    def update_user(self, username, email, phone, resume):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET email = ?, phone = ?, resume = ? WHERE username = ?',
                (email, phone, resume, username)
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise ValueError('User not found or no changes made.')


# Instantiate UserRepository
user_repository = UserRepository(DB_PATH)


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    print("vlegov")
    if not username or not password:
        return jsonify({'error': 'Both username and password are required.'}), 400

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            if row and row[0] == password:
                return jsonify({'message': 'Login successful'}), 200
            elif row:
                return jsonify({'error': 'Incorrect password.'}), 401
            else:
                return jsonify({'error': 'Username does not exist.'}), 404
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500


@app.route('/profile', methods=['GET'])
def get_profile():
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Username is required'}), 400

    user = user_repository.find_user(username=username)
    if user:
        return jsonify({
            'email': user.get('email'),
            'phone': user.get('phone'),
            'resume': user.get('resume')
        }), 200
    else:
        return jsonify({'error': 'User not found'}), 404


@app.route('/update_profile', methods=['POST'])
def update_profile():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    phone = data.get('phone')
    resume = data.get('resume')

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    try:
        user_repository.update_user(username=username, email=email, phone=phone, resume=resume)
        return jsonify({'message': 'Profile updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not password or not email:
        return jsonify({'error': 'Username, email, and password are required.'}), 400

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Check if the username already exists
            cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                return jsonify({'error': 'The username is already taken.'}), 400

            # Check if the email already exists
            cursor.execute('SELECT 1 FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                return jsonify({'error': 'The email is already registered.'}), 400

            # Insert the new user
            cursor.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, password)
            )
            conn.commit()
            return jsonify({'message': 'Signup successful!'}), 201
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
    # app.run(debug=True, port=5001)

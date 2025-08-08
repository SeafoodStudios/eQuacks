from flask import Flask, request
from filelock import FileLock
import json
import hashlib
import os
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
database_path = "equacks_database.json"
lock_path = "equacks_database.lock"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
lock = FileLock(lock_path)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["10 per minute"]
)

@app.route('/create_account', methods=['POST'])
def create_account():
    try:
        with lock:
            if request.is_json:
                data = request.json
            else:
                data = request.form
            username = data.get('username')
            password = data.get('password')

            if not isinstance(username, str):
                return "Username must be string.", 400
            if not isinstance(password, str):
                return "Password must be string.", 400

            if len(username) > 50:
                return "Username cannot be longer than 50 characters.", 400
            if len(password) > 50:
                return "Password cannot be longer than 50 characters.", 400

            if not os.path.exists(database_path):
                with open(database_path, "w") as f:
                    json.dump({}, f)

            with open(database_path, 'r') as f:
                database = json.load(f)

            if username in database:
                return "Username taken. Pick another one.", 400

            hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            database[username] = {"password": hashed_password, "balance": 0}

            temp_path = database_path + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(database, f)
            os.rename(temp_path, database_path)

            logging.info(f"Account successfully created: {username}")
            return '<p>Success, user added!</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>', 200
    except Exception as e:
        logging.error("Account unsuccessfully created: " + str(e))
        return "Generic error.", 500
@app.route('/delete_account', methods=['POST'])
def delete_account():
    try:
        with lock:
            if request.is_json:
                data = request.json
            else:
                data = request.form
            username = data.get('username')
            password = data.get('password')

            if not isinstance(username, str):
                return "Username must be string.", 400
            if not isinstance(password, str):
                return "Password must be string.", 400

            if len(username) > 50:
                return "Username cannot be longer than 50 characters.", 400
            if len(password) > 50:
                return "Password cannot be longer than 50 characters.", 400

            if not os.path.exists(database_path):
                with open(database_path, "w") as f:
                    json.dump({}, f)

            with open(database_path, 'r') as f:
                database = json.load(f)

            if not username in database:
                return "User does not exist.", 400

            hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if not database[username]["password"] == hashed_password:
                return "Incorrect password.", 400

            balance = database[username]['balance']
            del database[username]

            temp_path = database_path + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(database, f)
            os.rename(temp_path, database_path)

            logging.info(f"Account successfully deleted: {username} with a balance of {balance}.")
            return '<p>Success, user deleted!</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>', 200
    except Exception as e:
        logging.error("Account unsuccessfully deleted: " + str(e))
        return "Generic error.", 500
@app.route('/transfer_currency', methods=['POST'])
def transfer_currency():
    try:
        with lock:
            if request.is_json:
                data = request.json
            else:
                data = request.form
            username = data.get('username')
            password = data.get('password')
            receiver = data.get('receiver')
            amount = data.get('amount')

            if not isinstance(username, str):
                return "Username must be string.", 400
            if not isinstance(password, str):
                return "Password must be string.", 400
            if not isinstance(receiver, str):
                return "Receiver must be string.", 400
            if not isinstance(amount, str):
                return "Amount must be string.", 400

            if amount.isdigit():
                if int(amount) > 0:
                    amount = int(amount)
                else:
                    return "Amount must be larger than zero.", 400
            else:
                return "Amount must be a digit.", 400

            if len(username) > 50:
                return "Username cannot be longer than 50 characters.", 400
            if len(password) > 50:
                return "Password cannot be longer than 50 characters.", 400
            if len(receiver) > 50:
                return "Receiver cannot be longer than 50 characters.", 400

            if not os.path.exists(database_path):
                with open(database_path, "w") as f:
                    json.dump({}, f)

            with open(database_path, 'r') as f:
                database = json.load(f)

            if not username in database:
                return "User does not exist.", 400
            if not receiver in database:
                return "Receiver does not exist.", 400

            hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if not database[username]["password"] == hashed_password:
                return "Incorrect password.", 400

            if not database[username]['balance'] >= amount:
                return "You don't have enough currency to make this transaction.", 400

            if username == receiver:
                return "You cannot transfer currency to yourself.", 400

            database[username]['balance'] = database[username]['balance'] - amount
            database[receiver]['balance'] = database[receiver]['balance'] + amount

            temp_path = database_path + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(database, f)
            os.rename(temp_path, database_path)

            logging.info(f"Transaction successfully sent from {username} to {receiver} with an amount of {amount}.")
            return '<p>Success, transaction sent!</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>', 200
    except Exception as e:
        logging.error("Transaction unsuccessfully sent: " + str(e))
        return "Generic error.", 500
@app.route('/get_balance', methods=['POST'])
def get_balance():
    try:
        with lock:
            if request.is_json:
                data = request.json
            else:
                data = request.form
            username = data.get('username')
            password = data.get('password')

            if not isinstance(username, str):
                return "Username must be string.", 400
            if not isinstance(password, str):
                return "Password must be string.", 400

            if len(username) > 50:
                return "Username cannot be longer than 50 characters.", 400
            if len(password) > 50:
                return "Password cannot be longer than 50 characters.", 400

            if not os.path.exists(database_path):
                with open(database_path, "w") as f:
                    json.dump({}, f)

            with open(database_path, 'r') as f:
                database = json.load(f)

            if not username in database:
                return "User does not exist.", 400

            hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if not database[username]["password"] == hashed_password:
                return "Incorrect password.", 400

            balance = str(database[username]['balance'])

            logging.info(f"{username} successfully counted a balance of {balance}.")
            return f"""<p>You have {balance} currency.</p> <a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 200
    except Exception as e:
        logging.error(f"{username} unsuccessfully counted their balance. " + str(e))
        return "Generic error.", 500
@app.route('/ping', methods=['GET'])
def ping():
    try:
        return "Pinged!", 200
    except:
        return "Generic error.", 500

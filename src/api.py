from flask import Flask, request
from filelock import FileLock
import json
import hashlib
import os
import time
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from markupsafe import escape
import requests

ph = PasswordHasher()
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
                return """<p>Username cannot be longer than 50 characters.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400
            if len(password) > 50:
                return """<p>Password cannot be longer than 50 characters.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400

            if not os.path.exists(database_path):
                with open(database_path, "w") as f:
                    json.dump({}, f)

            with open(database_path, 'r') as f:
                database = json.load(f)

            if username in database:
                return """<p>Username taken. Pick another one.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400

            hashed_password = ph.hash(password)
            database[username] = {"password": hashed_password, "balance": 0}

            temp_path = database_path + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(database, f)
            os.rename(temp_path, database_path)

            logging.info(f"Account successfully created: {username}")
            return '<p>Success, user added!</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>', 200
    except Exception as e:
        logging.error("Account unsuccessfully created: " + str(e))
        return """<p>Generic error.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 500
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
                return """<p>Username cannot be longer than 50 characters.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400
            if len(password) > 50:
                return """<p>Password cannot be longer than 50 characters.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400

            if not os.path.exists(database_path):
                with open(database_path, "w") as f:
                    json.dump({}, f)

            with open(database_path, 'r') as f:
                database = json.load(f)

            if not username in database:
                return """<p>User does not exist.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400

            try:
                ph.verify(database[username]["password"], password)
            except VerifyMismatchError:
                logging.error(f"{username} unsuccessfully logged in because of invalid password.")
                return """<p>Incorrect password.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400

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
        return """<p>Generic error.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 500
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
                    return """<p>Amount must be larger than zero.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400
            else:
                return """<p>Amount must be a digit.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400

            if len(username) > 50:
                return """<p>Username cannot be longer than 50 characters.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400
            if len(password) > 50:
                return """<p>Password cannot be longer than 50 characters.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400
            if len(receiver) > 50:
                return """<p>Receiver cannot be longer than 50 characters.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400

            if not os.path.exists(database_path):
                with open(database_path, "w") as f:
                    json.dump({}, f)

            with open(database_path, 'r') as f:
                database = json.load(f)

            if not username in database:
                return """<p>User does not exist.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400
            if not receiver in database:
                return """<p>Receiver does not exist.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400

            try:
                ph.verify(database[username]["password"], password)
            except VerifyMismatchError:
                logging.error(f"{username} unsuccessfully logged in because of invalid password.")
                return """<p>Incorrect password.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400

            if not database[username]['balance'] >= amount:
                return """<p>You don't have enough currency to make this transaction.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400

            if username == receiver:
                return """<p>You cannot transfer currency to yourself.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400

            database[username]['balance'] = database[username]['balance'] - amount
            database[receiver]['balance'] = database[receiver]['balance'] + amount

            temp_path = database_path + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(database, f)
            os.rename(temp_path, database_path)

            record_data = {
                "password": os.environ.get("record_db_password"),
                "record": f"""{username} sent {receiver} {amount} eQuacks on {int(time.time())} Unix time."""
            }
            record_response = requests.post("https://equacksrecord.pythonanywhere.com/submit_record", json=record_data)
            if record_response.status_code == 200:
                logging.info(f"Transaction successfully sent from {username} to {receiver} with an amount of {amount}.")
                return f"""<p>Success, transaction sent!</p><p>Permanent transaction receipt:</p><a href="{escape('https://equacksrecord.pythonanywhere.com/get_record/' + record_response.text)}">{escape('https://equacksrecord.pythonanywhere.com/get_record/' + record_response.text)}</a><br><br><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 200
            else:
                logging.info(f"Transaction successfully sent from {username} to {receiver} with an amount of {amount}. But, receipt could not be made because {escape(record_response.text)}.")
                return """<p>Success, transaction sent! But, the receipt could not be made.<p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 200
    except Exception as e:
        logging.error("Transaction unsuccessfully sent: " + str(e))
        return """<p>Generic error.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 500
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
                return """<p>Username cannot be longer than 50 characters.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400
            if len(password) > 50:
                return """<p>Password cannot be longer than 50 characters.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400

            if not os.path.exists(database_path):
                with open(database_path, "w") as f:
                    json.dump({}, f)

            with open(database_path, 'r') as f:
                database = json.load(f)

            if not username in database:
                return """<p>User does not exist.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400

            try:
                ph.verify(database[username]["password"], password)
            except VerifyMismatchError:
                logging.error(f"{username} unsuccessfully logged in because of invalid password.")
                return """<p>Incorrect password.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 400

            balance = str(database[username]['balance'])

            logging.info(f"{username} successfully counted a balance of {balance}.")
            return f"""<p>You have {balance} eQuack/s.</p> <a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 200
    except Exception as e:
        logging.error(f"{username} unsuccessfully counted their balance. " + str(e))
        return """<p>Generic error.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 500
@app.route('/ping', methods=['GET'])
def ping():
    try:
        return "Pinged!", 200
    except:
        return "Generic error.", 500
@app.route('/total_supply', methods=['GET'])
def total_supply():
    try:
        if not os.path.exists(database_path):
            with open(database_path, "w") as f:
                json.dump({}, f)

        with open(database_path, 'r') as f:
            database = json.load(f)

        supply = 0

        for user in database:
            supply += database[user]['balance']

        return f"""<p>There is a total supply of {supply} eQuack/s.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 200

    except Exception as e:
        logging.error(f"Unsuccessfully counted the total supply." + str(e))
        return """<p>Generic error.</p><a href="https://equacks.seafoodstudios.com/">Go back to homepage</a>""", 500

from flask import Flask, request
import json
import secrets
import os
from markupsafe import escape
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from filelock import FileLock

app = Flask(__name__)
limiter = Limiter(app=app, key_func=get_remote_address)

admin_password = os.environ.get("secret_password")
record_db_path = "equacks_record_db.json"

lock = FileLock(record_db_path + ".lock")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@limiter.limit("100 per minute")
@app.route('/submit_record', methods=["POST"])
def submit_record():
    with lock:
        try:
            if request.is_json:
                data = request.json
            else:
                data = request.form

            record = data.get('record')
            password = data.get('password')

            if not isinstance(password, str):
                return "Password must be string", 400

            if not password == admin_password:
                return "Invalid password. Please note that only admins should use this.", 400

            if not isinstance(record, str):
                return "Record must be a string.", 400

            if len(record) > 200:
                return "Record is too long.", 400

            if os.path.exists(record_db_path):
                with open(record_db_path, 'r') as f:
                    database = json.load(f)
            else:
                database = {}

            unique_id = str(secrets.token_urlsafe(32))
            database[unique_id] = record

            temp_path = record_db_path + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(database, f)
            os.replace(temp_path, record_db_path)

            logger.info(f"ID '{unique_id}' successfully recorded.")
            return unique_id, 200
        except Exception as e:
            logger.error(str(e))
            return "Internal error.", 500

@limiter.limit("10 per minute")
@app.route('/get_record/<path:subpath>', methods=["GET"])
def get_record(subpath):
    if not os.path.exists(record_db_path):
        return "Record does not exist.", 404

    with lock:
        with open(record_db_path, 'r') as f:
            database = json.load(f)

    if not isinstance(subpath, str):
        return "Record must be string.", 400

    if not subpath in database:
        return "Record does not exist.", 404

    return f"""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.7/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.7/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        body {{
          margin: 0;
          height: 100vh;
          display: flex;
          justify-content: center;
          align-items: center;
          flex-direction: column;
        }}

        p, h1, h2, h3, h4, h5, h6 {{
          text-align: center;
          margin: 0.5em 0;
        }}
    </style>
    <h1>eQuacks Record</h1>
    <h2>{escape(database[subpath])}</h2>
    """, 200

from flask import Flask, request, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from groq import Groq
from wonderwords import RandomWord
from better_profanity import profanity
from markupsafe import escape
import os
import json
import requests
import logging
from filelock import FileLock, Timeout

lock_path = "riddle.txt.lock"
riddle_lock = FileLock(lock_path, timeout=20)

profanity.load_censor_words()
app = Flask(__name__)
client = Groq(api_key=os.getenv('faucet_secret_groq_api_key'))
r = RandomWord()
riddle_path = "riddle.txt"
faucet_username = os.getenv('faucet_username')
faucet_password = os.getenv('faucet_password')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
def global_key():
    return "global"

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[]
)

logger = logging.getLogger(__name__)

@app.route('/guess', methods=['POST'])
@limiter.limit("20 per minute", key_func=global_key)
@limiter.limit("30 per hour")
def guess():
    with riddle_lock:
        try:
            if request.is_json:
                data = request.json
            else:
                data = request.form
            username = data.get('username')
            guess = data.get('guess')

            if not (isinstance(username, str) and isinstance(guess, str)):
                return "Both fields must be strings.", 400

            if not os.path.exists(riddle_path):
                while True:
                    answer = r.word()
                    if not profanity.contains_profanity(answer):
                        break

                completion = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": f"""Create a riddle on '{answer}'. Make a different answer anytime. Make the riddle moderately hard but solvable. When appropriate, you can include ducks in the riddle. Do not make any other comments like 'Here is your riddle' or 'Here you go!'. Only the riddle please."""}]
                )
                riddle = completion.choices[0].message.content

                default_riddle = {
                    "riddle": riddle,
                    "answer": answer
                }


                temp_path = riddle_path + ".tmp"
                with open(temp_path, "w") as f:
                    json.dump(default_riddle, f)
                os.replace(temp_path, riddle_path)
                return "Riddle initialized, please try again.", 409

            with open(riddle_path, 'r') as f:
                riddle_data = json.load(f)

            if guess.lower() == riddle_data["answer"].lower():
                payload = {
                    "username": faucet_username,
                    "password": faucet_password,
                    "receiver": username,
                    "amount": "5"
                }
                try:
                    reward_response = requests.post("https://equacks.pythonanywhere.com/transfer_currency", data=payload)
                    if not reward_response.status_code == 200:
                        logger.error(f"'{username}' could not recieve the currency after getting the answer right because '{reward_response.text}'")
                        return """<p>Reward could not be sent because the username was incorrect or there are internal issues.</p> <a href="https://equacksfaucet.pythonanywhere.com/">Go back to faucet</a>""", 400
                except Exception as e:
                    logger.error(f"'{username}' could not recieve the currency after getting the answer right because '{e}'")
                    return "Could not provide the currency because server could not be contacted.", 500

                while True:
                    answer = r.word()
                    if not profanity.contains_profanity(answer):
                        break

                completion = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": f"""Create a riddle on '{answer}'. Make a different answer anytime. Make the riddle moderately hard but solvable. When appropriate, you can include ducks in the riddle. Do not make any other comments like 'Here is your riddle' or 'Here you go!'. Only the riddle please."""}]
                )
                riddle = completion.choices[0].message.content

                default_riddle = {
                    "riddle": riddle,
                    "answer": answer
                }

                temp_path = riddle_path + ".tmp"
                with open(temp_path, "w") as f:
                    json.dump(default_riddle, f)
                os.replace(temp_path, riddle_path)
                logger.info(f"'{username}' guessed the riddle of '{riddle}' with the answer '{answer}' correctly! The reward was successfully sent to them.")
                return """<p>Correct answer! Five eQuacks have been sent to the winner.</p><a href="https://equacksfaucet.pythonanywhere.com/">Go back to faucet</a>""", 200
            else:
                return """<p>Wrong answer.</p><a href="https://equacksfaucet.pythonanywhere.com/">Go back to faucet</a>""", 400
        except Exception as e:
            logger.error(str(e))
            return "Internal error.", 500
@app.route('/riddle', methods=['GET'])
@limiter.limit("20 per minute", key_func=global_key)
def riddle():
    with riddle_lock:
        try:
            with open(riddle_path, 'r') as f:
                riddle_data = json.load(f)
            return escape(str(riddle_data["riddle"])), 200
        except Exception as e:
            logger.error(str(e))
            return "Internal error.", 500
@app.route('/', methods=['GET'])
def index():
    with riddle_lock:
        try:
            with open(riddle_path, 'r') as f:
                riddle_data = json.load(f)
            return render_template('index.html', riddle = escape(str(riddle_data["riddle"])))
        except Exception as e:
            logger.error(str(e))
            return "Internal error.", 500

from flask import Flask
from threading import Thread
import logging

# Disable Flask logging to avoid conflicts
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

@app.route('/healthz')
def health_check():
    return {"status": "healthy", "message": "Telegram bot is running"}

def run():
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
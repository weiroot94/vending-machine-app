# main.py
import os
from flask import Flask
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from src.route.route import setup_routes
from src.api.api import Api
from src.database.dbconnection import init_connection_pool
from src.database.autopatch import DatabaseUpdater
from src.controller.controller import get_ads
import threading
import subprocess
import base64
from flask_socketio import SocketIO

# Load .env file
load_dotenv()
debug_mode = os.getenv('DEBUG', 'False').lower() in ['true']
fullscreen_mode = os.getenv('FULLSCREEN', 'False').lower() in ['true']
api_server = os.getenv('WEB_API_SERVER')

# Create Flask App
app = Flask(__name__)

# Configure app to create JWT
app.config['JWT_SECRET_KEY'] = os.getenv('QRSECRET')
jwt = JWTManager(app)

# Create websocket
socketio = SocketIO(app)

# Configure Flask app
db_directory = os.path.join(os.getcwd(), 'db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(os.path.join(db_directory, 'vm.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Setup routes
setup_routes(app, socketio, debug_mode)

# Create Database connection Pool
init_connection_pool()

# Real-time Patch
db_updater = DatabaseUpdater(api_server)

# Create ad video file
ads = get_ads()
ad_path = "static/video/ads/ad.mp4"
os.makedirs(os.path.dirname(ad_path), exist_ok=True)
with open(ad_path, "wb") as f:
    f.write(base64.b64decode(ads.ads))

# Start CCtalk in separate thread
if(debug_mode == False):
    from src.cctalk.cctalk_note_vend import *
    print(Note(8).connect_mech())
    cctalk_thread = threading.Thread(target=poll_device, args=())
    cctalk_thread.start()

def open_browser():
    url = 'http://localhost:5000'
    chrome_path = ''
    if debug_mode == True:
        chrome_path = '/usr/bin/google-chrome'
    else:
        chrome_path = '/usr/bin/chromium-browser'
        
    chrome_flags = [
    '--disable-background-networking',
    '--disable-background-timer-throttling',
    '--disable-renderer-backgrounding',
    '--disable-gpu',
    '--disable-gpu-compositing'
    ]

    if (fullscreen_mode == True) :
        chrome_flags.append('--kiosk')
        chrome_command = [chrome_path] + chrome_flags + [url]
        subprocess.Popen(chrome_command)
    else :
        chrome_command = [chrome_path] + chrome_flags + [url]
        subprocess.Popen(chrome_command)

# window = webview.create_window("Vending Machine", app, js_api=api, width=1100, height=1920, fullscreen=fullscreen_mode, gui='chrome')

if __name__ == '__main__':
    # webview.start(http_server=True, http_port=3000, debug=debug_mode)
    threading.Timer(1, open_browser).start()
    socketio.run(app, allow_unsafe_werkzeug=True)

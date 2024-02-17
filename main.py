from flask import Flask, request, redirect, url_for, session, render_template
from flask_socketio import SocketIO, emit
import msal
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a strong secret key
socketio = SocketIO(app)

# Microsoft Authentication Configuration
CLIENT_ID = 'your_client_id_here'  # Replace with your registered application's client ID
CLIENT_SECRET = 'your_client_secret_here'  # Replace with your registered application's client secret
AUTHORITY = 'https://login.microsoftonline.com/common'
REDIRECT_PATH = '/get_token'
SCOPE = ['User.Read']

# Custom Minecraft Server Configuration
CUSTOM_SERVER_IP = 'your_custom_server_ip_here'
CUSTOM_SERVER_PORT = 25565

# Token cache to store user tokens
token_cache = msal.SerializableTokenCache()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    auth_url = _build_auth_url()
    return redirect(auth_url)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/get_token')
def get_token():
    token_response = _get_token(request.url)
    
    if 'error' in token_response:
        return f"Error: {token_response['error_description']}"
    
    session['user'] = token_response['id_token_claims']['preferred_username']
    session['access_token'] = token_response['access_token']
    
    return redirect(url_for('home'))

@socketio.on('connect')
def handle_connect():
    if 'user' in session:
        emit('authenticated', {'user': session['user']})

@socketio.on('join_custom_server')
def handle_join_custom_server():
    if 'user' in session:
        emit('redirect_custom_server', {'ip': CUSTOM_SERVER_IP, 'port': CUSTOM_SERVER_PORT})

def _build_auth_url():
    auth_client = msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY,
    )

    auth_url = auth_client.get_authorization_request_url(
        scopes=SCOPE,
        redirect_uri=url_for('get_token', _external=True),
    )

    return auth_url

def _get_token(redirect_url):
    auth_client = msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY,
        token_cache=token_cache,
    )

    token_response = auth_client.acquire_token_by_authorization_code(
        request.args['code'],
        scopes=SCOPE,
        redirect_uri=url_for('get_token', _external=True),
    )

    return token_response

if __name__ == '__main__':
    socketio.run(app, debug=True)

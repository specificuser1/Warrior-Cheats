import os, json, requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback_key')

# Config File Path
CONFIG_PATH = 'data/config.json'

# Load Config
def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)

# Admin Login Decorator
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# Get Discord Member Count
def get_discord_members():
    guild_id = os.getenv('DISCORD_GUILD_ID')
    if not guild_id:
        return "5000+"
    try:
        # Using Discord Public API (No Bot Token Needed for Basic Info)
        url = f"https://discord.com/api/v9/guilds/{guild_id}/widget.json"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            presence_count = data.get('presence_count', 0)
            return f"{presence_count}+" if presence_count > 0 else "1000+"
    except:
        pass
    return "5000+"  # Fallback

# Routes
@app.route('/')
def home():    config = load_config()
    member_count = get_discord_members()
    return render_template('index.html', 
                         config=config, 
                         members=member_count,
                         site_name=os.getenv('SITE_NAME', 'WARRIOR CHEATS'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == os.getenv('ADMIN_PASSWORD'):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        return render_template('admin.html', error="❌ Wrong Password!")
    return render_template('admin.html', error=None)

@app.route('/admin/panel')
@admin_required
def admin_panel():
    config = load_config()
    return render_template('admin.html', config=config, admin_mode=True)

@app.route('/api/update-status', methods=['POST'])
@admin_required
def update_status():
    data = request.json
    config = load_config()
    region = data.get('region')
    state = data.get('state')  # online, offline, custom
    text = data.get('text', 'Operational')
    
    if region in config['status']:
        config['status'][region]['state'] = state
        config['status'][region]['text'] = text
        save_config(config)
        return jsonify({'success': True, 'message': f'{region} updated!'})
    return jsonify({'success': False, 'error': 'Invalid region'}), 400

@app.route('/api/update-links', methods=['POST'])
@admin_required
def update_links():
    data = request.json
    config = load_config()
    config['links'].update(data)
    save_config(config)
    return jsonify({'success': True, 'message': 'Links updated!'})

@app.route('/api/discord-sync', methods=['POST'])
@admin_requireddef discord_sync():
    # Trigger bot to refresh status (optional webhook)
    return jsonify({'success': True, 'message': 'Sync signal sent!'})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

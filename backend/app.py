# backend/app.py
from flask import Flask, request, jsonify, send_from_directory
from FileSystem import FileSystem
from QuotaManager import QuotaManager
from flask_cors import CORS 
import os 

qm = QuotaManager()
fs = FileSystem(qm)

app = Flask(__name__, static_folder='../frontend', static_url_path='') 
CORS(app) 

@app.route('/')
def serve_index(): return send_from_directory('../frontend', 'index.html')

@app.route('/register', methods=['POST'])
def register():
    if fs.current_user: return jsonify({'message': f"HATA: Lütfen logout olun.", 'success': False})
    data = request.json
    response_msg = fs.register_user(data.get('user_id'), data.get('password'))
    return jsonify({'message': response_msg, 'success': 'HATA' not in response_msg})

@app.route('/login', methods=['POST'])
def login():
    if fs.current_user: return jsonify({'message': f"HATA: Lütfen logout olun.", 'success': False})
    data = request.json
    response_msg = fs.login(data.get('user_id'), data.get('password'))
    return jsonify({'message': response_msg, 'success': 'Başarıyla' in response_msg})

@app.route('/create_file', methods=['POST'])
def create_file_api():
    if not fs.current_user: return jsonify({'message': "HATA: Giriş yapın.", 'success': False})
    data = request.json
    try: response_msg = fs.create_file(data.get('file_path'), float(data.get('size_mb')))
    except Exception as e: return jsonify({'message': str(e), 'success': False})
    return jsonify({'message': response_msg, 'success': 'BAŞARILI' in response_msg})

@app.route('/write_file', methods=['POST'])
def write_file_api():
    if not fs.current_user: return jsonify({'message': "HATA: Giriş yapın.", 'success': False})
    data = request.json
    response_msg = fs.write_to_file(data.get('file_path'), data.get('content'))
    return jsonify({'message': response_msg, 'success': 'BAŞARILI' in response_msg})

@app.route('/read_file', methods=['POST'])
def read_file_api():
    if not fs.current_user: return jsonify({'message': "HATA: Giriş yapın.", 'success': False})
    content = fs.read_file(request.json.get('file_path'))
    is_success = not (content.startswith("HATA") or content.startswith("Erişim"))
    return jsonify({'message': content, 'success': is_success})

@app.route('/execute_file', methods=['POST'])
def execute_file_api():
    if not fs.current_user: return jsonify({'message': "HATA: Giriş yapın.", 'success': False})
    response_msg = fs.execute_file(request.json.get('file_path'))
    return jsonify({'message': response_msg, 'success': False})

@app.route('/delete_file', methods=['POST'])
def delete_file_api():
    if not fs.current_user: return jsonify({'message': "HATA: Giriş yapın.", 'success': False})
    response_msg = fs.delete_file(request.json.get('file_path'))
    return jsonify({'message': response_msg, 'success': 'BAŞARILI' in response_msg})

@app.route('/ls', methods=['GET'])
def list_files_api():
    if not fs.current_user: return jsonify({'message': "HATA: Giriş yapın.", 'success': False})
    return jsonify({'message': fs.list_files(), 'success': True})

@app.route('/status', methods=['GET'])
def get_status_api():
    if not fs.current_user: return jsonify({'message': "HATA: Giriş yapın.", 'success': False})
    return jsonify({'message': fs.get_user_status(), 'success': True})

@app.route('/logout', methods=['POST'])
def logout_api():
    if not fs.current_user: return jsonify({'message': "HATA: Oturum yok.", 'success': False})
    return jsonify({'message': fs.logout(), 'success': True})

# --- ADMIN ---
@app.route('/list_users', methods=['GET'])
def list_users_api():
    if fs.current_user != 'admin': return jsonify({'message': "HATA: Admin yetkisi gerekli.", 'success': False})
    return jsonify({'message': fs.list_users(), 'success': True})

@app.route('/delete_user/<user_id>', methods=['DELETE'])
def delete_user_api(user_id):
    if fs.current_user != 'admin': return jsonify({'message': "HATA: Admin yetkisi gerekli.", 'success': False})
    return jsonify({'message': fs.delete_user(user_id), 'success': True})

@app.route('/set_quota', methods=['POST'])
def set_quota_api():
    if fs.current_user != 'admin': return jsonify({'message': "HATA: Admin yetkisi gerekli.", 'success': False})
    data = request.json
    try: response_msg = fs.set_user_quota(data.get('user_id'), float(data.get('quota_mb')))
    except ValueError: return jsonify({'message': "HATA: Kota sayı olmalı.", 'success': False})
    return jsonify({'message': response_msg, 'success': 'HATA' not in response_msg})

if __name__ == '__main__': pass
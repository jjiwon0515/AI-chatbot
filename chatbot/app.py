from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)  # 모든 요청에 대해 CORS 허용

# 데이터베이스 연결 함수
def get_db_connection():
    conn = sqlite3.connect('unibot_extended.db')  # DB 파일 경로
    conn.row_factory = sqlite3.Row  # row_factory로 딕셔너리 형식 반환
    return conn

# restaurants 데이터를 반환하는 API
@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    conn = get_db_connection()
    restaurants = conn.execute('SELECT * FROM restaurants').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in restaurants])  # 리스트로 반환

# liberal_arts 데이터를 반환하는 API
@app.route('/liberal_arts', methods=['GET'])
def get_liberal_arts():
    conn = get_db_connection()
    liberal_arts = conn.execute('SELECT * FROM liberal_arts').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in liberal_arts])  # 리스트로 반환

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

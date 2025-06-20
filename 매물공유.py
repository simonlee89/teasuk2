from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
from datetime import datetime
import os
import json

app = Flask(__name__)

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('property_links.db')
    cursor = conn.cursor()
    
    # 링크 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            platform TEXT NOT NULL,
            added_by TEXT NOT NULL,
            date_added TEXT NOT NULL,
            rating INTEGER DEFAULT 5,
            liked BOOLEAN DEFAULT 0,
            disliked BOOLEAN DEFAULT 0,
            memo TEXT DEFAULT '',
            customer_name TEXT DEFAULT '000',
            move_in_date TEXT DEFAULT ''
        )
    ''')
    
    # 고객 정보 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_info (
            id INTEGER PRIMARY KEY,
            customer_name TEXT DEFAULT '000',
            move_in_date TEXT DEFAULT ''
        )
    ''')
    
    # 기본 고객 정보 삽입
    cursor.execute('INSERT OR IGNORE INTO customer_info (id, customer_name, move_in_date) VALUES (1, "제일좋은집 찾아드릴분", "")')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('property_links.db')
    cursor = conn.cursor()
    
    # 고객 정보 가져오기
    cursor.execute('SELECT customer_name, move_in_date FROM customer_info WHERE id = 1')
    customer_info = cursor.fetchone()
    customer_name = customer_info[0] if customer_info else '제일좋은집 찾아드릴분'
    move_in_date = customer_info[1] if customer_info else ''
    
    conn.close()
    
    return render_template('index.html', customer_name=customer_name, move_in_date=move_in_date)

@app.route('/api/customer_info', methods=['GET', 'POST'])
def customer_info():
    conn = sqlite3.connect('property_links.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        data = request.json
        customer_name = data.get('customer_name', '제일좋은집 찾아드릴분')
        move_in_date = data.get('move_in_date', '')
        
        cursor.execute('UPDATE customer_info SET customer_name = ?, move_in_date = ? WHERE id = 1', 
                      (customer_name, move_in_date))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    
    else:
        cursor.execute('SELECT customer_name, move_in_date FROM customer_info WHERE id = 1')
        info = cursor.fetchone()
        conn.close()
        
        return jsonify({
            'customer_name': info[0] if info else '제일좋은집 찾아드릴분',
            'move_in_date': info[1] if info else ''
        })

@app.route('/api/links', methods=['GET', 'POST'])
def links():
    conn = sqlite3.connect('property_links.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        data = request.json
        url = data.get('url')
        platform = data.get('platform')
        added_by = data.get('added_by')
        memo = data.get('memo', '')
        
        if not url or not platform or not added_by:
            return jsonify({'success': False, 'error': '필수 정보가 누락되었습니다.'})
        
        date_added = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT INTO links (url, platform, added_by, date_added, memo)
            VALUES (?, ?, ?, ?, ?)
        ''', (url, platform, added_by, date_added, memo))
        
        conn.commit()
        link_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'id': link_id})
    
    else:
        # 필터 파라미터
        platform_filter = request.args.get('platform', 'all')
        user_filter = request.args.get('user', 'all')
        like_filter = request.args.get('like', 'all')
        date_filter = request.args.get('date', '')
        
        query = 'SELECT * FROM links WHERE 1=1'
        params = []
        
        if platform_filter != 'all':
            query += ' AND platform = ?'
            params.append(platform_filter)
        
        if user_filter != 'all':
            query += ' AND added_by = ?'
            params.append(user_filter)
        
        if like_filter == 'liked':
            query += ' AND liked = 1'
        elif like_filter == 'disliked':
            query += ' AND disliked = 1'
        
        if date_filter:
            query += ' AND date_added = ?'
            params.append(date_filter)
        
        query += ' ORDER BY id DESC'
        
        cursor.execute(query, params)
        links_data = cursor.fetchall()
        conn.close()
        
        links_list = []
        for link in links_data:
            links_list.append({
                'id': link[0],
                'url': link[1],
                'platform': link[2],
                'added_by': link[3],
                'date_added': link[4],
                'rating': link[5],
                'liked': bool(link[6]),
                'disliked': bool(link[7]),
                'memo': link[8] if len(link) > 8 else ''
            })
        
        return jsonify(links_list)

@app.route('/api/links/<int:link_id>', methods=['PUT', 'DELETE'])
def update_link(link_id):
    conn = sqlite3.connect('property_links.db')
    cursor = conn.cursor()
    
    if request.method == 'PUT':
        data = request.json
        action = data.get('action')
        
        if action == 'rating':
            rating = data.get('rating', 5)
            cursor.execute('UPDATE links SET rating = ? WHERE id = ?', (rating, link_id))
        
        elif action == 'like':
            liked = data.get('liked', False)
            cursor.execute('UPDATE links SET liked = ?, disliked = ? WHERE id = ?', 
                          (liked, False if liked else 0, link_id))
        
        elif action == 'dislike':
            disliked = data.get('disliked', False)
            cursor.execute('UPDATE links SET disliked = ?, liked = ? WHERE id = ?', 
                          (disliked, False if disliked else 0, link_id))
        
        elif action == 'memo':
            memo = data.get('memo', '')
            cursor.execute('UPDATE links SET memo = ? WHERE id = ?', (memo, link_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM links WHERE id = ?', (link_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})

@app.route('/api/backup', methods=['GET'])
def backup_data():
    """데이터베이스 내용을 JSON으로 백업"""
    try:
        conn = sqlite3.connect('property_links.db')
        cursor = conn.cursor()
        
        backup_data = {
            'backup_date': datetime.now().isoformat(),
            'links': [],
            'customer_info': None
        }
        
        # 링크 데이터 백업
        cursor.execute('SELECT * FROM links')
        links = cursor.fetchall()
        
        # 컬럼 이름 가져오기
        cursor.execute("PRAGMA table_info(links)")
        columns = [row[1] for row in cursor.fetchall()]
        
        for link in links:
            link_dict = dict(zip(columns, link))
            backup_data['links'].append(link_dict)
        
        # 고객 정보 백업
        cursor.execute('SELECT * FROM customer_info')
        customer = cursor.fetchone()
        if customer:
            cursor.execute("PRAGMA table_info(customer_info)")
            customer_columns = [row[1] for row in cursor.fetchall()]
            backup_data['customer_info'] = dict(zip(customer_columns, customer))
        
        conn.close()
        
        return jsonify(backup_data)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/restore', methods=['POST'])
def restore_data():
    """JSON 백업 데이터로 데이터베이스 복원"""
    try:
        backup_data = request.json
        
        if not backup_data or 'links' not in backup_data:
            return jsonify({'success': False, 'error': '잘못된 백업 데이터입니다.'})
        
        conn = sqlite3.connect('property_links.db')
        cursor = conn.cursor()
        
        # 기존 데이터 삭제
        cursor.execute('DELETE FROM links')
        cursor.execute('DELETE FROM customer_info')
        
        # 고객 정보 복원
        if backup_data.get('customer_info'):
            customer_info = backup_data['customer_info']
            cursor.execute('''
                INSERT INTO customer_info (id, customer_name, move_in_date)
                VALUES (?, ?, ?)
            ''', (
                customer_info.get('id', 1),
                customer_info.get('customer_name', '제일좋은집 찾아드릴분'),
                customer_info.get('move_in_date', '')
            ))
        else:
            # 기본 고객 정보 삽입
            cursor.execute('INSERT INTO customer_info (id, customer_name, move_in_date) VALUES (1, "제일좋은집 찾아드릴분", "")')
        
        # 링크 데이터 복원
        for link_data in backup_data['links']:
            cursor.execute('''
                INSERT INTO links (url, platform, added_by, date_added, rating, liked, disliked, memo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                link_data.get('url', ''),
                link_data.get('platform', 'other'),
                link_data.get('added_by', 'unknown'),
                link_data.get('date_added', datetime.now().strftime('%Y-%m-%d')),
                link_data.get('rating', 5),
                link_data.get('liked', 0),
                link_data.get('disliked', 0),
                link_data.get('memo', '')
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'{len(backup_data["links"])}개의 링크가 복원되었습니다.'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000) 
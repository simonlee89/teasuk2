import sqlite3
import json
from datetime import datetime

def backup_data():
    """데이터베이스 내용을 JSON 파일로 백업"""
    if not os.path.exists('property_links.db'):
        print("데이터베이스 파일이 없습니다.")
        return
    
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
    
    # JSON 파일로 저장
    filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    print(f"백업 완료: {filename}")
    print(f"총 {len(backup_data['links'])}개의 링크가 백업되었습니다.")
    return filename

if __name__ == "__main__":
    import os
    backup_data() 
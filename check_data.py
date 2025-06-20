import sqlite3
import os

if os.path.exists('property_links.db'):
    conn = sqlite3.connect('property_links.db')
    cursor = conn.cursor()
    
    # 테이블 구조 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"테이블: {tables}")
    
    # links 테이블 데이터 확인
    cursor.execute('SELECT COUNT(*) FROM links')
    count = cursor.fetchone()[0]
    print(f"총 {count}개의 링크가 저장되어 있습니다.")
    
    if count > 0:
        cursor.execute('SELECT * FROM links LIMIT 5')
        rows = cursor.fetchall()
        print("\n최근 5개 링크:")
        for row in rows:
            print(f"- ID: {row[0]}, URL: {row[1][:50]}..., 플랫폼: {row[2] if len(row) > 2 else 'N/A'}")
    
    # 고객 정보 확인
    cursor.execute('SELECT * FROM customer_info')
    customer = cursor.fetchone()
    if customer:
        print(f"\n고객 정보: {customer}")
    
    conn.close()
else:
    print("property_links.db 파일이 없습니다.") 
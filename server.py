#!/usr/bin/env python3
"""
발표자료 리뷰 서버
- 프레젠테이션 파일 서빙
- 메모 저장/조회 API
- 실시간 메모 확인 가능

실행: python3 server.py
접속: http://localhost:8000
"""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

NOTES_FILE = 'review_notes.json'
PORT = 8000

class ReviewServer(SimpleHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)

        # API: 메모 조회
        if parsed.path == '/api/notes':
            self.send_json_response(load_notes())

        # API: 특정 슬라이드 메모 조회
        elif parsed.path.startswith('/api/notes/'):
            slide_key = parsed.path.replace('/api/notes/', '')
            notes = load_notes()
            self.send_json_response(notes.get(slide_key, {}))

        # 관리자 페이지: 전체 메모 보기
        elif parsed.path == '/admin':
            self.send_admin_page()

        # 일반 파일 서빙
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)

        # API: 메모 저장
        if parsed.path == '/api/notes':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            notes = load_notes()
            slide_key = data.get('key')
            note_content = data.get('note', '').strip()
            slide_info = data.get('slideInfo', '')

            if note_content:
                notes[slide_key] = {
                    'note': note_content,
                    'slideInfo': slide_info,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                notes.pop(slide_key, None)

            save_notes(notes)
            self.send_json_response({'success': True, 'message': '저장됨'})

        # API: 전체 메모 삭제
        elif parsed.path == '/api/notes/clear':
            save_notes({})
            self.send_json_response({'success': True, 'message': '전체 삭제됨'})

        else:
            self.send_error(404)

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def send_admin_page(self):
        notes = load_notes()

        # 슬라이드 순서대로 정렬
        sorted_keys = sorted(notes.keys(), key=lambda x: (
            int(x.split('_')[1]) if len(x.split('_')) > 1 else 0,
            int(x.split('_')[2]) if len(x.split('_')) > 2 else 0
        ))

        html = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>리뷰 메모 관리</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f3f4f6;
            padding: 30px;
            line-height: 1.6;
        }
        .header {
            background: white;
            padding: 25px 30px;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 {
            color: #1f2937;
            font-size: 24px;
        }
        .refresh-info {
            color: #6b7280;
            font-size: 14px;
        }
        .stats {
            background: #3b82f6;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
        }
        .notes-container {
            display: grid;
            gap: 20px;
        }
        .note-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            border-left: 4px solid #3b82f6;
        }
        .note-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .slide-info {
            font-weight: 700;
            color: #1f2937;
            font-size: 16px;
        }
        .timestamp {
            color: #9ca3af;
            font-size: 13px;
        }
        .note-content {
            background: #f9fafb;
            padding: 15px;
            border-radius: 8px;
            color: #374151;
            white-space: pre-wrap;
            font-size: 15px;
        }
        .empty-state {
            text-align: center;
            padding: 60px;
            color: #9ca3af;
        }
        .empty-state h2 {
            font-size: 20px;
            margin-bottom: 10px;
            color: #6b7280;
        }
        .btn {
            display: inline-block;
            padding: 10px 20px;
            background: #ef4444;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
        }
        .btn:hover { background: #dc2626; }
        .actions { margin-top: 20px; text-align: right; }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>발표자료 리뷰 메모</h1>
            <button class="btn" style="background:#3b82f6;margin-left:10px;" onclick="location.reload()">🔄 새로고침</button>
        </div>
        <span class="stats">총 ''' + str(len(notes)) + '''개 메모</span>
    </div>
'''

        if notes:
            html += '<div class="notes-container">'
            for key in sorted_keys:
                data = notes[key]
                html += f'''
    <div class="note-card">
        <div class="note-header">
            <span class="slide-info">{data.get('slideInfo', key)}</span>
            <span class="timestamp">{data.get('timestamp', '')}</span>
        </div>
        <div class="note-content">{data.get('note', '')}</div>
    </div>
'''
            html += '</div>'
            html += '''
    <div class="actions">
        <button class="btn" onclick="if(confirm('모든 메모를 삭제하시겠습니까?')) fetch('/api/notes/clear', {method:'POST'}).then(()=>location.reload())">
            전체 삭제
        </button>
    </div>
'''
        else:
            html += '''
    <div class="empty-state">
        <h2>아직 작성된 메모가 없습니다</h2>
        <p>발표자가 리뷰 모드에서 메모를 작성하면 여기에 표시됩니다.</p>
    </div>
'''

        html += '</body></html>'

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_notes(notes):
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    print(f'''
╔══════════════════════════════════════════════════════════╗
║           발표자료 리뷰 서버 시작                          ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  발표자료:  http://localhost:{PORT}/presentation_2.html    ║
║  메모확인:  http://localhost:{PORT}/admin                  ║
║                                                          ║
║  종료: Ctrl+C                                            ║
╚══════════════════════════════════════════════════════════╝
''')

    server = HTTPServer(('0.0.0.0', PORT), ReviewServer)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n서버 종료')
        server.shutdown()
